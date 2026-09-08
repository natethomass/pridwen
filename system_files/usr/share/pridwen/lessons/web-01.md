# HTTP as a surface

A web server is a program that listens for requests over the network and answers
them, and because it answers anyone who can reach it, it is one of the most
probed surfaces on any host. The good news is that a request and its reply are
just plain text: once you can read that text, the attack and the defence both
stop being mysterious. This lesson is about seeing the exchange as it really is.

Everything here runs only against Range targets you own. The Range is Pridwen's
lab: Rocky 9 practice machines you start yourself (`pridwen enter rocky` drops
you into one) and reach by a lab name like `range-web`. You never point these
tools at a site you do not control. On a real job this same reading skill is how
you shrink what your own servers give away to a stranger.

## Words you'll meet

- **HTTP**: HyperText Transfer Protocol, the plain-text rules a browser and a web server use to ask for and return pages.
- **request**: the message a client sends, whose first line names the method, the path, and the version, like `GET / HTTP/1.1`.
- **response**: the message the server sends back, whose first line is a status line like `HTTP/1.1 200 OK`.
- **header**: a `Name: value` line carrying extra facts (who is asking, what software answered) before the body.
- **status code**: a three-digit number that says how the request went: 200 success, 403 forbidden, 404 not found, 500 server error.
- **curl**: a command-line program that sends one HTTP request and prints the reply, so you see the raw exchange without a browser in the way.

## How it works

The quickest way to see a server's own words is to ask for just the response
headers. The `-I` flag makes curl send a HEAD request, which asks for the
headers without the page body, and `-s` is silent, meaning it drops the progress
meter so only the reply is printed.

```
{user}@{host}:~$ curl -sI http://range-web/
HTTP/1.1 200 OK
Server: nginx/1.24.0
Content-Type: text/html; charset=UTF-8
Content-Length: 1256
```

Read that back line by line. The first line is the status line: `HTTP/1.1` is
the version the server speaks, and `200 OK` is the status code, meaning the
request you sent (a plain `GET /`, asking for the root path `/`) succeeded. The
next line, `Server: nginx/1.24.0`, is the tell a defender cares about: it names
the web software and its exact version, which is a gift to anyone deciding what
to attack. `Content-Type` says the body is HTML text, and `Content-Length` says
how many bytes the body would have been. A normal, healthy result is a 200 with
as few extra headers as possible.

When you ask for a path that does not exist, the status line changes, and a
verbose server often prints a longer body that leaks internal detail:

```
{user}@{host}:~$ curl -sI http://range-web/nope | head -n 1
HTTP/1.1 404 Not Found
```

Here the pipe (`|`) sends curl's output into `head -n 1`, which keeps only the
first line. That line is the status: `404 Not Found` means the path was not on
the server. On the Range, your defensive move is to trim the giveaways: hide the
`Server` version, replace error pages that print file paths and versions, and
turn off directory listings that expose files. Every request above is also one
line in the server's access log, so the same exchange you read as a probe is
what a defender reads afterward.

## When it goes wrong

`curl: (6) Could not resolve host: range-web` means curl could not turn the name
`range-web` into an address. The lab host is not up or its name is not known
yet; start the Range target and use the address or name it prints.

`curl: (7) Failed to connect to range-web port 80: Connection refused` means the
machine answered but nothing is listening on port 80. The web server is not
running on the target, or it listens on another port; check the service on the
Range host before probing again.

`curl: (22) The requested URL returned error: 404` appears when you pass `-f`
(fail): curl treats any status of 400 or above as an error and exits non-zero.
Run `pridwen why` right after and the Coach reads that exit code back for you.

## Try it

1. Start a Range web target with `pridwen enter rocky` (or your lab's start step) and note its name.
2. Run `curl -sI http://range-web/` and read the status line and the `Server` header back.
3. Point at the status code and the `Server` header in the output and say what each reveals.
4. Ask for a path that does not exist and read the `404` status the server returns.
5. Open the server's access log on the target and find the two requests you just made.

## Remember

- An HTTP request and response are plain text; `curl -sI` shows the status line and headers the server sends back.
- The status code and the `Server` header are the first things a stranger reads, so they are the first things a defender trims.
- Every request you send is a logged line at the other end, which is why the attacker's view and the defender's record are the same text.
