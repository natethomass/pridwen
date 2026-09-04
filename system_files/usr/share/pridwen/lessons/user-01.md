# Who you are

A Linux system knows you by numbers, not names. Your account has a user id and a
primary group id, plus a list of supplementary groups. The names are a
convenience mapped from `/etc/passwd` and `/etc/group`; the kernel checks the
numbers.

`id` prints all of it in one line. `whoami` gives just the name, and `groups`
lists the group names. The group that matters most on Pridwen is `wheel`, since
membership in it is what lets `sudo` work.

```
$ id
uid=1000(nate) gid=1000(nate) groups=1000(nate),10(wheel),18(dialout)
$ groups
nate wheel dialout
```

`/etc/passwd` has one line per account: name, an `x` where the password used to
sit, the uid, the gid, a comment field, the home directory, and the login
shell. It is world-readable so that tools can turn uid 1000 into "nate". The
password hashes moved long ago to `/etc/shadow`, which only root can read.
Reading accounts through `getent passwd` uses the same path programs do, so it
keeps working when accounts come from a network directory later.

## Try it

1. Run `id` and identify your uid, primary group, and whether you are in wheel.
2. Run `getent passwd $USER` and name each of the seven fields.
3. Compare the modes of `/etc/passwd` and `/etc/shadow` with `ls -l`.
4. Run `groups` and look up one group name in `/etc/group`.
