# Watching for change

Detection is noticing something before you would have stumbled on it. It builds
on log analysis by turning a question you would ask by hand into a watch that
answers itself. The first kind of watch is for change in things that should be
stable.

On Pridwen the base image cannot change between boots, so the places worth
watching are `/etc`, `/var`, user accounts, and what listens on the network.
`sudo ss -tulnp` captured now and compared later shows a new listener; the audit
subsystem can watch a path and record every access. auditd rules live in
`/etc/audit/rules.d/` and load at boot.

```
$ sudo auditctl -w /etc/passwd -p wa -k passwd_changes
$ sudo ausearch -k passwd_changes -ts today
```

That rule watches `/etc/passwd` for writes and attribute changes, tagging them
with a key you can search. On a Range host you set a watch, trigger it with a
change, and confirm the record appears. The point is to move from reacting to
what you happened to see toward being told when a specific, security-relevant
thing happens, which is the difference between analysis and detection.

## Try it

1. On a Range host, add an audit watch on `/etc/passwd` with a key.
2. Make a change that trips it, then find the record with `ausearch -k`.
3. Capture `ss -tulnp` now and compare it after starting a new service.
4. Explain why an immutable `/usr` narrows what you need to watch.
