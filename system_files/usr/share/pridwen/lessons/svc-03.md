# User units and drop-ins

systemd, the service manager, runs one manager for the whole system as pid 1,
and it also starts a separate, smaller manager for each person who logs in.
That second one is your user manager. It runs as you, it owns your session's
background pieces, and it can run units of your own. A unit is one thing
systemd manages, described by a small text file. You control your user manager
with `systemctl --user`, and because everything under it belongs to you, it
never needs root.

This matters for two reasons. First, a user unit is the tidy way to run a
personal background task that starts at login, with a name, a log, and a clean
stop, instead of a loose background job. Second, the same idea of layering a
small change on top of a shipped file, called a drop-in, is how Pridwen itself
adjusts stock services without touching the read-only copies in `/usr`, and it
is how you will change a service on any Fedora or RHEL machine at work.

## Words you'll meet

- **system manager**: the systemd process with pid 1 that runs the system's services as root.
- **user manager**: a systemd process started for you at login that runs units as you.
- **user unit**: a unit file in `~/.config/systemd/user/` that your user manager loads.
- **bus**: the message channel a `systemctl` command uses to talk to a manager; each manager has its own.
- **drop-in**: a file under `name.service.d/` that overrides a few lines of a unit without replacing it.
- **default.target**: the user manager's "logged in" target; enabling a user unit hangs it off this.
- **oneshot**: a service type for a command that runs once and exits instead of staying up.

## How it works

Start by looking at what your user manager already runs. Every `--user`
command is the same `systemctl` you know, pointed at your own manager.

```
{user}@{host}:~$ systemctl --user list-units --type=service | head -n 5
  UNIT                          LOAD   ACTIVE SUB     DESCRIPTION
  dbus-broker.service           loaded active running D-Bus User Message Bus
  gnome-session-manager@gnome.service loaded active running GNOME Session Manager (session: gnome)
  pipewire.service              loaded active running PipeWire Multimedia Service
  pridwend.service              loaded active running Pridwen coach daemon
```

`--type=service` keeps only services. UNIT is the name, LOAD says the file
was read, ACTIVE and SUB are the coarse and fine state, and DESCRIPTION is
from the unit file. `pridwend`, the Pridwen coach that prints hints under
failed commands, is a user unit like these: it runs as you, not as root.

Now make one of your own. User units live in `~/.config/systemd/user/`, which
may not exist yet; `mkdir -p` creates the whole path and does nothing if it is
already there. This unit prints one line and exits, so it is `Type=oneshot`.

```
{user}@{host}:~$ mkdir -p {home}/.config/systemd/user
{user}@{host}:~$ cat > {home}/.config/systemd/user/hello.service <<'EOF'
[Unit]
Description=Say hello at login

[Service]
Type=oneshot
ExecStart=/usr/bin/echo hello from {user}

[Install]
WantedBy=default.target
EOF
{user}@{host}:~$ systemctl --user daemon-reload
{user}@{host}:~$ systemctl --user enable --now hello.service
Created symlink {home}/.config/systemd/user/default.target.wants/hello.service → {home}/.config/systemd/user/hello.service.
```

The `cat > file <<'EOF'` form writes everything up to the line `EOF` into
the file. `[Unit]` describes it, `[Service]` says what to run and how, and
`[Install]` says where it hooks in when enabled: `WantedBy=default.target`
means "start at login". `daemon-reload` makes the manager read the new file,
and `enable --now` creates the link for future logins and runs it once now. The
`Created symlink` line is the enable happening, exactly as with system units,
only under your home instead of `/etc`. Check what it printed with `journalctl
--user -u hello.service`, which reads your user manager's part of the journal.

```
{user}@{host}:~$ journalctl --user -u hello.service -n 3
Sep 07 10:41:12 {host} systemd[1820]: Starting hello.service - Say hello at login...
Sep 07 10:41:12 {host} echo[5310]: hello from {user}
Sep 07 10:41:12 {host} systemd[1820]: Finished hello.service - Say hello at login.
```

The middle line is the program's output, captured by the journal; the number
in `systemd[1820]` is your user manager's pid, not 1.

One thing catches everyone: `sudo systemctl --user`. `sudo` runs the command
as root, and `--user` then asks for root's user manager, which usually does
not exist, so the command fails to connect. Drop the `sudo` for your own units
and keep it for system ones. The two managers are separate on purpose, so that
a user can run things without any power over the system.

To change a shipped system unit, add a drop-in rather than editing or copying
it. `sudo systemctl edit name` opens an editor on
`/etc/systemd/system/name.service.d/override.conf`, an empty file where you
put only the section and lines you want to change; systemd merges them over
the original, which stays untouched under `/usr`. `systemctl cat name` then
shows the shipped file followed by the drop-in. Because `/etc` survives image
updates on Pridwen (it is merged across upgrades, while `/usr` is replaced
whole), your change stays even when a new image arrives. The same command with
`--user` edits a drop-in for one of your own units, under
`~/.config/systemd/user/`.

```
{user}@{host}:~$ sudo systemctl edit chronyd
```

Quit the editor without saving to leave the unit as it was. `pridwen explain
systemctl` annotates the `--user` and `edit` forms.

## When it goes wrong

`Failed to connect to bus: No medium found` after `sudo systemctl --user` means
root has no user manager to talk to. Run the same command without `sudo`.

`Unit hello.service could not be found.` from `systemctl --user` means the
file is not in `~/.config/systemd/user/` or the manager has not read it yet.
Check the path and the `.service` suffix, then `systemctl --user daemon-reload`.

`hello.service: Failed to execute /usr/bin/echoo: No such file or directory`
in the journal means the `ExecStart=` path is wrong; it must be an absolute
path to a real program. Fix the line, `daemon-reload`, and start it again.
`pridwen why` walks through the last one you hit.

## Try it

1. Run `systemctl --user list-units --type=service` and find `pridwend.service` in the list.
2. Run `sudo systemctl --user status`, read the bus error, then run it without `sudo`.
3. Create `~/.config/systemd/user/hello.service` as shown, `daemon-reload`, and `enable --now` it.
4. Run `journalctl --user -u hello.service` and find your hello line.
5. Run `systemctl --user disable hello.service` and watch the symlink be removed.
6. Run `sudo systemctl edit chronyd`, look at the empty override file, and quit without saving.

## Remember

- Your user manager runs units as you from `~/.config/systemd/user/`; `systemctl --user` controls it with no root.
- Never `sudo systemctl --user`: root's user manager is not yours.
- Change shipped units with a drop-in from `systemctl edit`, which lives in `/etc` and survives image updates.
