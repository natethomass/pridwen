# Removing and preventing

Finding persistence is half the job; removing it cleanly and keeping it from
recurring is the other half. Removal has to be complete, because a single missed
mechanism re-establishes the rest, and prevention is about closing the paths that
let it be planted at all.

Removal means disabling and deleting the unit, timer, key, or profile line, then
rebooting and re-checking to confirm nothing brought it back. Because persistence
often chains, one entry recreating another, you verify from a clean baseline
rather than trusting a single pass. Prevention ties back to the earlier tiers:
least-privilege sudo, correct file ownership, keys-only SSH, and detection watches
on the startup locations.

```
$ systemctl --user disable --now sneaky.service
$ rm ~/.config/systemd/user/sneaky.service
$ sudo auditctl -w /etc/systemd/system -p wa -k unit_changes
$ # reboot, then re-run the persistence checklist to confirm it is gone
```

On the Range you remove a planted mechanism, add a watch so a future one raises an
alert, and reboot to prove the host comes up clean. This is where the whole tree
closes: the attack tier taught you where to look, the defend tier how to watch,
and the secure tier how to shut the doors. Persistence removed and prevented is
the final state a defender is working toward, on the Range and beyond.

## Try it

1. On a Range host, fully remove a planted persistence mechanism.
2. Add an audit watch on a startup directory so a new entry alerts.
3. Reboot and re-run the checklist to confirm the host is clean.
4. Explain why persistence is verified from a baseline rather than a single check.
