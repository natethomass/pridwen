# Reading logs as a story

Log analysis is less about tools than about a habit: read the journal as a
narrative and notice the line that does not fit the others. Normal activity has a
rhythm, and an incident breaks it. The journal is where that rhythm lives.

The core moves are filtering to a window and following forward. `journalctl
--since --until` bounds a time; once you find the first odd event, drop the
`--until` and read forward to see what followed. `-g pattern` greps with a regex
and keeps the field awareness, so `journalctl _COMM=sshd -g 'Failed|Accepted'`
puts failures and successes side by side.

```
$ journalctl --since "09:00" --until "09:15" -o short-precise
$ journalctl _COMM=sshd -g 'Accepted' --since today
```

On a Range host you practise this where the stakes are a scenario, not a real
breach. A run of failed logins followed by one accepted from the same address is
a story worth reading closely. The precise timestamp format matters when ordering
is the whole question, which is why `-o short-precise` earns its place. Build the
timeline first, then explain it; the tools in the next lessons only sharpen the
same reading.

## Try it

1. On a Range host, bound a fifteen-minute window with `--since` and `--until`.
2. Use `-g` to pull both failed and accepted SSH lines together.
3. Find one interesting event, then read forward from it without an end bound.
4. Add `-o short-precise` and explain when the extra precision matters.
