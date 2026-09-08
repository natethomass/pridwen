# Turning recon into hardening

Recon is only an attacker's opening move, but for a defender it is a gift: a map
of your own attack surface, drawn by the very method an attacker would use.
Running it against yourself turns an adversary technique into a hardening
checklist, one line per open port, each with a decision attached. This lesson
folds the last two together into that workflow.

This is a defensive lesson on the attack tier, run only against Rocky 9 Range
hosts you own, arriving in milestone M4, and against your own Pridwen host. On a
job, the same pass is done before a server goes live and again after every
change, and the list it produces is the honest answer to "what is exposed".

## Words you'll meet

- **enumerate**: to list everything of a kind, here every listener and banner, without missing one.
- **attack surface**: every service reachable from outside; the shorter the list, the less there is to attack.
- **decision**: for each open port, either "needed, and hardened" or "not needed, removed".
- **enabled unit**: a systemd service set to start at boot, which is how a listener comes back after a reboot.
- **firewall service**: a named rule in firewalld, such as `ssh` or `http`, that opens the ports a service needs.
- **re-enumerate**: run the same listing again after a change to prove the change took.

## How it works

Enumerate from the inside first, because it is complete. Restating the essential
from the last two lessons: `ss -tulnp` lists TCP and UDP listeners with ports
and processes, and `curl -sI` reads a web server's banner. Sorting the `ss`
output makes it comparable later.

```
{user}@{host}:~$ sudo ss -tulnp | sort
Netid State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
tcp   LISTEN 0      128          0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=812,fd=3))
tcp   LISTEN 0      32           0.0.0.0:21         0.0.0.0:*    users:(("vsftpd",pid=1101,fd=3))
tcp   LISTEN 0      511          0.0.0.0:80         0.0.0.0:*    users:(("nginx",pid=1044,fd=6))
udp   UNCONN 0      0            0.0.0.0:111        0.0.0.0:*    users:(("rpcbind",pid=640,fd=5))
```

Four lines, four decisions. Reading them: SSH on 22, FTP on 21, a web server on
80, and `rpcbind` on UDP 111, which is a helper for NFS that many hosts run
without needing. `0.0.0.0` on every one means all addresses. Next, which of
these come back at boot. `systemctl list-unit-files --state=enabled` lists
enabled units, and the `grep -Ei` (extended regex, case-insensitive) narrows to
the ones that match the listeners.

```
{user}@{host}:~$ systemctl list-unit-files --state=enabled | grep -Ei 'ssh|http|nginx|ftp|rpc'
nginx.service          enabled  disabled
rpcbind.service        enabled  enabled
rpcbind.socket         enabled  enabled
sshd.service           enabled  enabled
vsftpd.service         enabled  disabled
```

The second column is the current state, the third is the vendor default. Then
the outside view, from the attacker box, which shows what the firewall lets
through.

```
{user}@lab:~$ nmap -sV -sU -p 21,22,80,111 web-01
PORT    STATE  SERVICE VERSION
21/tcp  open   ftp     vsftpd 3.0.5
22/tcp  open   ssh     OpenSSH 8.7 (protocol 2.0)
80/tcp  open   http    nginx
111/udp closed rpcbind
```

`-sU` adds a UDP scan and `-p` limits it to the ports you already know, which
keeps it fast. Port 111 is `closed` from outside because the firewall does not
open it, but the listener still exists; a firewall is one layer, and a service
that does not run is a better one. Now the decisions, written down before
touching anything.

```
{user}@{host}:~$ cat {home}/pridwen/surface.txt
22/tcp  sshd     keep: admin access. harden: keys only, no root login
80/tcp  nginx    keep: it is the web host. harden: server_tokens off, patched
21/tcp  vsftpd   remove: nothing uses FTP here
111/udp rpcbind  remove: no NFS on this host
```

Then act on each `remove` line, both the service and its firewall opening, and
on each `keep` line's hardening. `disable --now` stops the unit and keeps it
from returning at boot; for `rpcbind` the socket unit must go too, or systemd
will start the service on demand.

```
{user}@{host}:~$ sudo systemctl disable --now vsftpd
{user}@{host}:~$ sudo systemctl disable --now rpcbind.socket rpcbind.service
{user}@{host}:~$ sudo firewall-cmd --remove-service=ftp --permanent && sudo firewall-cmd --reload
success
success
{user}@{host}:~$ sudo ss -tulnp | sort
Netid State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
tcp   LISTEN 0      128          0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=812,fd=3))
tcp   LISTEN 0      511          0.0.0.0:80         0.0.0.0:*    users:(("nginx",pid=1044,fd=6))
```

Re-enumerating is the proof: two listeners, both on the `keep` list. Rescan from
the attacker box and 21 and 111 are gone from the report as well. Save the new
`ss` output as the baseline from the Detection node, so the next drift shows.

This is where the attack tier folds back into the secure one. A port you close
is a Firewall lesson; a service you disable is a Services lesson; a banner you
trim is a configuration lesson; an SSH server you restrict to keys is an SSH
lesson. Doing it on the Range, where you can scan freely and break things
safely, builds the instinct to see your own machine the way an attacker would,
which is the most useful thing recon offers a defender.

## When it goes wrong

`Failed to disable unit: Unit file vsftpd.service does not exist.` The service
is not installed under that name on this host. Find the real unit with
`systemctl list-units --type=service | grep -i ftp` and use that.

`Error: NOT_ENABLED: ftp` from `firewall-cmd --remove-service`. The zone never
had that service opened; the port was reachable for another reason, such as a
direct port rule. `sudo firewall-cmd --list-all` shows every opening in the
active zone so you can remove the right one.

A listener comes back after reboot. You stopped it but did not disable it, or a
socket unit reactivates it. Check `systemctl is-enabled <unit>` and
`systemctl list-unit-files | grep <name>` for a `.socket` twin.

## Try it

1. On a Range host, run `sudo ss -tulnp | sort` and `systemctl list-unit-files --state=enabled | grep -Ei 'ssh|http|nginx|ftp|rpc'`; write the listeners into `{home}/pridwen/surface.txt`.
2. From the attacker box, run `nmap -sV -sU -p <the ports> <target>` and mark which are reachable from outside.
3. Next to each line write `keep` with a hardening note or `remove` with a reason.
4. For each `remove`, run `sudo systemctl disable --now <unit>` and, if the firewall opens it, `sudo firewall-cmd --remove-service=<name> --permanent` then `--reload`.
5. Re-enumerate with the same `ss` command and rescan; confirm only the `keep` lines remain. Save the `ss` output as a baseline.
6. For each closure, name the secure-tier node it maps back to.

## Remember

- Enumerate your own host as an attacker would: `ss -tulnp`, enabled units, banners, and a scan from a box you own.
- Every open port gets a written decision: keep and harden, or disable the unit and close the firewall.
- Re-enumerate after each change; the shorter list is the proof, and it becomes your next baseline.
