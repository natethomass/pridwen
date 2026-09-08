# Scheduling with systemd

Some jobs need to happen without you: a backup every night, a cleanup every Sunday, a report on the first of the month. For decades the tool for this was cron, a daemon that reads a table of times and commands and runs each one when its time comes. Pridwen does not install cron. It uses systemd timers instead, because a timer is a systemd unit like any service, and that means every run is logged, its next run is visible, and a failure is recorded rather than lost.

On a job you will meet both. A cron line like `0 3 * * * /usr/local/bin/backup` is compact, but when it fails nothing tells you, and when someone asks "when does this next run" you have to work it out from the five fields by hand. A timer answers both questions with one command. You already know that a service unit describes something to run and that `systemctl` starts and stops units; a timer is the unit that starts a service on a schedule.

## Words you'll meet

- **cron**: the traditional scheduler; its table of jobs is a crontab, edited with `crontab -e`.
- **unit**: one thing systemd manages, described by a text file; a service, a timer, a mount, and so on.
- **service unit**: a `.service` file that says what to run.
- **timer unit**: a `.timer` file that says when to start the service of the same name.
- **user units**: units that live in `{home}/.config/systemd/user/` and run as you, no root needed; managed with `systemctl --user`.
- **system units**: units under `/etc/systemd/system/` that run as root or a system account and need `sudo` to manage.
- **enable**: telling systemd to start a unit automatically; for a timer, enabling is what puts it on the schedule.
- **daemon-reload**: asking systemd to re-read unit files after you create or edit one.

## How it works

First see what is already scheduled. `list-timers` shows every timer systemd knows about for your user, and `--all` includes inactive ones.

```
{user}@{host}:~$ systemctl --user list-timers --all
NEXT                        LEFT     LAST                        PASSED  UNIT                ACTIVATES
Tue 2026-09-08 00:00:00 UTC 14h left Mon 2026-09-07 00:00:04 UTC 9h ago  backup.timer        backup.service
-                           -        -                           -       grub-boot-success.timer grub-boot-success.service

2 timers listed.
```

Read the columns left to right. `NEXT` is the next time it will fire and `LEFT` is how far away that is. `LAST` is when it last fired and `PASSED` how long ago. `UNIT` is the timer, and `ACTIVATES` is the service it starts. A dash in `NEXT` means the timer is not active. This one screen is the answer cron never gives: exactly when, and exactly what.

A timer is always a pair of files with the same name and different endings. Write the service first: it says what to run.

```
{user}@{host}:~$ mkdir -p {home}/.config/systemd/user
{user}@{host}:~$ cat > {home}/.config/systemd/user/backup.service <<'EOF'
[Unit]
Description=Copy Documents to the backup directory

[Service]
Type=oneshot
ExecStart=%h/.local/bin/backup
EOF
```

`Type=oneshot` says the program runs to completion and exits, which is what a scheduled job does; the default type is for long-running daemons. `ExecStart` is the command, and `%h` is systemd's shorthand for your home directory, so the unit works for whoever installs it. The `backup` script is the one from the scripting node; any executable works.

Now the timer, which says when.

```
{user}@{host}:~$ cat > {home}/.config/systemd/user/backup.timer <<'EOF'
[Unit]
Description=Run the backup every day

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

`OnCalendar=daily` means midnight every day, one of several shorthands the next lesson covers. `Persistent=true` means that if the machine was off at midnight, the job runs once as soon as it is back. `WantedBy=timers.target` in the `[Install]` section is what `enable` uses: it hooks the timer into the group of timers systemd starts at login.

Two commands make it live. The reload tells systemd the files exist; the enable puts the timer on the schedule, and `--now` also starts it immediately rather than at the next login.

```
{user}@{host}:~$ systemctl --user daemon-reload
{user}@{host}:~$ systemctl --user enable --now backup.timer
Created symlink '{home}/.config/systemd/user/timers.target.wants/backup.timer' -> '{home}/.config/systemd/user/backup.timer'.
{user}@{host}:~$ systemctl --user list-timers backup.timer
NEXT                        LEFT     LAST PASSED UNIT         ACTIVATES
Tue 2026-09-08 00:00:00 UTC 14h left -    -      backup.timer backup.service
```

The symlink line is systemd's way of saying it enabled the unit. Notice that you enable the timer, not the service. Enabling the service would start it once at login and never again; the timer is what fires it on the schedule. When it has run, the service's output is in the journal.

```
{user}@{host}:~$ journalctl --user -u backup.service --since today
Sep 07 00:00:04 {host} systemd[1834]: Starting backup.service - Copy Documents to the backup directory...
Sep 07 00:00:05 {host} systemd[1834]: Finished backup.service - Copy Documents to the backup directory.
```

`-u backup.service` selects one unit and `--since today` limits the time. `Starting` and `Finished` bracket the run; anything the script printed appears between them, and a failure appears as `Failed with result 'exit-code'`. This is what cron cannot show you.

## When it goes wrong

`bash: crontab: command not found` is exit 127: cron is not in the image. Write a `.service` and `.timer` pair instead. If a course truly requires cron, `rpm-ostree install cronie` layers it, at the cost of slower upgrades.

`Failed to enable unit: Unit file backup.timer does not exist.` means systemd has not read your new file yet, or the file is in the wrong directory. Check it is under `{home}/.config/systemd/user/`, then run `systemctl --user daemon-reload` and enable again.

The timer is listed but the job never seems to run. Check `systemctl --user status backup.service` for the last result. If the service reports `status=203/EXEC`, the `ExecStart` path is wrong or the script is not executable; `chmod +x` it. `pridwen why` will translate the message you saw, and `pridwen explain systemctl` walks through the subcommands.

## Try it

1. Run `systemctl --user list-timers --all` and read the `NEXT` and `LAST` columns for anything already there.
2. Create `stamp.service` under `{home}/.config/systemd/user/` with `Type=oneshot` and `ExecStart=/usr/bin/date`, and `stamp.timer` with `OnCalendar=minutely` and the same `[Install]` section as above.
3. Run `systemctl --user daemon-reload` then `systemctl --user enable --now stamp.timer`, and expect the `Created symlink` line.
4. Run `systemctl --user list-timers stamp.timer` and expect a `NEXT` under a minute away.
5. Wait two minutes, then run `journalctl --user -u stamp.service --since -5min` and expect two runs, each printing the date between `Starting` and `Finished`.
6. Run `systemctl --user disable --now stamp.timer` to take it off the schedule, and confirm it shows a dash in `NEXT`.

## Remember

- A timer is a `.timer` and `.service` pair with the same name; the timer says when, the service says what.
- `daemon-reload`, then `enable --now name.timer`: you enable the timer, never the service.
- `systemctl --user list-timers` shows when it runs next; `journalctl --user -u name.service` shows what happened, which cron never tells you.
