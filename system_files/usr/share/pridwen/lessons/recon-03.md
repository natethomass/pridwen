# Turning recon into hardening

Recon is only the opening move, but for a defender it is a gift: it is a map of
your own attack surface drawn by the very method an attacker would use. Running
it against yourself, on the Range, turns an adversary technique into a hardening
checklist.

The workflow is to enumerate your own host as an attacker would, then close what
you find that does not need to be open. `ss -tulnp` for listeners, `curl -sI` for
banners, and a scan from a Range box together produce a list. Each item gets a
decision: needed and hardened, or removed.

```
$ ss -tulnp | sort
$ systemctl list-unit-files --state=enabled | grep -Ei 'ssh|http|ftp'
$ # decide per line: keep and harden, or stop and disable
```

This is where the attack tier folds back into the secure one. A port you close is
a firewall lesson; a service you disable is a systemd lesson; a banner you trim is
a configuration lesson. Doing it on the Range, where you can scan freely and break
things safely, builds the instinct to see your own machine the way an attacker
would, which is the most useful outcome recon has to offer a defender.

## Try it

1. Enumerate your own Range host's listeners and banners as an attacker would.
2. For each open port, decide whether it is needed and note why.
3. Close or harden one item and re-enumerate to confirm the change.
4. Explain how each closure maps back to a secure-tier skill.
