# Space and encryption

Two everyday questions about storage are "how full is it" and "what is using the
space". `df` answers the first per filesystem; `du` answers the second per
directory. And underneath it all on Pridwen sits LUKS, the encryption that
protects the disk at rest.

`df -h` prints each filesystem with a human-readable size and how full it is.
`du -sh dir` totals a directory, and `du -xsh /var/* /home/* | sort -h` ranks
what is eating space without wandering into other filesystems or the read-only
image. Both `du` and `df` read without root, though `du` from `/` will hit
directories you cannot enter and report them on stderr.

```
$ df -h /
Filesystem  Size  Used Avail Use% Mounted on
/dev/mapper/luks-...  38G   12G   26G  32% /
$ sudo du -xsh /var/* 2>/dev/null | sort -h | tail -n 3
```

The LUKS layer is visible with `sudo cryptsetup luksDump`, which shows the
cipher, the key slots, and the key-derivation function that deliberately slows
down guessing a passphrase. You can add a second passphrase with `luksAddKey`
and remove one with `luksKillSlot`. This is the layer that makes a stolen laptop
a brick rather than a breach.

## Try it

1. Run `df -h` and read how full your root filesystem is.
2. Find the three largest directories under `/var` with `du` and `sort -h`.
3. Run `sudo cryptsetup luksDump` on your root device and find the cipher line.
4. Explain what the LUKS layer protects and what it does not protect once booted.
