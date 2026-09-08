# Images and copies

To examine a disk without changing it, you work on a copy, and you prove the
copy matches the original with a hash. This is the discipline that keeps
evidence trustworthy: never analyse the only copy, and never analyse the live
original if you can avoid it. Every read of a mounted filesystem can update an
access time; every mistake on the original is permanent. A copy absorbs both.

On a job this is the chain of custody, and it is what lets a conclusion be
traced back to untouched evidence. This lesson is for a Rocky 9 Range host you
own, arriving in milestone M4, where a scenario attaches a small second disk for
you to image. Do not image the disk of your own Pridwen host: it is LUKS
encrypted and in use, and there is nothing to learn from a copy of it that the
Range volume does not teach more safely.

## Words you'll meet

- **block device**: a disk or partition the kernel exposes as a file under `/dev`, read in fixed-size blocks.
- **image**: a byte-for-byte copy of a block device stored as an ordinary file.
- **dd**: the command that copies raw bytes from an input (`if=`) to an output (`of=`).
- **lsblk**: the command that lists block devices with their sizes and mount points.
- **loop device**: a way to mount an image file as if it were a disk.
- **read-only mount**: a mount with `-o ro`, so nothing you do can write to it.
- **working copy**: a second copy of the image that you are allowed to change.

## How it works

Restating the essential from the Storage node: `lsblk` shows every disk and
partition, its size, and where it is mounted. Look before you copy, because `dd`
will write wherever you point it.

```
{user}@{host}:~$ lsblk
NAME        MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
sda           8:0    0   20G  0 disk
├─sda1        8:1    0    1G  0 part /boot
└─sda2        8:2    0   19G  0 part /
sdb           8:16   0  256M  0 disk
```

`sda` is the system disk with its two partitions and their mount points. `sdb`
is a 256 MiB disk with no partitions and no mount point: the evidence volume the
scenario attached. `RO` is `0` for all of them, meaning the kernel would allow
writes. The name is what you need: `/dev/sdb`, and nothing else.

Now image it. `dd if=/dev/sdb of=~/case/sdb.img` reads the input file (`if`) and
writes the output file (`of`). `bs=4M` sets the block size to 4 MiB per read,
which is faster than the 512-byte default. `status=progress` prints a running
count so you can see it is working. Reading a block device needs root, so `sudo`
is required; the `~` in the output path is expanded by your shell before `sudo`
runs, so the file lands in your home.

```
{user}@{host}:~$ mkdir -p ~/case
{user}@{host}:~$ sudo dd if=/dev/sdb of=~/case/sdb.img bs=4M status=progress
268435456 bytes (268 MB, 256 MiB) copied, 1 s, 251 MB/s
64+0 records in
64+0 records out
268435456 bytes (268 MB, 256 MiB) copied, 1.07052 s, 251 MB/s
```

`64+0 records in` means sixty-four full 4 MiB blocks and zero partial ones were
read, and the same were written; 64 times 4 MiB is 256 MiB, which matches
`lsblk`. Any `+1` would mean a partial final block, which is normal for disks
whose size is not a multiple of the block size. If the source has read errors,
add `conv=noerror,sync` so `dd` continues past them and pads the bad block with
zeros rather than stopping.

Prove the copy. Hash the device and the image the same way. The device is still
root-only, so `sudo` again.

```
{user}@{host}:~$ sudo sha256sum /dev/sdb ~/case/sdb.img
9c0b3e2f4a1d5c6b7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d  /dev/sdb
9c0b3e2f4a1d5c6b7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d  /home/{user}/case/sdb.img
{user}@{host}:~$ sudo sha256sum /dev/sdb > ~/case/sdb.sha256
```

Two identical hashes mean the image is the device, byte for byte. Save the hash
so anyone can rerun `sha256sum -c` later. From here on you touch the device no
more.

Mount the image read-only through a loop device and browse it. `-o ro,loop` sets
two options: read-only, and "this is a file, give it a loop device".

```
{user}@{host}:~$ sudo mount -o ro,loop ~/case/sdb.img /mnt
{user}@{host}:~$ ls -la /mnt
total 16
drwxr-xr-x.  3 root root 4096 Sep  7 09:11 .
dr-xr-xr-x. 18 root root 4096 Sep  4 14:20 ..
drwx------.  2 root root 4096 Sep  7 09:11 .hidden
-rw-r--r--.  1 root root  118 Sep  7 09:11 notes.txt
{user}@{host}:~$ sudo touch /mnt/probe
touch: cannot touch '/mnt/probe': Read-only file system
{user}@{host}:~$ sudo umount /mnt
```

The failed `touch` is the read-only mount doing its job: even root cannot write.
If you need to change something, for instance to run a tool that insists on
writing, copy the image first (`cp ~/case/sdb.img ~/case/sdb-work.img`) and work
on that. The chain is the point: original, hashed image, working copy, each step
recorded in your notes file, so that whatever you conclude can be traced back to
evidence nobody altered.

## When it goes wrong

`dd: failed to open '/dev/sdb': Permission denied`. Block devices are root-only.
Run it with `sudo`.

`mount: /mnt: wrong fs type, bad option, bad superblock on /dev/loop0`. The image
is not a filesystem the kernel recognises, often because the device held a
partition table and the filesystem starts partway in. Run `sudo fdisk -l
~/case/sdb.img` to see the partitions, then mount with `-o
ro,loop,offset=<start sector times 512>`.

A write landed on the wrong `of=`. There is no undo; `dd` does what it is told.
That is why `lsblk` comes first and the target is read back twice before Enter.
On the Range the worst case is a rebuilt lab; on a real machine it is lost data.

## Try it

1. On a Range host, run `lsblk` and identify the small unmounted disk by name and size.
2. Run `mkdir -p ~/case` and `sudo dd if=/dev/sdb of=~/case/sdb.img bs=4M status=progress`; read the records line back and check it against the size.
3. Run `sudo sha256sum /dev/sdb ~/case/sdb.img` and confirm the two hashes match, then save the device hash to `~/case/sdb.sha256`.
4. Mount with `sudo mount -o ro,loop ~/case/sdb.img /mnt`, list it with `ls -la /mnt`, and try `sudo touch /mnt/probe` to see the refusal.
5. Unmount, copy the image to `sdb-work.img`, and write three lines in your notes file: imaged, hashed, working copy made, each with `date +%T`.
6. Explain in one sentence why you analyse a copy rather than the original device.

## Remember

- `lsblk` first, then `sudo dd if=/dev/<device> of=<image> bs=4M status=progress`; the target is checked twice.
- Hash the device and the image with `sha256sum`; matching hashes make the image evidence.
- Mount the image `-o ro,loop`, change only a working copy, and record every step.
