# What the logs remember

Every web request leaves a trace, and for a defender those traces are the record
of who tried what. Reading web logs closes the loop from the attacker's probe back
to the defender's account, and it is where the web node meets log analysis.

A web server's access log records the address, time, request line, status, and
often the user agent. The signatures of probing are visible in aggregate: a burst
of 404s walking through paths is scanning, a run of 500s may be someone finding an
error, and repeated odd parameters are injection attempts. The counting habit from
log analysis applies directly.

```
$ journalctl -u nginx --since -1h | grep -oE '"[A-Z]+ [^"]+"' | sort | uniq -c | sort -rn | head
     40 "GET / HTTP/1.1"
      8 "GET /admin HTTP/1.1"
      3 "GET /../../etc/passwd HTTP/1.1"
```

That last line, a path-traversal attempt, is the kind of thing counting surfaces
even in a busy log. On the Range you generate traffic, some benign and some
probing, then read it back and pick out the attacks. The skill is the same one
from the defend tier: turn a stream of requests into a ranked story, and know
which patterns mean someone is testing the door rather than walking through it.

## Try it

1. On the Range, generate a mix of normal and probing requests to a web host.
2. Read the access log and count request lines by frequency.
3. Pick out a scanning or traversal pattern from the counts.
4. Explain how this reuses the counting method from log analysis.
