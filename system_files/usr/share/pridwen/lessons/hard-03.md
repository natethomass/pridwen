# Names, time, and accounts

The rest of the baseline covers the plumbing that other controls depend on:
encrypted name lookups, an accurate clock, an audit trail, and account lockout.
None is dramatic on its own, but each closes a gap that would weaken the others.

DNS on Pridwen goes over TLS through systemd-resolved, so lookups cannot be read
or tampered with on the wire; `resolvectl status` shows it as on. The clock is
kept by chrony, and an accurate clock is what makes log timelines and TLS
certificates trustworthy, so setting it by hand fights the system. auditd records
security events, and `pam_faillock` locks an account after too many failed
passwords.

```
$ resolvectl status | grep -i "DNS over TLS"
$ timedatectl | grep -i "NTP service"
$ sudo faillock --user nate         # show failed attempts
```

If a fat-fingered password locks an account, `sudo faillock --user name --reset`
clears the counter. Password quality itself is set in
`/etc/security/pwquality.conf`, and loosening it weakens every account at once,
so that is a lab change, not a daily one. The posture panel reads all of these
and reports drift, turning each control from an invisible default into something
you can check and defend.

## Try it

1. Confirm DNS over TLS is active with `resolvectl status`.
2. Check that NTP is synchronising with `timedatectl`.
3. Read your own failed-login counter with `sudo faillock --user $USER`.
4. Explain why an accurate clock matters for both logs and TLS.
