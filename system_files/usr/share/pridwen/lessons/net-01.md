# Addresses and routes

Every machine on a network has at least one address, and it needs to know
which neighbour to hand packets to when the destination is not on its own
network. Those two facts, addresses and routes, are the first things you
check whenever "the network is down". On Fedora, and so on Pridwen, the tool
that shows them is `ip`, from a package called iproute2.

If you learned Linux from an older book you may reach for `ifconfig` and
`route`. Pridwen does not ship them. They came from a package called net-tools
that stopped keeping up with the kernel years ago, so they could not show
things like multiple addresses on one interface. Everything they did, `ip`
does, and more. On a real job you will meet both, but every current Red Hat
and Fedora system expects `ip`.

## Words you'll meet

- **interface**: one network connection the kernel knows about, such as a Wi-Fi card or an Ethernet port, with a name like `wlp3s0` or `enp1s0`.
- **loopback**: the interface named `lo` that only talks to the machine itself, always at `127.0.0.1`.
- **IP address**: the number that identifies your machine on a network, written like `192.168.1.42`.
- **prefix length**: the `/24` after an address; it says how many leading bits name the network, so `/24` means the first three numbers are the network and the last one is your host.
- **MAC address**: the hardware address of an interface, six pairs of hex digits, used only on the local network.
- **route**: a rule that says which interface, and optionally which neighbour, to use for a given range of destinations.
- **default route**: the route used when no other route matches, pointing at your gateway, usually the home router.
- **gateway**: the neighbour that forwards your traffic to networks you are not directly on.
- **NetworkManager**: the service that owns network configuration on a desktop; `nmcli` is its command-line front end.

## How it works

Start with the short form of the address listing. The `-br` flag means brief:
one line per interface instead of a block of several lines.

```
{user}@{host}:~$ ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
wlp3s0           UP             192.168.1.42/24 fe80::9a4b:1cff:fe2e:7d10/64
```

Read each line left to right. The first column is the interface name. The
second is its state: `UP` means the link is live, `DOWN` means it is not, and
`lo` always says `UNKNOWN`, which is normal. The rest of the line is every
address on that interface. `192.168.1.42/24` is your IPv4 address and prefix
length; the long address starting `fe80::` is an IPv6 link-local address that
every interface gives itself. A healthy desktop shows one non-loopback
interface `UP` with a `192.168.x.x` or `10.x.x.x` style address.

The same command without `-br` prints the full block per interface, which
adds the MAC address and lifetimes. `ip link` shows only the interfaces and
their MAC addresses, which is useful when you want to know what hardware is
present before it has an address.

Next, the routing table. `ip route` prints one route per line.

```
{user}@{host}:~$ ip route
default via 192.168.1.1 dev wlp3s0 proto dhcp src 192.168.1.42 metric 600
192.168.1.0/24 dev wlp3s0 proto kernel scope link src 192.168.1.42 metric 600
```

The line that starts with `default` is the one that matters most: it says
that anything not otherwise listed goes `via 192.168.1.1`, your gateway,
leaving through `dev wlp3s0`. `proto dhcp` means the route was learned from
the router by DHCP, the protocol that hands out addresses automatically. The
second line says the `192.168.1.0/24` network is directly reachable on the
same interface, so packets to neighbours do not need the gateway. If there is
no `default` line at all, you can reach neighbours but nothing beyond them.

To ask the kernel which route a specific destination would use, give it an
address with `ip route get`.

```
{user}@{host}:~$ ip route get 1.1.1.1
1.1.1.1 via 192.168.1.1 dev wlp3s0 src 192.168.1.42 uid 1000
    cache
```

This says a packet to `1.1.1.1` would go through the gateway, leave by
`wlp3s0`, and carry your address `192.168.1.42` as its source. When two
interfaces are up at once, this command settles which one is actually in use.

On a desktop, NetworkManager owns the configuration. That is why a change you
make with `ip` by hand is temporary: NetworkManager puts its own settings back
the next time the interface reconnects. Pridwen keeps the division of labour
simple. Read with `ip`, change with `nmcli`. `nmcli device status` lists the
interfaces with the connection each is using, so you can match its names to
the ones `ip` showed.

```
{user}@{host}:~$ nmcli device status
DEVICE  TYPE      STATE                   CONNECTION
wlp3s0  wifi      connected               home
lo      loopback  connected (externally)  lo
```

Note that `wlp3s0` here is the same name `ip` printed. `CONNECTION` is the
saved profile NetworkManager applied to it, named `home` in this example.

## When it goes wrong

`bash: ifconfig: command not found` means exactly what it says: the program
is not on this system. Use `ip -br addr` instead. The Coach prints this hint
under the failed command, and `pridwen why` repeats it with the replacements
listed.

`RTNETLINK answers: Operation not permitted` appears when you try to change
an address or route as a normal user, for example `ip addr add`. Reading is
open to everyone; changing needs root. On Pridwen the lasting fix is `nmcli
connection modify`, which the next lesson covers, because a change made with
`sudo ip` is undone at the next reconnect anyway.

`ip route` printing no `default` line means you have no gateway. Check that
`nmcli device status` shows the interface `connected`; if it says
`disconnected`, the link itself is down, which is a cable, Wi-Fi password, or
router problem rather than a Linux one. `pridwen explain ip` annotates any
flag in this lesson if one is unfamiliar.

## Try it

1. Type `ip -br addr` and find the line that is not `lo`. Write down its address and prefix length.
2. Type `ip addr` and find the same interface. Locate the `link/ether` line, which is the MAC address.
3. Type `ip route` and find the `default` line. The address after `via` is your gateway; note the interface after `dev`.
4. Type `nmcli device status` and match each `DEVICE` to the interface names `ip` showed. The `CONNECTION` column names the saved profile.
5. Type `ip route get 1.1.1.1` and read back which interface a packet would leave by and what source address it would carry.
6. Type `pridwen explain ip` and read the descriptions of `-br` and `route get`.

## Remember

- `ip -br addr` shows interfaces and addresses; `ip route` shows the routing table and the `default` line is the gateway.
- `ifconfig` and `route` are not shipped; iproute2 replaced them and `ip` does everything they did.
- Read with `ip`, change with `nmcli`; NetworkManager overwrites hand changes on the next reconnect.
