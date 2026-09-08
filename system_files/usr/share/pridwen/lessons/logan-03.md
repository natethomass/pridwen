# From logs to a timeline

The output of log analysis is a timeline: an ordered list of what happened and
when, built from more than one source. The systemd journal, the audit log, and a
service's own log files each hold part of the story. None of them holds all of
it. Lining them up by time is what turns a pile of clues into an account that
someone else can follow.

On a job, the timeline is the first thing anyone asks for after an incident, and
the first thing a report is judged on. On Pridwen you practise the discipline on
your own host, where the "incident" can be something as plain as a password
change, and later on Rocky 9 Range hosts you own, arriving in milestone M4,
where a scenario plants a real sequence for you to reconstruct.

## Words you'll meet

- **anchor**: one event you are sure of, with a precise time, that everything else is placed around.
- **audit log**: the kernel's record of security-relevant actions, written by `auditd`, searched with `ausearch`.
- **ausearch**: the tool that pulls audit records by time, key, user, or event type.
- **interleave**: to merge two lists by time so their entries alternate in true order.
- **chrony**: the service that keeps the clock accurate against network time servers, so timestamps from different sources are comparable.
- **source**: which log a timeline line came from; every line cites one.

## How it works

Restating the essential from the last two lessons: bound a window with `--since`
and `--until`, and use `-o short-precise` when ordering is the question, because
it prints microseconds. Start by anchoring on one confirmed event. Here the
anchor is a password change on your own host.

```
{user}@{host}:~$ journalctl --since "09:10:00" --until "09:12:00" -o short-precise
Sep 07 09:10:41.220913 {host} sudo[6210]: {user} : TTY=pts/0 ; PWD={home} ; USER=root ; COMMAND=/usr/bin/passwd {user}
Sep 07 09:10:41.224107 {host} sudo[6210]: pam_unix(sudo:session): session opened for user root(uid=0) by {user}(uid=1000)
Sep 07 09:10:52.918330 {host} passwd[6214]: pam_unix(passwd:chauthtok): password changed for {user}
Sep 07 09:10:52.931775 {host} sudo[6210]: pam_unix(sudo:session): session closed for user root
```

Reading it back: the timestamp column now has six decimal places. Line one is
`sudo` recording who ran what. Line two is PAM, the login and authentication
library, opening a root session. Line three is `passwd` itself saying the
password changed, eleven seconds later, which is you typing it twice. Line four
closes the session. Four lines, one event, and every line has a time you could
sort on.

Now gather what the audit log says about the same two minutes. `ausearch -ts`
(time start) and `-te` (time end) take the same clock times. The audit log is
root-only, so `sudo` is required. `-i` (interpret) turns numeric user ids and
syscall numbers into names.

```
{user}@{host}:~$ sudo ausearch -ts 09:10:00 -te 09:12:00 -i | grep -E 'type=(USER_CMD|USER_CHAUTHTOK)'
type=USER_CMD msg=audit(09/07/2026 09:10:41.219:412) : pid=6210 uid={user} auid={user} ses=3 msg='cwd={home} cmd=passwd {user} exe=/usr/bin/sudo terminal=pts/0 res=success'
type=USER_CHAUTHTOK msg=audit(09/07/2026 09:10:52.917:415) : pid=6214 uid=root auid={user} ses=3 msg='op=PAM:chauthtok grantors=pam_pwquality,pam_unix acct={user} exe=/usr/bin/passwd terminal=pts/0 res=success'
```

Audit records are dense. The part in `audit(...)` is the time and a serial
number. `auid` is the audit user id, the account that originally logged in,
which survives `sudo` and is why the audit log can say it was you even when
`uid=root`. `res=success` is the outcome. The `grep` keeps two record types: a
command run through sudo and a password change.

Now interleave. The audit `USER_CMD` at 09:10:41.219 lands one millisecond before
the journal's `sudo` line at 09:10:41.220, because the audit record is written
first. The two sources agree, and because chrony keeps the clock accurate on
every Pridwen and Range host, times from two logs on one machine, or from two
machines, sit in true order. That is why an accurate clock is part of the
hardening baseline and not a convenience.

Write the timeline as you go, one line per event, with time, source, and what
happened, in a plain text file.

```
{user}@{host}:~$ cat {home}/pridwen/timeline.txt
09:10:41.219  audit    USER_CMD: {user} ran `passwd {user}` via sudo from pts/0
09:10:41.220  journal  sudo: session opened for root by {user}
09:10:52.917  audit    USER_CHAUTHTOK: password changed for {user}, res=success
09:10:52.918  journal  passwd: password changed for {user}
09:10:52.931  journal  sudo: session closed
```

On a Range scenario this file is the deliverable: a short, ordered story with a
source on every line. Citing the source is what makes it defensible, because
anyone can go back to the log and see the same line.

## When it goes wrong

`<no matches>` from `ausearch`. Either the window is wrong or the clock format
is. `-ts` wants `HH:MM:SS` or a date and time; it does not accept `-1h`. Widen
the window by a few minutes and try again.

`Error opening /var/log/audit/audit.log (Permission denied)`. `ausearch` ran
without `sudo`. The audit log is root-only on purpose. Run it with `sudo`.

Two sources disagree by seconds or more. Check `timedatectl` on each host. If
`System clock synchronized: no`, chrony is not keeping time on that machine and
its timestamps cannot be trusted next to another's. The Timers node in Academy
covers how time sync is checked and fixed.

## Try it

1. On your own host, run `sudo passwd {user}` and set the same password again. Note the time to the second.
2. Run `journalctl --since "<that minute>" --until "<the next minute>" -o short-precise` and find the four lines above.
3. Run `sudo ausearch -ts <start> -te <end> -i | grep -E 'type=(USER_CMD|USER_CHAUTHTOK)'` for the same window.
4. Create `{home}/pridwen/timeline.txt` and write five lines: time, source, event, in order.
5. Run `timedatectl` and confirm `System clock synchronized: yes`, then explain in one sentence why that matters for step 4.
6. On a Range host, repeat with the scenario's anchor event and hand in the timeline.

## Remember

- Anchor on one event you are sure of, then pull every source for the window around it.
- Interleave by time; chrony's accurate clock is what makes two logs one order.
- One line per event, with its time and its source, is the deliverable.
