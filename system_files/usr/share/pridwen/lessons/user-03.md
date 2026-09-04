# Becoming another user

Sometimes you need to act as another user, most often root. Linux has two tools
for this, and Pridwen deliberately steers you to one of them. `su` switches to
another user by asking for that user's password. `sudo` runs a command as
another user by asking for your own, and it records what you did.

Pridwen keeps the root account locked, so `su` with no argument has no password
to accept. The path to root is `sudo -i` for a login shell or `sudo command`
for a single action. Both check that you are in wheel and both leave a line in
the journal.

```
$ sudo -i
# whoami
root
# exit
$ sudo -u grace -i
$ whoami
grace
```

Passwords are personal. `passwd` with no argument changes yours; changing
another user's password is a root action, `sudo passwd grace`. The reasoning
behind all of this is accountability: a locked root account means there is no
shared secret to leak, and every privileged action is tied to a named person
you can find in the log.

## Try it

1. Run `sudo -i`, confirm with `whoami`, then `exit` back to yourself.
2. Try `su -` and observe that the locked root account gives you nowhere to go.
3. Change your own password with `passwd` (you can set it back).
4. On a Range host, use `sudo -u otheruser id` to run one command as someone else.
