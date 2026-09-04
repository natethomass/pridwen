# Audit and the old files

The journal holds most logs, but two other places matter. The audit log, written
by auditd, records security-relevant events at the kernel level, and the classic
`/var/log` text files exist only if a program writes them, which on Pridwen is
rare.

The audit log lives in `/var/log/audit/` and is root-only. Its tools are
`ausearch` to query and `aureport` to summarise. `sudo ausearch -m USER_CMD -ts
today` shows commands run under sudo; `-m avc` shows SELinux denials; `-m
LOGIN` shows logins. This is where you look when the journal is not detailed
enough for a security question.

```
$ sudo ausearch -m LOGIN -ts today | tail
$ sudo aureport --summary
```

Old habits point at files that are not here: `/var/log/messages`,
`/var/log/secure`, `/var/log/auth.log`. Their contents are in the journal:
`journalctl -k` for the kernel, `journalctl _COMM=sudo` for the sudo lines, and
`journalctl -u name` for a service. Login history, once in `/var/log/wtmp`, now
comes from `wtmpdb last` and `systemd-logind`. Knowing where each kind of record
actually lives saves a lot of `cat`-ing files that were never written.

## Try it

1. Run `sudo ausearch -m USER_CMD -ts today` and read a decoded sudo command.
2. Run `sudo aureport --summary` and skim the counts.
3. Confirm `/var/log/secure` is absent, then find its content with `journalctl _COMM=sudo`.
4. Run `journalctl -k | tail` and read a few kernel messages.
