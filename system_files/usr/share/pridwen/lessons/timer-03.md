# One-shots and debugging

Not every scheduled task deserves a pair of files. For a quick or one-time job,
`systemd-run` schedules a transient unit on the fly, and the journal captures its
output the same way. It is the fastest way to test scheduling behaviour.

`systemd-run --user --on-active=5min command` runs something once, five minutes
from now. `--on-calendar="2026-09-05 09:00"` picks an absolute time, replacing the
old `at` command, which is not installed. Because it creates a real unit, you find
its output under a generated name in the journal.

```
$ systemd-run --user --on-active=30s /usr/bin/logger "timer fired"
Running timer as unit: run-r42.timer
$ journalctl --user -t root --since -1min
```

When a scheduled job misbehaves, debug it as a unit. `journalctl --user -u
name.service` has the output and the exit status of the last run; a failing
service keeps retrying on its schedule until it succeeds or you disable the timer.
Because every run is recorded, you can answer "did it run and what did it do"
without adding logging to the script itself, which is the main reason to prefer
timers over a bare background loop.

## Try it

1. Schedule a one-shot with `systemd-run --user --on-active=30s` and wait for it.
2. Find its output in the journal afterward.
3. Make a timer's service fail on purpose and read the failure with `journalctl`.
4. Explain when a transient `systemd-run` job is better than writing unit files.
