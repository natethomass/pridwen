# Units and systemctl

On a modern Fedora system, background services are managed by systemd. Each
service is described by a unit file, and `systemctl` is the one command you use
to inspect and control them. Reading state never needs root; changing it does.

`systemctl status name` is the most useful view. It shows whether the unit is
loaded, whether it is enabled for boot, whether it is active now, and the last
few lines it logged. `systemctl list-units` shows what is loaded, and
`list-unit-files` shows what is installed and its enabled state.

```
$ systemctl status chronyd
* chronyd.service - NTP client/server
     Loaded: loaded (/usr/lib/systemd/system/chronyd.service; enabled)
     Active: active (running) since Thu 2026-09-04 09:00:11
```

Unit files live in three places, searched in order: `/etc/systemd/system` for
local overrides, `/run/systemd/system` for runtime, and
`/usr/lib/systemd/system` for the ones shipped in the image. Because `/usr` is
read-only on Pridwen, your changes go in `/etc`, and `systemctl edit name`
creates a drop-in there for you. After editing a unit by hand, run
`systemctl daemon-reload` so systemd rereads it.

## Try it

1. Run `systemctl status chronyd` and name the Loaded and Active lines.
2. List failed units with `systemctl --failed` and hope it is empty.
3. Run `systemctl list-unit-files | grep enabled | head` to see boot services.
4. Run `systemctl cat chronyd` to read the unit file it loaded.
