# User units and drop-ins

systemd runs a manager for each logged-in user as well as the system one. Your
user manager handles units under `~/.config/systemd/user/`, and you control them
with `systemctl --user`, which needs no root because they are yours.

This matters because `sudo systemctl --user` talks to root's user manager, not
yours, and usually fails to find it. Drop the sudo for your own units and keep
it for system ones. A user service is a tidy way to run a personal background
task, and it can start at login.

```
$ systemctl --user status
$ mkdir -p ~/.config/systemd/user
$ systemctl --user daemon-reload
$ systemctl --user enable --now myjob.service
```

Rather than editing a shipped unit, add a drop-in. `systemctl edit name` opens a
small override file under `/etc/systemd/system/name.service.d/` that changes only
the lines you set, and it survives image updates because it lives in `/etc`.
This is the same mechanism Pridwen itself uses to adjust stock services without
touching the read-only copies in `/usr`.

## Try it

1. Run `systemctl --user list-units` and see what your session runs.
2. Try `sudo systemctl --user status` and read why it behaves oddly.
3. Create a simple `~/.config/systemd/user/hello.service` and enable it.
4. Run `systemctl edit chronyd` to see the drop-in editor (quit without saving).
