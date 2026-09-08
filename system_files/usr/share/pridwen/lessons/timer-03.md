# One-shots and debugging

Not every scheduled job deserves two files in `{home}/.config/systemd/user/`. Sometimes you want "run this once in ten minutes" or "run this at nine tomorrow and then forget it". Traditional systems used the `at` command for that. Pridwen uses `systemd-run`, which creates a temporary timer and service on the spot, with all the same logging as a permanent pair, and throws them away when the job has run.

The same machinery is also the fastest way to learn how timers behave, because you can schedule something thirty seconds away and watch it happen. And when a permanent timer misbehaves, the way to find out why is the same as for any unit: read its journal and its status. On a job, "did the backup run last night, and what did it say" is a question you will be asked, and this lesson is how you answer it in under a minute.

## Words you'll meet

- **transient unit**: a unit created on the fly by `systemd-run`, with no file on disk, gone once it has finished.
- **at**: the traditional one-shot scheduler, not installed on Pridwen.
- **tag**: a short label attached to a journal line so you can find it later; `logger -t` sets one.
- **exit code**: the number a program returns when it finishes; `0` is success and the journal records any other value.
- **status**: `systemctl status`, a summary of a unit's state, last result, and recent log lines.
- **failed state**: what a service enters when its program returned non-zero; the timer still fires again next time.

## How it works

`systemd-run --user` creates and starts a transient unit as you. With `--on-active=30s` it makes a timer that fires thirty seconds after it is created; without any `--on-` option it would run the command immediately. The command after the options is what to run, and it needs a full path, because the unit does not use your shell's PATH.

```
{user}@{host}:~$ systemd-run --user --on-active=30s /usr/bin/logger -t oneshot "timer fired"
Running timer as unit: run-r7c2a1e5d9b.timer
Will run service as unit: run-r7c2a1e5d9b.service
```

The two lines name the units systemd created; the random part is different every time. `logger -t oneshot` writes a line to the journal with the tag `oneshot`. After thirty seconds the timer fires the service, the service runs `logger`, and both units disappear. Find the line by its tag.

```
{user}@{host}:~$ journalctl --user -t oneshot --since -2min
Sep 07 09:52:41 {host} oneshot[5210]: timer fired
```

`-t oneshot` selects lines with that tag and `--since -2min` limits the window. The line shows the time it actually ran, which should be about thirty seconds after you typed the command. That is a complete round trip: schedule, fire, log, read.

For a specific moment rather than a delay, use `--on-calendar` with a date and time in the same grammar as `OnCalendar` in a timer file.

```
{user}@{host}:~$ systemd-run --user --on-calendar="2026-09-08 09:00" /usr/bin/logger -t oneshot "good morning"
Running timer as unit: run-r3f9e0b2c71.timer
Will run service as unit: run-r3f9e0b2c71.service
{user}@{host}:~$ systemctl --user list-timers run-r3f9e0b2c71.timer
NEXT                        LEFT     LAST PASSED UNIT                   ACTIVATES
Tue 2026-09-08 09:00:00 UTC 23h left -    -      run-r3f9e0b2c71.timer  run-r3f9e0b2c71.service
```

This is what `at` did, and the transient timer shows up in `list-timers` like any other, so you can see it is waiting. `systemctl --user stop run-r3f9e0b2c71.timer` cancels it.

Now debugging a permanent timer. When the job it runs fails, the service goes into the failed state and the journal has the details. Make `backup.service` fail on purpose by pointing its `ExecStart` at a script that exits with `1`, reload, and start the service by hand rather than waiting for the timer.

```
{user}@{host}:~$ systemctl --user start backup.service
Job for backup.service failed because the control process exited with error code.
See "systemctl --user status backup.service" and "journalctl --user -xeu backup.service" for details.
{user}@{host}:~$ systemctl --user status backup.service
x backup.service - Copy Documents to the backup directory
     Loaded: loaded ({home}/.config/systemd/user/backup.service; static)
     Active: failed (Result: exit-code) since Mon 2026-09-07 09:58:10 UTC; 5s ago
    Process: 5388 ExecStart={home}/.local/bin/backup (code=exited, status=1/FAILURE)

Sep 07 09:58:10 {host} backup[5388]: rsync failed
Sep 07 09:58:10 {host} systemd[1834]: backup.service: Main process exited, code=exited, status=1/FAILURE
Sep 07 09:58:10 {host} systemd[1834]: backup.service: Failed with result 'exit-code'.
```

Read the status from the top. `Active: failed (Result: exit-code)` says the program itself returned a failure. The `Process` line shows the exact command and `status=1/FAILURE`, the exit code. Under it are the last journal lines, including the `rsync failed` message the script logged, which is why the scripting node asked you to log on the failure path. `journalctl --user -u backup.service` gives the full history, and `-xe` adds explanations and jumps to the end.

A failed service does not stop the timer. The timer fires again at its next elapse, the service tries again, and each attempt is recorded, so a job that was broken for a week shows a week of `Failed` lines. That record, without adding any logging of your own, is the main reason to prefer timers over a script that loops with `sleep` in the background.

## When it goes wrong

`bash: at: command not found` is exit 127: `at` is not in the image. `systemd-run --user --on-calendar="2026-09-08 09:00" command` is the replacement, and `list-timers` shows it waiting.

`Failed to start transient timer unit: Unit run-r....service is not loaded properly: Exec format error` or a status of `203/EXEC` means the command could not be executed: usually a relative name like `backup` rather than the full `/usr/bin/logger` or `{home}/.local/bin/backup`, or a script without the execute bit. Give the absolute path and check `chmod +x`.

The journal shows `Starting` and `Finished` but not the output you expected. Output that goes to a file appears in the file, not the journal; only what the program prints, or sends with `logger`, is captured. Add a `logger -t` line and look for its tag. `pridwen why` will translate any of these after they happen, and `pridwen explain systemd-run` walks through the flags.

## Try it

1. Run `systemd-run --user --on-active=30s /usr/bin/logger -t oneshot "timer fired"` and note the unit names it prints.
2. Run `systemctl --user list-timers` straight away and find the `run-` timer with under a minute in `LEFT`.
3. Wait a minute, run `journalctl --user -t oneshot --since -2min`, and expect `timer fired` with the time it ran.
4. Schedule one for tomorrow with `--on-calendar`, see it in `list-timers`, then cancel it with `systemctl --user stop` on the timer name.
5. Edit `backup.service` so `ExecStart` points at `/usr/bin/false` (a program that always exits `1`), run `systemctl --user daemon-reload`, then `systemctl --user start backup.service`, and read the failure.
6. Run `systemctl --user status backup.service` and find `status=1/FAILURE`. Put `ExecStart` back, reload, and start it again to see `Finished`.

## Remember

- `systemd-run --user --on-active=30s command` schedules a one-off transient job; `--on-calendar` replaces `at`.
- Debug a scheduled job as a unit: `systemctl --user status name.service` for the last result, `journalctl --user -u name.service` for the history.
- A failed service does not stop its timer; every attempt is recorded, which is why timers beat a background loop.
