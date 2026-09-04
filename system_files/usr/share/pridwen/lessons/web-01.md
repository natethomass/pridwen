# HTTP as a surface

A web server is a door that answers strangers, which makes it one of the most
probed surfaces on any host. Understanding it defensively starts with seeing a
request and response as plain text, because that is all they are.

`curl -v` shows the whole exchange: the request line, the headers you send, and
the status and headers that come back. The status code is the first tell: 200 is
success, 403 is forbidden, 404 is not found, 500 is a server error. Response
headers can leak the server software and version, which recon feeds on.

```
$ curl -v http://web-01/ 2>&1 | head -n 20
> GET / HTTP/1.1
> Host: web-01
< HTTP/1.1 200 OK
< Server: nginx/1.24.0
```

On a Range web host you read these exchanges and then trim what gives too much
away: unnecessary headers, verbose error pages that reveal paths and versions,
directory listings that expose files. Every response is also a line in the
server's log, so the same exchange you study as an attacker's probe is what a
defender reads afterward. Seeing HTTP as readable text, logged at both ends,
demystifies both the attack and the defence.

## Try it

1. On the Range, run `curl -v` against a web host and read the request and response.
2. Identify the status code and the `Server` header.
3. Trigger a 404 and read how much the error page reveals.
4. Find the matching line in the server's access log.
