# Owners and why some files are closed

A file belongs to exactly one user and exactly one group, and when you try to open it the kernel checks your identity against those two before it looks at a single permission bit. The order is fixed: if you are the owner, only the owner bits count; otherwise, if you belong to the file's group, only the group bits count; otherwise the other bits count. Your identity is the set of numbers `id` prints, and the kernel never looks past the first match, so an owner with no read bit is refused even when "other" could read.

Understanding this is how you stop treating "Permission denied" as an error and start reading it as information. The system is telling you who it thinks you are and what the file's owner decided. On Pridwen, some of the most important files are closed to you on purpose, `/etc/shadow` most of all, and there is a second, different kind of "no" on top: the read-only image under `/usr`. Telling those two apart is a skill you will use every day of a sysadmin career.

## Words you'll meet

- **identity**: the user id, primary group, and supplementary groups your processes run with; `id` prints it.
- **uid** and **gid**: the numbers behind a user name and a group name; the kernel checks numbers, not names.
- **root**: the administrator account with uid 0, which the mode bits do not restrict.
- **shadow file**: `/etc/shadow`, the root-only file where password hashes are kept.
- **hash**: a scrambled, one-way form of a password; the system stores the hash, never the password.
- **read-only file system**: a mount that refuses every change, whoever asks, even root.
- **image**: the prebuilt copy of `/usr` that Pridwen boots from and replaces whole on upgrade.
- **sudo**: the tool that runs one command as root after checking that you are in the `wheel` group.

## How it works

Start with who you are.

```
{user}@{host}:~$ id
uid=1000({user}) gid=1000({user}) groups=1000({user}),10(wheel) context=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
```

`uid=1000({user})` is your user number and name; the first ordinary user on Fedora gets 1000. `gid=1000({user})` is your primary group, a private group with your own name. `groups=` lists every group you belong to, and `10(wheel)` is the one that lets you use `sudo`. The `context=` part is your SELinux label, which the SELinux node explains.

Now look at the file that holds every account's password hash.

```
{user}@{host}:~$ ls -l /etc/passwd /etc/shadow
-rw-r--r--. 1 root root 2314 Sep  7 08:50 /etc/passwd
----------. 1 root root 1187 Sep  7 08:50 /etc/shadow
```

`/etc/passwd` is `644`, owned by root: anyone may read it, and it is meant to be read, because it maps uid 1000 to `{user}` for every tool that prints a name. `/etc/shadow` is mode `000`: no bits at all, for anyone. Root can still read it, because root is not subject to the mode bits, but every other account is refused before the file is even opened.

```
{user}@{host}:~$ cat /etc/shadow
cat: /etc/shadow: Permission denied
{user}@{host}:~$ sudo head -n 1 /etc/shadow
[sudo] password for {user}:
root:!locked::20000:0:99999:7:::
```

The first attempt was refused: you are not the owner, not in group `root`, and the other bits are `---`. The second ran `head` as root through `sudo`, which asked for your own password and then recorded the use in the journal. The line it printed is root's entry: the name, then `!locked` where a hash would be, which means the root account has no usable password on Pridwen, then dates and limits separated by colons. A locked root is why you use `sudo` instead of logging in as root.

Home directories are the same idea applied to people. Fedora creates each one with mode `700`, so nobody else may list, enter, or change it.

```
{user}@{host}:~$ ls -ld {home}
drwx------. 1 {user} {user} 210 Sep  7 09:14 {home}
```

Configuration under `/etc` is a third pattern: readable by everyone, writable only by root, so any program can read its settings but only an administrator can change them. Editing such a file as yourself opens fine, and the save is what fails.

Then there is the second kind of "no", which is not about permissions at all.

```
{user}@{host}:~$ sudo touch /usr/test
touch: cannot touch '/usr/test': Read-only file system
{user}@{host}:~$ touch pridwen/test
{user}@{host}:~$ ls pridwen/test
pridwen/test
```

Even with `sudo`, the answer is `Read-only file system`, not `Permission denied`. Pridwen is image-based: `/usr` comes from a container image that is mounted read-only, so every machine on the same version is identical byte for byte and `bootc rollback` can always put the previous version back. Nothing is written there, by anyone, ever. Changes go in `/etc` for configuration, `/var` for data, your home for your own files, or the image build itself. The second `touch` in your home worked and printed nothing, which is success.

## When it goes wrong

`cat: /etc/shadow: Permission denied`. The mode is `000` and you are not root. If you truly need to see it, `sudo cat /etc/shadow` reads it as root and leaves a line in the journal saying you did. `pridwen why` explains which of the three checks refused you.

`touch: cannot touch '/usr/local/bin/tool': Read-only file system` after `sudo`. This is the image, not a permission. Put the script in `~/.local/bin` for yourself, or in `/usr/local/bin`, which on Pridwen is a link into the writable `/var/usrlocal`, for everyone.

`nano: /etc/hosts: Permission denied` when saving. The file is root's and `644`. `sudo -e /etc/hosts` edits a copy as you and installs it as root when you finish, which `pridwen explain sudo` describes under `-e`.

## Try it

1. Type `id` and read out your uid, your primary group, and whether `wheel` is in the `groups=` list.
2. Type `ls -l /etc/passwd /etc/shadow` and compare the two modes: `644` and `000`.
3. Type `cat /etc/shadow`, read the refusal, then `sudo head -n 1 /etc/shadow` and find `!locked` in root's line.
4. Type `ls -ld ~` and confirm your home is `drwx------`, which is `700`.
5. Type `sudo touch /usr/test` and read the message carefully: it says `Read-only file system`, not `Permission denied`.
6. Type `touch ~/pridwen/test`, then `ls ~/pridwen`, then `rm ~/pridwen/test` to tidy up.

## Remember

- The kernel checks owner first, then group, then other, and stops at the first match; root skips the check entirely.
- `/etc/shadow` is mode `000` on purpose: it holds password hashes and only root may read it.
- `Permission denied` is about the mode; `Read-only file system` is the Pridwen image under `/usr`, which nobody can change in place.
