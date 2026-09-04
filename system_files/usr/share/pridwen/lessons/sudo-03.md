# The audit trail

Every sudo invocation is recorded, and on a hardened system that record is a
feature you can read. It is what lets you answer "who changed this" after the
fact, and it is the reason a shared root password is discouraged.

The lines go to the journal and, through auditd, to the audit log. From the
journal, `journalctl _COMM=sudo` shows sudo's own view: the user, the terminal,
the working directory, the target user, and the exact command. From auditd,
`sudo ausearch -m USER_CMD` shows the same events decoded, and
`sudo aureport -x --summary` ranks executables by frequency.

```
$ journalctl _COMM=sudo --since today | tail -n 2
$ sudo ausearch -m USER_CMD -ts today | tail
```

Reading this well is a defender's skill. A sudo command you cannot explain, from
a terminal nobody was at, is the sort of line that starts an investigation. On
your own machine the same trail helps you retrace a change that broke something,
because you can see exactly what you ran and when. The trail is only as good as
the discipline of using sudo instead of a root shell for everything.

## Try it

1. Run three different `sudo` commands, then read them back with `journalctl _COMM=sudo`.
2. Run `sudo aureport -x --summary` and see which programs ran most under audit.
3. Find one sudo line and name the TTY, PWD and COMMAND fields.
4. Explain why a locked root account makes this trail more trustworthy.
