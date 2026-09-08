# Mounting and fstab

A filesystem has to be mounted before you can use it. Mounting attaches the
filesystem to a directory in the tree, called the mount point, so that
opening `/mnt/photo.jpg` reads a file from the drive behind `/mnt`. Because
mounting changes what every process on the machine sees, it is normally a
root action, done with `mount` and undone with `umount`.

This matters on Pridwen because the desktop hides most of it from you. Plug
in a USB stick and it appears in Files without a password. Understanding how
that happens, and how to mount something permanently, is what separates using
a computer from administering one. On a server there is no desktop helper,
and a mistake in the permanent mount table can stop the machine booting.

## Words you'll meet

- **mount**: attaching a filesystem to a directory so its files appear there.
- **mount point**: the directory a filesystem is attached to.
- **udisks**: the desktop service that mounts removable drives for logged-in users; `udisksctl` is its command-line tool.
- **fstab**: the file `/etc/fstab`, the table of filesystems to mount at every boot.
- **UUID**: the unique identifier a filesystem carries; fstab uses it so a drive is found even if its device name changes.
- **nofail**: an fstab option meaning "do not stop the boot if this drive is missing".
- **emergency mode**: the minimal root shell systemd drops into when a boot-time mount fails.
- **busy**: the state of a mount that some process is still using, which blocks `umount`.

## How it works

On the desktop you rarely type `mount`, because udisks mounts removable
media for you under `/run/media/{user}/` the moment you plug it in. That is
the same thing Files does when you click a drive. From a terminal you can ask
udisks to do it, as your own user, with no `sudo`. First find the device.

```
{user}@{host}:~$ lsblk -f /dev/sdb
NAME   FSTYPE FSVER LABEL UUID                                 MOUNTPOINTS
sdb
`-sdb1 vfat   FAT32 USB   1A2B-3C4D
```

The stick is `sdb`, its one partition is `sdb1`, formatted `vfat` with the
label `USB`, and `MOUNTPOINTS` is empty because it is not mounted yet. Now
mount it. The `-b` flag means "this is a block device".

```
{user}@{host}:~$ udisksctl mount -b /dev/sdb1
Mounted /dev/sdb1 at /run/media/{user}/USB
{user}@{host}:~$ ls /run/media/{user}/USB
photos  notes.txt
{user}@{host}:~$ udisksctl unmount -b /dev/sdb1
Unmounted /dev/sdb1
```

The first reply tells you the mount point, which is built from your user
name and the drive's label. `ls` proves the files are visible. `unmount`
detaches it; always do that before pulling the stick so the last writes land.
udisks asked polkit, the desktop's permission service, whether you may do
this, and polkit said yes because you are sitting at the machine.

The manual way works too and is what you would use on a server.

```
{user}@{host}:~$ sudo mount /dev/sdb1 /mnt
{user}@{host}:~$ findmnt /mnt
TARGET SOURCE    FSTYPE OPTIONS
/mnt   /dev/sdb1 vfat   rw,relatime,fmask=0022,dmask=0022,...
{user}@{host}:~$ sudo umount /mnt
```

`mount` prints nothing on success; `findmnt /mnt` confirms what is attached
there and with which options. A manual mount lasts only until reboot.

To mount something at every boot, add a line to `/etc/fstab`. Each line has
six fields: the device, usually written as `UUID=...` taken from `lsblk -f`;
the mount point; the filesystem type; a comma-separated list of options; and
two numbers that are almost always `0 0` today. A line for an optional
second drive looks like this.

```
UUID=9e8d7c6b-5a4f-4e3d-2c1b-0a9f8e7d6c5b  /mnt/data  btrfs  defaults,nofail  0 0
```

`defaults` is the ordinary set of options, and `nofail` tells systemd not
to stop the boot if the drive is missing. On Pridwen `/etc` is part of the
three-way merge at every `bootc upgrade`, so a line you add to fstab survives
updates.

A mistake in fstab drops the next boot into emergency mode, a root shell
with almost nothing running. Check the file while you still can. `findmnt
--verify` reads fstab and reports problems, and `mount -a` tries every entry
that is not yet mounted.

```
{user}@{host}:~$ sudo findmnt --verify
Success, no errors or warnings detected
{user}@{host}:~$ sudo mount -a
```

That success line is the one you want. If `--verify` names a line, fix it
before rebooting. The Coach prints this reminder whenever it sees fstab
edited.

## When it goes wrong

`mount: only root can do that` appears when you run `mount` without `sudo`.
For removable media use `udisksctl mount -b`, which works as you; for
anything else, `sudo mount`.

`umount: /mnt: target is busy.` means a process still has a file open there,
or its current directory is under the mount point. A shell that did `cd /mnt`
counts. `fuser -vm /mnt` names the processes, with `-v` verbose and `-m`
meaning "using this mount". Leave the directory or close the program, then
unmount again. `pridwen why` prints the same steps under the failed command.

`mount: /mnt: wrong fs type, bad option, bad superblock on /dev/sdb1` means
either the filesystem type is not what you said or the option is misspelled.
`lsblk -f /dev/sdb1` shows the real type; check the options against
`pridwen explain mount`.

## Try it

1. Plug in a USB stick and type `lsblk -f`. Find its partition, note the `FSTYPE`, `LABEL`, and `UUID`, and check that `MOUNTPOINTS` is empty.
2. Type `udisksctl mount -b /dev/sdb1`, using your device name, and read the mount point it reports.
3. Type `ls` on that mount point to see the files, then `udisksctl unmount -b /dev/sdb1`.
4. Type `sudo findmnt --verify` and read the success line, which shows the current fstab is well formed.
5. Type `cat /etc/fstab` and identify the six fields on one line.
6. Explain what `nofail` would do for a second drive that is sometimes unplugged.

## Remember

- Removable media: `udisksctl mount -b /dev/sdX1` as your user; `udisksctl unmount -b` before pulling it.
- Permanent mounts go in `/etc/fstab` by `UUID=`, with `nofail` for optional drives; `/etc` edits survive upgrades.
- After editing fstab run `sudo findmnt --verify` and `sudo mount -a` before rebooting; `fuser -vm` names what makes a mount busy.
