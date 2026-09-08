# How guessing works

Credentials are the front door of most systems, and the oldest attack is simply
to try the door: guess a username and password until one works. Understanding
this defensively means knowing what makes guessing cheap and what makes it
expensive, because the defender sets that price. Once you can see the levers,
you can make the door too slow and too quiet to be worth attacking.

Everything here runs only against Range targets you own: Rocky 9 lab hosts you
start yourself with `pridwen enter rocky`, where you may create a throwaway
account and watch it get locked out. You never guess passwords against a system
you do not control. On a real job this is why you count login surfaces and turn
on lockouts before an attacker counts them for you.

## Words you'll meet

- **credential**: the pair of secrets that proves who you are, usually a username and a password (or a key).
- **online guessing**: trying passwords against a live service that answers each attempt, like an SSH or web login.
- **offline cracking**: guessing against a stolen copy of the password store, with no live service to slow you down.
- **rate limit**: a cap on how many attempts a service will accept in a stretch of time.
- **lockout**: disabling an account after too many failures, so further guesses do nothing.
- **PAM**: Pluggable Authentication Modules, the framework Linux uses to decide whether a login succeeds.
- **pam_faillock**: the PAM piece that counts failed logins per account and locks the account when the count is too high.

## How it works

The defender's first lever is to have fewer doors. Pridwen ships with `sshd`
(the SSH login service) turned off and the root account locked, which removes
the two targets guessing attacks reach for first. On a Range host you can turn a
service on to study it, but the habit is to ask what is listening at all.

To work on a Range host, you first connect to it from your own Pridwen machine
with SSH, which opens a command line on the far end and changes your prompt to
that host's name:

```
{user}@{host}:~$ ssh labuser@range-01
labuser@range-01:~$
```

The prompt now reads `labuser@range-01`, so every command below runs on the
Range target, not on your own machine.

The second lever is the lockout. On a Range host, after a few wrong passwords
for an account, `pam_faillock` records the failures. You read the counter with
the `faillock` command, naming the account with `--user`:

```
labuser@range-01:~$ sudo faillock --user labuser
labuser:
When                Type  Source   Valid
2026-09-07 09:12:41 RHOST 10.88.0.5    V
2026-09-07 09:12:44 RHOST 10.88.0.5    V
2026-09-07 09:12:47 RHOST 10.88.0.5    V
```

Read that back. Each row is one failed attempt: the time, the type, the source
address it came from, and whether it is still valid (`V`) toward the lockout
count. Three valid failures here means the account is close to, or past, its
limit, at which point further guesses are refused no matter what password is
sent. When you have studied it, you clear the counter with `--reset`:

```
labuser@range-01:~$ sudo faillock --user labuser --reset
```

That prints nothing and returns you to the prompt, which is the normal result;
the counter is now zero. On the Range you watch a guessing run fill this table
and trip the lockout, then see that a keys-only service removes the game
entirely because there is no password field to guess against. The defender's
levers are all arithmetic: fewer login surfaces, slower attempts, and secrets
strong enough that even fast guessing gets nowhere. The next lessons cover the
offline side and where keys change the maths for good.

## When it goes wrong

`faillock: Error resetting the tally file: Permission denied` means you ran it
without root; the tally lives in a root-owned directory. Put `sudo` in front so
it runs as root, which `pridwen why` will also point out after the failure.

An empty table under the account name means no failures are recorded: either the
account has not been guessed at, or the counter was already reset. That is the
healthy state, not an error.

`Unknown user` from `getent` or a login tool means the account does not exist on
that host; create the throwaway lab account first, then guess against it.

## Try it

1. On a Range host, create a throwaway account you own for the exercise.
2. Read its failed-login counter with `sudo faillock --user labuser` and note it is empty.
3. Trigger a lockout with repeated wrong passwords, then read the counter again and see the rows.
4. Reset the counter with `sudo faillock --user labuser --reset` and confirm it is empty.
5. Switch the service to keys-only and explain in a sentence why guessing no longer applies.

## Remember

- Guessing comes in two forms: online against a live service the defender can slow, and offline against a stolen store the defender cannot.
- The defender's levers are arithmetic: fewer login surfaces, lockouts and rate limits, and secrets too strong to guess.
- `faillock --user <name>` shows the failure count per account, and `--reset` clears it; Pridwen ships sshd off and root locked to remove the first targets.
