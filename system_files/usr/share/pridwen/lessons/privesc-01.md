# Finding the doors

Privilege escalation is going from an ordinary shell to root through a
misconfiguration, and the defensive skill is finding those misconfigurations
first. Most are about programs that run with more power than the caller, and
about files that let the wrong person change what root does.

The classic hunt is for setuid-root binaries, which run as root no matter who
starts them, so a flaw in one is a path up. `find / -perm -4000 -type f
2>/dev/null` lists them; the defender keeps that list short and known. World-
writable files in sensitive places are the other door: a writable unit file or
script that root runs hands root to anyone.

```
$ find / -perm -4000 -type f 2>/dev/null
/usr/bin/sudo
/usr/bin/passwd
$ find /etc/systemd /usr/lib/systemd -perm -0002 -type f 2>/dev/null
```

On the Range you run these audits, compare against what should be there, and
remove the bit or fix the ownership on anything that should not. On Pridwen the
read-only image keeps the setuid set fixed and known, which is itself a defence.
The mindset is to look at your own host the way an attacker with a foothold would,
enumerating every program and file that could lift them higher.

## Try it

1. On a Range host, list setuid binaries and compare against a known-good set.
2. Search for world-writable files under the systemd directories.
3. Remove a needless setuid bit on a lab file and confirm the change.
4. Explain how an immutable `/usr` keeps the setuid inventory trustworthy.
