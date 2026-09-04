# How guessing works

Credentials are the front door, and attackers try to walk through it by guessing.
Understanding this defensively means knowing what makes guessing cheap or
expensive, so you can make it expensive. The two forms are online guessing against
a live service and offline cracking of stolen hashes.

Online guessing tries passwords against a login, and its cost is set by the
defender: rate limits, lockouts, and the absence of a login to attack at all.
Pridwen keeps sshd off by default and root locked, which removes the most common
target. `pam_faillock` locks an account after repeated failures, and you can see
the counter with `faillock`.

```
$ sudo faillock --user testuser
testuser:
When    Type  Source   Valid
...three failed attempts logged...
$ sudo faillock --user testuser --reset
```

On a Range host you watch a guessing attempt fill the log and trip the lockout,
then see how keys-only SSH removes the whole game because there is no password to
guess. The defender's levers are all about arithmetic: fewer login surfaces,
slower attempts, and secrets strong enough that even fast guessing gets nowhere.
The next lessons cover the offline side and where keys change the maths entirely.

## Try it

1. On a Range host, read an account's failed-login counter with `faillock`.
2. Trigger a lockout with repeated wrong passwords, then reset it.
3. Switch a service to keys-only and explain why guessing no longer applies.
4. List the login surfaces on your host and which you could remove.
