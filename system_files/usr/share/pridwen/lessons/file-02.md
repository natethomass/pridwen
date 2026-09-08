# Copy, move, and remove

Three commands do most of the work of shaping a directory. `cp` copies a file or directory to a new place, `mv` moves it or renames it, and `rm` removes it. They are fast and quiet: a successful `cp` or `rm` prints nothing at all, because on Linux silence means success. That quietness is also why a moment of care pays off. The command line has no recycle bin. When `rm` finishes, the file is gone, and no menu brings it back.

On a real job these three commands are how you back up a configuration file before editing it, rotate a log out of the way, tidy an install, or clean up after a test. On Pridwen the system image under `/usr` is read-only, so a slip there is refused rather than carried out, but your home, `/etc` and `/var` are ordinary writable directories and deserve the habits in this lesson.

## Words you'll meet

- **source**: the file or directory a command starts from; always named first.
- **destination**: where it ends up; always named last.
- **recursive**: acting on a directory and everything inside it, all the way down; the `-r` flag.
- **rename**: moving a file to a new name in the same directory; `mv` does both.
- **interactive**: asking before each action; the `-i` flag.
- **glob**: a pattern like `*.bak` that the shell turns into a list of matching names before the command runs.
- **timestamp**: the recorded date and time a file was last changed.

## How it works

Start in the practice directory from the previous lesson, or make it. `cp source destination` copies one file. Give the copy a different name and it lands beside the original.

```
{user}@{host}:~$ cd pridwen
{user}@{host}:~/pridwen$ cp notes.txt notes.bak
{user}@{host}:~/pridwen$ ls -l
total 0
-rw-r--r--. 1 {user} {user} 0 Sep  7 09:14 notes.txt
-rw-r--r--. 1 {user} {user} 0 Sep  7 09:31 notes.bak
```

Two lines now, same size, and the copy carries the time of the copy, not of the original. `cp -a` (archive) keeps the original's timestamp and permissions, which matters when you back up configuration. A directory needs `cp -r` (recursive), because a directory is a list of other things and `cp` wants you to say that you mean all of them.

```
{user}@{host}:~/pridwen$ cp -r practice practice-copy
{user}@{host}:~/pridwen$ ls practice-copy/one
two
```

`mv` moves. If the destination is a directory that exists, the file goes inside it. If the destination is a new name, the file is renamed, because renaming is just moving within the same directory. Make an `archive` directory first; `mv` will not create one for you.

```
{user}@{host}:~/pridwen$ mkdir archive
{user}@{host}:~/pridwen$ mv notes.bak archive/
{user}@{host}:~/pridwen$ ls archive
notes.bak
{user}@{host}:~/pridwen$ mv archive/notes.bak archive/notes-old.txt
{user}@{host}:~/pridwen$ ls archive
notes-old.txt
```

The trailing slash on `archive/` is a habit worth keeping: it tells `mv` (and you) that the destination is meant to be a directory, and if it does not exist the command fails instead of silently renaming the file to `archive`.

`rm` removes files. `rm -i` (interactive) asks before each one and is the right form while you are learning. Answer `y` to remove or `n` to keep.

```
{user}@{host}:~/pridwen$ rm -i archive/notes-old.txt
rm: remove regular file 'archive/notes-old.txt'? y
{user}@{host}:~/pridwen$ ls archive
```

The empty output means the directory is now empty. Removing a directory needs `rm -r`, and `rmdir` removes one only if it is already empty, which makes `rmdir` a safe check.

```
{user}@{host}:~/pridwen$ rmdir archive
{user}@{host}:~/pridwen$ rm -r practice-copy
{user}@{host}:~/pridwen$ ls
notes.txt  practice
```

Patterns deserve a preview. `ls *.bak` shows exactly what the shell will expand `*.bak` into; if that list is what you expect, then `rm *.bak` removes exactly those files and nothing else. The classic mistake is a stray space: `rm -rf / home` names two things, `/` and `home`, instead of the one directory `/home`. GNU `rm` refuses `/` on its own, but the same slip inside your home would not be refused.

## When it goes wrong

`cp: -r not specified; omitting directory 'practice'`. You asked `cp` to copy a directory without `-r`, so it skipped it and copied nothing. Add the flag: `cp -r practice practice-copy`.

`mv: cannot move 'notes.bak' to 'archive/': Not a directory` or `mv: target 'archive/' is not a directory`. The destination directory does not exist. `mkdir -p archive` first, then run the move again. `pridwen why` prints both steps.

`rm: cannot remove 'practice': Is a directory`. `rm` needs `-r` to remove a directory and its contents. Check what is inside with `ls -A practice` first, then `rm -ri practice` to be asked about each file, or `rmdir practice` if it should already be empty.

## Try it

1. Type `cd ~/pridwen` and `cp notes.txt notes.bak`. Then `ls -l` and compare the two timestamps.
2. Type `mkdir archive` and `mv notes.bak archive/`. Confirm with `ls archive`.
3. Rename it with `mv archive/notes.bak archive/notes-old.txt` and check with `ls archive`.
4. Type `ls *.txt` to preview a pattern, then `touch a.bak b.bak`, `ls *.bak`, and finally `rm -i *.bak`, answering `y` twice.
5. Type `cp -r practice practice-copy` and `ls -R practice-copy` to confirm the whole tree came along.
6. Type `rm practice-copy`, read the `Is a directory` message, then `rm -r practice-copy`.
7. Type `rm -i archive/notes-old.txt`, answer `y`, then `rmdir archive`. `ls` should show `notes.txt` and `practice` only.

## Remember

- `cp` copies, `mv` moves or renames, `rm` removes, and none of them can be undone.
- A directory needs `-r` for `cp` and `rm`; `mv` never creates the destination directory for you.
- Preview any pattern with `ls` before giving it to `rm`, and use `rm -i` while learning.
