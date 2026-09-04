# Mapping from both sides

Recon is how an attacker learns what a network offers before choosing a target,
and the best way to understand it is to watch it happen against a host you
control. Every scan a defender can see is a lesson in what to close.

The common tool is `nmap`, which probes a range of addresses and ports to learn
what responds. It is not in the base image and must never be pointed at machines
you do not own; on the Range you scan your own hosts. From the target's side, the
same information is visible without any scanning: `sudo ss -tlnp` lists exactly
the ports a scan would find open.

```
$ ss -tlnp                     # the target's own view of what listens
$ # from an attacker box on the Range, against a host you own:
$ nmap -sV web-01
```

Seeing the two views together is the point. What `nmap` discovers from outside is
just the set of listeners `ss` shows from inside, so shrinking that set, by
stopping services and closing firewall ports, directly shrinks what recon can
find. The defender's move is not to hide the ports but to have fewer of them, and
to know exactly which ones and why.

## Try it

1. On a host you own, run `ss -tlnp` and list what is open.
2. From a Range attacker box, scan that host and compare the results.
3. Stop one service, rescan, and watch the open port disappear.
4. Explain why scanning only your own lab hosts is the rule.
