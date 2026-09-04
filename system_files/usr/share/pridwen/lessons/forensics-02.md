# Finding by time

An investigation usually starts with a window: something happened between these
two times, so which files changed then. `find` answers this directly, walking the
tree and testing each file's timestamps, which turns a vague suspicion into a
concrete list.

`find` takes time tests in days with `-mtime` or minutes with `-mmin`, and
`-newermt` accepts an actual timestamp, which is easier to reason about.
`find /etc -newermt "2026-09-04 09:00" ! -newermt "2026-09-04 09:20"` lists files
in `/etc` changed inside a twenty-minute window. Adding `-printf` shows the time
alongside the name so the list is already ordered evidence.

```
$ find /etc -newermt "09:00" ! -newermt "09:20" -printf '%TY-%Tm-%Td %TH:%TM %p\n' \
    2>/dev/null | sort
2026-09-04 09:07 /etc/passwd
2026-09-04 09:07 /etc/shadow
```

Because `find` reports directories you cannot enter on stderr, `2>/dev/null`
keeps the list clean, and running it under `sudo` gives root's full view when the
scenario calls for it. On a Range host, narrowing to the window and reading the
changed files in time order is often enough to reconstruct what an attacker
touched, which is the heart of a timeline built from the disk rather than the
logs.

## Try it

1. On a Range host, list `/etc` files changed today with `find -mtime 0`.
2. Narrow to a specific window with two `-newermt` tests.
3. Add `-printf` so each result shows its modification time, then sort.
4. Explain why `2>/dev/null` and `sudo` change what the search returns.
