# Who you are

A Linux system knows you by numbers, not by name. Your account has a user id (uid), a primary group id (gid), and a list of extra groups called supplementary groups. Names like `{user}` and `wheel` are a convenience for humans, looked up in two plain text files, `/etc/passwd` for users and `/etc/group` for groups. The kernel never reads those names; when it checks whether you may open a file, it compares the numbers on the file with the numbers your process carries. That is why a file can show up owned by `1001` instead of a name: the number outlived the account.

Knowing your own identity precisely is the first step of every permissions problem and every privilege question. On Pridwen the one group that matters most is `wheel`, because only its members may use `sudo`; the welcome wizard put your account in it. On a real job, `id` is the first thing you run on an unfamiliar machine, and `getent` is how you look up an account the same way the system does, whether the account lives in a local file or in a company directory.

## Words you'll meet

- **uid**: the user id, a number; `0` is root and the first ordinary user on Fedora is `1000`.
- **gid**: the group id, a number; your primary group is the one new files get by default.
- **primary group**: the single group an account belongs to first; on Fedora it is a private group named after the user.
- **supplementary groups**: any further groups an account belongs to, such as `wheel`.
- **wheel**: the group whose members may run `sudo` on Pridwen.
- **`/etc/passwd`**: one line per account with its uid, gid, home and shell; readable by everyone.
- **`/etc/shadow`**: one line per account with its password hash; readable only by root.
- **`/etc/group`**: one line per group with its gid and its members.
- **getent**: a tool that reads accounts and groups through the same lookup path programs use.

## How it works

`id` prints your whole identity on one line.

```
{user}@{host}:~$ id
uid=1000({user}) gid=1000({user}) groups=1000({user}),10(wheel) context=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
```

`uid=1000({user})` is your user number with the name in brackets. `gid=1000({user})` is your primary group; Fedora gives every user a private group with the same name and usually the same number. `groups=` is the full list you belong to, which always includes the primary group; `10(wheel)` is the one that unlocks `sudo`. The `context=` part is your SELinux label and belongs to a later node. Two smaller tools show pieces of the same thing: `whoami` prints just the name, and `groups` prints just the group names.

```
{user}@{host}:~$ whoami
{user}
{user}@{host}:~$ groups
{user} wheel
```

Now look at where the names come from. `getent passwd {user}` asks for one account's entry, and the answer is the line from `/etc/passwd`.

```
{user}@{host}:~$ getent passwd {user}
{user}:x:1000:1000:Your Name:{home}:/bin/bash
```

Seven fields separated by colons. First the login name. Then `x`, a placeholder where the password hash used to sit decades ago; it moved to `/etc/shadow` so that the rest of this line could stay readable by everyone. Then the uid `1000` and the gid `1000`. The fifth field is a comment, normally the full name you typed in the welcome wizard. Then the home directory, `{home}`, and finally the login shell, `/bin/bash`, which is the program started when you open a terminal or log in.

The same lookup works for groups. `getent group wheel` shows the group's line from `/etc/group`: name, an `x` placeholder, the gid, and a comma-separated list of members.

```
{user}@{host}:~$ getent group wheel
wheel:x:10:{user}
```

Why `getent` rather than reading the file directly? Because on a company network accounts may come from a directory server instead of a local file, and `getent` follows whatever the system is configured to use. `cat /etc/passwd` would only show the local ones.

The two files have very different modes on purpose.

```
{user}@{host}:~$ ls -l /etc/passwd /etc/shadow
-rw-r--r--. 1 root root 2314 Sep  7 08:50 /etc/passwd
----------. 1 root root 1187 Sep  7 08:50 /etc/shadow
```

`/etc/passwd` is `644`: anyone may read it, because every `ls -l` needs it to turn `1000` into `{user}`. `/etc/shadow` is `000`: nobody but root may read it, because it holds the hashes an attacker would try to crack. Splitting the two files is one of the oldest security decisions on Unix, and Pridwen keeps it exactly as Fedora ships it.

## When it goes wrong

`cat: /etc/shadow: Permission denied`. Expected: the file is mode `000`. `sudo cat /etc/shadow` reads it as root and records the use. `pridwen why` explains why the hashes live apart from `/etc/passwd`.

`{user} is not in the sudoers file.` The account is not in `wheel`. Run `id` and check `groups=`. An administrator adds you with `sudo usermod -aG wheel {user}`, and the change applies at your next login, not in the current terminal.

`ls -l` shows a number such as `1001` instead of an owner name. The uid on the file has no matching line in `/etc/passwd`, usually because the account was deleted. The file is intact; only the name is gone. `getent passwd 1001` confirms there is no such account.

## Try it

1. Type `id`. Say your uid, your primary group, and whether `10(wheel)` appears in `groups=`.
2. Type `whoami` and `groups`. They should agree with the `id` line.
3. Type `getent passwd {user}` and count the seven colon-separated fields aloud: name, `x`, uid, gid, comment, home, shell.
4. Type `getent group wheel` and confirm your name is in the member list at the end.
5. Type `ls -l /etc/passwd /etc/shadow` and compare `644` with `000`.
6. Type `getent passwd 0` to see root's entry, and note that its shell is `/bin/bash` even though its password is locked.

## Remember

- The kernel checks uid and gid numbers; `/etc/passwd` and `/etc/group` only supply the names.
- `id` prints your uid, primary group, and every supplementary group; `wheel` is the one that allows `sudo`.
- `/etc/passwd` is world-readable and holds no secrets; the hashes are in `/etc/shadow`, mode `000`.
