# Services and versions

Beyond which ports are open, recon tries to learn what software sits behind each
one and which version, because a version maps to a list of known weaknesses.
An attacker who reads `nginx/1.24.0` in a header goes and looks up what that
release is known to get wrong. The defence is to give away less, and to keep
what you do run current so a known version is not a known hole.

This is a defensive lesson on the attack tier: everything here is run against
Rocky 9 Range hosts you own, arriving in milestone M4, and against your own
Pridwen host, never against anyone else's machine. On a job, reading your own
banners is a routine part of a hardening pass, and trimming them is one of the
cheapest changes with a real effect.

## Words you'll meet

- **banner**: the text a service sends when you connect, often naming itself and its version.
- **header**: a line of metadata in an HTTP response, such as `Server: nginx`.
- **HEAD request**: an HTTP request that asks for headers only, not the page.
- **curl**: the command-line HTTP client; `-s` is silent, `-I` sends a HEAD request.
- **version string**: the `SSH-2.0-OpenSSH_8.7` line an SSH server sends before any login.
- **patch**: an update that fixes a known weakness; a current version has the fixes applied.

## How it works

Start with the web server, because HTTP is the chattiest protocol. `curl -sI`
sends a HEAD request (`-I`) without a progress bar (`-s`) and prints the
response headers.

```
{user}@{host}:~$ curl -sI http://web-01
HTTP/1.1 200 OK
Server: nginx/1.24.0
Date: Mon, 07 Sep 2026 11:52:14 GMT
Content-Type: text/html
Content-Length: 615
Last-Modified: Fri, 04 Sep 2026 14:30:02 GMT
Connection: keep-alive
ETag: "68b9b0aa-267"
Accept-Ranges: bytes
```

Reading it back: the first line is the status, `200 OK` meaning the page
exists. `Server` names the software and version. `Date` is the server's clock.
`Last-Modified` says when the page file changed, which leaks a little about
activity on the host. The rest describes the page. Of these, `Server` is the
line recon wants. `grep -i server` (case-insensitive) pulls just that line,
which is the form you will use in a loop over many hosts.

```
{user}@{host}:~$ curl -sI http://web-01 | grep -i server
Server: nginx/1.24.0
```

SSH announces itself too, before any password is asked. `ssh -v` (verbose)
prints the negotiation, and the remote version string is in it. Adding `-o
BatchMode=yes` stops it from prompting for a password, and `2>&1` sends the
verbose output, which goes to stderr, into the pipe.

```
{user}@{host}:~$ ssh -v -o BatchMode=yes web-01 2>&1 | grep 'remote software version'
debug1: Remote protocol version 2.0, remote software version OpenSSH_8.7
```

That is the same `OpenSSH 8.7` the `nmap -sV` report in the last lesson showed,
and this is where the scanner got it: the server said so. From the target's
side, `sudo ss -tlnp | grep :22` confirms `sshd` is the listener; the version is
in the package, `rpm -q openssh-server`.

Now trim. nginx has a switch for the version part of its `Server` header:
`server_tokens off;` inside the `http` block of `/etc/nginx/nginx.conf`. Restating
the essential from the Services node, a configuration change takes effect after
`systemctl reload`, which asks the running service to reread its files without
dropping connections. On the Range target:

```
{user}@{host}:~$ sudo grep -n server_tokens /etc/nginx/nginx.conf
{user}@{host}:~$ sudo sed -i '/^http {/a \    server_tokens off;' /etc/nginx/nginx.conf
{user}@{host}:~$ sudo nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
{user}@{host}:~$ sudo systemctl reload nginx
{user}@{host}:~$ curl -sI http://web-01 | grep -i server
Server: nginx
```

The first `grep` returns nothing, meaning the option is not set. `sed -i` edits
the file in place, and the expression appends (`a`) a line after the one that
starts with `http {`. `nginx -t` tests the configuration before you reload,
which is the habit that keeps a typo from taking the site down. After the
reload, the header says `nginx` and nothing more. The port is still open and
the service still answers, because it must; what changed is that a stranger no
longer gets the version for free.

Versions you cannot hide, you keep current. On a Rocky host, `sudo dnf check-update`
lists packages with newer versions available and `sudo dnf upgrade` applies them.
`rpm -q --changelog openssh-server | head` shows what the installed version
fixed, which is how you check whether a weakness someone might look up is
already closed. On your own Pridwen host, the same job is one `bootc upgrade`,
because every package on the host comes from the image. The sentence to
remember: recon rewards a chatty, out-of-date host and gets little from a quiet,
current one, and both of those are within your control.

## When it goes wrong

`curl: (7) Failed to connect to web-01 port 80`. Nothing is listening or the
firewall dropped you. Check `sudo ss -tlnp | grep :80` on the target and
`firewall-cmd --list-services`. `pridwen explain curl` covers the flags.

`nginx: [emerg] "server_tokens" directive is not allowed here`. The line landed
outside the `http` block, for instance at the top of the file. Open the file,
move the line under `http {`, and run `nginx -t` again before reloading.

`ssh -v` shows no `remote software version` line and ends with `Connection
refused`. SSH is not running on that host, which on your own Pridwen host is the
default; use a Range target.

## Try it

1. On the Range, run `curl -sI http://web-01` and read every header back; name the one recon cares about.
2. Run `ssh -v -o BatchMode=yes web-01 2>&1 | grep 'remote software version'` and match it to the `nmap -sV` line from the last lesson.
3. Say in one sentence what an attacker would look up with `nginx/1.24.0` and `OpenSSH_8.7` in hand.
4. On the target, add `server_tokens off;` to the `http` block, run `sudo nginx -t`, then `sudo systemctl reload nginx`.
5. Rerun `curl -sI http://web-01 | grep -i server` and confirm the version is gone.
6. Run `sudo dnf check-update` on the target and `rpm -q --changelog openssh-server | head` to see what is current and what has been fixed.

## Remember

- `curl -sI` reads HTTP headers and `ssh -v` reads the SSH version string; both are where `nmap -sV` gets its answers.
- Trim banners where the service allows it (`server_tokens off;` for nginx), test with `nginx -t`, then reload.
- What you cannot hide, keep patched; a known version is only a known hole if it is out of date.
