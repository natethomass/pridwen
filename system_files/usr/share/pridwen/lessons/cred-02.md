# Hashes and cracking

When an attacker steals a password store, the passwords are not sitting in plain
text; they are hashes, and turning a hash back into a password is cracking.
Understanding it defensively explains why modern hashing is slow on purpose and
why password strength still matters.

A hash is a one-way function, so cracking means guessing a password, hashing the
guess, and comparing. A fast hash lets an attacker try billions of guesses a
second; a slow, salted hash like the yescrypt Fedora uses in `/etc/shadow` is
deliberately expensive per guess, and the salt means identical passwords hash
differently. On the Range you inspect a shadow entry to read its scheme.

```
$ sudo getent shadow testuser | cut -d: -f2 | cut -c1-3
$y$      # yescrypt; $6$ would be sha512crypt, $1$ old md5
```

The `$y$` prefix names the algorithm, and its slowness is a defence you get for
free. The part you control is password strength: length beats complexity, because
each extra character multiplies the guesses needed. Pridwen's
`pwquality.conf` sets a floor. On the Range you can see how a short password falls
quickly to a guessing tool while a long passphrase does not, which is the whole
argument for length made concrete.

## Try it

1. On a Range host, read the hash prefix in a shadow entry and name the scheme.
2. Explain what the salt does when two users share a password.
3. Reason about why a slow hash helps the defender.
4. Compare the guess counts implied by a short password and a long passphrase.
