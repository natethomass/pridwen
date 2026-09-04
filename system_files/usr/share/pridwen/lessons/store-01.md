# Disks and layers

Storage on Linux is a stack of layers, and `lsblk` shows the stack as a tree.
At the bottom is the physical disk, then its partitions, and on Pridwen a LUKS
encryption layer, and inside that the btrfs filesystem that holds the system.

```
$ lsblk
NAME                  SIZE TYPE  MOUNTPOINTS
vda                    40G disk
|-vda1                600M part  /boot/efi
|-vda2                  1G part  /boot
`-vda3               38.4G part
  `-luks-...          38G crypt
    `-...              38G btrfs /, /home, /var
```

Read it from the bottom up: the `crypt` line is the decrypted view of the LUKS
volume, and everything above it on disk is ciphertext. `lsblk -f` adds the
filesystem type and UUID of each layer, which is what you reference in
`/etc/fstab`. Because Pridwen puts `/`, `/home` and `/var` on one btrfs volume as
subvolumes, they share the same free space, which is why `df` reports the same
number for each. This layering is the foundation the encryption and rollback
features rest on.

## Try it

1. Run `lsblk` and read the tree from disk up to the mount points.
2. Run `lsblk -f` and find the filesystem type of your root.
3. Identify the `crypt` layer and explain what sits below it on disk.
4. Run `findmnt /` and see which device and subvolume back your root.
