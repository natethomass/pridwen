# What sudo does

`sudo` runs one command as another user, by default root, the administrator
account that may do anything on the machine. Before it does, it checks that
you are allowed and asks for your own password, not root's. That last part is
the whole point. There is no shared root password to leak or forget, and
every use is tied to a named person who typed their own password.

On Pridwen the root account has no password at all, so nobody can log in as
root directly, at the greeter or over the network. The only way to root goes
through `sudo`, and `sudo` writes a line to the log every time. On a job this
is the rule on every serious system: the question "who changed this" has to
have an answer, and a shared root login cannot give one.

## Words you'll meet

- **root**: the administrator account, user ID 0, which the kernel lets do anything.
- **sudo**: the program that runs a command as another user after checking you are allowed.
- **wheel**: the group whose members may use `sudo` on Pridwen; the welcome wizard put your account in it.
- **sudoers**: the file `/etc/sudoers`, and the directory `/etc/sudoers.d/`, that say who may run what.
- **credential cache**: sudo's memory of your password, per terminal, for five minutes, so a run of commands prompts once.
- **exit status**: the number a command finishes with; `0` is success and anything else is failure.
- **journal**: systemd's log, where sudo records every attempt.

## How it works

First, confirm you are in the group. `id` prints your user and every group
you belong to.

```
{user}@{host}:~$ id
uid=1000({user}) gid=1000({user}) groups=1000({user}),10(wheel) context=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
```

`uid` is your user ID, `gid` your primary group, and `groups` lists all of
them; `10(wheel)` is the one that matters here. The `context=` part is your
SELinux label, which a later node covers. Now ask sudo what it allows. The
`-l` flag means list.

```
{user}@{host}:~$ sudo -l
[sudo] password for {user}:
Matching Defaults entries for {user} on {host}:
    !visiblepw, always_set_home, match_group_by_gid, always_query_group_plugin, env_reset, ...

User {user} may run the following commands on {host}:
    (ALL) ALL
```

The prompt asked for your password, which proves the point that it is yours,
not root's. The `Defaults` lines are sudo's settings, and `(ALL) ALL` is the
permission itself: you may run any command as any user. It comes from one
line in `/etc/sudoers`, `%wheel ALL=(ALL) ALL`, where `%wheel` means the
group, the first `ALL` is any host, `(ALL)` is any target user, and the last
`ALL` is any command.

Run something harmless as root and watch the log.

```
{user}@{host}:~$ sudo systemctl restart chronyd
{user}@{host}:~$ journalctl _COMM=sudo -n 1
Sep 07 09:14:02 {host} sudo[4312]:    {user} : TTY=pts/0 ; PWD={home} ; USER=root ; COMMAND=/usr/bin/systemctl restart chronyd
```

The second command did not prompt, because your password was cached from
`sudo -l` a moment earlier. `journalctl _COMM=sudo` selects lines written by
the program named `sudo`, and `-n 1` shows the newest one. Read the fields:
who ran it, `TTY=pts/0` is the terminal, `PWD=` the directory they were in,
`USER=root` who it ran as, and `COMMAND=` the full path of what ran. That one
line is the reason Pridwen uses `sudo` instead of a root login. Members of
`wheel` can read the journal, so you can read your own trail.

The cache is per terminal and expires after five minutes. `sudo -k`, where
`-k` means kill the cached credentials, clears it now, so the next `sudo`
prompts again. Do that before walking away from a terminal.

```
{user}@{host}:~$ sudo -k
{user}@{host}:~$ sudo true
[sudo] password for {user}:
```

`true` is a command that does nothing and succeeds, which makes it a safe
way to test whether sudo will prompt. When you need a whole root shell rather
than one command, `sudo -i` gives a login shell as root, with root's own
environment, and the journal records that you opened it.

## When it goes wrong

`Sorry, try again.` means the password did not match. After three tries sudo
prints `sudo: 3 incorrect password attempts` and exits with status 1, and
the journal records the failed attempts as well. Type it again slowly; the
password is your own login password.

`{user} is not in the sudoers file.` means your account is not in `wheel`
and no rule names it. This is the case for a second, non-administrator user
created by an admin. `id` shows your groups; an administrator can add you
with `sudo usermod -aG wheel name`, where `-aG` appends a group, and the
change applies at your next login.

`sudo` exiting 1 after the command ran is usually the command's own failure
passed back through: `sudo systemctl restart nosuch.service` exits with the
status `systemctl` gave. Read the command's error text, not sudo's. The Coach
prints this split under any `sudo` that exits 1, and `pridwen why` shows
`id`, `sudo -l`, and the journal line to check. `pridwen explain sudo`
annotates `-l`, `-k`, and `-i`.

## Try it

1. Type `id` and confirm `wheel` appears in the `groups=` list.
2. Type `sudo -l`, enter your password, and read the `(ALL) ALL` line that grants your permission.
3. Type `sudo true` and notice it does not prompt, because the password is cached.
4. Type `journalctl _COMM=sudo -n 3` and read the newest line: find the `TTY=`, `PWD=`, `USER=`, and `COMMAND=` fields.
5. Type `sudo -k`, then `sudo true` again, and notice it prompts this time.
6. Type `grep wheel /etc/sudoers` with `sudo` in front, and find the `%wheel ALL=(ALL) ALL` line.

## Remember

- `sudo` runs one command as root after checking you are in `wheel` and asking for your own password; root itself has no password.
- `sudo -l` shows what you may run; the grant is `%wheel ALL=(ALL) ALL` in `/etc/sudoers`.
- Every use lands in the journal with user, terminal, directory, target, and command; `sudo -k` clears the five-minute cache.
