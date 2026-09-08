# Where defenders look

Finding persistence is a matter of knowing every place a program can be set to
start and checking each one against what should be there. It is the detection
skill from the defend tier aimed at a single question: what runs on this host
without me asking, and did any of it appear recently. This lesson turns the tour
from the last lesson into a repeatable hunt.

Everything here runs only against Range targets you own: Rocky 9 lab hosts you
start with `pridwen enter rocky`, where a mechanism has been planted for you to
find. You never sweep a system you do not control. On a real job this checklist
is what you run when you suspect a host is compromised, and the baseline habit
below is what turns a slow read into a fast diff.

## Words you'll meet

- **checklist**: the fixed set of startup locations you walk every time, so nothing is forgotten under pressure.
- **baseline**: a snapshot of those locations taken when the host is known good, to compare against later.
- **diff**: the difference between now and the baseline; the short list of what changed.
- **shell profile**: files the shell runs at login, such as `{home}/.bashrc`, `{home}/.bash_profile`, and scripts in `/etc/profile.d/`.
- **mtime**: a file's modification time, which `find` can test to catch files touched after a chosen date.
- **immutable**: unchangeable; Pridwen's `/usr` is read-only, so nothing can be planted there.

## How it works

The checklist covers unit files (system and user), timers, login and shell
profiles, desktop autostart, added SSH keys, and cron if it was ever installed.
Walking it fresh works, but the sharpest single move is to ask which startup
entries are new. The `-newermt` test in `find` matches files modified after a
timestamp you give it, so a known-good date turns the hunt into a diff:

```
{user}@{host}:~$ find /etc/systemd/system /etc/systemd/user -newermt "2026-09-01" 2>/dev/null
/etc/systemd/system/sneaky.service
```

Read that back. `find` walked the two systemd directories, `-newermt
"2026-09-01"` kept only files changed after the first of September, and
`2>/dev/null` dropped permission noise. The one hit, `sneaky.service`, is a unit
that appeared after your known-good date: exactly the kind of thing a fresh read
of the whole directory would bury. That single line is the finding.

The shell profiles are the other place to read directly, because a single added
line there runs at every login. You dump them and read the tail:

```
{user}@{host}:~$ grep -r . {home}/.bashrc {home}/.bash_profile /etc/profile.d 2>/dev/null | tail -n 3
{home}/.bashrc:# Pridwen coach hooks
{home}/.bashrc:source /usr/share/pridwen/shell/coach.bash
/etc/profile.d/lang.sh:export LANG
```

Here `grep -r .` prints every non-empty line (`-r` recurses into the given
paths, `.` matches any character), and `tail -n 3` keeps the last three. These
three are expected: the Coach hook and a language setting. A line that runs an
unfamiliar program from a hidden path would be the finding instead. Because
Pridwen's `/usr` is immutable, persistence cannot hide there and must live in
these mutable, checkable places, which shortens the hunt and is one more benefit
of the image-based design.

## When it goes wrong

An empty result from the `-newermt` search means nothing under those directories
changed after your date, which is the clean answer, not a failure. If you expected
a hit, check that your baseline date is actually before the plant.

`grep: {home}/.bash_profile: No such file or directory` means that particular
profile does not exist on the account; that is normal, and the `2>/dev/null`
already hides it. The absence of a file is one less place to hide.

`find: unknown primary or operator` near `-newermt` means the date string was
not quoted or is malformed; wrap it in quotes as `"2026-09-01"`. Run `pridwen
explain find` if the test flags are the unclear part.

## Try it

1. On a Range host, walk the persistence checklist and read each location once.
2. Use `find ... -newermt "<known-good date>"` to list startup entries created after that date.
3. Read the shell profiles with `grep -r . ...` and pick out any line you cannot account for.
4. Locate the planted mechanism and say which category it used.
5. Explain in one sentence why an immutable `/usr` shortens the list of places to check.

## Remember

- Persistence hunting is a fixed checklist plus a baseline: unit files, timers, profiles, autostart, SSH keys, and cron.
- `find ... -newermt "<date>"` is the sharpest move, turning a slow full read into a short diff of what is new.
- Pridwen's immutable `/usr` means nothing can hide in the system tree, so the hunt narrows to the mutable places.
