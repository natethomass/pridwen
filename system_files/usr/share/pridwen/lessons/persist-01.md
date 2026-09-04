# Staying after a reboot

Persistence is how an attacker keeps access after a reboot or a fixed password,
and knowing the mechanisms is how a defender finds them. Almost every method
reuses a legitimate way to start a program automatically, which is why the same
places you would use for a service are the places to check.

On a systemd host the honest tour is short: a service or timer unit that starts
something at boot, a user unit under `~/.config/systemd/user/`, a shell profile
that runs on login, and an added SSH key. Each is a normal feature, which is what
makes it a good hiding place. `systemctl list-unit-files` and `list-timers`,
across system and user, enumerate the unit-based ones.

```
$ systemctl list-unit-files --state=enabled
$ systemctl --user list-unit-files --state=enabled
$ ls -la ~/.config/autostart ~/.config/systemd/user
```

On the Range you plant a benign persistence mechanism, reboot, and confirm it
survived, then hunt it down from the defender's side using these same listings.
The lesson is that persistence hides in plain sight among legitimate startup
entries, so the defence is knowing your own startup surface well enough that a new
entry stands out, which the next lessons turn into a routine.

## Try it

1. On a Range host, enumerate enabled system and user units.
2. Plant a harmless user service that runs at login and reboot to confirm it starts.
3. Find it again from the defender's side using the listings.
4. List the categories of startup location an attacker could use.
