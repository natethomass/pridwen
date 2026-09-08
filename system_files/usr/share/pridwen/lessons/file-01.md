# Listing and moving around

Every file on a Linux system lives in one tree of directories that starts at `/`, which is called the root of the filesystem. There is no C: drive or D: drive; other disks and USB sticks are attached somewhere inside the same tree. Your home directory, `{home}`, is one branch of it. Configuration lives under `/etc`, programs under `/usr`, logs under `/var/log`, and so on. You move through the tree with `cd` and look at it with `ls`, which you met in the Terminal node. This lesson goes deeper into `ls`, because its long listing packs almost everything you will later need to know about a file into one line.

On a real job you read long listings dozens of times a day: to see who owns a file, whether it was changed today, how big a log has grown, whether a name is a directory or a link. On Pridwen the tree has one twist worth knowing from the start: `/usr` comes from a read-only image, so it looks like every other directory but will not let anything change it. A later lesson explains why; for now, just notice that `ls` works exactly the same there.

## Words you'll meet

- **root**: the top directory of the tree, written `/`; not the same as the root user.
- **long listing**: the `ls -l` view, one line per file with its details.
- **mode**: the first column of a long listing; the file type plus who may read, write, and run it.
- **link count**: how many names point at the file; 1 for an ordinary file, and on Pridwen's btrfs filesystem 1 for directories too.
- **owner** and **group**: the user account that owns the file and the group account it is shared with.
- **dot file**: a name starting with `.`; hidden from plain `ls` because it is usually configuration.
- **parent directory**: the directory that contains another one; `Documents` is the parent of `Documents/work`.
- **flag**: a word beginning with `-` that changes how a command behaves; short flags stack, so `-l -a` is `-la`.

## How it works

`ls -l` (`-l` for long format) shows one file per line. Make a small directory first so you have something predictable to look at. `mkdir` (make directory) creates one, and `touch` creates an empty file or updates the time on an existing one.

```
{user}@{host}:~$ mkdir pridwen
{user}@{host}:~$ touch pridwen/notes.txt
{user}@{host}:~$ ls -l pridwen
total 0
-rw-r--r--. 1 {user} {user} 0 Sep  7 09:14 notes.txt
```

Read the file line left to right. `-rw-r--r--.` is the mode: the very first character is the type, where `-` means a regular file and `d` means a directory, and the next nine characters say who may read, write and run it (the Permissions node decodes those). The trailing dot means the file carries an SELinux label, which every file on Pridwen does. `1` is the link count. The first `{user}` is the owner and the second is the group; on Fedora each user gets a private group with the same name. `0` is the size in bytes. `Sep  7 09:14` is when the contents last changed. `notes.txt` is the name. The `total 0` line above is the disk space used by everything listed, in blocks, and is safe to ignore.

Now look at your home, where there are directories.

```
{user}@{host}:~$ ls -l
total 0
drwxr-xr-x. 1 {user} {user}  0 Sep  7 08:50 Desktop
drwxr-xr-x. 1 {user} {user}  0 Sep  7 08:50 Documents
drwxr-xr-x. 1 {user} {user} 18 Sep  7 09:14 pridwen
```

The leading `d` marks each one as a directory. The size of a directory is the size of its list of names, not of the files inside it, which is why it is small.

Flags stack. `-a` (all) includes dot files, `-h` (human-readable) prints sizes as K, M and G instead of raw bytes, `-t` sorts by modification time with the newest first, and `-R` (recursive) descends into every subdirectory. `ls -lah` is the combination most admins type without thinking.

```
{user}@{host}:~$ ls -lah pridwen
total 0
drwxr-xr-x. 1 {user} {user}  18 Sep  7 09:14 .
drwx------. 1 {user} {user} 210 Sep  7 09:14 ..
-rw-r--r--. 1 {user} {user}   0 Sep  7 09:14 notes.txt
```

With `-a` the two special entries appear: `.` is this directory and `..` is its parent, your home. Notice the parent's mode begins `drwx------`, which is the private mode Fedora gives every home directory.

Making a chain of directories at once is `mkdir -p` (`-p` for parents). It creates every missing level and treats "already exists" as success rather than an error, which is what scripts want.

```
{user}@{host}:~$ mkdir -p pridwen/practice/one/two
{user}@{host}:~$ ls -R pridwen/practice
pridwen/practice:
one

pridwen/practice/one:
two

pridwen/practice/one/two:
```

`ls -R` prints each directory's path followed by a colon, then its contents, walking down the tree. The last one is empty.

## When it goes wrong

`mkdir: cannot create directory 'pridwen/practice': File exists`. You asked for a directory that is already there. Nothing was changed. If you are not sure whether it exists, use `mkdir -p`, which is quiet in that case.

`mkdir: cannot create directory 'notes/a/b': No such file or directory`. A parent in the chain is missing; plain `mkdir` only creates the last name. `mkdir -p notes/a/b` creates all three.

`ls: cannot access 'Docments': No such file or directory`. A typo, or you are in a different directory than you think. `pwd` says where you are, `ls` shows the real names, and Tab completion avoids the retype. `pridwen explain ls` lists every flag used here if one is unclear.

## Try it

1. Type `mkdir pridwen` (if it says the directory exists, that is fine) and `touch pridwen/notes.txt`.
2. Type `ls -l pridwen` and name each column of the `notes.txt` line: mode, link count, owner, group, size, date, name.
3. Type `ls -l` in your home and find the `d` at the start of each directory line.
4. Type `ls -la` and find `.`, `..` and at least one dot file such as `.bashrc`.
5. Type `mkdir -p pridwen/practice/one/two`, then `ls -R pridwen/practice`, and read the tree top to bottom.
6. Type `mkdir pridwen/practice` again without `-p`, read the `File exists` message, then repeat it with `-p` and notice the silence.
7. Type `ls -lt` in your home and confirm the newest entry, `pridwen`, is at the top.

## Remember

- A long listing reads left to right as mode, link count, owner, group, size, modification time, name.
- The first character of the mode is the type: `-` for a file, `d` for a directory.
- `ls -lah` shows everything with readable sizes, and `mkdir -p` builds a whole chain of directories in one go.
