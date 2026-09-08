# Disks and layers

Storage on Linux is a stack of layers. At the bottom is a physical disk. It
is divided into partitions, which are named regions of the disk. On Pridwen
one partition holds a LUKS container, an encrypted box that only opens with
your passphrase, and inside that box lives a btrfs filesystem, the structure
that turns raw space into directories and files. `lsblk` shows this stack as
a tree so you can see which layer sits on which.

Knowing the layers matters because every storage task names one of them.
Encryption questions are about the LUKS layer, free-space questions are about
the filesystem, and "which disk is this" questions are about the partition.
On a job you will read `lsblk` before touching any disk, because it is the
fastest way to avoid formatting the wrong one.

## Words you'll meet

- **block device**: anything the kernel treats as a disk, such as `/dev/vda` or `/dev/sda`.
- **partition**: a named region of a disk, such as `vda3`; partitions are numbered.
- **LUKS**: Linux Unified Key Setup, the standard for full-disk encryption; version 2 is what Pridwen uses.
- **crypt**: the type `lsblk` gives the decrypted view of a LUKS container; it appears under `/dev/mapper/`.
- **btrfs**: the filesystem Pridwen uses; it can hold several subvolumes on one pool of space and supports snapshots.
- **subvolume**: a separately mountable directory tree inside one btrfs filesystem; Pridwen uses them for the root, home and var.
- **mount point**: the directory where a filesystem is attached, such as `/` or `/boot`.
- **UUID**: a long unique identifier a filesystem carries, used in `/etc/fstab` so a drive is found even if its device name changes.

## How it works

Start with the plain tree. `lsblk` needs no flags and no `sudo`.

```
{user}@{host}:~$ lsblk
NAME                                          MAJ:MIN RM  SIZE RO TYPE  MOUNTPOINTS
vda                                           252:0    0   40G  0 disk
|-vda1                                        252:1    0  600M  0 part  /boot/efi
|-vda2                                        252:2    0    1G  0 part  /boot
`-vda3                                        252:3    0 38.4G  0 part
  `-luks-3f2a9c1e-7b44-4d1a-9e0c-5a6b7c8d9e0f 253:0    0 38.4G  0 crypt /var/home
                                                                        /var
                                                                        /
```

`NAME` is the device, indented to show what is inside what. `SIZE` is its
capacity, `TYPE` is the layer kind, and `MOUNTPOINTS` is where it is
attached. Read it from the top down as "inside": the disk `vda` contains three
partitions. `vda1` is the EFI partition the firmware reads. `vda2` is `/boot`,
holding the kernel and boot loader entries, unencrypted so the machine can
start. `vda3` holds the LUKS container, and the `crypt` line under it is the
decrypted view. Everything above the `crypt` line on the physical disk is
ciphertext; the kernel only exposes readable data through the `crypt` device
after you type your passphrase at boot.

The `crypt` line has three mount points because the one btrfs filesystem
inside it holds three subvolumes: the root at `/`, `/var`, and `/var/home`.
On Pridwen `/home` is a link that points to `/var/home`, so your files live on
the persistent `var` side. `/usr`, the programs, comes from the image and is
mounted read-only, which is why installing software on the host is not done
with `dnf`. `/etc` is merged three ways at each `bootc upgrade`: the old
image's version, the new image's version, and your local edits. `/var` and
home are never touched by an upgrade at all.

Add `-f` for filesystem details: the type, the label, and the UUID.

```
{user}@{host}:~$ lsblk -f
NAME        FSTYPE      FSVER LABEL UUID                                 MOUNTPOINTS
vda
|-vda1      vfat        FAT32       7A1B-2C3D                            /boot/efi
|-vda2      ext4        1.0         c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f /boot
`-vda3      crypto_LUKS 2           3f2a9c1e-7b44-4d1a-9e0c-5a6b7c8d9e0f
  `-luks-.. btrfs             fedora 9e8d7c6b-5a4f-4e3d-2c1b-0a9f8e7d6c5b /var/home
```

`FSTYPE` is what the layer holds: `vfat` for the EFI partition, `ext4` for
`/boot`, `crypto_LUKS` for the container with `FSVER` showing version `2`,
and `btrfs` inside. `UUID` is the identifier you would write in `/etc/fstab`
instead of a device name, because device names like `vda` can change between
boots and UUIDs do not.

To ask which device and subvolume back a single directory, use `findmnt`.

```
{user}@{host}:~$ findmnt /
TARGET SOURCE                                                       FSTYPE OPTIONS
/      /dev/mapper/luks-3f2a9c1e-7b44-4d1a-9e0c-5a6b7c8d9e0f[/root] btrfs  rw,relatime,seclabel,compress=zstd:1,subvol=/root
```

`SOURCE` is the decrypted device, and `[/root]` names the subvolume inside
it. `OPTIONS` says the root is `rw`, has SELinux labels (`seclabel`), and
compresses files with `zstd`. Because all three subvolumes share one btrfs
pool, `df` reports the same free space for each; that is expected, not a
mistake.

This layering is the foundation two Pridwen features rest on. LUKS below the
filesystem makes a stolen laptop unreadable. Subvolumes on btrfs let the
image side and the data side be treated separately, which is what lets
`bootc` swap the whole operating system underneath your files.

## When it goes wrong

`lsblk: /dev/sdb: not a block device` means you named something that is not
a disk, often a typo. Run plain `lsblk` first and copy the name from its
output.

`Device /dev/vda3 does not exist or access denied.` from `cryptsetup` means
the tool needs root to read the LUKS header. Look first with `lsblk -f`, which
does not need `sudo`, and use `sudo cryptsetup` only when you mean it. The
Coach reminds you of this under any disk tool run without `sudo`.

`fdisk: cannot open /dev/vda: Permission denied` is the same story for
partition tools: anything that opens a disk directly needs root. `pridwen
explain lsblk` annotates the `-f` flag and the columns if they blur together.

## Try it

1. Type `lsblk` and read the tree from the disk line down to the `crypt` line. Name the partition that holds the LUKS container.
2. Type `lsblk -f` and find the `FSTYPE` of the line mounted at `/var/home`. It should say `btrfs`.
3. Find the line whose `FSTYPE` is `crypto_LUKS` and check that `FSVER` is `2`.
4. Type `findmnt /` and read the subvolume name in square brackets after the source device.
5. Type `findmnt /var/home` and confirm it is the same device with a different subvolume.
6. Type `ls -ld /home` and read the arrow: `/home` points to `/var/home`.

## Remember

- `lsblk` shows disk, partitions, the LUKS `crypt` layer, and the filesystem inside it as a tree; `lsblk -f` adds types and UUIDs.
- Everything under the LUKS layer on disk is ciphertext; the `crypt` device is the readable view after your passphrase.
- `/usr` is read-only from the image, `/etc` is merged at upgrade, `/var` and `/var/home` persist and share one btrfs pool.
