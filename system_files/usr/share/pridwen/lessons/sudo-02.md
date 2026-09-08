# Using sudo well

sudo has sharp edges, and they all come from one simple fact: your shell
prepares the command line before sudo runs anything. The shell is the program
reading what you type, bash on Pridwen. It handles redirections like `>`,
pipes like `|`, aliases, and builtins such as `cd` itself, as you, and only
then hands the remaining words to sudo. sudo elevates the program it is
given, and nothing else.

Knowing where the shell stops and sudo starts saves real time, because the
failures look mysterious: a command with `sudo` in front still says
`Permission denied`. It also keeps you safer. The habits in this lesson,
`tee` for writing, `sudo -e` for editing, `visudo` for the rules file, are
the ones that keep a root mistake small on a machine you are paid to look
after.

## Words you'll meet

- **shell**: the program that reads your command line, bash here; it sets up redirections and pipes before running anything.
- **redirection**: `>` sends a command's output into a file, replacing it; `>>` appends.
- **pipe**: `|` sends one command's output into the next command's input.
- **builtin**: a command the shell does itself with no separate program, such as `cd`, `export`, and `alias`.
- **tee**: a program that copies its input to a file and to the screen; with `sudo` it becomes a way to write a file as root.
- **sudoedit**: what `sudo -e` runs; it edits a copy of a file as you and installs the result as root.
- **visudo**: the editor wrapper for `/etc/sudoers` that checks the syntax before saving.

## How it works

The classic trap is writing a system file with a redirection.

```
{user}@{host}:~$ sudo echo 'Welcome to {host}' > /etc/motd
bash: /etc/motd: Permission denied
```

Notice who complained: `bash`, not `sudo`. The shell opened `/etc/motd`
for writing, as you, before sudo ever ran, and you may not write there. `echo`
would have run as root, but its output had nowhere to go. The fix is to
elevate the part that writes. `tee` reads its input and writes it to the
file named, so put `sudo` in front of `tee`. The `-a` flag appends instead
of replacing.

```
{user}@{host}:~$ echo 'Welcome to {host}' | sudo tee /etc/motd
Welcome to {host}
{user}@{host}:~$ echo 'net.ipv4.ip_forward = 0' | sudo tee -a /etc/sysctl.d/99-local.conf
net.ipv4.ip_forward = 0
```

`tee` echoes what it wrote, which is why the line appears on screen; that is
normal. The pipe carried the text from `echo`, run as you, into `tee`, run as
root. The second example appends a kernel setting to a file under
`/etc/sysctl.d/`, the directory sysctl reads at boot. On Pridwen `/etc` is
merged three ways at each `bootc upgrade`, so a file you add there survives
updates.

Builtins are the second edge. `cd` changes the shell's own current
directory, so there is no program called `cd` for sudo to run, and even if
there were, it would change a child process's directory, not your shell's.

```
{user}@{host}:~$ sudo cd /root
sudo: cd: command not found
```

For a quick look, run a real program: `sudo ls /root`. For more than a look,
`sudo -i` opens a login shell as root, where `cd` works because the shell
itself is root; type `exit` to leave. `sudo su` also gets there, but it takes
a detour through `su` and makes two log entries where `sudo -i` makes one.

Editing is the third. `sudo vim /etc/hosts` runs a whole editor, with its
plugins and your saved settings, as root. `sudo -e` is safer: it copies the
file to a temporary location, opens your editor as your normal user, and
when you save, installs the result back as root.

```
{user}@{host}:~$ sudo -e /etc/hosts
```

It uses the editor named in your `EDITOR` or `SUDO_EDITOR` variable, `nano`
if none is set. Nothing is printed on success; the file simply changes.

The rules file gets its own tool. A syntax error in `/etc/sudoers` locks
everyone out of sudo, on a system where root has no password, which means
no one can fix it without booting into rescue mode. `visudo` opens the file
in your editor and refuses to save a broken one. The `-c` flag checks
without editing.

```
{user}@{host}:~$ sudo visudo -c
/etc/sudoers: parsed OK
/etc/sudoers.d/pridwen: parsed OK
```

Each file is named with `parsed OK`. Rules for one purpose belong in a small
file under `/etc/sudoers.d/`, edited with `sudo visudo -f /etc/sudoers.d/name`,
so the main file stays untouched. Avoid `NOPASSWD` in any rule: it means
anyone who gets a shell as that user is root without a prompt, which defeats
the reason the password is asked for.

## When it goes wrong

`bash: /etc/motd: Permission denied` after a `sudo ... >` command is the
redirection trap. Rewrite as `... | sudo tee /etc/motd`, or `sudo tee -a` to
append. The Coach recognises this shape and prints the fix under it;
`pridwen why` shows the `tee` and `sudo sh -c` alternatives side by side.

`sudo: cd: command not found` is the builtin trap. Use `sudo ls` for a look
or `sudo -i` for a root shell.

`>>> /etc/sudoers: syntax error near line 12 <<<` comes from `visudo`
when you try to save a broken file. It then asks `What now?`; type `e` to go
back and edit, never `Q`, which quits and leaves the broken file in place.
`pridwen explain sudo` annotates `-e`, `-i`, and `-k`, and `pridwen explain
tee` covers `-a`.

## Try it

1. Type `sudo echo test > /tmp/sudo-test.txt` and notice it works, because `/tmp` is writable by you; the shell did the write, not sudo.
2. Type `sudo echo test > /etc/pridwen-test` and read the `Permission denied` from bash.
3. Type `echo test | sudo tee /etc/pridwen-test` and see the line echoed back, then `sudo rm /etc/pridwen-test` to clean up.
4. Type `sudo cd /root` and read the error, then `sudo ls /root` to see the directory instead.
5. Type `sudo -e /etc/motd`, add one line, save, and type `cat /etc/motd` to confirm the change landed.
6. Type `sudo visudo -c` and read the `parsed OK` lines.

## Remember

- The shell does `>` and `|` as you before sudo runs; write system files with `... | sudo tee file` or `sudo tee -a`.
- Builtins like `cd` have no program to elevate; use `sudo -i` for a root shell and `exit` to leave it.
- Edit with `sudo -e`, never `sudo vim`; edit sudoers only with `sudo visudo`, which checks the syntax first.
