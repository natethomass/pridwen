# Hardening sshd

Once sshd is running, a few settings make it much harder to attack. On Fedora the
clean place to put them is a small file in `/etc/ssh/sshd_config.d/`, which is
read before the main config and survives image updates.

The two changes with the most effect are disabling root login and disabling
password authentication, so only keys work. Before you turn passwords off, make
sure your key is already installed and keep your current session open while you
test a new one, or you can lock yourself out.

```
$ sudo tee /etc/ssh/sshd_config.d/10-pridwen.conf <<'EOF'
PermitRootLogin no
PasswordAuthentication no
EOF
$ sudo sshd -t && sudo systemctl restart sshd
```

`sudo sshd -t` checks the configuration before you apply it, which is the habit
that prevents a broken restart. `PermitRootLogin no` matters even though Pridwen
locks root already, because it is defence in depth. Keys-only login removes the
whole category of password guessing that fills logs on any internet-facing host.
Test the new settings from a second terminal before you close the one that still
works.

## Try it

1. Create a drop-in in `sshd_config.d` with `PermitRootLogin no`.
2. Run `sudo sshd -t` to validate, then restart sshd.
3. From a second session, confirm you can still log in with your key.
4. Explain why keeping the first session open during testing matters.
