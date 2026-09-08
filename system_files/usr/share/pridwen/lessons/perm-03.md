# Changing permissions and ownership

Two commands change what the mode describes. `chmod` (change mode) sets the permission bits, and `chown` (change owner) sets which user and group a file belongs to. There is a rule about who may run each one. The owner of a file may change its mode, because the bits are the owner's decision. Giving a file to a different user is reserved for root, because if anyone could hand files to anyone else, disk quotas and several security checks would stop meaning anything. You may, however, move a file into a group you belong to with `chgrp`.

You will use `chmod` the first time you write a script and it refuses to run, and `chown` the first time a service cannot read a file you copied in as root. On a real job the temptation is to reach for `chmod 777`, which makes everything work and makes every account on the machine able to rewrite the file. This lesson shows the narrower moves that give exactly the access you mean, which is the habit every security baseline, including Pridwen's, is built on.

## Words you'll meet

- **symbolic mode**: a `chmod` argument written with letters, such as `u+x` or `go-w`.
- **numeric mode**: a `chmod` argument written as an octal number, such as `644`.
- **u**, **g**, **o**, **a**: user (the owner), group, other, and all, in symbolic modes.
- **execute bit**: the `x` permission; on a file it means "may run", on a directory "may enter".
- **shebang**: the first line of a script, `#!/bin/bash`, naming the program that should run it.
- **supplementary group**: a group you belong to in addition to your primary one; `id` lists them.
- **recursive**: applying a change to a directory and everything inside it; `-R` on `chmod` and `chown`.

## How it works

Take the script from the earlier lesson. It is `644`, so running it fails. Symbolic `chmod` names who (`u` for the owner), an operation (`+` adds, `-` removes, `=` sets exactly), and which bits.

```
{user}@{host}:~/pridwen$ ./hello.sh
bash: ./hello.sh: Permission denied
{user}@{host}:~/pridwen$ chmod u+x hello.sh
{user}@{host}:~/pridwen$ ls -l hello.sh
-rwxr--r--. 1 {user} {user} 24 Sep  7 09:40 hello.sh
{user}@{host}:~/pridwen$ ./hello.sh
shield
```

The `./` in front of the name tells the shell to run the file in the current directory rather than search the PATH. After `chmod u+x` the owner triplet went from `rw-` to `rwx`, and the script ran, printing `shield`. Plain `chmod +x` (no letter) adds `x` for user, group and other, which is the common form for a script others may run: `-rwxr-xr-x`, or `755`.

Numeric `chmod` sets all nine bits at once and is the clearest way to state a whole policy. `644` is readable data, `600` is private data, `755` is a program anyone may run, `750` a program only your group may run.

```
{user}@{host}:~/pridwen$ chmod 600 notes.txt
{user}@{host}:~/pridwen$ ls -l notes.txt
-rw-------. 1 {user} {user} 27 Sep  7 09:35 notes.txt
{user}@{host}:~/pridwen$ chmod 640 notes.txt
{user}@{host}:~/pridwen$ stat -c '%A %a' notes.txt
-rw-r----- 640
```

`600` closed the file to everyone but you; `640` reopened it for reading by the group. `stat -c '%A %a'` prints letters and number side by side so you can check your arithmetic: read 4 plus write 2 is 6, read alone is 4, nothing is 0.

`chown` takes `user:group` and the file. Without `sudo`, changing the owner fails even on your own file, because the kernel keeps that power for root.

```
{user}@{host}:~/pridwen$ chown root:root hello.sh
chown: changing ownership of 'hello.sh': Operation not permitted
{user}@{host}:~/pridwen$ sudo chown root:root hello.sh
{user}@{host}:~/pridwen$ ls -l hello.sh
-rwxr--r--. 1 root root 24 Sep  7 09:40 hello.sh
{user}@{host}:~/pridwen$ sudo chown {user}:{user} hello.sh
```

The refusal says `Operation not permitted`, which is the kernel's wording for "this needs root", as opposed to `Permission denied`, which is about mode bits. With `sudo` the owner and group both became `root`, and the last line gives the file back so you can keep using it.

Changing only the group is different: `chgrp` (change group) lets you move a file into any group you are a member of, no root needed. That is how a team shares files. Put the people in a group, give the directory to that group, and open the group write bit.

```
{user}@{host}:~/pridwen$ chgrp wheel notes.txt
{user}@{host}:~/pridwen$ chmod g+w notes.txt
{user}@{host}:~/pridwen$ ls -l notes.txt
-rw-rw----. 1 {user} wheel 27 Sep  7 09:35 notes.txt
```

Now every member of `wheel` may read and write the file, and nobody else may see it. That is exactly the access you meant, and no more.

Resist `chmod 777`. It lets every account on the machine, including any compromised service, write and run the file; it fixes the symptom and opens a hole. The real fix is almost always ownership, group membership, or a narrower mode, and the Coach will say so if it sees a `777`.

## When it goes wrong

`bash: ./hello.sh: Permission denied` after you wrote a script. No `x` bit. `chmod u+x hello.sh` adds it for you alone; `chmod +x` adds it for everyone. Alternatively `bash hello.sh` runs it through the interpreter without changing the mode.

`chown: changing ownership of 'hello.sh': Operation not permitted`. Only root may give a file to another user. `sudo chown user:group file` does it; if you only wanted a group change, `chgrp group file` works as yourself for any group `id` lists.

`chmod: changing permissions of '/etc/hosts': Operation not permitted`. Only a file's owner or root may change its mode, and `/etc/hosts` belongs to root. `sudo chmod` if you really mean to change a system file; usually you do not, and `pridwen why` will suggest working on a copy.

## Try it

1. Type `cd ~/pridwen` and `./hello.sh`. Read the refusal, then `chmod u+x hello.sh` and run it again. Expect `shield`.
2. Type `ls -l hello.sh` and confirm the owner triplet now reads `rwx`.
3. Type `chmod 600 notes.txt`, then `chmod 640 notes.txt`, checking each with `stat -c '%A %a' notes.txt`.
4. Type `chown root:root hello.sh` without sudo and read `Operation not permitted`. Then do it with `sudo`, look with `ls -l`, and give it back with `sudo chown {user}:{user} hello.sh`.
5. Type `id` to see your groups, then `chgrp wheel notes.txt` and `chmod g+w notes.txt`. `ls -l notes.txt` should show `-rw-rw----` and group `wheel`.
6. Type `chmod 644 notes.txt` and `chgrp {user} notes.txt` to put things back the way they were.

## Remember

- `chmod u+x file` adds one bit; `chmod 644 file` sets all nine; `stat -c '%A %a'` shows both spellings.
- Only root may `chown` a file to another user; you may `chgrp` to any group you belong to.
- Never `chmod 777`: state the exact access you mean with a narrower mode, the right owner, or a group.
