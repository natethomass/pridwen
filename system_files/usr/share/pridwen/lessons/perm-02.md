# Owners and why some files are closed

A file belongs to one user and one group, and the mode is checked against your
identity in that order: if you are the owner, the owner bits apply; else if you
are in the group, the group bits apply; else the other bits apply. Your identity
is what `id` prints.

This is why some files are closed to you by design. `/etc/shadow` holds password
hashes and is mode 0000 owned by root, so no ordinary user can read it. Home
directories are created mode 0700, so each person's files are private. System
configuration in `/etc` is writable only by root.

```
$ ls -l /etc/shadow
----------. 1 root root 1234 Sep  1 07:00 /etc/shadow
$ cat /etc/shadow
cat: /etc/shadow: Permission denied
$ sudo cat /etc/shadow | head -n 1
root:!locked::0:99999:7:::
```

On Pridwen there is a second layer: `/usr` is part of a read-only image, so even
root gets "Read-only file system" there. That is not a permission problem but a
mount property, and it is what makes the base system identical on every machine
and safe to roll back. Changes belong in `/etc`, `/var`, your home, or the image
build.

## Try it

1. Run `id` and note your user, primary group, and supplementary groups.
2. Try to read `/etc/shadow` as yourself, then with `sudo`, and compare.
3. Run `ls -ld ~` and confirm your home is mode 0700.
4. Try `touch /usr/test` and read the error, then try `touch ~/test` instead.
