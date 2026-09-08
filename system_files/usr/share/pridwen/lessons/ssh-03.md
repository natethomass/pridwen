# Hardening sshd

Once sshd is running and reachable, it is the one door into your machine that
the whole internet can knock on. A few settings make that door much harder to
force. The two with the most effect are refusing root logins and refusing
passwords altogether, so that only keys work. A password can be guessed by a
script trying thousands per hour, and on any internet-facing host those
attempts fill the logs within minutes of the port opening; a key cannot be
guessed, so the whole category of attack disappears.

On Fedora the clean place to put sshd settings is a small file of your own in
`/etc/ssh/sshd_config.d/`. Those files are read before the main
`/etc/ssh/sshd_config`, and in sshd the first setting wins, so your file
overrides the default. On Pridwen that also means your change survives `bootc
upgrade`, because `/etc` is merged three ways across upgrades and a file you
created is kept. Hardening sshd this way is the RHCSA and Security+ material
in miniature: change one setting, validate, apply, and never lock yourself
out.

## Words you'll meet

- **sshd_config**: the main server configuration file, `/etc/ssh/sshd_config`, owned by the image.
- **drop-in**: a small file in `/etc/ssh/sshd_config.d/` that sshd reads first; the way to override settings without editing the main file.
- **`PermitRootLogin`**: whether the root account may log in over SSH; `no` refuses it.
- **`PasswordAuthentication`**: whether a password is accepted as proof of identity; `no` means keys only.
- **`sshd -t`**: test mode; reads the configuration and reports errors without starting anything.
- **`tee`**: writes what it reads from standard input to a file and also to the screen; with `sudo` it is the usual way to create a root-owned file from a shell.
- **here-document** (`<<'EOF'`): a way of handing several lines to a command as input, ending at a line containing only `EOF`.
- **defence in depth**: more than one independent guard on the same door, so one failure does not open it.

## How it works

Before changing anything, make sure your key already works, because you are
about to turn off the fallback. From a second terminal, or another machine,
`ssh {user}@{host}` should log in with no password prompt; if it asks for one,
go back to the first SSH lesson and `ssh-copy-id` first.

Then write the drop-in. `sudo tee` creates the root-owned file, and the
here-document supplies its two lines; `tee` echoes them back as it writes.

```
{user}@{host}:~$ sudo tee /etc/ssh/sshd_config.d/10-pridwen.conf <<'EOF'
PermitRootLogin no
PasswordAuthentication no
EOF
PermitRootLogin no
PasswordAuthentication no
{user}@{host}:~$ ls -l /etc/ssh/sshd_config.d/
total 8
-rw-------. 1 root root 51 Sep  7 09:52 10-pridwen.conf
-rw-------. 1 root root 35 Aug 14 12:00 50-redhat.conf
```

The number at the front of the filename sets the order: `10-pridwen.conf` is
read before `50-redhat.conf`, and both before the main file, so your `no` wins.
`50-redhat.conf` is Fedora's own drop-in, which loads the system crypto policy;
leave it alone.

Validate before applying. `sshd -t` reads every configuration file and says
nothing when they are all correct; it needs `sudo` because the files are
root-only.

```
{user}@{host}:~$ sudo sshd -t
{user}@{host}:~$ echo $?
0
```

No output and exit status 0 means the configuration is valid. Only now restart
the daemon, and confirm the settings it actually loaded with `-T`, which
prints the effective configuration (`-T` needs `sudo` too).

```
{user}@{host}:~$ sudo systemctl restart sshd
{user}@{host}:~$ sudo sshd -T | grep -E '^(permitrootlogin|passwordauthentication)'
permitrootlogin no
passwordauthentication no
```

`-T` prints keywords in lowercase; both read `no`, so the running daemon has
the new settings. Keep the terminal that is already logged in open, and from a
second terminal or another machine test a fresh login.

```
{user}@{host}:~$ ssh {user}@{host} 'echo still in'
still in
```

The key login still works. If instead it said `Permission denied (publickey)`,
the first session is still open, so you can fix the drop-in from it (usually
the key was never installed for this user) and restart sshd again. Only close
the first session after the second one succeeded.

Why both settings matter. `PermitRootLogin no` is worth setting even though
Pridwen already locks the root account (it has no password, so a password
login could not succeed anyway): it is defence in depth, a second guard that
holds if someone later sets a root password. `PasswordAuthentication no`
removes the guessing attack entirely; with it, a scanner's `Failed password`
lines stop appearing in `journalctl -u sshd`, because passwords are never
even tried.

Two more settings are common on servers and reasonable here.
`MaxAuthTries 3` limits guesses per connection, and `AllowUsers {user}` names
the only accounts that may log in at all. Add them to the same drop-in, run
`sudo sshd -t`, and restart.

## When it goes wrong

`/etc/ssh/sshd_config.d/10-pridwen.conf line 2: Bad configuration option:
PasswordAuthentification` from `sshd -t` is a typo in a keyword; the line
number tells you which. Fix the spelling, run `sshd -t` again, and only then
restart. If you skipped `-t` and restarted, `systemctl status sshd` shows
`failed` and no one can log in until the file is fixed.

`Permission denied (publickey).` on the second terminal after the restart
means passwords are now off and your key is not in that user's
`~/.ssh/authorized_keys` on this machine. From the still-open first session,
`ssh-copy-id {user}@localhost` will not work (passwords are off), so append
the key by hand: `cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys` and
`chmod 600 ~/.ssh/authorized_keys`.

`tee: /etc/ssh/sshd_config.d/10-pridwen.conf: Permission denied` means the
`sudo` was left off `tee`. The redirection belongs to `tee`, not to the shell,
which is why `sudo tee` works where `sudo echo > file` does not. `pridwen
explain sshd` annotates the flags, and `pridwen why` under a failed restart
points at the `sshd -t` step.

## Try it

1. From a second terminal, type `ssh {user}@localhost 'echo ok'` and confirm it logs in with your key and prints `ok`; if it asks for a password, install your key first.
2. Type the `sudo tee /etc/ssh/sshd_config.d/10-pridwen.conf <<'EOF'` block above with `PermitRootLogin no` and `PasswordAuthentication no`.
3. Type `sudo sshd -t` and expect no output; type `echo $?` and expect `0`.
4. Type `sudo systemctl restart sshd`, then `sudo sshd -T | grep -E '^(permitrootlogin|passwordauthentication)'` and expect both `no`.
5. From the second terminal, type `ssh {user}@localhost 'echo still in'` and expect `still in` before you close the first.
6. Explain why keeping the first session open during testing matters.

## Remember

- Settings go in a drop-in under `/etc/ssh/sshd_config.d/`; it is read first, wins, and survives upgrades.
- `sudo sshd -t` before every restart; `sudo sshd -T` after, to read what is really in effect.
- Turn passwords off only after a key login works, and keep the working session open while you test the new one.
