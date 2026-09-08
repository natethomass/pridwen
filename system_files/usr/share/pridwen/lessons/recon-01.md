# Mapping from both sides

Recon, short for reconnaissance, is how an attacker learns what a network offers
before choosing a target: which machines answer, which ports are open, what is
listening behind them. The best way to understand it is to watch it happen
against a host you control, from both sides at once. Every scan a defender can
see is a lesson in what to close.

This is a defensive lesson on the attack tier. You run it only against Rocky 9
Range hosts you own, arriving in milestone M4, and against your own Pridwen
host. Scanning a machine you do not own is unauthorised access in most places
and is never part of this course. On a job, the same technique run against your
own fleet is called attack surface review, and it is the first step of
hardening.

## Words you'll meet

- **port**: a numbered door on a host, 1 to 65535, that a service listens on; SSH is 22, HTTP is 80.
- **listener**: a program waiting on a port for connections.
- **scan**: sending a probe to many ports or hosts and recording which ones answer.
- **nmap**: the standard scanner; not in the Pridwen base image.
- **Distrobox**: a mutable container on Pridwen where CLI tools like `nmap` can be installed without touching the host image.
- **attacker box**: the Range machine you scan from, as opposed to the target you scan.
- **attack surface**: everything reachable from outside, which is exactly the set of open ports.

## How it works

Start from the inside. Restating the essential from the Networking node, `ss`
lists sockets. `ss -tlnp` shows TCP (`-t`) listeners (`-l`) with numeric ports
(`-n`) and the process (`-p`, `sudo` to see other users' processes). On your own
Pridwen host, this is the whole attack surface as the host sees it.

```
{user}@{host}:~$ sudo ss -tlnp
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      4096       127.0.0.1:631        0.0.0.0:*    users:(("cupsd",pid=1210,fd=7))
```

One listener, the print service, bound to `127.0.0.1`, which means it accepts
connections only from this machine. Nothing on `0.0.0.0` or `[::]`, the
addresses that mean "any interface". A scanner on the network would find no open
TCP port on this host, which is what `sshd` off and a `drop` firewall zone are
for. On a Range web host the same command shows more.

```
{user}@{host}:~$ sudo ss -tlnp
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      128          0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=812,fd=3))
LISTEN 0      511          0.0.0.0:80         0.0.0.0:*    users:(("nginx",pid=1044,fd=6))
LISTEN 0      32           0.0.0.0:21         0.0.0.0:*    users:(("vsftpd",pid=1101,fd=3))
```

Three listeners on all addresses: SSH, a web server, and an FTP server. That
list is what recon will discover from outside, no more and no less, provided the
firewall lets the ports through.

Now the outside view. `nmap` is not in the base image and does not belong on
the host. Put it in a Distrobox, or use the Range attacker box, which has it
installed. `distrobox create` makes a container, `distrobox enter` drops you
into it, and inside it `dnf` works as on any Fedora.

```
{user}@{host}:~$ distrobox create -n lab -i registry.fedoraproject.org/fedora:43
{user}@{host}:~$ distrobox enter lab
{user}@lab:~$ sudo dnf install -y nmap
{user}@lab:~$ nmap -sV web-01
Starting Nmap 7.95 ( https://nmap.org ) at 2026-09-07 11:40 UTC
Nmap scan report for web-01 (192.168.122.21)
Host is up (0.00041s latency).
Not shown: 997 filtered tcp ports (no-response)
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.5
22/tcp open  ssh     OpenSSH 8.7 (protocol 2.0)
80/tcp open  http    nginx 1.24.0
```

The prompt shows `lab` because you are inside the container. `-sV` (service
version) asks each open port what it is running. Reading the report: the host
answered, 997 ports were filtered (the firewall dropped the probe with no
reply), and three ports are open with the service and version behind each. Set
that next to the `ss` output from the target: 21, 22, 80, the same three, with
the same programs. What `nmap` discovers from outside is the set of listeners
`ss` shows from inside, minus whatever the firewall blocks.

The defender's move follows directly. Shrink the set by stopping services that
do not need to run, and close the firewall to ports that do not need to be
reached. On the target:

```
{user}@{host}:~$ sudo systemctl disable --now vsftpd
{user}@{host}:~$ sudo firewall-cmd --remove-service=ftp --permanent && sudo firewall-cmd --reload
success
success
```

`disable --now` stops the unit and keeps it from starting at boot. The firewall
line removes the `ftp` service from the active zone permanently and reloads.
Rescan from the attacker box and port 21 is gone from the report. The lesson is
not to hide ports but to have fewer of them, and to know exactly which remain
and why.

## When it goes wrong

`bash: nmap: command not found` on the host. It is not in the image, on purpose.
Enter the Distrobox (`distrobox enter lab`) or use the Range attacker box.
`pridwen why` says the same.

`Note: Host seems down. If it is really up, but blocking our ping probes, try
-Pn`. The target's firewall dropped the ping `nmap` sends first, which a `drop`
zone does. Add `-Pn` (no ping) to scan anyway: `nmap -Pn -sV web-01`.

`Failed to resolve "web-01"`. The name is not known from where you are. Use the
address that `ip -brief addr` prints on the target, or the address the Range
scenario gives you.

## Try it

1. On your own host, run `sudo ss -tlnp` and list every open port and the address it is bound to.
2. Run `distrobox create -n lab -i registry.fedoraproject.org/fedora:43`, then `distrobox enter lab` and `sudo dnf install -y nmap`.
3. On the host, run `ip -brief addr` to read your own address; inside the box, run `nmap -Pn -sV <that address>` and confirm it finds nothing open (the box shares the host's network, so this is the host scanning itself).
4. On a Range target, run `sudo ss -tlnp`; from the attacker box, run `nmap -sV <target>`; write the two lists side by side.
5. On the target, stop one service with `systemctl disable --now` and remove its firewall service; rescan and watch the port disappear.
6. Write one sentence on why only your own lab hosts are ever scanned.

## Remember

- `sudo ss -tlnp` on the target and `nmap -sV` from outside describe the same set of open ports.
- `nmap` lives in a Distrobox or on the Range attacker box, never on the host, and only ever points at hosts you own.
- The defence is fewer listeners, not hidden ones: stop the service, close the port, rescan.
