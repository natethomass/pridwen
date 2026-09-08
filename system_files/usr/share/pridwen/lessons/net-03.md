# NetworkManager and changes

Reading the network is safe and needs no special rights. Changing it is
where care comes in, because a wrong address or a deleted route cuts you off
from the machine you are working on. On Pridwen the desktop's connections
are managed by NetworkManager, the service that watches your interfaces,
talks to the router, and applies saved settings whenever a link comes up.

The command-line front end for NetworkManager is `nmcli`. It matters for two
reasons. A change made through `nmcli` is saved, so it survives a reconnect
and a reboot. And on a real job, servers without a desktop are configured
with exactly the same `nmcli` commands, so learning it here transfers
directly to Rocky and RHEL.

## Words you'll meet

- **NetworkManager**: the service that owns network configuration on the desktop and applies saved settings to interfaces.
- **nmcli**: the command-line tool that talks to NetworkManager.
- **device**: an interface as NetworkManager sees it, such as `wlp3s0`.
- **connection**: a saved profile of settings, such as your home Wi-Fi with its password and DNS choices; one device uses one connection at a time.
- **property**: a single setting inside a connection, like `ipv4.method` or `ipv4.dns`.
- **polkit**: the desktop's permission service; it decides which actions a logged-in user may take without `sudo`.
- **reapply**: bringing a connection down and up so a changed property takes effect.

## How it works

Two listing commands cover most of what you need. `nmcli device status`
shows what each interface is doing right now; `nmcli connection show` lists
the saved profiles.

```
{user}@{host}:~$ nmcli device status
DEVICE  TYPE      STATE                   CONNECTION
wlp3s0  wifi      connected               home
lo      loopback  connected (externally)  lo
```

`STATE` says `connected` when the device has an active connection, and the
`CONNECTION` column names it. `disconnected` means no profile is applied,
and `unavailable` means the hardware is off or has no link.

```
{user}@{host}:~$ nmcli connection show
NAME  UUID                                  TYPE  DEVICE
home  6f1a2b3c-9d8e-4f70-a1b2-c3d4e5f60718  wifi  wlp3s0
lo    2a7c0e91-7f3b-4d8a-9b1c-0e5f6a7b8c9d  loopback  lo
```

Each saved connection has a `NAME` you type in commands, a `UUID` that never
changes even if you rename it, a `TYPE`, and the `DEVICE` it is active on. A
connection with an empty `DEVICE` column is saved but not in use.

To look inside one connection, ask for the fields you care about. The `-f`
flag chooses which sections to print, and `device show` reports the live
state of a device.

```
{user}@{host}:~$ nmcli -f GENERAL,IP4 device show wlp3s0
GENERAL.DEVICE:       wlp3s0
GENERAL.TYPE:         wifi
GENERAL.STATE:        100 (connected)
GENERAL.CONNECTION:   home
IP4.ADDRESS[1]:       192.168.1.42/24
IP4.GATEWAY:          192.168.1.1
IP4.DNS[1]:           192.168.1.1
```

These are the same facts `ip -br addr` and `ip route` showed in the earlier
lesson, seen from NetworkManager's side. `IP4.DNS[1]` is the server the
router handed out; systemd-resolved then wraps queries to it in DNS over TLS
where the server supports it.

Changing a setting is a two-step pattern: modify the saved property, then
reapply the connection so the change takes effect.

```
{user}@{host}:~$ nmcli connection modify home ipv4.dns "1.1.1.1 1.0.0.1"
{user}@{host}:~$ nmcli connection up home
Connection successfully activated (D-Bus active path: /org/freedesktop/NetworkManager/ActiveConnection/5)
```

`modify` takes the connection name, then a property, then its new value. It
prints nothing on success. `up` brings the connection up again, which drops
and restores the link for a second; the success line confirms it. Because
this is saved, the next reboot uses the new DNS servers too.

Compare that with `ip addr add`, which changes the running kernel only. It
is honest about being temporary: the moment NetworkManager reconnects the
interface, its saved profile wins and the hand change is gone. That makes
`ip` fine for a throwaway test and wrong for anything you want to keep.

Permissions follow polkit. From your own desktop session you may modify and
reapply your own connections without `sudo`, because polkit trusts the person
sitting at the machine. System-wide connections, and some device operations,
still need `sudo nmcli`. From a remote or text-only session, polkit is
stricter and `sudo` is needed for most changes.

## When it goes wrong

`Error: unknown connection 'Home'.` means the name did not match; names are
case-sensitive. `nmcli connection show` lists the exact spelling, and you can
use the `UUID` instead of the name in any command.

`Error: Failed to modify connection 'home': Insufficient privileges.`
means polkit did not allow the change from this session. Run the command again
with `sudo nmcli`. The Coach notes this under the failed command and
`pridwen why` explains which sessions polkit trusts.

`RTNETLINK answers: Operation not permitted` comes from `ip` when you try to
change an address or route without root. Even with `sudo`, NetworkManager
will undo that change on the next reconnect, so if you meant it to last,
use `nmcli connection modify` instead. `pridwen explain nmcli` annotates the
`-f` flag and the `modify` and `up` verbs if you need them spelled out.

## Try it

1. Type `nmcli device status` and read the `STATE` of each device. Note which connection your main interface uses.
2. Type `nmcli connection show` and find the row whose `DEVICE` column is filled; that is the active connection. Note its `NAME`.
3. Type `nmcli -f GENERAL,IP4 device show wlp3s0`, using your own device name, and compare `IP4.ADDRESS[1]` with what `ip -br addr` shows.
4. Type `nmcli connection show home | less`, using your own connection name, and page through the properties with the space bar; press `q` to leave.
5. Type `nmcli connection modify home connection.autoconnect yes` and confirm it prints nothing, which is success. This sets a property that is almost certainly already `yes`, so nothing changes.
6. Explain in one sentence why `sudo ip addr add 192.168.1.99/24 dev wlp3s0` would not survive a reconnect.

## Remember

- `nmcli device status` shows live state; `nmcli connection show` lists saved profiles.
- Change with `nmcli connection modify name property value`, then `nmcli connection up name` to apply it; the change is saved.
- `ip` changes last only until NetworkManager next touches the interface; use it for throwaway tests only.
