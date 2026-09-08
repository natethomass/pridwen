# Space and encryption

Two everyday questions about storage are "how full is it" and "what is using
the space". `df` answers the first, per filesystem: how big each one is and
how much is left. `du` answers the second, per directory: how much a folder
and everything inside it adds up to. Underneath all of it on Pridwen sits
LUKS, the layer that encrypts the whole disk so a lost laptop stays private.

These matter together because a full disk is one of the most common causes
of a broken machine, and because on a hardened system the encryption layer is
something you should be able to inspect, not just trust. On a job, "the
server is out of space" is a call you will take, and "is that laptop
encrypted" is a question an auditor will ask.

## Words you'll meet

- **filesystem**: a mounted structure of directories and files; `df` reports per filesystem.
- **human-readable**: sizes shown as `12G` or `640M` instead of raw byte counts; the `-h` flag on `df` and `du`.
- **stderr**: the error stream, separate from normal output; `2>/dev/null` throws it away.
- **LUKS**: Linux Unified Key Setup, the disk encryption standard; Pridwen uses version 2.
- **cipher**: the encryption algorithm, such as `aes-xts-plain64`.
- **key slot**: one of several places a LUKS header can store a passphrase; each slot unlocks the same disk.
- **key derivation function**: the deliberately slow maths that turns a passphrase into a key; on LUKS2 it is `argon2id`.
- **at rest**: data on a disk that is powered off or locked, as opposed to data in a running system.

## How it works

Start with `df -h`. The `-h` flag prints human-readable sizes.

```
{user}@{host}:~$ df -h /
Filesystem                                              Size  Used Avail Use% Mounted on
/dev/mapper/luks-3f2a9c1e-7b44-4d1a-9e0c-5a6b7c8d9e0f   38G   12G   26G  32% /
```

`Filesystem` is the decrypted LUKS device that holds btrfs. `Size` is the
whole pool, `Used` and `Avail` are what is taken and free, and `Use%` is the
figure to watch. Run plain `df -h` and you will see `/`, `/var`, and
`/var/home` all report the same numbers; that is correct, because they are
subvolumes sharing one btrfs pool, as the first storage lesson explained.
Anything above about 90% deserves attention.

`du` totals directories. `-s` means summarise, one line per argument instead
of every subdirectory, `-h` is human-readable again, and `-x` means stay on
one filesystem, which keeps it out of `/proc` and the read-only image.

```
{user}@{host}:~$ du -sh {home}
4.2G    {home}
```

To rank what is eating space, total each directory and sort. `sort -h`
understands human-readable sizes so `640M` sorts before `4.2G`. `2>/dev/null`
hides the errors about directories you may not enter, and `tail -n 3` keeps
the last three lines, which are the largest.

```
{user}@{host}:~$ sudo du -xsh /var/* 2>/dev/null | sort -h | tail -n 3
312M    /var/log
1.1G    /var/lib
4.2G    /var/home
```

Read it bottom up: `/var/home` is the largest, which is your own files. On
Pridwen the interesting places are always under `/var`, because that is
where everything that persists lives: your home, logs, container images
under `/var/lib/containers`, and Flatpak apps. `/usr` is the read-only image
and never grows on its own.

Now the encryption. The LUKS header sits at the start of the encrypted
partition and describes how the disk is locked. Reading it needs root.

```
{user}@{host}:~$ sudo cryptsetup luksDump /dev/vda3
LUKS header information
Version:        2
Epoch:          3
...
Keyslots:
  0: luks2
        Key:        512 bits
        Cipher:     aes-xts-plain64
        PBKDF:      argon2id
        Time cost:  4
        Memory:     1048576
        Threads:    4
```

`Version: 2` confirms LUKS2. Under `Keyslots`, slot `0` is your passphrase.
`Cipher: aes-xts-plain64` is the algorithm, `Key: 512 bits` is the key
length, and `PBKDF: argon2id` is the key derivation function. The `Time
cost` and `Memory` lines are what make guessing slow: every attempt at the
passphrase must spend that much time and memory, so a brute-force attack on
a stolen disk takes lifetimes instead of hours.

You can add a second passphrase, for a colleague or a recovery envelope,
with `sudo cryptsetup luksAddKey /dev/vda3`, which asks for an existing
passphrase and then the new one; it lands in the next free slot. `sudo
cryptsetup luksKillSlot /dev/vda3 1` removes slot 1. Never remove the last
slot, because nothing can open the disk afterwards.

LUKS protects data at rest. Once you have typed the passphrase at boot, the
`crypt` device is readable to anyone with the right file permissions, which is
why file permissions, SELinux and the screen lock still matter on a running
machine.

## When it goes wrong

`du: cannot read directory '/var/lib/private': Permission denied` appears
when `du` meets a directory you may not enter. It exits 1 but the totals for
what it could read are still right. Append `2>/dev/null` to hide the noise,
or run `sudo du` for the full picture. `pridwen why` explains the exit code.

`du -sh /` runs for minutes and walks the whole system, including the
read-only image and `/proc`. Use `-x` and start at `/var` instead; the Coach
suggests the exact line when it sees `du` pointed at `/`.

`Device /dev/vda3 does not exist or access denied.` from `cryptsetup` means
it was run without `sudo`. `lsblk -f` shows which partition is
`crypto_LUKS` without root; the dump itself needs `sudo`. `pridwen explain
df` and `pridwen explain du` annotate every flag used here.

## Try it

1. Type `df -h` and find the `Use%` for `/`. Notice that `/var` and `/var/home` show the same figures.
2. Type `du -sh {home}` and read your home directory's total.
3. Type `sudo du -xsh /var/* 2>/dev/null | sort -h | tail -n 3` and name the three largest directories under `/var`.
4. Type `lsblk -f` and find the partition whose `FSTYPE` is `crypto_LUKS`.
5. Type `sudo cryptsetup luksDump /dev/vda3`, using that partition, and find the `Cipher` and `PBKDF` lines.
6. Explain what LUKS protects and what it does not protect once the machine is booted and unlocked.

## Remember

- `df -h` reports per filesystem; subvolumes on one btrfs pool show the same free space.
- `sudo du -xsh /var/* 2>/dev/null | sort -h` ranks where the space went; everything that grows lives under `/var`.
- `sudo cryptsetup luksDump` shows the LUKS2 header: cipher, key slots, and the slow `argon2id` derivation that protects data at rest.
