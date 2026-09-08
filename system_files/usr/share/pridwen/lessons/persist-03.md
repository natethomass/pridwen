# Removing and preventing

Finding persistence is only half the job; removing it cleanly and keeping it
from coming back is the other half. Removal has to be complete, because a single
missed mechanism can re-establish the rest, and prevention is about closing the
paths that let anything be planted in the first place. This lesson is where the
whole skill tree closes: the attack tier told you where to look, the defend tier
how to watch, and the secure tier how to shut the doors.

Everything here runs only against Range targets you own: Rocky 9 lab hosts you
start with `pridwen enter rocky`, where you remove a planted mechanism and prove
the host comes up clean. You never modify a system you do not control. On a real
job this is the tail end of an incident: not just deleting what you found, but
rebooting, re-checking from a baseline, and adding a watch so the next attempt
announces itself.

## Words you'll meet

- **disable**: tell systemd to stop starting a unit automatically; `--now` also stops it immediately.
- **unit file**: the systemd file defining a service or timer; removing persistence often means deleting one.
- **auditd**: the Linux auditing service that records events; `auditctl` adds rules to it at runtime.
- **watch**: an audit rule on a path that logs every read or write to it, tagged with a key you choose.
- **baseline**: the known-good snapshot of startup locations you compare against after removal.
- **chain**: when one persistence mechanism recreates another, so removing one alone is not enough.

## How it works

Removal is two steps per mechanism: stop it from starting, then delete the file
that defines it. For a planted user service you disable it and remove its unit
file:

```
{user}@{host}:~$ systemctl --user disable --now sneaky.service
Removed "/home/{user}/.config/systemd/user/sneaky.service".
{user}@{host}:~$ rm {home}/.config/systemd/user/sneaky.service
```

Read that back. `systemctl --user disable --now sneaky.service` turns off the
autostart link (`disable`) and stops the running copy (`--now`) in the user's
own systemd instance (`--user`); the confirmation names the link it removed.
`rm` then deletes the unit file itself, so nothing can re-enable it. If you only
disabled it, the file would still be there to switch back on.

Prevention ties back to the earlier tiers, and the sharpest single addition is a
watch on the startup locations so a future plant is logged. `auditctl -w` adds
that watch:

```
{user}@{host}:~$ sudo auditctl -w /etc/systemd/system -p wa -k unit_changes
```

Read the flags. `-w /etc/systemd/system` names the directory to watch, `-p wa`
watches for write and attribute changes (the `w` and `a` permissions), and `-k
unit_changes` tags every matching event with the key `unit_changes` so you can
find them later in the audit log. From now on, any new or changed unit file
there is recorded, turning a silent plant into an alert.

The last step is trust but verify. Because persistence can chain, you reboot and
re-run the persistence checklist from your known-good baseline rather than
trusting a single pass:

```
{user}@{host}:~$ systemctl --user list-unit-files --state=enabled
UNIT FILE            STATE
pridwend.service     enabled
```

Only the expected Coach daemon remains, which is the clean result you were
working toward. Persistence removed, a watch in place, and a reboot that comes
up clean is the final state a defender wants, on the Range and beyond.

## When it goes wrong

`Failed to disable unit: Unit file sneaky.service does not exist` means it was
already removed, or lived under a different scope; check both `--user` and the
system units, since a mechanism may have planted itself in either.

`rm: cannot remove '...': No such file or directory` after a successful disable
just means the file was already gone; that is fine, and re-running the checklist
confirms it.

`Error sending add rule request` from `auditctl` usually means you left off
`sudo`; audit rules need root. Add `sudo`, and `pridwen explain auditctl` walks
through the watch flags if `-p` or `-k` is the unclear part.

## Try it

1. On a Range host, fully remove a planted mechanism: `disable --now`, then delete its unit file.
2. Add an audit watch on a startup directory with `auditctl -w ... -p wa -k <key>`.
3. Reboot the host and re-run the persistence checklist from your baseline.
4. Confirm only expected startup entries remain and the host is clean.
5. Explain why persistence is verified from a baseline rather than trusting one pass.

## Remember

- Removal is two steps per mechanism: disable it so it will not start, then delete the file so it cannot be re-enabled.
- Persistence can chain, so verify from a known-good baseline after a reboot instead of trusting a single pass.
- An `auditctl` watch on the startup directories turns the next plant into a logged, tagged alert.
