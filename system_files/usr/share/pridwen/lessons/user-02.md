# Creating accounts and groups

Adding a user writes to `/etc/passwd`, `/etc/shadow`, and `/etc/group`, all
owned by root, so account tools need `sudo`. `useradd` creates the account,
`passwd` gives it a password, and `usermod` changes it afterward.

The important detail with groups is the difference between replacing and adding.
`usermod -aG group user` appends a supplementary group. Leaving out the `-a`
replaces the entire supplementary set, which can quietly remove someone from
wheel. Group changes take effect at the next login, not in the current session.

```
$ sudo useradd -m -c "Grace Hopper" grace
$ sudo passwd grace
$ sudo usermod -aG wheel grace
$ id grace
uid=1001(grace) gid=1001(grace) groups=1001(grace),10(wheel)
```

On Fedora `useradd -m` creates the home directory and copies the skeleton files
from `/etc/skel`; a fresh account has no password until you set one, so nobody
can log in yet. When you remove an account, `userdel -r` also removes its home;
plain `userdel` leaves the files behind owned by a now-nameless uid, which is
worth knowing when `ls -ln` later shows numbers instead of names.

## Try it

1. On a Range container, `sudo useradd -m tester` and set a password.
2. Run `id tester` before and after `sudo usermod -aG wheel tester`.
3. Explain why `usermod -G` without `-a` is risky.
4. Remove the account with `sudo userdel -r tester` and confirm the home is gone.
