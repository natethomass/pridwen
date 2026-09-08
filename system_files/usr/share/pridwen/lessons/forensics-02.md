# Finding by time

An investigation usually starts with a window: something happened between these
two times, so which files changed then. `find` answers this directly. It walks a
directory tree, tests each file against the conditions you give it, and prints
the ones that pass. With time tests, it turns a vague suspicion ("someone was in
`/etc` this morning") into a concrete list you can read in order.

On a job, a list of files changed inside the incident window is often enough to
reconstruct what an attacker touched, and it comes from the disk rather than the
logs, so it works even when the logs were cleaned. On Pridwen you practise on
your own `/etc`, where the changes are the ones you made in earlier missions,
and later on a Rocky 9 Range host you own, arriving in milestone M4, where a
scenario has planted the changes.

## Words you'll meet

- **find**: the command that walks a tree and prints files matching tests.
- **test**: a condition `find` checks per file, such as a name, a type or a time.
- **mtime**: modification time, when a file's contents last changed; `-mtime` tests it in days, `-mmin` in minutes.
- **-newermt**: a test that passes for files modified after a given clock time.
- **stderr**: the error stream, separate from normal output, where `find` reports directories it cannot enter.
- **-printf**: a `find` action that prints chosen fields in a format you specify, instead of just the path.

## How it works

Restating the essential from the last lesson: every file carries an mtime for
its contents and a ctime for its metadata. `find` can test either. Start with
the coarse question, what changed today.

```
{user}@{host}:~$ sudo find /etc -mtime 0 -type f
/etc/passwd
/etc/shadow
/etc/audit/rules.d/50-passwd.rules
/etc/resolv.conf
```

`-mtime 0` means modified less than one day ago (`-mtime` counts whole days, and
`0` is "within the last 24 hours"); `-type f` keeps only regular files, not
directories. `sudo` matters because `find` skips directories it cannot enter,
and `/etc` has several, so root's view is the complete one. Reading the list
back: the first three are things you did in earlier lessons and `resolv.conf` is
rewritten by the network stack, which is the sort of noise you learn to expect.

Days are too coarse for an incident. `-mmin -20` means modified in the last
twenty minutes, and `-newermt "time"` (newer than a modification time) accepts
an actual clock time, which is easier to reason about than "minutes ago" when
the window is in the past. Two of them, the second negated with `!`, bound a
window.

```
{user}@{host}:~$ sudo find /etc -type f -newermt "09:00" ! -newermt "09:20"
/etc/passwd
/etc/shadow
```

A bare `09:00` means today at nine; `"2026-09-07 09:00"` names a day. `!`
negates the test that follows it, so `! -newermt "09:20"` means "not modified
after 09:20". Together: modified after 09:00 and not after 09:20. Two files, and
from the last lesson you know that pair is a password or account change.

Add `-printf` so each line carries its time and the list is already ordered
evidence. `%TY-%Tm-%Td` is the modification year, month and day, `%TH:%TM` the
hour and minute, `%p` the path, and `\n` ends the line. Piping into `sort` puts
them in time order because the time comes first.

```
{user}@{host}:~$ sudo find /etc -type f -newermt "09:00" ! -newermt "09:20" -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort
2026-09-07 09:07 /etc/passwd
2026-09-07 09:07 /etc/shadow
```

`2>/dev/null` sends stderr, stream number 2, to the discard device, so
`Permission denied` lines for directories `find` could not enter do not mix
into the list. Under `sudo` there are none, but the habit keeps the output
clean when you run it as yourself. Without `sudo` the same command silently
misses anything under `/etc/audit`, `/etc/sudoers.d` and the other root-only
directories, so the two choices change what the search returns: `sudo` widens
it, `2>/dev/null` hides the evidence that it was narrowed.

Because `touch -d` can rewrite mtime, a careful intruder resets it. ctime cannot
be set by hand, so `-cmin -60` (ctime within the last hour) or `-newerct` catches
files whose metadata changed even when their mtime claims otherwise. Run the
same window with the `c` variants when the `m` results look too clean.

```
{user}@{host}:~$ sudo find /etc -type f -newerct "09:00" ! -newerct "09:20" -printf '%CY-%Cm-%Cd %CH:%CM %p\n' | sort
2026-09-07 09:07 /etc/passwd
2026-09-07 09:07 /etc/shadow
2026-09-07 09:11 /etc/cron.d/backup
```

A third file appears: its mtime was set to an old date, but its ctime says
09:11. `%C` fields are the ctime versions of `%T`. That is the file to open.

## When it goes wrong

`find: paths must precede expression`. The tests came before the directory, or a
quoted argument lost its quotes. The order is always `find <where> <tests>
<actions>`; `pridwen explain find` lays out the flags.

`find: '/etc/audit': Permission denied`. You are running as yourself and `find`
cannot enter that directory. The list is incomplete. Rerun with `sudo`, or add
`2>/dev/null` if you only want your own view and know it is partial.

`find: invalid argument '!' to '-newermt'` or an empty result for a window you
are sure of. The time string was not understood; use `HH:MM` or `YYYY-MM-DD
HH:MM` in quotes, and check `date` to see what the host thinks the time is.

## Try it

1. Run `sudo find /etc -mtime 0 -type f` and name which of the results you changed yourself.
2. Narrow to a window with `-newermt` and `! -newermt` around a change you made earlier today.
3. Add `-printf '%TY-%Tm-%Td %TH:%TM %p\n'` and `| sort` so each line carries its time.
4. Run the same command without `sudo` and with `2>/dev/null`, and count how many results disappear.
5. Run `touch -d '2020-01-01' {home}/pridwen/notes.txt`, then find it with `-newerct "<a minute ago>"` under `{home}/pridwen` even though `-newermt` does not list it.
6. On a Range host, list `/etc` changes in the scenario window with ctime, and read the changed files in time order.

## Remember

- `find /etc -type f -newermt "start" ! -newermt "end"` lists files changed inside a window.
- `-printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort` makes the list a timeline; `sudo` makes it complete.
- When mtimes look too clean, ask for ctime with `-newerct` or `-cmin`; it cannot be faked.
