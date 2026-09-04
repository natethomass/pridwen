# Scheduling with systemd

To run something on a schedule, Pridwen uses systemd timers rather than cron,
which is not installed by default. A timer is a small unit that starts a matching
service on a schedule, and because it is a unit, each run is logged and its next
fire time is visible.

A timer comes in a pair: `job.service` says what to run, and `job.timer` says
when. You enable the timer, not the service, and enabling the timer is what
schedules it. `systemctl --user list-timers` shows your timers with their next
and last run times.

```
# ~/.config/systemd/user/backup.service
[Service]
ExecStart=%h/.local/bin/backup.sh

# ~/.config/systemd/user/backup.timer
[Timer]
OnCalendar=daily
Persistent=true
[Install]
WantedBy=timers.target
```

After writing the pair, `systemctl --user daemon-reload` and `systemctl --user
enable --now backup.timer`. User timers need no root and run in your session;
system timers live in `/etc/systemd/system/` and need sudo. The advantage over
cron is visibility: `list-timers` shows exactly when it will next run, and
`journalctl --user -u backup.service` shows what happened last time, which a
crontab line cannot.

## Try it

1. Run `systemctl --user list-timers --all` and read the NEXT and LAST columns.
2. Write a simple service-and-timer pair that runs `date` and logs it.
3. Enable the timer with `enable --now` and confirm it appears in the list.
4. Read the service output afterward with `journalctl --user -u name`.
