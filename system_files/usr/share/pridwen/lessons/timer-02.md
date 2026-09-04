# Calendar and catch-up

The schedule of a timer is usually an `OnCalendar` expression, and systemd gives
you a way to check one before you trust it. `systemd-analyze calendar` takes an
expression and prints the next times it would fire, so you never have to guess.

Calendar expressions read left to right as day-of-week, then date, then time:
`Mon *-*-* 09:00` is every Monday at nine, `*-*-* 03:00` is every day at three,
and shorthands like `daily`, `weekly` and `hourly` cover the common cases.
Verifying beforehand catches the off-by-one that would otherwise run at the wrong
hour.

```
$ systemd-analyze calendar "Mon *-*-* 09:00"
  Normalized form: Mon *-*-* 09:00:00
    Next elapse: Mon 2026-09-08 09:00:00
$ systemd-analyze calendar --iterations 3 daily
```

`Persistent=true` is the setting that makes timers work on a laptop. Without it, a
job scheduled for 03:00 simply does not run if the machine was asleep; with it,
systemd runs the missed job once after the machine wakes. It applies to
`OnCalendar` timers, which track wall-clock time, not to monotonic ones like
`OnBootSec`. Choosing the right kind and verifying the expression are what make a
schedule reliable rather than hopeful.

## Try it

1. Run `systemd-analyze calendar "Mon *-*-* 09:00"` and read the next elapse.
2. Try an invalid expression and read how it is rejected.
3. Add `Persistent=true` to a timer and explain what it changes for a laptop.
4. Use `--iterations 3` to see the next three runs of a `daily` timer.
