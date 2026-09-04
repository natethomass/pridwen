# Baselines and anomalies

A detection is only as good as the baseline it compares against. To know what is
abnormal you first have to record what normal looks like: which services listen,
which users log in, what runs on a schedule. An anomaly is a departure from that
recorded normal.

Build a baseline from the same commands you would use to investigate, saved when
the system is known good. `systemctl list-unit-files --state=enabled`, `ss
-tulnp`, `sudo aureport -x --summary`, and the list of accounts each capture a
facet. Store them, then diff a later capture against them to see what moved.

```
$ ss -tulnp | sort > ~/baseline/listeners.txt
$ ss -tulnp | sort | diff ~/baseline/listeners.txt -
> LISTEN 0 0.0.0.0:4444 users:(("nc",pid=6001))
```

That `diff` line is a new listener on a suspicious port, the kind of thing a
baseline makes jump out. On a Range host you can create the anomaly deliberately
and watch your comparison catch it. The judgement is in choosing a baseline that
is stable enough to be meaningful but complete enough to matter, and in
remembering to refresh it after legitimate changes so real drift does not hide in
a stale comparison.

## Try it

1. Capture a baseline of listeners and enabled units on a Range host.
2. Start an unexpected listener and diff the new capture against the baseline.
3. Add a legitimate service and update the baseline to match.
4. Explain the risk of comparing against a baseline you never refresh.
