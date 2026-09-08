# Creating accounts and groups

Adding a user is the moment a person becomes an identity on the machine. It writes a line into `/etc/passwd`, a line into `/etc/shadow`, and a line into `/etc/group`, creates a home directory, and copies a few starter files into it. All three files are owned by root, so every account tool needs `sudo`. Three commands do the work: `useradd` creates an account, `passwd` gives it a password, and `usermod` changes an existing account, most often to add it to a group. `userdel` removes one.

This is bread-and-butter administration and a core RHCSA exam skill. It also carries the single most common quiet mistake in the trade: `usermod -G` without `-a` silently removes a user from every group not named in the command, including `wheel`. Practise these commands where a slip costs nothing: inside a Distrobox (a throwaway Fedora or Rocky container where `sudo` works and nothing you do reaches the host) or on a Range target once the lab is available, not on your own Pridwen desktop unless you mean it.

## Words you'll meet

- **account**: a login name with a uid, a home directory, a shell, and usually a password.
- **home directory**: the account's own directory under `/home`, created by `useradd -m`.
- **skeleton**: `/etc/skel`, the template directory whose contents are copied into every new home.
- **login shell**: the program started when the account logs in; `/bin/bash` on Pridwen.
- **supplementary group**: a group an account belongs to in addition to its primary group.
- **append**: adding to a list without replacing it; the `-a` flag on `usermod`.
- **lock**: marking a password unusable without deleting the account, `passwd -l`.
- **orphaned file**: a file whose owner uid no longer matches any account, shown as a number by `ls -l`.

## How it works

Create an account called `tester`. `-m` (make home) creates the home directory from `/etc/skel`, and `-c` (comment) fills the full-name field you saw in `getent passwd`.

```
{user}@{host}:~$ sudo useradd -m -c "Test account" tester
{user}@{host}:~$ id tester
uid=1001(tester) gid=1001(tester) groups=1001(tester)
```

`useradd` printed nothing, which means it worked. `id tester` shows the new account got the next free uid, `1001`, and a private group of the same name. It has no supplementary groups yet. Fedora's `useradd` creates the home directory by default, but `-m` says so explicitly and works the same on every Linux, which is why the lesson always includes it.

A fresh account has no password, so nobody can log in as it yet. `passwd` asks for the new password twice and never shows what you type.

```
{user}@{host}:~$ sudo passwd tester
New password:
Retype new password:
passwd: all authentication tokens updated successfully.
```

The last line is the success message. If the two entries do not match, `passwd` says `Sorry, passwords do not match.` and asks again.

Adding an account to a group is `usermod -aG` (`-a` for append, `-G` for supplementary groups). Watch the difference with and without `-a`.

```
{user}@{host}:~$ sudo usermod -aG wheel tester
{user}@{host}:~$ id tester
uid=1001(tester) gid=1001(tester) groups=1001(tester),10(wheel)
```

`10(wheel)` was added to the list and everything already there was kept. Without `-a`, `usermod -G wheel tester` means "the supplementary groups are exactly: wheel", and any other memberships vanish. On a server where someone was in `wheel` and `docker` and you add them to `developers` without `-a`, they lose `sudo` at once and nobody knows why until the next login fails. Group changes apply at the next login, not in the current session, because a running shell carries the identity it started with.

Removing an account is `userdel`. With `-r` (remove) the home directory and mail spool go too; without it, the files stay behind, owned by a uid that no longer has a name.

```
{user}@{host}:~$ sudo userdel tester
{user}@{host}:~$ sudo ls -ln /home
drwx------. 1 1001 1001 80 Sep  7 10:02 tester
{user}@{host}:~$ cd /home
{user}@{host}:/home$ sudo rm -r tester
{user}@{host}:/home$ cd
```

`ls -ln` (`-n` for numeric) prints uids and gids instead of names, and here plain `ls -l` would print the same numbers because there is no longer a name to show. That is what an orphaned directory looks like. `userdel -r tester` in the first place avoids the clean-up.

## When it goes wrong

`useradd: Permission denied.` or `useradd: cannot lock /etc/passwd; try again later.` when run without `sudo`. Account files belong to root. Put `sudo` in front: `sudo useradd -m tester`. `pridwen why` shows the three files involved.

`useradd: user 'tester' already exists` with exit code 9. The account is there from a previous attempt. `getent passwd tester` shows its entry; use `usermod` to change it or `userdel -r tester` to start over.

`userdel: user tester is currently used by process 4321` with exit code 8. Someone is logged in as that account. `loginctl list-sessions` shows who; `sudo loginctl terminate-user tester` ends the session, then `userdel -r` works.

`id tester` still lacks `wheel` after `usermod -aG wheel tester` from tester's own terminal. The change is written but the running session predates it. Log out and back in, or open a new login with `su - tester`, and check again.

## Try it

1. Enter a throwaway box first: `distrobox create -n practice -i fedora:43` then `distrobox enter practice`. Everything below happens inside it.
2. Type `sudo useradd -m -c "Test account" tester` and then `id tester`. Note the uid and the single group.
3. Type `sudo passwd tester` and set a password you can remember for the next lesson.
4. Type `sudo usermod -aG wheel tester` and `id tester` again. `10(wheel)` should have appeared.
5. Type `getent passwd tester` and read the seven fields: the comment should say `Test account` and the shell `/bin/bash`.
6. Type `sudo userdel tester` (without `-r`), then `sudo ls -ln /home`, and find the directory owned by a bare number.
7. Type `cd /home`, then `sudo rm -r tester` to remove the orphan, then `cd` to go home. Now recreate the account with `sudo useradd -m tester` and remove it properly with `sudo userdel -r tester`. `ls /home` should no longer show it.

## Remember

- `useradd -m` creates the account and its home, `passwd` gives it a password, and both need `sudo`.
- `usermod -aG group user` appends a group; without `-a` every other supplementary group is removed.
- `userdel -r` removes the home too; plain `userdel` leaves files owned by a number with no name.
