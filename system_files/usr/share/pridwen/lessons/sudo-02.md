# Using sudo well

sudo has sharp edges that come from a simple fact: your shell sets up the command
line before sudo elevates anything. Redirections, pipes, aliases and builtins are
the shell's, so sudo does not cover them.

The classic trap is `sudo echo text > /etc/file`, where the `>` is done by your
shell as you, so the write fails. The fix is to elevate the part that writes:
`echo text | sudo tee /etc/file` runs `tee` as root, and `tee -a` appends.
Shell builtins like `cd` and `export` have no program for sudo to run, so
`sudo cd` cannot work; use `sudo -i` for a root shell instead.

```
$ echo 'net.ipv4.ip_forward=0' | sudo tee /etc/sysctl.d/99-local.conf
$ sudo -e /etc/hosts        # sudoedit: edits a copy as you, installs as root
```

For editing, prefer `sudo -e` (sudoedit) over `sudo vim`. It copies the file,
runs your editor as your normal user with your config, and writes the result back
as root, which avoids running a whole editor and its plugins as root. And when
you edit sudoers itself, always use `sudo visudo`, which checks the syntax before
saving, because a broken sudoers file locks everyone out.

## Try it

1. Try `sudo echo hi > /etc/motd` and watch it fail, then do it with `sudo tee`.
2. Use `sudo -e` to open a file, make a change, and save it.
3. Explain why `sudo cd /root` cannot work and what to use instead.
4. Run `sudo visudo -c` to check the sudoers syntax is valid.
