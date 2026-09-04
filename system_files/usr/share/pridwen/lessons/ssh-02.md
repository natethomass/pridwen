# Running sshd on purpose

Pridwen ships the SSH server but leaves it off, because a laptop rarely needs to
accept logins and an open port 22 is the first thing scanners try. Turning it on
is a deliberate two-step, and turning it off again is just as easy.

First start and enable the daemon, then open the port in the firewall, because
the drop zone would discard connections even with sshd running. Both steps are
explicit so that accepting logins is always a choice you made.

```
$ sudo systemctl enable --now sshd
$ sudo firewall-cmd --add-service=ssh --permanent
$ sudo firewall-cmd --reload
$ ssh localhost   # test from the machine itself
```

If `ssh localhost` fails with exit 255 before you do this, that is sshd being
off, not a bug. After enabling, test from the host itself first, then from
another machine on the network. To stop accepting logins, `sudo systemctl
disable --now sshd` and remove the firewall service. Running a service you
understand, and only when you mean to, is the habit the whole secure tier is
built around.

## Try it

1. Try `ssh localhost` first and confirm it is refused while sshd is off.
2. Enable and start sshd, open the firewall service, and reload.
3. Run `ssh localhost` again and log in to your own machine.
4. Turn it back off with `disable --now` and confirm the port is closed.
