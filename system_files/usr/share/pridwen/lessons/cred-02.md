# Hashes and cracking

When an attacker gets hold of a password store, the passwords are not sitting
there in plain text; they are hashes, and turning a hash back into the password
is called cracking. Understanding cracking defensively explains two things you
will otherwise take on faith: why modern password hashing is slow on purpose,
and why the length of a password matters more than its punctuation.

Everything here runs only against Range targets you own: a Rocky 9 lab host
whose `/etc/shadow` you may read and whose lab accounts you may test. You never
crack hashes from a system you do not control. On a real job this is why you
check which hashing scheme your systems use and set a minimum password length,
because those two settings decide how a stolen store holds up.

## Words you'll meet

- **hash**: the output of a one-way function that turns a password into a fixed string you cannot reverse.
- **one-way function**: a calculation that is easy to run forward and impractical to run backward.
- **cracking**: guessing a password, hashing the guess, and comparing it to the stored hash until they match.
- **salt**: a random value mixed into the hash so two equal passwords hash to different strings.
- **/etc/shadow**: the root-only file that stores each account's password hash and aging rules.
- **yescrypt**: the deliberately slow, salted hashing scheme Fedora and Rocky use by default.
- **pwquality**: the PAM piece that enforces a minimum password length and complexity when a password is set.

## How it works

A hash is one-way, so there is no "decrypt" step. Cracking is a loop: take a
candidate password, run it through the same hash function the system used, and
see if the result equals the stored hash. The only lever the attacker has is
speed: how many candidates per second. That is exactly the lever a slow hash
takes away.

To work on a Range host, you first connect to it from your own Pridwen machine
with SSH, which opens a command line on the far end and changes your prompt to
that host's name:

```
{user}@{host}:~$ ssh labuser@range-01
labuser@range-01:~$
```

The prompt now reads `labuser@range-01`, so the commands below run on the Range
target. There you read a lab account's hash from `/etc/shadow`, which is
readable only by root, and look at the front of it to name the scheme. The
prefix between dollar signs is the algorithm id:

```
labuser@range-01:~$ sudo getent shadow labuser | cut -d: -f2 | cut -c1-3
$y$
```

Read that back. `getent shadow labuser` prints the shadow line for the account,
`cut -d: -f2` keeps the second colon-separated field (the hash), and `cut -c1-3`
keeps its first three characters. The result `$y$` names yescrypt. A `$6$`
prefix would mean sha512crypt, and an old `$1$` would mean md5crypt. The
important part is that yescrypt is slow and salted on purpose: slow means each
guess costs the attacker real time, and salted means the random salt stored with
the hash makes two identical passwords hash differently, so an attacker cannot
crack one and get the rest for free.

The part you control is length. Each extra character multiplies the number of
guesses needed, so a long passphrase beats a short complex password by a wide
margin. Rocky and Pridwen enforce a floor through pwquality; you can read the
current minimum length setting:

```
labuser@range-01:~$ grep -E '^\s*minlen' /etc/security/pwquality.conf
minlen = 12
```

Here `grep -E '^\s*minlen'` finds the line that begins with optional spaces and
`minlen` (extended regex, `-E`). The value `12` is the shortest password the
system will accept. On the Range you can watch a short password fall quickly to
a guessing tool while a long passphrase does not, which is the whole argument
for length made concrete.

## When it goes wrong

`Permission denied` when reading the hash means you ran `getent shadow` without
root; the shadow file is root-only by design. Add `sudo` so the command runs as
root, which is the whole reason the hashes are not in the world-readable
`/etc/passwd`.

An empty result from the `cut` pipeline means the account has no password set
(the field may be `!` or `*`, meaning locked). That is a locked account, not an
error; pick a lab account that has a password.

If `grep` prints nothing for `minlen`, the setting is left at its built-in
default rather than written in the file. Run `pridwen explain grep` if the flags
are the part you are unsure about.

## Try it

1. On a Range host, read a lab account's hash prefix with the `getent shadow ... | cut` pipeline and name the scheme.
2. Explain in one sentence what the salt does when two accounts share the same password.
3. Reason out loud why a slow hash helps the defender and hurts the attacker.
4. Read the `minlen` value in `pwquality.conf` and say what it enforces.
5. Compare the guess counts implied by a short password and a long passphrase.

## Remember

- A hash is one-way, so cracking means guessing, hashing the guess, and comparing; the attacker's only lever is speed.
- A slow, salted scheme like yescrypt (`$y$` in `/etc/shadow`) makes each guess expensive and stops one crack from unlocking the rest.
- Length is the lever you control: each extra character multiplies the guesses needed, which is why pwquality sets a minimum length.
