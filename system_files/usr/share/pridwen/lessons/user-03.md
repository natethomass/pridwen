# Becoming another user

Sometimes you need to act as an account other than your own, and most of the time that account is root, the administrator with uid 0 whom the permission bits do not restrict. Linux has two tools for changing identity, and they answer a different question about trust. `su` (substitute user) switches to another account by asking for that account's password: it trusts whoever knows the secret. `sudo` runs a command as another account by asking for your own password, checks that a policy allows it, and writes a line in the journal saying who did what: it trusts a named person and keeps a record.

Pridwen deliberately steers you to the second one. The root account has no password at all, so `su` to root has nothing to accept, and every privileged action goes through `sudo` under your own name. That is the same setup you will find on well-run servers and in every compliance baseline: a locked root means there is no shared secret to leak, phish or reuse, and the log always names a person. The habit of typing `sudo` in front of one command, rather than living in a root shell, is the one this lesson builds.

## Words you'll meet

- **root**: the administrator account, uid 0; the kernel skips permission checks for it.
- **locked account**: one whose password field holds `!locked` or `!`, so no password can match; the account still exists.
- **su**: switch to another user by giving that user's password.
- **sudo**: run one command, or a shell, as another user by giving your own password, if policy allows.
- **login shell**: a shell started as if you had just logged in, with that user's environment and home.
- **journal**: the system log kept by systemd, where every `sudo` use is recorded.
- **wheel**: the group whose members `sudo` accepts on Pridwen.
- **credential**: the password or other secret that proves who you are.

## How it works

Try the direct road first and watch it close. `su -` with no name means "become root with a login shell".

```
{user}@{host}:~$ su -
Password:
su: Authentication failure
```

Whatever you type, the answer is `Authentication failure`, because root's password field is `!locked` and nothing matches a locked field. This is not a mistake on your part; it is the design.

The road Pridwen wants you on is `sudo -i` (`-i` for a login shell as the target user, root by default). It asks for your own password, checks that you are in `wheel`, and opens a root shell.

```
{user}@{host}:~$ sudo -i
[sudo] password for {user}:
root@{host}:~# whoami
root
root@{host}:~# exit
logout
{user}@{host}:~$
```

Read the prompt: the name changed to `root`, the home became root's, and the final character changed from `$` to `#`, which is the traditional warning that every command now runs unrestricted. `whoami` confirms it. `exit` closes the root shell and returns to your own prompt. For a single action, `sudo command` is shorter and safer, because there is no root shell left open to forget about.

```
{user}@{host}:~$ sudo journalctl -n 1 _COMM=sudo
Sep 07 10:15:02 {host} sudo[4210]:   {user} : TTY=pts/0 ; PWD={home} ; USER=root ; COMMAND=/usr/bin/journalctl -n 1 _COMM=sudo
```

That line is the record: your name, the terminal, the working directory, the user you became and the exact command. `sudo -l` (list) shows what the policy allows you to run.

Becoming another ordinary user works the same way. `sudo -u tester -i` (`-u` for which user) opens a login shell as `tester` using your password, not theirs, and it is logged. Use the `tester` account from the previous lesson inside your Distrobox.

```
{user}@{host}:~$ sudo -u tester -i
tester@{host}:~$ whoami
tester
tester@{host}:~$ exit
```

Passwords are personal. `passwd` with no argument changes your own; it asks for the current one first so that someone at an unlocked screen cannot change it. Changing another user's password is a root action, `sudo passwd tester`, and it does not ask for their old one, because an administrator resets passwords for people who have forgotten them.

```
{user}@{host}:~$ passwd
Changing password for user {user}.
Current password:
New password:
Retype new password:
passwd: all authentication tokens updated successfully.
```

One thing not to do: `sudo passwd root`. It would give root a password and reopen the direct road that Pridwen closed. If it happens, `sudo passwd -l root` (`-l` for lock) closes it again.

## When it goes wrong

`su: Authentication failure` after `su -`. Root is locked, so there is no password that works. `sudo -i` is the root shell on Pridwen. `pridwen why` explains the locked-root design after this failure.

`{user} is not in the sudoers file.  This incident will be reported.` The account is not in `wheel`. `id` shows the groups; an administrator adds you with `sudo usermod -aG wheel {user}`, and it applies at your next login.

`passwd: Only root can specify a user name.` You ran `passwd tester` as yourself. Plain `passwd` changes your own password; `sudo passwd tester` changes someone else's. `pridwen explain passwd` lists the rest of its flags, including `-l` to lock.

## Try it

1. Type `su -`, enter anything at `Password:`, and read `Authentication failure`. Nothing is wrong.
2. Type `sudo -i` and your own password. Confirm with `whoami` that you are root and that the prompt ends in `#`. Type `exit`.
3. Type `sudo journalctl -n 3 _COMM=sudo` and find the line that records the `sudo -i` you just ran.
4. Type `sudo -l` and read what the policy allows for members of `wheel`.
5. Inside your Distrobox, where `tester` exists, type `sudo -u tester -i`, then `whoami`, then `exit`.
6. Type `passwd`, change your own password, then change it back the same way.
7. Type `passwd tester` without `sudo`, read `Only root can specify a user name`, and understand why.

## Remember

- `su` asks for the other account's password; `sudo` asks for yours, checks `wheel`, and logs the command.
- Root is locked on Pridwen, so `sudo -i` is the root shell and `sudo command` is the everyday form.
- Never set a root password; if one exists, `sudo passwd -l root` locks it again.
