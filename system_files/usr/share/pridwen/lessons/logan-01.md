# Reading logs as a story

Log analysis is less about tools than about a habit: you read the journal as a
narrative and notice the one line that does not fit the others. Normal activity
on a machine has a rhythm. Services start, users log in, timers fire, and the
same handful of messages repeat all day. An incident breaks that rhythm, and the
break is usually visible as a line that appears where nothing like it appeared
before.

On Pridwen the rhythm lives in the systemd journal, the same log you met in the
Logging node. On a real job, reading logs this way is how you answer the first
question anyone asks after something odd happens: what actually took place, and
in what order. This lesson works on your own host's journal and, once the Range
arrives in milestone M4, on Rocky 9 lab machines you own, where the stakes are a
scenario rather than a real breach.

## Words you'll meet

- **journal**: the binary log that systemd keeps for every service and the kernel, read with `journalctl`.
- **field**: a named piece of each journal entry, such as `_COMM` (the program that wrote it) or `_PID`.
- **window**: a start time and an end time that bound which entries you look at.
- **regex**: a regular expression, a pattern such as `Failed|Accepted` where `|` means "or".
- **sshd**: the SSH server daemon, off on your Pridwen host by default and running on Range hosts.
- **timeline**: an ordered list of events with their times, the product of every log investigation.

## How it works

Restating the essential from the Logging node: `journalctl` with no arguments
prints the whole journal, oldest first, and your account is in the `wheel` group,
which on Fedora may read the system journal without `sudo`. The first move in
analysis is never to read everything. It is to bound a window.

```
{user}@{host}:~$ journalctl --since "09:00" --until "09:15" -o short-precise
Sep 07 09:00:01.113402 {host} systemd[1]: Started dnf-makecache.service.
Sep 07 09:03:44.872210 {host} sudo[4121]: {user} : TTY=pts/0 ; PWD={home} ; USER=root ; COMMAND=/usr/bin/systemctl status sshd
Sep 07 09:12:19.004587 {host} gnome-shell[2310]: Window manager warning: ...
```

`--since` and `--until` take a time; a bare `09:00` means today at nine. `-o
short-precise` is an output format: the same one-line-per-entry layout as the
default, but with microseconds on the timestamp. Reading the output back: the
first column is the date and time, then the hostname, then the program and its
process id in square brackets, then the message. The `sudo` line is the kind of
entry that matters in an investigation, because it names who ran what, from
where, as whom. A normal quarter hour on a desktop is mostly service chatter like
the first and third lines.

The second move is to filter by field and pattern at the same time. `_COMM=sshd`
keeps only entries written by the program named `sshd`. `-g` (grep) keeps only
entries whose message matches a regex, and unlike piping into `grep` it keeps the
journal's field awareness, so the two filters combine.

```
{user}@{host}:~$ journalctl _COMM=sshd -g 'Failed|Accepted' --since today
Sep 07 09:06:02 {host} sshd[5120]: Failed password for invalid user admin from 203.0.113.9 port 51022 ssh2
Sep 07 09:06:05 {host} sshd[5120]: Failed password for invalid user admin from 203.0.113.9 port 51022 ssh2
Sep 07 09:06:31 {host} sshd[5133]: Accepted password for deploy from 203.0.113.9 port 51040 ssh2
```

That output is the story this lesson is about. Two failures for a user that does
not exist, from one address, then twenty-six seconds later an accepted password
for a real user from the same address. On your own Pridwen host this command
prints nothing, because `sshd` is off by default and has written no lines; on a
Range host it is the first thing to run. Once you find the first odd event, drop
`--until` and read forward from it, because what happened after the accepted
login is the part that tells you whether anything was done with it.

```
{user}@{host}:~$ journalctl --since "09:06:31" -o short-precise | head -n 20
```

`head -n 20` shows only the first twenty lines, so you can read forward in
pages rather than being buried. Build the timeline first, then explain it. The
next two lessons sharpen the same reading with counting and with merging the
audit log in.

## When it goes wrong

`Failed to parse timestamp: 9am`. `journalctl` did not understand the time. It
accepts `09:00`, `2026-09-07 09:00`, `today`, `yesterday`, and relative forms like
`-1h` (one hour ago). Retype the time in one of those shapes.

`-- No entries --`. Nothing matched. On a Pridwen host with `_COMM=sshd` this is
the normal result, because the SSH server is not running. Either move to a Range
host or swap in a program that does write on your desktop, such as `_COMM=sudo`.
`pridwen why` after the empty result will say the same.

`Hint: You are currently not seeing messages from other users and the system.`
Your account cannot read the system journal, which means it is not in `wheel`.
Prefix `sudo` if you can, or ask the owner of the machine. `pridwen explain
journalctl` annotates every flag used above.

## Try it

1. Run `journalctl --since -15m -o short-precise` on your own host. Read the timestamp, hostname, program and message columns back to yourself on one line.
2. Run `journalctl _COMM=sudo --since today`. Every line names who ran what as whom; find your own most recent command in it.
3. Run `journalctl _COMM=sshd -g 'Failed|Accepted' --since today`. On Pridwen expect `-- No entries --`; say why before moving on.
4. On a Range host, run the same command and find the first `Accepted` line that follows a run of `Failed` lines from the same address.
5. Drop `--until`, set `--since` to that line's time, and pipe into `head -n 20` to read forward.
6. Write the first five events down, one per line, with their times.

## Remember

- Bound a window with `--since` and `--until` first; never start by reading everything.
- `_COMM=name` filters by program and `-g pattern` filters by regex; together they put failures and successes side by side.
- Find the first odd line, then read forward from it without an end bound.
