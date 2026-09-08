# Timestamps and hashes

Forensics is saying what happened after the fact, with evidence that holds up
when someone else checks it. Two primitives underlie everything else: the
timestamps a filesystem keeps for every file, which tell you when, and hashes,
which prove a file has not changed since you looked. Both are things you read.
Neither is something you alter, and reading them carefully is most of the skill.

On a job these two humble tools are what make a finding defensible: "this file
changed at 09:07 and here is the fingerprint of the copy I examined". On Pridwen
you practise on your own host, where `/etc/passwd` and your own notes are the
subjects, and later on a Rocky 9 Range host you own, arriving in milestone M4,
where a scenario has touched files inside a window for you to find.

## Words you'll meet

- **mtime**: modification time, when a file's contents last changed.
- **ctime**: change time, when a file's metadata (owner, mode, link count) or contents last changed; the kernel sets it and you cannot set it by hand.
- **atime**: access time, when the file was last read; on Pridwen it is updated lazily, so it is the least reliable of the three.
- **inode**: the record the filesystem keeps about a file, holding the three times, the owner and the mode.
- **hash**: a fixed-length fingerprint computed from a file's bytes; change one byte and the hash changes.
- **SHA-256**: the hash algorithm `sha256sum` uses; 64 hexadecimal characters.

## How it works

`stat` prints everything the inode knows about a file. Run it plain first so you
can see all three times in one place.

```
{user}@{host}:~$ stat /etc/passwd
  File: /etc/passwd
  Size: 2941      	Blocks: 8          IO Block: 4096   regular file
Device: 0,42	Inode: 262401      Links: 1
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Context: system_u:object_r:passwd_file_t:s0
Access: 2026-09-07 08:48:02.117530000 +0000
Modify: 2026-09-07 09:07:12.503811000 +0000
Change: 2026-09-07 09:07:12.503811000 +0000
 Birth: 2026-09-04 14:22:40.000000000 +0000
```

Reading it back: size in bytes, the inode number, the mode in octal and in
`ls -l` form, the owner and group, the SELinux context, then the three times
plus `Birth` (creation, which not every filesystem records). `Modify` and
`Change` are equal here, which is what a normal edit looks like: writing the
contents updates both at once. `Access` is earlier, from a program reading the
file at login.

`stat -c` (custom format) picks fields by letter: `%y` is mtime, `%z` is ctime,
`%x` is atime, `%n` is the name. That makes a one-line-per-file listing you can
sort or save.

```
{user}@{host}:~$ stat -c 'mtime=%y ctime=%z name=%n' /etc/passwd /etc/shadow
mtime=2026-09-07 09:07:12.503811000 +0000 ctime=2026-09-07 09:07:12.503811000 +0000 name=/etc/passwd
mtime=2026-09-07 09:07:12.611204000 +0000 ctime=2026-09-07 09:07:12.611204000 +0000 name=/etc/shadow
```

Both files changed within a tenth of a second of each other at 09:07, which is
the signature of a password change or a new account: `passwd` and `useradd`
rewrite both. A file whose mtime sits inside your incident window is worth a
closer look. One whose ctime is later than its mtime had its metadata touched
after its contents, which is what `chmod` or `chown` does. And because `touch -d`
can set mtime to any date but nothing can set ctime by hand, a file whose mtime
is old and whose ctime is recent has probably had its clock turned back on
purpose. ctime is the honest one.

Now the fingerprint. `sha256sum` reads a file and prints its hash and name.
Saving that line to a file, then checking it later with `-c` (check), proves the
file is the same bytes you hashed.

```
{user}@{host}:~$ mkdir -p {home}/case
{user}@{host}:~$ sha256sum /etc/passwd > {home}/case/evidence.sha256
{user}@{host}:~$ cat {home}/case/evidence.sha256
5a1d8e9f0c2b7a6e4d3f2e1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a  /etc/passwd
{user}@{host}:~$ sha256sum -c {home}/case/evidence.sha256
/etc/passwd: OK
```

The saved line is the hash, two spaces, the path. `-c` reads that file, hashes
each named path again, and prints `OK` when they match or `FAILED` when they do
not. Note that `-c` means "check" here and "custom format" for `stat`; the same
letter, two commands, two meanings. Record hashes of evidence the moment you
collect it, and you can show later that the copy you analysed is the copy you
took. On a Range host you combine the two halves: list the files changed in a
window, then hash each one, which is the raw material of a forensic account.

## When it goes wrong

`stat: cannot statx '/etc/shadow': Permission denied`. `stat` needs to read the
inode, and `/etc/shadow` is readable only by root. Prefix `sudo`; `pridwen why`
will say the same. The example above assumes it.

`/etc/passwd: FAILED` with `WARNING: 1 computed checksum did NOT match`. The file
has changed since you hashed it. That is not an error in the tool; it is a
finding. Note the time, run `stat` on it, and look for what changed it in the
journal.

`sha256sum: {home}/case/evidence.sha256: no properly formatted checksum lines
found`. The file is not in hash-space-space-path form, usually because it was
edited by hand or saved from the wrong command. Regenerate it with `sha256sum
path > file`.

## Try it

1. Run `stat /etc/passwd` and read the three times back: which is `Modify`, which is `Change`, and are they equal.
2. Run `stat -c 'mtime=%y ctime=%z name=%n' /etc/passwd` and `sudo stat -c ... /etc/shadow`; note how close their times are.
3. Create `{home}/pridwen/notes.txt`, run `stat -c '%y %z' {home}/pridwen/notes.txt`, then `chmod 600` it and run `stat` again; only ctime moves.
4. Run `touch -d '2020-01-01' {home}/pridwen/notes.txt` and `stat` once more; mtime goes back in time, ctime does not.
5. Hash `{home}/pridwen/notes.txt` into `{home}/case/evidence.sha256`, run `sha256sum -c` for `OK`, append a line to the file, and run `-c` again for `FAILED`.
6. On a Range host, run `sudo find /etc -mtime 0 -type f` to list files modified today, and hash each one into an evidence file.

## Remember

- `stat` shows mtime (contents), ctime (metadata, set only by the kernel) and atime; ctime is the one that cannot be faked with `touch`.
- `sha256sum file > list` records a fingerprint; `sha256sum -c list` proves the file is unchanged.
- Read, record, and hash; never edit evidence.
