# Filtering well

The previous lesson showed that the journal is one store holding every message
the system writes, and that `journalctl` reads it. The skill with the journal is
turning that flood into an answer, and that means combining filters. Four kinds
of filter do most of the work: which **unit**, which **priority**, which
**time window**, and which **field** values. They stack: each one you add
removes lines, and you keep adding until what is left is the answer.

This is the exact motion a log analyst makes during an incident: start with
everything, narrow to the service, narrow to the hour, narrow to the failures,
and the story of what happened is what remains. On Pridwen the journal is where
your own failed commands, sudo uses and SELinux denials all land, so the same
filters explain your own desktop. The RHCSA asks you to find a specific message
under time pressure, and stacking filters is how.

## Words you'll meet

- **unit**: a systemd-managed thing, usually a service; `-u sshd` selects its messages.
- **priority**: how serious a message is, from `emerg` (0) through `alert`, `crit`, `err` (3), `warning` (4), `notice`, `info` to `debug` (7).
- **field**: a named piece of metadata journald attaches to every message, like `_COMM` (the program) or `_PID` (its process id).
- **`_COMM`**: the field holding the command name that wrote the message.
- **`_PID`**: the field holding the process id that wrote it.
- **`-g`**: grep inside the journal with a regular expression.
- **regular expression** (regex): a pattern language where `Failed|Accepted` means "Failed or Accepted".
- **index**: the lookup structure that makes exact field matches fast.

## How it works

Take a Range host running sshd (Pridwen's own sshd is off by default, so this
is a lab example). Ask for one unit, at priority warning or worse, in the last
two hours. `-u` names the unit, `-p warning` means warning and everything more
serious, and `--since -2h` means two hours ago until now.

```
{user}@{host}:~$ journalctl -u sshd -p warning --since -2h --no-pager
Sep 07 08:12:40 {host} sshd[2231]: error: maximum authentication attempts exceeded for invalid user admin from 203.0.113.9 port 51022 ssh2 [preauth]
Sep 07 08:12:40 {host} sshd[2231]: Disconnecting invalid user admin 203.0.113.9 port 51022: Too many authentication failures [preauth]
```

Two lines out of thousands. The program is `sshd`, the message says someone at
`203.0.113.9` tried the username `admin` too many times and was disconnected.
Drop `-p warning` and the same window shows every login too; add `-p err` and
only the first line remains, because the second was logged at `warning`.
Priorities are a scale, and `-p` names the least serious level you want.

Field matches are exact and fast because they use the index. A field match is
written as `FIELD=value` with no dash.

```
{user}@{host}:~$ journalctl _COMM=sudo --since today --no-pager
Sep 07 09:20:14 {host} sudo[7710]:    {user} : TTY=pts/0 ; PWD={home} ; USER=root ; COMMAND=/usr/bin/firewall-cmd --list-all
Sep 07 09:20:14 {host} sudo[7710]: pam_unix(sudo:session): session opened for user root(uid=0) by {user}(uid=1000)
Sep 07 09:20:14 {host} sudo[7710]: pam_unix(sudo:session): session closed for user root
```

`_COMM=sudo` selects messages written by the program named `sudo`, which on
Pridwen is the audit trail of every privileged command since midnight
(`--since today`). The three lines are one sudo use: the command, the session
opening, the session closing. `_PID=7710` would select that one process
instead, and `journalctl -o verbose -n 1` shows every field attached to a
message so you can see what else there is to match on.

`-g` greps inside the journal with a regular expression. It beats piping to an
external `grep` because it stays inside the tool, keeps the colours, and
combines with the other filters.

```
{user}@{host}:~$ journalctl -g 'Failed|Accepted' -u sshd --since today --no-pager
Sep 07 07:58:03 {host} sshd[2104]: Accepted publickey for {user} from 192.168.56.1 port 50210 ssh2: ED25519 SHA256:h1Qk...
Sep 07 08:12:31 {host} sshd[2231]: Failed password for invalid user admin from 203.0.113.9 port 51022 ssh2
```

The pattern `Failed|Accepted` matches either word, so the output is the login
story: one accepted key login from your own machine, one failed password from
a stranger. `-u sshd` keeps it to the ssh daemon, and `--since today` bounds it.
Case matters in `-g` unless the pattern is all lowercase, in which case it
matches either.

When order matters to the second, `-o short-precise` adds microseconds to the
timestamp, and `-o json` prints each message as a JSON object for a script.
`--until` closes a window: `--since "2026-09-07 08:00" --until "2026-09-07
09:00"` is one hour on one day, and the quotes are needed because of the
space.

The habit to build is start broad, then add one filter at a time until the
noise is gone. If a filter removes the line you wanted, take it back off; the
journal does not change between runs, so you can iterate freely.

## When it goes wrong

`Failed to parse timestamp: 10 min ago` means `--since` got the words without
quotes, so the shell split them into three arguments. Write `--since "10 min
ago"`, or use a form with no spaces like `-1h` or `today`.

`Failed to add match 'COMM=sudo': Invalid argument` means the field name was
missing its leading underscore. Trusted fields set by journald begin with `_`:
`_COMM`, `_PID`, `_UID`, `_SYSTEMD_UNIT`.

`-- No entries --` means the filters removed everything. Take the last one off
and look again; commonly the priority was too strict or the unit name needs
`.service` spelled the same way `systemctl` shows it. `pridwen explain
journalctl` annotates the flags, and `pridwen why` under the failed command
says which of these applied.

## Try it

1. Type `systemctl list-units --type=service --state=running | head` and pick a running service by name.
2. Type `journalctl -u NAME --since -1h --no-pager` with that name and count the lines with `| wc -l`.
3. Add `-p warning` to the same command and see how much the count shrinks.
4. Type `journalctl -u NAME -g 'start|stop' --since today --no-pager` and read the matches.
5. Type `journalctl _COMM=sudo --since today --no-pager | tail -3` and read your own most recent sudo command.
6. Type `journalctl -o verbose -n 1 --no-pager` and find the `_COMM=` and `_PID=` fields in the output.

## Remember

- Filters stack: `-u` unit, `-p` priority and worse, `--since` and `--until` a window, `FIELD=value` an exact match.
- `-g pattern` greps inside the journal and combines with the other filters.
- Start broad, add one filter at a time, and remove the one that took your line away.
