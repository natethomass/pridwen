# Staying after a reboot

Persistence is how an attacker keeps access after a reboot or after a password
changes, and knowing the mechanisms is exactly how a defender finds them.
Almost every method reuses a legitimate way to start a program automatically,
which is the whole trick: the same places you would use to start a service are
the places an attacker hides in, so the defender's map and the attacker's map
are the same map.

Everything here runs only against Range targets you own: Rocky 9 lab hosts you
start with `pridwen enter rocky`, where you may plant a harmless startup entry,
reboot, and hunt it down. You never install startup entries on a system you do
not control. On a real job this is why knowing your own startup surface cold is
worth more than any single tool: a new entry only stands out if you know what
belonged there.

## Words you'll meet

- **persistence**: any mechanism that re-launches an attacker's program automatically, surviving logout or reboot.
- **unit file**: the systemd file that defines a service or timer; a system one lives under `/etc/systemd/system`.
- **user unit**: a unit that runs under one account, kept in `{home}/.config/systemd/user/`, started at that user's login.
- **enabled**: set to start automatically; distinct from merely running now.
- **autostart**: the desktop mechanism that launches programs at login from `.desktop` files under an autostart directory.
- **shell profile**: files like `{home}/.bashrc` that the shell runs at login, another place to hide a launch line.

## How it works

The honest tour of startup places is short, and enumerating it is the skill.
Start with enabled units at the system level. The `list-unit-files` subcommand
lists every installed unit and whether it is set to start, and `--state=enabled`
keeps only the ones that will:

```
{user}@{host}:~$ systemctl list-unit-files --state=enabled | head -n 5
UNIT FILE                  STATE
auditd.service             enabled
firewalld.service          enabled
sshd.service               disabled
NetworkManager.service     enabled
```

Read that back. The left column is the unit's name, the right column is its
state. Every line here is a legitimate service Pridwen ships. The defender's job
is to know this list well enough that an unfamiliar name jumps out. Note `sshd`
is `disabled`, matching Pridwen's default of no remote login.

A per-user attacker does not need root; they can drop a unit under their own
account, which starts at their login. You list those with `--user`, which asks
about the user's own systemd instance:

```
{user}@{host}:~$ systemctl --user list-unit-files --state=enabled
UNIT FILE            STATE
pridwend.service     enabled
```

Here `--user` switches from the system manager to the one that runs as you, and
the single expected entry is Pridwen's own Coach daemon. Anything else you did
not add is worth a look. The other hiding places are the desktop autostart
folder and the shell profiles, which you read directly:

```
{user}@{host}:~$ ls -la {home}/.config/autostart {home}/.config/systemd/user
```

On a Range host you plant a benign user service, reboot, confirm it came back,
then hunt it down from the defender's side using these same listings. The lesson
is that persistence hides in plain sight among legitimate startup entries, so
the defence is simply knowing your own startup surface.

## When it goes wrong

`Failed to connect to bus` when you run `systemctl --user` over SSH means no
user session bus is set up for that non-interactive login. Log in at the desktop
or set `XDG_RUNTIME_DIR` for the session, then re-run the user listing.

`ls: cannot access '{home}/.config/autostart': No such file or directory` just
means that folder does not exist yet, which is normal on a fresh account; it is
not an error, only an empty hiding place.

A long enabled-units list is expected, not a red flag by itself; the finding is
an entry you cannot account for. Run `pridwen explain systemctl` if a subcommand
or flag is the unclear part.

## Try it

1. On a Range host, list enabled system units with `systemctl list-unit-files --state=enabled` and skim the names.
2. List enabled user units with `systemctl --user list-unit-files --state=enabled` and note what belongs.
3. Plant a harmless user service that runs at login, then reboot and confirm it started.
4. Find it again from the defender's side using the same listings.
5. List the categories of startup location an attacker could use on this host.

## Remember

- Persistence reuses legitimate startup features, so the attacker's hiding places and the defender's checklist are identical.
- The main categories are system units, user units under `{home}/.config/systemd/user/`, desktop autostart, and shell profiles.
- The defence is knowing your own startup surface well enough that one unfamiliar entry stands out at a glance.
