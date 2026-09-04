# Scheduled and writable paths

The last common escalation route is time and writability: something root runs on a
schedule, from a location the attacker can write to. If you can change what a
privileged job executes, you inherit its privilege when it next runs.

On a systemd host the equivalents of the old cron traps are writable unit files,
writable scripts that units call, and writable directories that hold either.
`find` locates them, and the fix is correct ownership and mode so only root can
change what root runs. `systemctl list-timers` shows what runs on a schedule, which
is the inventory to keep clean.

```
$ find /etc/systemd/system -perm -0002 2>/dev/null
$ systemctl list-timers --all
$ ls -l /usr/local/bin/backup.sh   # is a root-run script writable by others
```

On the Range you plant a writable script that a root timer runs, show how changing
it yields root, then lock it down and confirm the path is closed. The defensive
habit is to ask, for everything root executes automatically, whether a non-root
user could alter it, and to make the answer no. This is also where the defend
tier's detection meets the attack tier: a watch on those paths turns an escalation
attempt into an alert.

## Try it

1. On a Range host, find world-writable files under the systemd directories.
2. List scheduled timers and check the ownership of the scripts they run.
3. Demonstrate and then close an escalation through a writable root-run script.
4. Add an audit watch so a future change to that path raises an alert.
