# What the logs remember

Every web request leaves a trace, and for a defender those traces are the record
of who tried what and when. Reading web logs closes the loop from the probe you
sent in the earlier lessons back to the line it wrote at the other end, and it
is where the web node meets the log-analysis skills from the defend tier. The
job is to turn a stream of requests into a short, ranked story.

Everything here runs only against Range targets you own: a Rocky 9 lab web host
whose log you are free to read and fill with traffic. You never collect logs
from a system you do not control. On a real job this is the muscle that lets you
glance at an access log during an incident and say, in a sentence, what someone
was testing.

## Words you'll meet

- **access log**: the file or journal where a web server records one line per request it answered.
- **user agent**: a header the client sends naming its software, which the log usually stores.
- **journalctl**: the command that reads the systemd journal, the system's central log store.
- **pipe (`|`)**: the shell feature that sends one command's output straight into the next command as input.
- **path traversal**: a request that uses `../` to try to climb out of the web folder toward files like `/etc/passwd`.
- **aggregate**: to group many lines and count them, so a pattern hidden in the noise becomes a number you can rank.

## How it works

Start with one raw line so you know what you are counting. A single access-log
entry names who asked, when, what they asked for, and how it went:

```
{user}@{host}:~$ journalctl -u nginx --since -1h | tail -n 1
10.88.0.5 - - [07/Sep/2026:09:14:22 +0000] "GET /admin HTTP/1.1" 404 153 "-" "curl/8.6.0"
```

Read that back. `10.88.0.5` is the client address, the bracketed part is the
time, `"GET /admin HTTP/1.1"` is the request line, `404` is the status the
server returned, `153` is the bytes sent, and the last quoted field is the user
agent (the client's own name for its software). One line like this is not
interesting; the shape of many lines is. The move is to pull out just the
request line from each entry, count how often each one appears, and sort the
counts so the loudest activity floats to the top.

```
{user}@{host}:~$ journalctl -u nginx --since -1h | grep -oE '"[A-Z]+ [^"]+"' | sort | uniq -c | sort -rn | head
     40 "GET / HTTP/1.1"
      8 "GET /admin HTTP/1.1"
      3 "GET /../../etc/passwd HTTP/1.1"
```

Read that pipeline left to right. `journalctl -u nginx` reads only the nginx
service's log (`-u` selects a unit, the systemd word for a managed service), and
`--since -1h` keeps the last hour. `grep -oE '"[A-Z]+ [^"]+"'` prints only the
matched part of each line (`-o`) using extended regular expressions (`-E`),
pulling out the quoted request like `"GET / HTTP/1.1"`. `sort` puts identical
lines next to each other so `uniq -c` can collapse them and print a count in the
first column. The final `sort -rn` sorts by that number, reverse (`-r`) and
numeric (`-n`), and `head` keeps the top few.

Now read the result. The first column is a count, the second is the request. The
40 hits on `/` are ordinary traffic. The 8 on `/admin` might be curiosity or a
scan for an admin panel. The last line, three attempts at `/../../etc/passwd`,
is a path-traversal probe: someone testing whether they can climb out of the web
folder to read the password file. That is the line worth an alert, and counting
surfaced it even in a busy log.

On the Range you generate your own mix of benign and probing traffic, read it
back with this pipeline, and pick out the attacks. A burst of 404s marching
through paths is scanning; a run of 500s is often someone finding a crash; odd
repeated parameters are injection attempts. Same counting habit, every time.

## When it goes wrong

`No journal files were found` or empty output usually means the web server does
not log to the journal on that host; it may write a file such as
`/var/log/nginx/access.log` instead. Point the same pipeline at the file with
`cat` in place of `journalctl -u nginx`.

`-- No entries --` means the window is empty: nothing matched `--since -1h`.
Widen it (try `--since -24h`) or generate some traffic first, then re-run.

`grep: invalid option` means the flags landed in the wrong order or the pattern
was not quoted; keep the pattern inside single quotes so the shell does not
touch it. `pridwen explain journalctl` breaks down each flag if one is unclear.

## Try it

1. On a Range web host, send a mix of normal requests and a few probing ones (a missing path, a `../` attempt).
2. Read the access log with `journalctl -u nginx --since -1h` and skim the raw lines.
3. Run the counting pipeline and read the top counts back: which is normal, which is not.
4. Point at one scanning or traversal line and say what the requester was testing.
5. Explain in one sentence how this reuses the counting method from the log-analysis node.

## Remember

- A web server writes one log line per request, so the log is the defender's copy of every probe an attacker sent.
- Counting request lines with `sort | uniq -c | sort -rn` turns a wall of text into a ranked story where the odd activity stands out.
- Bursts of 404s are scanning, runs of 500s are crashes being found, and a `../` line is a traversal probe worth an alert.
