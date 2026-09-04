# Filtering well

The skill with the journal is turning a flood into an answer, and that means
combining filters. The four that do most of the work are unit, priority, time,
and field matches, and they stack.

`-u name` limits to one service. `-p err` limits to a priority and worse, on the
syslog scale from 0 (emerg) to 7 (debug). `--since` and `--until` bound a time
window, taking forms like `today`, `-1h`, or a quoted `"2026-09-04 08:00"`.
Field matches like `_COMM=sshd` or `_PID=1234` are exact and fast because they
use the index.

```
$ journalctl -u sshd -p warning --since -2h
$ journalctl _COMM=sudo --since today
$ journalctl -g 'Failed|Accepted' -u sshd
```

`-g pattern` greps inside the journal with a regex and keeps the colours, which
beats piping to an external `grep` because it stays field-aware. When ordering
matters, `-o short-precise` adds microseconds. The habit to build is to start
broad, then add one filter at a time until the noise is gone, which is exactly
how a log analyst narrows an incident to its window.

## Try it

1. Pick a running service and read its last hour with `-u name --since -1h`.
2. Add `-p warning` and see how much the output shrinks.
3. Use `-g` with a pattern to find matching lines within one unit.
4. Match on a field like `_COMM=sudo` and compare it with a text search.
