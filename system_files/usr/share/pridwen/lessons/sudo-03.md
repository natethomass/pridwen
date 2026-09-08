# The audit trail

Every `sudo` invocation is recorded, and on a hardened system that record is
a feature you can read. It is what lets you answer "who changed this" after
the fact, on your own machine when something you did yesterday broke today,
and on a shared server when a change appears that nobody admits to. It is
also the reason Pridwen locks the root account: a command run from a root
shell is recorded as root, which names no one, while a `sudo` line names the
person.

Two systems keep the record. The journal is systemd's log, where sudo writes
one line per command. auditd is the kernel's audit service, which records
security-relevant events in a stricter, tamper-resistant format that
auditors and incident responders rely on. Pridwen runs both, so you can
practise reading them here before you ever need to on a job.

## Words you'll meet

- **journal**: systemd's log, read with `journalctl`; sudo writes a line there for every command.
- **auditd**: the audit daemon, a background service that writes the kernel's audit events to `/var/log/audit/audit.log`.
- **event type**: the kind of audit record; `USER_CMD` is a command run through sudo.
- **ausearch**: the tool that finds audit events by type, time, or user.
- **aureport**: the tool that summarises audit events into counts.
- **TTY**: the terminal a command was typed on, such as `pts/0`; `unknown` means no terminal, for example a script.
- **auid**: the audit user ID, the user who originally logged in, which stays the same even after `sudo -i`.

## How it works

Start with the journal. `_COMM=sudo` selects lines written by the program
named sudo, `--since today` limits the range, and `tail -n 2` keeps the last
two.

```
{user}@{host}:~$ journalctl _COMM=sudo --since today | tail -n 2
Sep 07 09:14:02 {host} sudo[4312]:    {user} : TTY=pts/0 ; PWD={home} ; USER=root ; COMMAND=/usr/bin/systemctl restart chronyd
Sep 07 09:14:02 {host} sudo[4312]: pam_unix(sudo:session): session opened for user root(uid=0) by {user}(uid=1000)
```

The first line is the one to learn. After the timestamp and host, `sudo[4312]`
is the program and its process ID. Then the user who ran it, `TTY=` the
terminal, `PWD=` the directory they were in, `USER=` the target user, and
`COMMAND=` the full path of what ran with its arguments. The second line
comes from PAM, the login framework, and marks the root session opening; a
matching `session closed` line follows when the command finishes. Members of
`wheel` can read these lines without `sudo`.

Now the same event from auditd. `-m USER_CMD` selects sudo command events,
`-ts today` sets the start time, and `-i` interprets numbers into names so
`uid=1000` shows as your login name.

```
{user}@{host}:~$ sudo ausearch -m USER_CMD -ts today -i | tail -n 3
----
type=USER_CMD msg=audit(09/07/2026 09:14:02.118:412) : pid=4312 uid={user} auid={user} ses=3 subj=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023 msg='cwd={home} cmd=/usr/bin/systemctl restart chronyd exe=/usr/bin/sudo terminal=pts/0 res=success'
```

`type=USER_CMD` is the event kind. `pid=4312` matches the journal's process
ID, which is how you tie the two records together. `uid=` is who ran it,
`auid=` is who logged in, `ses=3` is the login session number, and `subj=`
is their SELinux context. Inside `msg=`, `cwd=` is the directory, `cmd=` the
command, `terminal=` the TTY, and `res=success` says sudo allowed it; a
refused attempt shows `res=failed`. The `auid` field is what makes the audit
log stronger than the journal: even after `sudo -i`, everything root does
still carries the audit ID of the person who logged in.

`aureport` turns the raw events into a summary. `-x` reports on executables
and `--summary` counts them.

```
{user}@{host}:~$ sudo aureport -x --summary -ts today

Executable Summary Report
=================================
total  file
=================================
14  /usr/bin/sudo
6   /usr/sbin/unix_chkpwd
2   /usr/libexec/gdm-session-worker
```

The left column is the count, the right the program. `/usr/bin/sudo` at the
top with fourteen events is a day of normal admin work. `unix_chkpwd` is PAM
checking passwords, and the GDM worker is your desktop login.

Reading this well is a defender's skill. A `sudo` line you cannot explain,
at three in the morning, from `TTY=unknown` with a `cwd=` in `/tmp`, is the
sort of record that starts an investigation. On your own machine the same
trail helps you retrace a change that broke something, because you can see
exactly what you ran and when. The trail is only as good as the discipline of
using `sudo` for each command instead of living in a root shell, and only as
trustworthy as the root account is locked: with no root password on Pridwen,
every privileged action had to pass through a line like these.

## When it goes wrong

`Error opening /var/log/audit/audit.log (Permission denied)` means
`ausearch` or `aureport` was run without `sudo`. The audit log is readable
only by root, deliberately, so that an attacker who gets your user account
cannot read or edit the record of what they did. Add `sudo`.

`<no matches>` from `ausearch` means no events of that type in that time
window. Check the type spelling, `USER_CMD` in capitals, and widen `-ts` to
`recent` or `this-week`.

`journalctl _COMM=sudo` printing `-- No entries --` for a normal user means
the journal is not readable by that account; only `wheel` and a few system
groups may read it. Run it as your admin user, or with `sudo`. The Coach
points at these commands under any `sudo` that exited 1, and `pridwen
explain journalctl` and `pridwen explain ausearch` annotate the flags.

## Try it

1. Type three different harmless `sudo` commands, such as `sudo true`, `sudo ls /root`, and `sudo systemctl status chronyd`.
2. Type `journalctl _COMM=sudo -n 6` and find all three; the `COMMAND=` field names each one.
3. Pick one line and name its `TTY=`, `PWD=`, and `COMMAND=` fields aloud.
4. Type `sudo ausearch -m USER_CMD -ts today -i | tail -n 5` and match one event's `pid=` to the journal's `sudo[pid]`.
5. Type `sudo aureport -x --summary -ts today` and read which program ran most.
6. Explain in one sentence why a locked root account makes this trail more trustworthy.

## Remember

- `journalctl _COMM=sudo` shows who ran what, from which terminal and directory, as whom; `wheel` members can read it.
- `sudo ausearch -m USER_CMD -i` shows the same events from auditd with `auid`, which survives `sudo -i`; `aureport -x --summary` counts them.
- The trail only names people because root is locked and every privileged command went through `sudo`.
