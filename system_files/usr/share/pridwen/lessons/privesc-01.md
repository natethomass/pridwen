# Finding the doors

Privilege escalation is going from an ordinary user shell to root through a
misconfiguration, and the defensive skill is finding those misconfigurations
before anyone else does. Most of them come down to two things: programs that run
with more power than the person who started them, and files that let the wrong
person change what root does. This lesson is about enumerating both on a host.

The read-only audits here are safe to run on your own Pridwen machine, and you
should: looking at your own host the way an attacker with a foothold would is
plain defence. The offensive follow-ups, where you actually plant a weakness and
climb it, run only against Range targets you own (Rocky 9 labs you start with
`pridwen enter rocky`). On a real job this same inventory is how you keep the
list of powerful programs short and known.

## Words you'll meet

- **root**: the superuser account (user id 0) that may do anything on the system; the prize of any escalation.
- **setuid**: a permission bit that makes a program run as its owner, not as the person who started it.
- **setuid-root**: a program owned by root with that bit set, so it runs as root for whoever launches it.
- **world-writable**: a file or directory anyone may change, shown by a `w` in the last group of an `ls -l` mode.
- **find**: the command that walks a directory tree and prints paths matching tests you give it.
- **enumerate**: to list everything of a kind so you can compare it against what should be there.

## How it works

Start with the setuid-root programs, because a flaw in one is a direct path to
root. You list them by asking `find` for files with the setuid bit set. The
`-perm -4000` test matches any file that has the setuid bit on (the `-` before
`4000` means "these bits at least"), and `-type f` keeps only regular files:

```
{user}@{host}:~$ find / -perm -4000 -type f 2>/dev/null
/usr/bin/sudo
/usr/bin/passwd
/usr/bin/su
/usr/bin/pkexec
```

Read that back. The `2>/dev/null` throws away the "Permission denied" noise from
directories you cannot enter, so you see only the hits. Each path is a program
that becomes root when run. This is a normal, short list: `sudo`, `passwd`,
`su`, and `pkexec` all legitimately need root. The defender's job is to know
this list and notice anything new on it. On Pridwen the read-only `/usr` keeps
this set fixed across upgrades, so the inventory stays trustworthy by design.

The second door is a writable file that root later trusts. If a script or unit
file that root runs can be edited by anyone, then anyone can decide what root
does. You search for world-writable files under the systemd directories, where a
writable unit would be most dangerous. The `-perm -0002` test matches the
world-write bit:

```
{user}@{host}:~$ find /etc/systemd /usr/lib/systemd -perm -0002 -type f 2>/dev/null
{user}@{host}:~$
```

An empty result, straight back to the prompt, is the healthy answer: nothing
under systemd is world-writable. On a Range host you deliberately create such a
file to see the danger, then fix the ownership and mode and confirm the search
comes back empty again. The mindset is to treat every powerful program and every
root-trusted file as a door, and to keep each one either shut or accounted for.

## When it goes wrong

A `find` command that prints many `find: '/proc/...': Permission denied` lines
just means you did not silence stderr; add `2>/dev/null` to send those messages
to the discard file so only real hits remain.

A setuid list longer than you expect on a Range host is the finding, not a bug:
compare it against the known-good set for the image and investigate anything
extra. `pridwen explain find` breaks down each test if the flags are the unclear
part.

`find: paths must precede expression` means an argument landed in the wrong
place, usually a path after a test; put the starting directory first, then the
`-perm` and `-type` tests.

## Try it

1. On your own host, list setuid-root programs with `find / -perm -4000 -type f 2>/dev/null` and read the short list back.
2. Explain in one sentence why each program on the list legitimately needs root.
3. Search for world-writable files under the systemd directories and confirm the result is empty.
4. On a Range host, create a world-writable file under a systemd directory, find it, then fix its mode and confirm it is gone.
5. Explain how an immutable `/usr` keeps the setuid inventory trustworthy across upgrades.

## Remember

- Escalation usually rides on a setuid-root program with a flaw, or a root-trusted file the wrong person can write.
- `find / -perm -4000 -type f` is your setuid inventory; keep it short, known, and unchanged.
- Pridwen's read-only `/usr` freezes the setuid set across upgrades, so a new entry there would stand out immediately.
