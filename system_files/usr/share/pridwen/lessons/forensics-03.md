# Images and copies

To examine a disk without changing it, you work on a copy, and you prove the copy
matches the original with a hash. This is the discipline that keeps evidence
trustworthy: never analyse the only copy, and never analyse the live original if
you can avoid it.

On a Range host you practise imaging a small volume. `dd` reads a block device
byte for byte into a file; hashing both the source and the image proves they
match. Because `dd` writes exactly where you tell it, the `of=` target is checked
twice against `lsblk`, since a wrong target overwrites real data with no warning.

```
$ lsblk /dev/sdb
$ sudo dd if=/dev/sdb of=~/case/sdb.img bs=4M status=progress
$ sha256sum /dev/sdb ~/case/sdb.img    # the two hashes must match
```

You then work on the image, mounting it read-only (`mount -o ro,loop`) so nothing
you do alters it, and any change you make happens to a working copy of the image,
never the evidence file. The chain is the point: original, hashed image, working
copy, each step recorded, so that whatever you conclude can be traced back to
untouched evidence. On the Range the volumes are small and the stakes are a grade,
but the method is exactly the one used where the stakes are real.

## Try it

1. On a Range host, image a small block device with `dd` to a file.
2. Hash the source and the image and confirm they match.
3. Mount the image read-only and browse it without changing it.
4. Explain why you analyse a copy rather than the original device.
