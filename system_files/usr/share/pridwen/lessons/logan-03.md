# From logs to a timeline

The output of analysis is a timeline: an ordered list of what happened and when,
built from more than one source. The journal, the audit log, and a service's own
logs each hold part of the story, and lining them up is what turns clues into an
account.

Anchor on a single confirmed event with a precise timestamp, then gather what
each source says around that moment. `journalctl -o short-precise` and `sudo
ausearch -ts` with the same window let you interleave system and audit views.
Because clocks are kept accurate by chrony, timestamps from different sources are
comparable, which is exactly why an accurate clock is part of the baseline.

```
$ journalctl --since "09:10:00" --until "09:12:00" -o short-precise
$ sudo ausearch -ts 09:10:00 -te 09:12:00
```

Write the timeline down as you go, one line per event with its time and source.
On a Range scenario this is the deliverable: a short, ordered story that a
teammate could follow. The discipline of citing which log each line came from is
what makes the account defensible, and it is the same discipline that carries
into real incident response, where the timeline is the first thing anyone asks
for.

## Try it

1. Pick a confirmed event on a Range host and note its precise time.
2. Pull the journal and audit views for a two-minute window around it.
3. Write a five-line timeline, citing the source of each line.
4. Explain how an accurate clock lets you merge two logs into one order.
