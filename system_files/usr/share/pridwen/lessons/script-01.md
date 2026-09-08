# From command to script

A script is a text file holding commands, one per line, that the shell runs in order exactly as if you had typed them. The moment a command line works, saving it as a script means you never retype it, never mistype it, and can hand it to someone else. Almost every automated job on a real server, from backups to deployments, starts life as a script somebody wrote after getting a command right once.

On Pridwen you write scripts in your home directory, which persists across upgrades, and later run them from systemd timers. Three things make a file runnable: a first line that names the interpreter, a permission bit that says "this may be executed", and a path that tells the shell where the file is. This lesson covers all three and the two errors that stop most first scripts.

## Words you'll meet

- **script**: a text file of shell commands run in order.
- **interpreter**: the program that reads a script and carries out its lines; for these scripts it is `bash`.
- **shebang**: the first line of a script, `#!` followed by the interpreter's path, which tells the kernel what to run the file with.
- **execute bit**: the permission flag, shown as `x` in `ls -l`, that allows a file to be run as a program.
- **PATH**: the list of directories the shell searches when you type a bare command name.
- **exit status**: the number a command hands back when it finishes; `0` means success, anything else is a kind of failure.
- **heredoc**: a way to feed several lines of text to a command, written between `<<'EOF'` and a closing `EOF`.

## How it works

Write the file first. A heredoc lets you create it in one go from the prompt: everything between `<<'EOF'` and the line `EOF` goes into the file, and the quotes around `EOF` stop the shell expanding anything inside.

```
{user}@{host}:~$ cat > hello.sh <<'EOF'
#!/usr/bin/bash
echo "Hello from $(hostname)"
EOF
{user}@{host}:~$ cat hello.sh
#!/usr/bin/bash
echo "Hello from $(hostname)"
```

The first line is the shebang. `#!/usr/bin/bash` tells the kernel: when someone executes this file, start `/usr/bin/bash` and hand it the file. The second line is an ordinary command; `$(hostname)` runs `hostname` and drops its output into the string. `cat hello.sh` shows the file back so you can check both lines arrived.

Now the permission. `ls -l` (`-l` is long format: one file per line with permissions, owner, size and date) shows the file cannot be executed yet.

```
{user}@{host}:~$ ls -l hello.sh
-rw-r--r--. 1 {user} {user} 47 Sep  7 09:20 hello.sh
{user}@{host}:~$ chmod +x hello.sh
{user}@{host}:~$ ls -l hello.sh
-rwxr-xr-x. 1 {user} {user} 47 Sep  7 09:20 hello.sh
```

The first column is the permissions. Before `chmod`, it reads `rw-r--r--`: you can read and write, everyone else can read, nobody can execute. `chmod +x` adds the execute bit for everyone, and the column becomes `rwxr-xr-x`. The dot after the permissions means the file carries an SELinux label, which is normal on Pridwen.

Finally the path. When you type a bare name like `ls`, the shell looks through the directories in PATH and runs the first match. The current directory is not on PATH on Fedora, on purpose: if it were, a file named `ls` that someone left in a shared directory would run instead of the real one the moment you listed that directory. So a local script is run with an explicit path, `./hello.sh`, where `.` means "the directory I am in".

```
{user}@{host}:~$ ./hello.sh
Hello from {host}
{user}@{host}:~$ echo $?
0
```

`$?` holds the exit status of the last command, and `0` means the script finished without error. That number is what a timer or another script will look at later to know whether your script worked.

Scripts you want everywhere belong in `{home}/.local/bin`, which is already on your PATH on Pridwen. Once a script is there, you run it by name from any directory.

```
{user}@{host}:~$ mv hello.sh {home}/.local/bin/hello
{user}@{host}:~$ cd /tmp
{user}@{host}:/tmp$ hello
Hello from {host}
```

The `.sh` ending is dropped on purpose: a command on PATH is used by name, and its callers should not care what language it is written in.

## When it goes wrong

`bash: ./hello.sh: Permission denied`, with exit status 126, means the file was found but the execute bit is not set. `chmod +x hello.sh` fixes it for good; `bash hello.sh` runs it once without the bit, because then bash reads the file as input rather than the kernel executing it.

`bash: hello.sh: command not found`, exit status 127, with the file sitting right there, means you left off the `./`. The shell searched PATH, not the current directory. Run `./hello.sh`.

`bash: ./hello.sh: /usr/bin/bash^M: bad interpreter: No such file or directory` means the file was edited on Windows and each line ends in a carriage return (shown as `^M`). The kernel looked for an interpreter called `bash^M` and there is none. `sed -i 's/\r$//' hello.sh` strips them (`-i` edits the file in place; `s/\r$//` replaces a carriage return at the end of each line with nothing). After any of these, `pridwen why` explains the exact failure, and `pridwen explain chmod` walks through the permission flags.

## Try it

1. Create `hello.sh` with the heredoc above and run `cat hello.sh` to confirm both lines.
2. Run `./hello.sh` before setting the bit and expect `Permission denied`. Run `echo $?` and expect `126`.
3. Run `chmod +x hello.sh`, then `./hello.sh`, and expect `Hello from {host}`.
4. Run `hello.sh` without the `./` and expect `command not found` and exit status `127`.
5. Run `chmod -x hello.sh` (`-x` removes the bit) and `ls -l hello.sh` to see the `x` letters disappear, then put the bit back.
6. Move the script to `{home}/.local/bin/hello`, `cd /tmp`, run `hello`, and expect the same greeting.

## Remember

- A script needs a shebang line, the execute bit from `chmod +x`, and a path such as `./name` or a home in `~/.local/bin`.
- Exit 126 means found but not executable; exit 127 means not found, usually a missing `./`.
- The current directory is off PATH on purpose, so a stray file cannot shadow a real command.
