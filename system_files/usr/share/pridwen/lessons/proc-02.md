# Signals and kill

Stopping a process means sending it a signal, a small numbered message the
kernel delivers. `kill` sends one to a pid, despite the name most signals are
polite requests rather than force.

The default is SIGTERM (15), which asks a program to shut down cleanly so it can
save and close files. SIGKILL (9) cannot be caught and ends the process
immediately, with no chance to clean up, so it is a last resort after SIGTERM
was ignored. You may only signal processes that run as you; another user's
process needs `sudo`, and a service is better stopped through its unit.

```
$ pgrep -a sleep
5001 sleep 600
$ kill 5001
$ pgrep sleep || echo gone
gone
```

`kill` wants a pid, not a name. To signal by name use `pkill name`, and check
first with `pgrep -a name` so you see exactly what would be hit. On Pridwen the
old `killall` from psmisc is not installed; `pkill` from procps does the same
job. If `kill` reports "No such process", the pid already exited, so re-check
the current one with `pgrep`.

## Try it

1. Start `sleep 300 &` and note the pid the shell prints.
2. Run `pgrep -a sleep` to confirm it, then `kill` that pid.
3. Start two sleeps and stop both by name with `pkill sleep`.
4. Explain when `kill -9` is justified and why it is not the default.
