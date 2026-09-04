# NetworkManager and changes

Reading the network is safe and needs no root; changing it is where care comes
in. On Pridwen the desktop's connections are managed by NetworkManager, and
`nmcli` is how you change them so the change survives a reconnect.

`nmcli connection show` lists the saved connections; `nmcli device status` shows
what each interface is doing now. To change one, `nmcli connection modify name`
sets a property, and `nmcli connection up name` reapplies it. A change made with
`ip` directly lasts only until NetworkManager next touches the interface.

```
$ nmcli connection show
NAME     UUID        TYPE      DEVICE
home     6f1a...     wifi      wlp3s0
$ nmcli -f GENERAL,IP4 device show wlp3s0 | head
```

From your own desktop session, polkit lets you manage your connections without
sudo; system-wide connections and some device operations still need `sudo
nmcli`. For a quick, deliberately temporary change, `ip` is fine and honest
about being temporary. The rule of thumb: `nmcli` for anything you want to keep,
`ip` for a throwaway test you expect to vanish.

## Try it

1. Run `nmcli device status` and read the state of each interface.
2. Run `nmcli connection show` and find the active connection's name.
3. Inspect one connection with `nmcli connection show name | less`.
4. Explain why an `ip addr add` change would not survive a reconnect.
