# Where defenders look

Finding persistence is a matter of knowing every place a program can be set to
start and checking each against what should be there. It is the detection tier
applied to one question: what runs without me asking, and did any of it appear
recently.

The checklist covers unit files (system and user), timers, login and shell
profiles (`~/.bashrc`, `~/.profile`, `/etc/profile.d/`), desktop autostart, added
SSH keys, and cron if it was ever installed. A baseline of these captured when the
host is known good turns the check into a diff, which is far faster than reading
each place fresh.

```
$ ls -la ~/.config/autostart /etc/xdg/autostart 2>/dev/null
$ find /etc/systemd/system /etc/systemd/user -newermt "2026-09-01" 2>/dev/null
$ grep -r . ~/.bashrc ~/.bash_profile /etc/profile.d 2>/dev/null | tail
```

The `-newermt` search is the sharpest single move: startup entries created after a
known-good date are exactly the suspicious ones. On the Range you hunt a planted
mechanism using this checklist and confirm you can find any category. Because
Pridwen's `/usr` is immutable, persistence cannot hide there and must live in the
mutable, checkable places, which narrows the hunt and is one more benefit of the
image-based design.

## Try it

1. On a Range host, walk the persistence checklist and read each location.
2. Use `-newermt` to find startup entries created after a known-good date.
3. Locate a planted mechanism and explain which category it used.
4. Explain why an immutable `/usr` shortens the list of places to check.
