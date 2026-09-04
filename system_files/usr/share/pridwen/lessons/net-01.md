# Addresses and routes

The modern tool for looking at networking on Fedora is `ip`, from the iproute2
package. The old `ifconfig` and `route` are not shipped because they stopped
keeping up with the kernel years ago. Everything they did, `ip` does, and more.

`ip addr` shows each interface with its state and addresses; `ip -br addr` is the
same in one line each. `ip link` shows the interfaces and their MAC addresses,
and `ip route` shows the routing table, including the default route that sends
traffic toward the wider network.

```
$ ip -br addr
lo      UNKNOWN  127.0.0.1/8 ::1/128
wlp3s0  UP       192.168.1.42/24 fe80::.../64
$ ip route
default via 192.168.1.1 dev wlp3s0 proto dhcp
```

On a desktop, NetworkManager owns the configuration, so changes made with `ip`
by hand are temporary and get overwritten on the next reconnect. To make a change
stick, use `nmcli`, its command-line front end: `nmcli device status` shows the
connections and `nmcli connection modify` edits one. Reading with `ip` and
changing with `nmcli` is the division of labour to remember.

## Try it

1. Run `ip -br addr` and find your machine's address and prefix length.
2. Run `ip route` and identify the default gateway.
3. Run `nmcli device status` and match it to the interfaces from `ip`.
4. Run `ip route get 1.1.1.1` and read which interface a packet would leave by.
