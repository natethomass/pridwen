# Reading the mode

Every file and directory on a Linux system carries a small record called its mode. The mode answers one question three times over: may this account read the file, may it write the file, and may it execute (run) the file. The question is asked once for the file's owner, once for the file's group, and once for everyone else. Those nine yes-or-no answers, plus a letter for the file's type, are the ten characters at the start of every `ls -l` line, and the same nine answers can be written as a three-digit number such as `644` or `750`.

Learning to read the mode is the root of everything in security. When a service cannot read its configuration, when a script will not run, when a private key is refused by `ssh` because it is "too open", the answer is in those ten characters. On Pridwen, where SELinux and a read-only image add further layers, the mode is still the first thing the kernel checks and the first thing you should look at.

## Words you'll meet

- **mode**: the type letter plus nine permission bits on every file; also called the permissions.
- **bit**: a single on-or-off switch; each of the nine permissions is one bit.
- **owner**: the one user account that owns the file, shown in the third column of `ls -l`.
- **group**: the one group account the file is shared with, shown in the fourth column.
- **other**: everyone who is neither the owner nor in the group.
- **read**, **write**, **execute**: the three permissions, written `r`, `w`, `x`.
- **octal**: a way of writing numbers in base 8, so each digit runs from 0 to 7 and holds exactly three bits.
- **umask**: the setting that decides which bits a new file starts without; `022` on Pridwen.

## How it works

Make a small script to look at. `printf` writes two lines into it: `#!/bin/bash`, which says "run me with bash", and a line that prints a word. Then read its mode two ways.

```
{user}@{host}:~$ printf '#!/bin/bash\necho shield\n' > pridwen/hello.sh
{user}@{host}:~$ ls -l pridwen/hello.sh
-rw-r--r--. 1 {user} {user} 24 Sep  7 09:40 pridwen/hello.sh
{user}@{host}:~$ stat -c '%A %a %U:%G' pridwen/hello.sh
-rw-r--r-- 644 {user}:{user}
```

Take the first column of the `ls -l` line, `-rw-r--r--.`, apart. The first character is the type: `-` is a regular file, `d` a directory, `l` a symbolic link (a name that points at another path). Then come three groups of three characters. `rw-` is for the owner: read on, write on, execute off. `r--` is for the group: read only. The final `r--` is for other: read only. A letter means the bit is on and a dash means it is off. The trailing `.` means the file has an SELinux label, which every file on Pridwen does. `stat` is a tool that prints a file's details; `-c` gives it a format, where `%A` is the mode as letters, `%a` as a number, and `%U:%G` the owner and group names.

The number is the same nine bits written in octal. Each group of three bits becomes one digit: read counts 4, write counts 2, execute counts 1, and you add up whichever are on. So `rw-` is 4 plus 2, which is `6`; `r--` is `4`; `rwx` is `7`; `r-x` is `5`; `---` is `0`. Reading `-rw-r--r--` as three digits gives `644`, exactly what `stat` printed. A new file gets `644` because the umask `022` removes the write bit from group and other when the file is created.

A mode like `750` reads back the other way: `7` is `rwx`, `5` is `r-x`, `0` is `---`, so `-rwxr-x---` is a file the owner may read, write and run, the group may read and run, and others may not touch at all.

Directories use the same three letters with different meanings. Read means "may list the names inside". Execute means "may enter, and may reach things inside by name". Write means "may create, rename or delete names inside", which is why deleting a file depends on the directory's write bit, not the file's. `ls -ld` (`-d` for the directory itself rather than its contents) shows a directory's own mode.

```
{user}@{host}:~$ ls -ld pridwen {home}
drwxr-xr-x. 1 {user} {user}  40 Sep  7 09:40 pridwen
drwx------. 1 {user} {user} 210 Sep  7 09:14 {home}
```

`pridwen` is `755`: you may do everything, and everyone else may list and enter it. Your home is `700`: nobody but you may list, enter, or change it. That is the default Fedora gives every home directory, and it is why another user's home is closed to you.

## When it goes wrong

`bash: ./pridwen/hello.sh: Permission denied` with exit code 126. The file is `644`: no `x` bit anywhere, so the kernel refuses to run it even though you own it. The next lesson but one shows `chmod`; the one-line fix is `chmod u+x pridwen/hello.sh`.

`ls: cannot open directory '/root': Permission denied`. `/root` is mode `700` and owned by root, so its read bit is off for you. Nothing is broken. `sudo ls -la /root` looks as root, and the journal records that you did.

`bash: cd: /var/lib/private: Permission denied` even though `ls -ld` shows you the directory's name. Seeing a name needs read on the parent; entering needs execute on the directory itself, and that bit is off for you here. `pridwen why` will point at the exact bit after a failure like this.

## Try it

1. Type `printf '#!/bin/bash\necho shield\n' > ~/pridwen/hello.sh`, then `ls -l ~/pridwen/hello.sh`. Read the ten characters aloud as type, owner, group, other.
2. Type `stat -c '%A %a %U:%G' ~/pridwen/hello.sh`. Match each letter group to a digit: `rw-` is 6, `r--` is 4.
3. Work out the octal number for `-rwxr-x---` before reading on: 7, 5, 0.
4. Type `ls -ld ~/pridwen ~` and explain why one is `755` and the other `700`.
5. Type `~/pridwen/hello.sh` and read the `Permission denied` message; then `echo $?` to confirm it is 126.
6. Type `ls -ld /root` and then `ls /root`. The first works because `/` lets you read names; the second fails because `/root` itself is closed.

## Remember

- The mode is one type character and nine bits: `rwx` for the owner, then the group, then everyone else.
- Read is 4, write is 2, execute is 1; add them per group to get the octal number, so `rw-r--r--` is `644`.
- On a directory, read lists names, execute enters, and write creates or deletes entries.
