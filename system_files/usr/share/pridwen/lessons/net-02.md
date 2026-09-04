# Sockets and names

Two questions come up constantly: what is listening on this machine, and why did
a name not resolve. `ss` answers the first, and `resolvectl` answers the second.

`ss -tulnp` is the phrase to keep: TCP and UDP, listening sockets, numeric ports,
and the owning process. With `sudo` it can name every process, not just yours.
`ss -tn` shows established connections. The old `netstat` is not installed; `ss`
replaced it and is faster.

```
$ ss -tlnp
State  Recv-Q Local Address:Port  Process
LISTEN 0      127.0.0.1:631       cups
LISTEN 0      [::1]:6600          mpd
$ resolvectl query example.com
example.com: 93.184.216.34
```

Name resolution on Pridwen goes through systemd-resolved over DNS-over-TLS, so
queries are encrypted to the resolver. When a name fails, `resolvectl query name`
tests DNS alone and `resolvectl status` shows which servers an interface is
using. `getent hosts name` resolves the same way programs do. Separating "can I
resolve the name" from "can I reach the address" is the fastest way to locate a
network problem.

## Try it

1. Run `ss -tlnp` and identify one listening service and its port.
2. Run `sudo ss -tlnp` and notice the extra process names root can see.
3. Run `resolvectl query` on a domain and read the address back.
4. Run `resolvectl status` and confirm DNS over TLS is on.
