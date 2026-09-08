# Alerts that reach you

A detection that no one reads is not much of a detection. The watches and
baselines from the last two lessons produce a record, but a record sits still
until someone looks. The last step is turning a noticed event into a message
that reaches a person. On Pridwen that means a desktop notification through
Dispatch, the same channel the Coach uses; on a server it means a high-priority
log line that a monitoring system watches for.

On a job, this is the difference between finding out on Monday morning and
finding out in the two minutes that mattered. This lesson runs on your own host,
where the notification lands on your desktop; the same script with the
`notify-send` line removed is what you would install on a Rocky 9 Range host
you own, arriving in milestone M4, where the journal line is the alert.

## Words you'll meet

- **timer**: a systemd unit that starts another unit on a schedule, the modern form of cron.
- **user unit**: a systemd unit that runs as you, under `systemctl --user`, without root.
- **logger**: the command that writes a line into the journal with a chosen facility and priority.
- **priority**: how urgent a log line is, from `debug` up to `emerg`; `warning` and above stand out.
- **notify-send**: the command that pops a desktop notification.
- **Dispatch**: Pridwen's notification layer; `pridwen dispatch test` sends one so you can see the shape.

## How it works

Start with the check itself, a short script that tests one specific condition
and does two things when it is true: writes a journal line and sends a
notification. Put it in `{home}/.local/bin`, which is on your PATH.

```
{user}@{host}:~$ mkdir -p {home}/.local/bin
{user}@{host}:~$ cat > {home}/.local/bin/detect-4444 <<'EOF'
#!/usr/bin/bash
if ss -tuln | grep -q ':4444'; then
    logger -p auth.warning -t detect "unexpected listener on 4444"
    notify-send "Detection" "Unexpected listener on port 4444"
fi
EOF
{user}@{host}:~$ chmod +x {home}/.local/bin/detect-4444
```

`cat > file <<'EOF'` writes everything up to the line `EOF` into the file. The
script runs `ss -tuln` (listening TCP and UDP sockets, numeric ports, no `-p`
because a process name is not needed and `-p` would want root) and `grep -q`
(quiet: exit 0 if the pattern is found, print nothing). `logger -p
auth.warning` sets the facility to `auth` and the priority to `warning`, and
`-t detect` tags the line so it can be filtered. `chmod +x` makes the file
runnable. Test it by hand before wiring it to a timer.

```
{user}@{host}:~$ python3 -m http.server 4444 --bind 127.0.0.1 &
[1] 8102
{user}@{host}:~$ detect-4444
{user}@{host}:~$ journalctl -t detect --since -5m
Sep 07 10:41:03 {host} detect[8110]: unexpected listener on 4444
```

The trailing `&` runs the server in the background and prints its job number
and process id. Running the script produces no terminal output; the result is a
notification on the desktop and the journal line, which `journalctl -t detect`
(the tag) shows. That is the whole alert. Now make it run on its own with a user
timer, which is two small files under `{home}/.config/systemd/user/`.

```
{user}@{host}:~$ mkdir -p {home}/.config/systemd/user
{user}@{host}:~$ cat > {home}/.config/systemd/user/detect-4444.service <<'EOF'
[Unit]
Description=Check for an unexpected listener on 4444

[Service]
Type=oneshot
ExecStart=%h/.local/bin/detect-4444
EOF
{user}@{host}:~$ cat > {home}/.config/systemd/user/detect-4444.timer <<'EOF'
[Unit]
Description=Run the 4444 check every minute

[Timer]
OnCalendar=*:*:00
AccuracySec=5s

[Install]
WantedBy=timers.target
EOF
{user}@{host}:~$ systemctl --user daemon-reload
{user}@{host}:~$ systemctl --user enable --now detect-4444.timer
Created symlink '/home/{user}/.config/systemd/user/timers.target.wants/detect-4444.timer' -> '/home/{user}/.config/systemd/user/detect-4444.timer'.
```

Restating the essential from the Timers node: a timer unit and a service unit
share a name, and the timer starts the service. `Type=oneshot` means the service
runs to completion each time. `%h` is systemd's shorthand for your home
directory. `OnCalendar=*:*:00` is every minute at zero seconds; `AccuracySec=5s`
tells systemd not to delay it by more than five seconds to save power (the
default is a full minute). `daemon-reload` makes systemd read the new files, and
`enable --now` both starts the timer and makes it start at login. Because the
check is a unit, its own runs are logged, so you can tell "nothing happened" from
"the check never ran".

```
{user}@{host}:~$ systemctl --user list-timers detect-4444.timer
NEXT                        LEFT  LAST                        PASSED  UNIT                ACTIVATES
Mon 2026-09-07 10:44:00 UTC 21s   Mon 2026-09-07 10:43:00 UTC 38s ago detect-4444.timer   detect-4444.service
```

`NEXT` and `LEFT` say when it fires again; `LAST` and `PASSED` prove it has
fired. Within a minute of the server still running, a notification arrives on
its own. The design question is threshold: an alert must fire on the real thing
often enough to trust and rarely enough to keep reading. One that fires every
minute for a listener you started on purpose gets muted, and a muted alert is
the same as none. Tuning is part of the work, which is why the script tests one
exact condition rather than "anything new".

## When it goes wrong

`Failed to enable unit: Unit file detect-4444.timer does not exist.` systemd has
not read the new files. Run `systemctl --user daemon-reload` and try again.

`bash: detect-4444: command not found`. The script is not executable or
`{home}/.local/bin` is not yet on PATH in this shell. Run `chmod +x` and open a
new Ptyxis tab. `pridwen why` will point at the missing execute bit.

The journal line appears but no notification. `notify-send` needs a desktop
session and the `DISPLAY` or `DBUS_SESSION_BUS_ADDRESS` variables, which user
units inherit on Pridwen. On a Range host there is no desktop, and the journal
line is the alert; a monitor watches for it there. `pridwen dispatch test`
confirms the desktop side works at all.

## Try it

1. Create `{home}/.local/bin/detect-4444` with the script above and `chmod +x` it.
2. Start `python3 -m http.server 4444 --bind 127.0.0.1 &`, run `detect-4444` by hand, and confirm both the notification and `journalctl -t detect --since -5m`.
3. Write the `.service` and `.timer` files, run `systemctl --user daemon-reload`, then `systemctl --user enable --now detect-4444.timer`.
4. Run `systemctl --user list-timers detect-4444.timer` and wait for `LAST` to fill in; a notification should arrive without you doing anything.
5. Bring the server to the foreground with `fg` and stop it with Ctrl-C. Confirm the next minute passes with no alert.
6. Write one sentence on why an alert that fires too often ends up ignored, then `systemctl --user disable --now detect-4444.timer` when you are done.

## Remember

- A check script does one exact test, then logs with `logger -p auth.warning -t tag` and pops `notify-send`.
- A user timer plus a oneshot service runs it on a schedule; `list-timers` proves it ran.
- Tune the threshold so the alert is rare enough to read and reliable enough to trust.
