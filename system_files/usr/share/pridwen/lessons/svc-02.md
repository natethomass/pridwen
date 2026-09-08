# Enabled versus started

The single most common confusion with systemd, the service manager that starts
and watches every service, is the difference between a service that is started
and one that is enabled. They answer two separate questions. Started, which
systemd calls active, means running right now. Enabled means set to start at
boot. A unit, one thing systemd manages, can be either, both, or neither, and
nothing you do to one setting changes the other unless you ask.

This matters because it is behind two classic support calls: "it worked until
we rebooted" and "it only works after a reboot". On Pridwen it also explains
the security posture. `sshd`, the remote login service, is present in the image
but is neither started nor enabled, so nobody can log in over the network until
you decide they can.

## Words you'll meet

- **active**: the unit is running now; `systemctl start` makes it so, `stop` undoes it.
- **enabled**: the unit will start at the next boot; `systemctl enable` makes it so, `disable` undoes it.
- **symlink**: a file that points at another file; enabling creates one under `/etc/systemd/system/`.
- **target**: a systemd unit that groups other units; `multi-user.target` is "the system is up", and enabled services hang off a target.
- **masked**: the unit is linked to `/dev/null` so it cannot be started by anything; the strongest off switch.
- **journal**: the system log that systemd keeps; `journalctl` reads it.
- **Range**: the Rocky 9 lab machines Pridwen gives you to practise on, where turning services on is safe.

## How it works

`sudo systemctl start name` runs the unit now and changes nothing about boot.
`sudo systemctl enable name` wires it into the next boot and does not start it
now. When you want both, `sudo systemctl enable --now name` does the two
together; `--now` means "and also start it". Two read-only checks keep it
straight, and neither needs root: `is-active` and `is-enabled`. Practise this
on a Range target, because on the Pridwen host `sshd` is off on purpose.

```
{user}@{host}:~$ systemctl is-active sshd
inactive
{user}@{host}:~$ systemctl is-enabled sshd
disabled
```

Both answers are one word, which makes them easy to use in scripts. Here the
service is neither running nor set to run at boot. Now enable and start it on
a Range machine in one step.

```
{user}@{host}:~$ sudo systemctl enable --now sshd
Created symlink /etc/systemd/system/multi-user.target.wants/sshd.service → /usr/lib/systemd/system/sshd.service.
{user}@{host}:~$ systemctl is-active sshd
active
{user}@{host}:~$ systemctl is-enabled sshd
enabled
```

The `Created symlink` line is what enabling actually is: a link placed in
`/etc/systemd/system/multi-user.target.wants/` that says "when the system
reaches multi-user.target, start this too". That is why the earlier lesson said
your changes live in `/etc` and the shipped unit stays in read-only `/usr`.
Disabling removes the link. Because it is only a link, enabling costs nothing
until the next boot, and starting is a separate action.

The four combinations explain the two classic complaints. Started but not
enabled works until the reboot, then is gone. Enabled but not started comes
back only after a reboot. `systemctl status name` shows both words on its
Loaded and Active lines, so one command tells you which case you are in.

```
{user}@{host}:~$ systemctl status sshd | head -n 3
* sshd.service - OpenSSH server daemon
     Loaded: loaded (/usr/lib/systemd/system/sshd.service; enabled; preset: disabled)
     Active: active (running) since Mon 2026-09-07 10:30:02 UTC; 2min ago
```

`enabled` on the Loaded line and `active (running)` on the Active line: both
true. The `preset: disabled` part says the distribution's default for this unit
is off, which is Pridwen's choice; the machine differs from the preset because
you changed it.

If a unit fails to start, `systemctl status name` shows the reason and the last
log lines, and `journalctl -u name -b` shows everything that unit logged since
boot; `-u` picks the unit and `-b` limits to the current boot. Exit code 3 from
`systemctl status` is not an error, it is the way `status` reports "inactive"
to scripts; the output above it is complete.

Masking is the strongest off switch. `sudo systemctl mask name` links the unit
to `/dev/null` in `/etc/systemd/system`, so nothing can start it, not a person,
not a dependency, not a timer. `disable` only removes the boot link, and
another unit that wants it can still start it. Use mask when a service must
stay off no matter what; `sudo systemctl unmask name` reverses it.

```
{user}@{host}:~$ sudo systemctl mask sshd
Created symlink /etc/systemd/system/sshd.service → /dev/null.
{user}@{host}:~$ systemctl is-enabled sshd
masked
```

`pridwen explain systemctl` annotates any of these verbs and flags.

## When it goes wrong

`Failed to enable unit: Interactive authentication required.` means you ran
`enable` without root. Add `sudo`; reading with `is-enabled` never needs it.

`Failed to start sshd.service: Unit sshd.service is masked.` means someone
masked it, on purpose. `systemctl is-enabled sshd` says `masked`; if you are
sure it should run, `sudo systemctl unmask sshd` first, then start it.

`Job for foo.service failed because the control process exited with error
code.` means the program started and then quit. The reason is in the log, not
on your screen: `systemctl status foo` for the summary, `journalctl -u foo -b`
for the full story. `pridwen why` points at the same place.

## Try it

1. On the host, run `systemctl is-active sshd` and `systemctl is-enabled sshd`; expect `inactive` and `disabled`.
2. On a Range target, run `sudo systemctl start sshd`, then `is-enabled`; expect `disabled`, because start touched only now.
3. Run `sudo systemctl enable sshd` and read the `Created symlink` line; then `is-active` and `is-enabled` should both be true.
4. Run `sudo systemctl disable --now sshd` and confirm both checks are false again.
5. Run `sudo systemctl mask sshd`, try `sudo systemctl start sshd`, read the error, then `unmask` it.
6. Say out loud which case "it worked until we rebooted" is.

## Remember

- Active means running now; enabled means starts at boot; they are set separately, and `enable --now` does both.
- Enabling is a symlink under `/etc/systemd/system/*.wants/`; `is-active` and `is-enabled` check each without root.
- Mask links a unit to `/dev/null` so nothing can start it; disable only removes the boot link.
