# Mounting and fstab

A filesystem has to be mounted before you can use it, which attaches it to a
point in the tree. Mounting changes what every process sees, so it is normally a
root action, done with `mount` and undone with `umount`.

On the desktop you rarely type `mount`, because udisks mounts removable media
for you under `/run/media/$USER/` when you plug it in, the same thing GNOME Files
does. From a terminal, `udisksctl mount -b /dev/sdb1` does it as your user
without sudo. The manual `sudo mount /dev/sdb1 /mnt` works too but lasts only
until reboot.

```
$ lsblk -f /dev/sdb1
$ udisksctl mount -b /dev/sdb1
Mounted /dev/sdb1 at /run/media/nate/USB
$ udisksctl unmount -b /dev/sdb1
```

To mount something at every boot, add a line to `/etc/fstab` using the UUID from
`lsblk -f`. A mistake there drops the next boot into an emergency shell, so check
it while you still can: `sudo findmnt --verify` validates the syntax and
`sudo mount -a` tries every entry now. Adding `nofail` to an optional drive
keeps its absence from blocking boot. If `umount` says "target is busy", a
process still has a file open there, and `fuser -vm /mnt` names it.

## Try it

1. Run `lsblk -f` and note the UUID of a partition.
2. Mount a USB stick with `udisksctl` and find it under `/run/media`.
3. Run `sudo findmnt --verify` and read that fstab is well formed.
4. Explain what `nofail` does for an optional drive in fstab.
