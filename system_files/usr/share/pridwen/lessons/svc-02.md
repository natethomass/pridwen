# Enabled versus started

The single most common systemd confusion is the difference between a service
that is started and one that is enabled. They answer two separate questions.
Active means running right now. Enabled means set to start at boot. A unit can
be either, both, or neither.

`systemctl start name` runs it now and changes nothing about boot.
`systemctl enable name` wires it into the next boot and does not start it now.
When you want both, `systemctl enable --now name` does them together. Two
read-only checks keep it straight: `is-active` and `is-enabled`.

```
$ sudo systemctl enable --now sshd
$ systemctl is-active sshd
active
$ systemctl is-enabled sshd
enabled
```

This is why a service can "work until you reboot" (started but not enabled) or
"come back only after a reboot" (enabled but not started). If a unit fails to
start, `systemctl status name` gives the reason and `journalctl -u name -b`
gives the full log since boot. Masking is the strongest off switch: it links the
unit to `/dev/null` so nothing, not even a dependency, can start it, and
`unmask` reverses it.

## Try it

1. On a Range host, `sudo systemctl start` a service and check `is-enabled`.
2. Then `sudo systemctl enable` it and check `is-active` versus `is-enabled`.
3. Use `enable --now` on a third service and confirm both are true at once.
4. Explain out loud when you would mask a unit instead of disabling it.
