# From power to desktop

Booting is a relay race. The firmware in the machine wakes up, finds a boot
loader on the disk, and hands over. The boot loader loads the kernel, the
core of Linux, along with a small starter filesystem called the initramfs.
The initramfs unlocks the encrypted disk, mounts the real root, and hands to
systemd, the program that starts every service up to the login screen.
Pridwen themes each of those steps, from the Plymouth splash to the GDM
greeter, but the sequence underneath is ordinary Fedora.

Knowing the relay matters because when a machine will not boot, the question
is always "which runner dropped the baton". `systemd-analyze` tells you how
long each leg took, and the journal keeps a diary of every boot so you can
read what happened even after the screen went black.

## Words you'll meet

- **firmware**: the program built into the motherboard that runs first; on modern machines it is UEFI.
- **boot loader**: the small program the firmware starts, GRUB on Pridwen, which loads the kernel.
- **kernel**: the core of Linux, which talks to the hardware and runs everything else.
- **initramfs**: a compressed starter filesystem loaded with the kernel; on Pridwen it unlocks LUKS and shows Plymouth.
- **Plymouth**: the program that draws the boot screen while the kernel and systemd work; Pridwen's theme shows the shield, a rail, and plain-English narration lines.
- **systemd**: the first real process, PID 1, which starts services in order.
- **unit**: one thing systemd manages, such as a service or a mount, with a name like `NetworkManager.service`.
- **userspace**: everything after the kernel hands to systemd.
- **journal**: systemd's log, read with `journalctl`; it remembers previous boots.

## How it works

Start with the timing summary. `systemd-analyze` with no arguments splits
the last boot into its legs.

```
{user}@{host}:~$ systemd-analyze
Startup finished in 3.1s (firmware) + 2.0s (loader) + 1.4s (kernel) + 2.8s (initrd) + 6.2s (userspace) = 15.6s
graphical.target reached after 6.1s in userspace.
```

Each number is one runner: firmware, then the loader, then the kernel, then
`initrd`, which is the initramfs including the time you spent typing the
LUKS passphrase, then userspace. The total is wall-clock time from power to
`graphical.target`, the state that means the login screen is up. A slow
firmware number is the motherboard, not Linux; a slow userspace number is
something systemd started.

To find that something, ask for `blame`, which lists units slowest first.
`head -n 3` keeps the first three lines.

```
{user}@{host}:~$ systemd-analyze blame | head -n 3
2.412s NetworkManager-wait-online.service
1.030s firewalld.service
  611ms systemd-udev-settle.service
```

The left column is how long the unit took, the right is its name. Raw time
can mislead, because a unit that ran in parallel with others cost nothing on
the critical path. `critical-chain` shows what waited on what.

```
{user}@{host}:~$ systemd-analyze critical-chain
graphical.target @6.1s
`-multi-user.target @6.1s
  `-NetworkManager-wait-online.service @3.6s +2.4s
    `-NetworkManager.service @3.2s +342ms
```

Each line is a unit; `@` is when it finished, `+` is how long it ran, and
indentation means "waited for the line above". Here the desktop waited on
`NetworkManager-wait-online`, which waited on `NetworkManager`. The unit with
the biggest `+` on this chain is the real bottleneck.

The journal remembers boots. `journalctl -b` shows this boot, where `-b`
means "boot" and takes an optional number: `-b -1` is the previous boot.
`--list-boots` shows what is kept.

```
{user}@{host}:~$ journalctl --list-boots
IDX BOOT ID                          FIRST ENTRY                 LAST ENTRY
 -2 3a9f0c1d2e4b4f6a8b7c9d0e1f2a3b4c Sat 2026-09-05 08:12:03 UTC Sat 2026-09-05 18:40:11 UTC
 -1 5c7e1a2b3d4f4a5b6c7d8e9f0a1b2c3d Sun 2026-09-06 09:01:45 UTC Sun 2026-09-06 22:15:30 UTC
  0 8e2d4f6a1b3c4d5e6f7a8b9c0d1e2f3a Mon 2026-09-07 07:55:12 UTC Mon 2026-09-07 09:14:02 UTC
```

`IDX` 0 is the boot you are in, `-1` the one before. When something went
wrong at startup, filter by priority: `-p err` keeps only messages at error
level or worse.

```
{user}@{host}:~$ journalctl -b -p err
-- No entries --
```

`-- No entries --` is the answer you want on a healthy boot. A line here
names the unit that failed and usually the reason.

Plymouth deserves a word because it is the part you see. It runs from the
initramfs, draws Pridwen's shield and rail, and prints the narration lines
that say in plain English what the machine is doing. Pressing Esc while it
runs shows the raw kernel and systemd messages underneath; press Esc again to
return. Because Pridwen builds the initramfs, and the Plymouth theme inside
it, into the image at build time, every machine running a given version boots
identically. That is also why running `dracut` or `plymouth-set-default-theme`
on the host is pointless: the next `bootc upgrade` replaces the initramfs
with the image's copy.

## When it goes wrong

`Data from the specified boot (-1) is not available: No such boot ID in
journal` means the journal does not hold that many boots, common on a fresh
install. `journalctl --list-boots` shows what exists.

`Failed to reboot system via logind: Interactive authentication required.`
appears when you type `reboot` from a remote or text-only session. polkit
trusts a person at the desktop but not a remote login, so use `sudo
systemctl reboot` there. In your own desktop session `systemctl reboot` works
without `sudo`.

A boot that stops at the Plymouth screen with no narration for more than a
minute usually means a unit is waiting for something. Press Esc to see the
messages; after the next successful boot, `journalctl -b -1 -p err` shows
what it was. `pridwen explain journalctl` and `pridwen explain
systemd-analyze` annotate the flags used here.

## Try it

1. Type `systemd-analyze` and write down the time for each of the five legs and the total.
2. Type `systemd-analyze blame | head` and name the slowest unit.
3. Type `systemd-analyze critical-chain` and find the unit with the largest `+` time on the chain.
4. Type `journalctl --list-boots` and count how many boots the journal holds.
5. Type `journalctl -b -p err` and check whether anything failed this boot. `-- No entries --` is good.
6. On your next boot, press Esc during the Plymouth screen, read a few raw lines, and press Esc again to return to the shield.

## Remember

- Boot is firmware, loader, kernel, initramfs (Plymouth and LUKS unlock), then systemd userspace to `graphical.target`.
- `systemd-analyze` times the legs, `blame` ranks units, `critical-chain` shows the real bottleneck.
- `journalctl -b` is this boot, `-b -1` the previous, `-p err` only the errors; the initramfs and Plymouth theme come from the image.
