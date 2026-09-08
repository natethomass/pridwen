# Sockets and names

Two questions come up constantly on any Linux machine. What is listening on
this box, and why did a name not resolve. The first is about sockets, the
endpoints that programs open to accept or make connections. The second is
about DNS, the system that turns a name like `example.com` into an address.
On Pridwen `ss` answers the first question and `resolvectl` answers the second.

Both matter on a job because they split a vague complaint into testable
pieces. "The website is down" becomes "can I resolve the name" and then "can
I reach the address on that port". Pridwen also encrypts DNS with DNS over
TLS, so knowing where a query goes and how to test it is part of
understanding your own machine's privacy.

## Words you'll meet

- **socket**: an endpoint a program opens for network traffic, identified by an address and a port.
- **port**: a number from 1 to 65535 that says which program on a machine a connection is for; `631` is printing, `22` is SSH.
- **listening**: a socket waiting for connections to arrive, as a server does.
- **established**: a connection that is open between two ends right now.
- **TCP and UDP**: the two common transport protocols; TCP keeps a connection and checks delivery, UDP sends single packets.
- **DNS**: the Domain Name System, which maps names to addresses.
- **resolver**: the part of the system that asks DNS servers on behalf of programs; on Pridwen it is systemd-resolved.
- **DNS over TLS**: DNS queries wrapped in encryption so the network in between cannot read or alter them.
- **ICMP**: the small control protocol `ping` uses; many hosts ignore it.

## How it works

The phrase to memorise is `ss -tulnp`. Each letter is a flag: `-t` TCP,
`-u` UDP, `-l` listening sockets only, `-n` numeric, meaning show port numbers
rather than service names, and `-p` the process that owns the socket. Here
is the TCP-only form.

```
{user}@{host}:~$ ss -tlnp
State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process
LISTEN  0       128     127.0.0.1:631        0.0.0.0:*
LISTEN  0       4096    [::1]:6600           [::]:*             users:(("mpd",pid=1342,fd=5))
```

`State` is `LISTEN` for every line because of `-l`. `Local Address:Port`
is where the socket listens: `127.0.0.1:631` means the printing service only
accepts connections from this machine, because `127.0.0.1` is the loopback
address. `0.0.0.0` or `[::]` in that column would mean it accepts from any
network, which is worth noticing on a hardened desktop. `Process` is filled
only for sockets you own; the printing line is blank because it belongs to
root. Run the same command with `sudo` and every process is named. A normal
Pridwen desktop shows only a few lines, all on loopback, because `sshd` is
off and the firewall is in its `drop` zone.

`ss -tn` without `-l` shows established connections instead, which tells you
who your machine is talking to right now. The old `netstat` is not installed;
`ss` replaced it and reads the kernel faster.

Now names. Pridwen sends DNS through systemd-resolved, a small service that
sits between programs and the real DNS servers and speaks DNS over TLS to
them. `resolvectl query` asks it directly.

```
{user}@{host}:~$ resolvectl query example.com
example.com: 93.184.216.34                     -- link: wlp3s0

-- Information acquired via protocol DNS in 18.4ms.
-- Data is authenticated: no; Data was acquired via local or encrypted transport: yes
```

The first line is the answer: the name and its address, with the interface
the query left by. The footer tells you the query took 18 milliseconds and
travelled over an encrypted transport, which is the DNS over TLS setting at
work. To see the servers and settings per interface, ask for status.

```
{user}@{host}:~$ resolvectl status
Global
       Protocols: LLMNR=resolve -mDNS +DNSOverTLS DNSSEC=no/unsupported
resolv.conf mode: stub

Link 2 (wlp3s0)
    Current Scopes: DNS
         Protocols: +DefaultRoute LLMNR=resolve -mDNS +DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 1.1.1.1#cloudflare-dns.com
       DNS Servers: 1.1.1.1#cloudflare-dns.com 1.0.0.1#cloudflare-dns.com
```

`+DNSOverTLS` with a plus sign means encryption is on. `Current DNS Server`
names the server in use, and the part after `#` is the certificate name the
encryption checks. Finally, `getent hosts` resolves a name the way ordinary
programs do, through the standard library, so it is the fairest test of what
an application will see.

```
{user}@{host}:~$ getent hosts example.com
93.184.216.34   example.com
```

The order of tests when something fails is fixed. First `ping 1.1.1.1` to
prove the network carries packets at all, then `resolvectl query` to prove
names resolve, then `curl -I` to a real port to prove the service answers.
Each step isolates one layer.

## When it goes wrong

`ping: example.com: Name or service not known` means the name did not
resolve, and `ping` exits with status 2. Test the address on its own with
`ping 1.1.1.1`; if that works, the network is fine and DNS is the problem, so
look at `resolvectl status`. The Coach prints this split under the failed
command; `pridwen why` shows the full ladder.

`curl: (6) Could not resolve host: exmaple.com` is the same failure seen from
`curl`, and very often it is a typo in the name, as it is here. `curl: (7)
Failed to connect to 192.168.1.50 port 80` means the name resolved but nothing
answered on that port: the service is not running, or a firewall dropped the
packet. On the target, `ss -tlnp` shows whether anything listens there.

`ping` sending packets and getting nothing back exits 1 and prints `100%
packet loss`. That does not prove the host is down. Many hosts, including a
Pridwen desktop in its `drop` zone, ignore ICMP, so test a real port with
`curl -I` instead. `pridwen explain ss` and `pridwen explain resolvectl`
annotate every flag used here.

## Try it

1. Type `ss -tlnp` and pick one `LISTEN` line. Read its port and whether the address is `127.0.0.1` (local only) or `0.0.0.0` (any network).
2. Type `sudo ss -tlnp` and notice the `Process` column now names root's services too.
3. Type `resolvectl query fedoraproject.org` and read the address and the transport line in the footer.
4. Type `resolvectl status` and confirm the `Protocols` line shows `+DNSOverTLS`.
5. Type `getent hosts fedoraproject.org` and compare it with the `resolvectl` answer.
6. Type `ping -c 3 1.1.1.1`, where `-c 3` sends three packets and stops, and read the packet loss line at the end.

## Remember

- `ss -tulnp` lists listening TCP and UDP sockets numerically with their owning process; `sudo` sees every process.
- `resolvectl query name` tests DNS alone; `resolvectl status` shows the servers and that DNS over TLS is on.
- Split a network problem into layers: packets (`ping 1.1.1.1`), names (`resolvectl query`), then the service (`curl -I`).
