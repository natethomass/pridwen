# Calendar and catch-up

A timer is only as good as the schedule written into it, and a schedule is easy to get wrong by an hour, a day, or a whole week. The difference between systemd and cron here is that systemd will tell you, before you enable anything, exactly when an expression would fire. Checking first is a habit that costs ten seconds and saves the report that ran on Sunday instead of Monday.

The second half of a reliable schedule is what happens when the machine was off at the appointed time. A desktop or laptop is asleep at three in the morning more often than not, and a job that simply never runs on those days is worse than useless because you believe it ran. You already know from the previous lesson that a `.timer` file has an `OnCalendar` line and that `list-timers` shows the next fire time; this lesson is about getting that line right.

## Words you'll meet

- **calendar expression**: the text after `OnCalendar=`, describing which moments on the clock a timer fires.
- **elapse**: systemd's word for a timer firing; "next elapse" is the next time it will run.
- **normalized form**: the full, unambiguous spelling of an expression, with every field filled in.
- **wall clock**: ordinary date and time, the kind that keeps moving while the machine is off.
- **monotonic time**: time measured from an event such as boot, which only counts while the machine is running.
- **catch-up**: running a job that was missed because the machine was off, done once when it comes back.
- **iteration**: one fire time in a list of future ones.

## How it works

A calendar expression reads left to right: an optional day of the week, then a date as year-month-day, then a time as hour:minute:second. A `*` in any position means "every". So `Mon *-*-* 09:00` is every Monday of every year, month and day, at nine. `systemd-analyze calendar` takes an expression and shows when it would next fire.

```
{user}@{host}:~$ systemd-analyze calendar "Mon *-*-* 09:00"
  Original form: Mon *-*-* 09:00
Normalized form: Mon *-*-* 09:00:00
    Next elapse: Mon 2026-09-14 09:00:00 UTC
       From now: 6 days left
```

`Original form` is what you typed. `Normalized form` is how systemd understood it, with the seconds filled in; if that line is not what you meant, the expression is wrong. `Next elapse` is the answer, and `From now` turns it into a distance. Reading the normalized form back is the whole check: a missing field or a misplaced number shows up there.

The shorthands are the expressions you will use most. `daily` is `*-*-* 00:00:00`, `hourly` is `*-*-* *:00:00`, `weekly` is `Mon *-*-* 00:00:00`, and `monthly` is `*-*-01 00:00:00`. `--iterations` shows more than one future time, which is the way to confirm a repeating pattern.

```
{user}@{host}:~$ systemd-analyze calendar --iterations 3 weekly
  Original form: weekly
Normalized form: Mon *-*-* 00:00:00
    Next elapse: Mon 2026-09-14 00:00:00 UTC
       From now: 6 days left
       Iter. #2: Mon 2026-09-21 00:00:00 UTC
       From now: 1 week 6 days left
       Iter. #3: Mon 2026-09-28 00:00:00 UTC
       From now: 2 weeks 6 days left
```

Three Mondays a week apart is what weekly should look like. If you wanted a job at three in the morning every day, you would write `*-*-* 03:00` and expect the iterations to be one day apart. A range works too: `Mon..Fri *-*-* 18:00` is six in the evening on weekdays, and `*-*-* 09..17:00` is every hour on the hour from nine to five.

Now the catch-up. Suppose `backup.timer` says `OnCalendar=daily`, so midnight, and the laptop was shut at eleven and opened at eight. Without any other setting, the midnight elapse simply passed while the machine was off, and nothing runs until the next midnight. `Persistent=true` changes that: systemd remembers the last time the timer fired, notices at wake that a scheduled time went by, and runs the service once, straight away.

```
{user}@{host}:~$ grep -A3 '^\[Timer\]' {home}/.config/systemd/user/backup.timer
[Timer]
OnCalendar=daily
Persistent=true
```

`grep -A3` prints the matching line and the three after it (`-A` means after). The two lines under `[Timer]` are the whole schedule: when, and catch up if missed. On a machine that is never off, `Persistent=true` changes nothing, so it is safe to write everywhere.

There is one kind of timer it does not apply to. `OnBootSec=15min` or `OnUnitActiveSec=1h` measure monotonic time, counted from boot or from the last run, and stop counting when the machine is off. There is no "missed" moment to catch up on, because the clock they use did not move. Use those for "a while after boot" or "every hour while running"; use `OnCalendar` with `Persistent=true` for "at this time of day, even if we were asleep".

## When it goes wrong

`Failed to parse calendar specification 'Mon 9am': Invalid argument` means the expression is not in systemd's grammar. There is no am or pm; times are 24-hour, and the date part is year-month-day. Write `Mon *-*-* 09:00` and run `systemd-analyze calendar` on it before putting it in the file.

The timer fires, but at the wrong hour. `Next elapse` is printed in the system time zone, and a fresh Pridwen install may be on UTC until the wizard's timezone page or `timedatectl set-timezone` sets a local one. Check `timedatectl` and read the `Time zone` line.

A `Persistent=true` timer runs the job the moment you log in after a few days away, which surprises people the first time. That is the catch-up working. If the job must never run in the daytime, add `OnCalendar` times only, and leave `Persistent` off. `pridwen explain systemd-analyze` walks through the flags used here.

## Try it

1. Run `systemd-analyze calendar "Mon *-*-* 09:00"` and read the `Next elapse` line. Count the days to the next Monday and compare with `From now`.
2. Run `systemd-analyze calendar --iterations 3 daily` and confirm the three times are exactly one day apart.
3. Run `systemd-analyze calendar "Mon..Fri *-*-* 18:00"` and check the normalized form says `Mon..Fri`.
4. Run `systemd-analyze calendar "Mon 9am"` and read the `Invalid argument` error.
5. Open `{home}/.config/systemd/user/backup.timer` from the previous lesson, confirm `Persistent=true` is there, and say in one sentence what it does for a laptop that was asleep at midnight.
6. Change `OnCalendar=daily` to `OnCalendar=*-*-* 03:00`, run `systemctl --user daemon-reload`, and check `list-timers` shows three in the morning as `NEXT`.

## Remember

- Always run `systemd-analyze calendar` on an expression before enabling it, and read the normalized form back.
- Day of week, then year-month-day, then hour:minute; `*` means every; `daily`, `weekly` and `hourly` are shorthands.
- `Persistent=true` runs a missed `OnCalendar` job once when the machine comes back; monotonic timers like `OnBootSec` have nothing to catch up.
