# Services and versions

Beyond which ports are open, recon tries to learn what software sits behind them
and which version, because a version maps to known weaknesses. The defence is to
give away less, and to keep what you do run current.

A version scan (`nmap -sV`) coaxes each service into revealing a banner. Many
services announce themselves by default: a web server sends a `Server` header, an
SSH daemon sends its version string at connect. On the Range you read these from
both ends, seeing what the scanner learns and where the service told it.

```
$ curl -sI http://web-01 | grep -i server
Server: nginx/1.24.0
$ ss -tlnp | grep :22    # then note the sshd version it would present
```

The defender's response is measured. You cannot hide that a port is open if it
must serve, but you can trim needless banners, keep versions patched so a known
version is not a known hole, and remove services that do not need to run at all.
The lesson is that recon rewards a sloppy, chatty, out-of-date host and gets
little from a lean, quiet, current one, which is entirely within your control.

## Try it

1. On the Range, read a web host's `Server` header with `curl -sI`.
2. Note the version and reason about what an attacker would look up.
3. Reduce or remove a banner where the service allows it.
4. Explain why keeping versions current blunts version-based recon.
