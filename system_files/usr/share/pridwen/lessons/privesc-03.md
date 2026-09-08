# Scheduled and writable paths

The last common escalation route is a combination of time and writability:
something root runs on a schedule, from a place an ordinary user can write to.
If you can change what a privileged job executes before it next runs, you
inherit its privilege when it does. This lesson is about finding those jobs and
the files behind them, and making sure only root can change what root runs.

The read-only audits here are safe on your own Pridwen host. Planting a writable
script and riding a root job up to root runs only against Range targets you own
(Rocky 9 labs you start with `pridwen enter rocky`). On a real job this is the
habit that turns "root runs a backup script every night" from a quiet risk into
a checked, locked-down fact, and it is where the attack tier meets detection.

## Words you'll meet

- **systemd**: the manager that starts services and runs scheduled jobs on a modern Linux host.
- **unit**: systemd's word for one managed thing, such as a service (a program) or a timer (a schedule).
- **timer**: a unit that starts another unit on a schedule, the systemd replacement for old cron jobs.
- **cron**: the older scheduler that ran commands from crontab files; still present on some hosts.
- **world-writable**: changeable by anyone, shown by a `w` in the last group of an `ls -l` mode.
- **auditd**: the Linux auditing service that can watch a path and log every change to it.

## How it works

First, inventory what runs on a schedule, because that is the list of jobs an
attacker would like to hijack. `systemctl list-timers` shows the timers and when
they next fire; `--all` includes ones not currently active:

```
{user}@{host}:~$ systemctl list-timers --all
NEXT                        LEFT     LAST                        UNIT
Mon 2026-09-08 00:00:00 UTC 14h left Sun 2026-09-07 00:00:00 UTC logrotate.timer
Mon 2026-09-08 03:10:00 UTC 17h left Sun 2026-09-07 03:10:00 UTC dnf-makecache.timer
```

Read that back. `NEXT` is when the timer fires again, `LEFT` is the time until
then, `LAST` is when it fired before, and `UNIT` is the timer's name. Each timer
starts a matching service that runs a program, often a script, as root. Those
scripts and their directories are what you check next.

The danger is a script that root runs but that someone else can edit. You look
at the mode of such a script with `ls -l`, whose `-l` flag prints one line per
file with permissions, owner, and group:

```
{user}@{host}:~$ ls -l /usr/local/bin/backup.sh
-rwxrwxrwx. 1 root root 214 Sep  7 08:02 /usr/local/bin/backup.sh
```

Read the mode field, `-rwxrwxrwx`. The three groups after the leading `-` are
owner, group, and other. The last group here is `rwx`, meaning any user may
read, write, and execute it. Since root runs this script on a schedule, any user
can rewrite it and have their code run as root at the next fire. That is the
finding. The fix is correct ownership and a tight mode so only root can change
it:

```
{user}@{host}:~$ sudo chmod 755 /usr/local/bin/backup.sh
```

`chmod 755` leaves read and execute for everyone but write for the owner (root)
only, closing the door. On a Range host you plant such a script, show that
changing it yields root at the next run, then lock it down and confirm the path
is closed. This is also where detection meets attack: an auditd watch on those
paths turns a future edit into a logged alert.

## When it goes wrong

`Failed to list timers: Access denied` is rare for listing, but if you see a
permission error, re-run without needing root first; listing timers does not
require sudo, while changing files does.

A mode like `-rw-rw-rw-` (no `x`) on a script still counts as writable by
others; the risk is the write bit, not the execute bit, because root re-reads
the file's contents when it runs it. Tighten any group- or other-write bit you
find.

`chmod: changing permissions of '...': Operation not permitted` means you are
not the owner and did not use sudo; the file is root-owned, so put `sudo` in
front. `pridwen explain chmod` explains the octal modes if that is the unclear
part.

## Try it

1. On a Range host, list scheduled jobs with `systemctl list-timers --all` and read the columns back.
2. Find the script a root timer runs and read its mode with `ls -l`.
3. Search for world-writable files under the systemd directories with `find ... -perm -0002`.
4. On the Range, demonstrate an escalation through a writable root-run script, then lock it with `chmod 755` and confirm.
5. Add an auditd watch on the script's directory so a future change raises an alert.

## Remember

- The escalation is time plus writability: a job root runs on a schedule, from a file the wrong person can edit.
- `systemctl list-timers --all` is the schedule inventory; `ls -l` on each script tells you who can change what root runs.
- The write bit is the risk, not the execute bit; a tight mode plus an auditd watch shuts the door and alerts on the next attempt.
