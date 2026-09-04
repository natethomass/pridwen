# Keys and secrets that hold

The way out of the password guessing game is to stop relying on a guessable
secret. Keys, multi-factor prompts, and lockouts each change the attacker's
arithmetic, and understanding why is the defensive payoff of the whole node.

An SSH key pair replaces a guessable password with a secret too large to guess,
kept off the server entirely; only the public half is on the host. Combined with
`PasswordAuthentication no`, it removes online guessing against SSH completely,
which is why the SSH node teaches keys first. Lockouts and rate limits handle the
services that must still take passwords.

```
$ ssh-keygen -t ed25519
$ ssh-copy-id nate@web-01
$ sudo tee /etc/ssh/sshd_config.d/20-nopw.conf <<'EOF'
PasswordAuthentication no
EOF
```

The broader lesson is that credentials should be strong, scarce, and revocable. A
key you can remove from `authorized_keys` is better than a shared password no one
can rotate; a secret that never touches the server cannot be stolen from it. On
the Range you take a host from password logins to keys-only and watch the guessing
attempts that used to fill the log simply stop finding a door, which is the most
satisfying defence in the tier.

## Try it

1. On a Range host, replace password SSH login with a key.
2. Turn off password authentication and confirm guessing attempts fail.
3. Remove a key from `authorized_keys` and note how revocation works.
4. Explain why a key kept off the server cannot be stolen from it.
