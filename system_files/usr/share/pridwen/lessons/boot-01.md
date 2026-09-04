# From power to desktop

Booting is a relay: firmware hands to a boot loader, which loads the kernel and a
small initial ramdisk, which mounts the real root and hands to systemd, which
starts everything else up to the login screen. On Pridwen each of those steps is
themed, from the Plymouth splash to the GDM greeter, but the sequence is
ordinary Fedora.

`systemd-analyze` breaks the time down. The plain command splits firmware,
loader, kernel, initrd and userspace. `systemd-analyze blame` ranks the slowest
units, and `critical-chain` shows what waited on what, which is more useful than
raw times because it reveals the bottleneck.

```
$ systemd-analyze
Startup finished in 3.1s (firmware) + 2.0s (loader) + 1.4s (kernel) +
2.8s (initrd) + 6.2s (userspace) = 15.6s
$ systemd-analyze blame | head -n 3
```

The journal remembers boots. `journalctl -b` is this boot, `journalctl -b -1`
the previous one, and `--list-boots` shows what is kept. When something goes
wrong during startup, `journalctl -b -p err` filters straight to the errors.
Because Pridwen builds the initramfs into the image, the boot experience is the
same on every machine running a given version.

## Try it

1. Run `systemd-analyze` and read the time spent in each phase.
2. Run `systemd-analyze blame | head` and name the slowest unit.
3. Run `journalctl -b -p err` and see if anything failed this boot.
4. Run `journalctl --list-boots` and count how many boots are stored.
