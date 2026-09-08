# Kernel arguments

Sometimes the kernel needs a setting handed to it before anything else runs:
a quirk for a piece of hardware, a debug flag, or an instruction such as
"which encrypted disk to unlock". Those settings travel on the kernel command
line, a single string of space-separated words, and each word is a kernel
argument, or karg for short. On a traditional system you would edit a GRUB
file and regenerate the menu. On a bootc system the boot entries are
generated from the deployment, so a hand edit is overwritten at the next
update. The supported path is `rpm-ostree kargs`.

This matters because kernel arguments are the most common reason people
break a boot, and because Pridwen's way of handling them is the safe one:
each deployment carries its own set, so a bad flag is undone by booting the
previous entry rather than by rescuing GRUB from a live USB.

## Words you'll meet

- **kernel command line**: the string of settings the boot loader passes to the kernel; visible after boot in `/proc/cmdline`.
- **kernel argument (karg)**: one word on that line, such as `quiet` or `rd.luks.uuid=...`.
- **GRUB**: the boot loader; on Pridwen its menu entries are generated, not hand-edited.
- **Boot Loader Specification entry**: a small file under `/boot/loader/entries/` describing one bootable deployment and its kargs.
- **deployment**: one complete copy of the operating system on disk; a karg change creates a new one.
- **pending**: a deployment that will boot next but is not the one running now.
- **rhgb**: the Fedora argument that turns on the graphical boot screen, which Pridwen's Plymouth theme draws.

## How it works

Show the current arguments first. Reading needs no `sudo`.

```
{user}@{host}:~$ rpm-ostree kargs
rd.luks.uuid=luks-3f2a9c1e-7b44-4d1a-9e0c-5a6b7c8d9e0f root=UUID=9e8d7c6b-5a4f-4e3d-2c1b-0a9f8e7d6c5b rootflags=subvol=root rw rhgb quiet
```

Read it word by word. `rd.luks.uuid=` tells the initramfs which LUKS
container to unlock, which is why you are asked for a passphrase before the
root filesystem exists. `root=UUID=` names the filesystem inside it, and
`rootflags=subvol=root` picks the btrfs subvolume. `rw` mounts it writable.
`rhgb` enables the graphical boot and `quiet` hides most kernel messages so
Plymouth's narration is what you see.

Compare that with what the running kernel actually received.

```
{user}@{host}:~$ cat /proc/cmdline
BOOT_IMAGE=(hd0,gpt2)/boot/ostree/default-8a1b2c3d/vmlinuz-6.17.4-200.fc43.x86_64 rd.luks.uuid=luks-3f2a9c1e-7b44-4d1a-9e0c-5a6b7c8d9e0f root=UUID=9e8d7c6b-5a4f-4e3d-2c1b-0a9f8e7d6c5b rootflags=subvol=root rw rhgb quiet ostree=/ostree/boot.1/default/8a1b2c3d/0
```

`/proc/cmdline` is the same words plus two that GRUB and ostree add on their
own: `BOOT_IMAGE=` is the kernel file that was loaded, and `ostree=` names
the deployment it belongs to. When `rpm-ostree kargs` and `/proc/cmdline`
disagree on a word you set, you have not rebooted into the new deployment yet.

Changing the set uses one of three actions. `--append=` adds a word,
`--delete=` removes one, and `--replace=old=new` swaps a value. Each creates
a new deployment, so the change takes effect at the next boot and the current
deployment stays as rollback.

```
{user}@{host}:~$ sudo rpm-ostree kargs --append=systemd.log_level=debug
Staging deployment... done
Kernel arguments updated.
Run "systemctl reboot" to start a reboot
{user}@{host}:~$ rpm-ostree status | head -n 4
State: idle
Deployments:
  ostree-image-signed:docker://ghcr.io/natethomass/pridwen:latest
                   Digest: sha256:d6c123f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
```

`Staging deployment` is the new copy being written; `Kernel arguments
updated` confirms the set changed. In `rpm-ostree status` the new deployment
is listed first, without the `*`, because it is pending and not booted. The
`systemd.log_level=debug` example makes systemd far more talkative in the
journal, which is a harmless thing to try and a useful thing to know.

To take it back out, `sudo rpm-ostree kargs --delete=systemd.log_level=debug`
creates another deployment without it. Or, if you have not rebooted yet,
`sudo rpm-ostree cleanup -p` discards the pending deployment entirely.

The same reasoning rules out `grub2-mkconfig`, `grubby`, `update-grub`, and
editing `/etc/default/grub` or the files under `/boot/loader/entries/`. None
of them are what regenerates the entries here; bootc writes a Boot Loader
Specification entry per deployment when it stages one, and the next staging
rewrites them. A hand edit might even work until the next update, which is
worse than failing, because it disappears silently.

## When it goes wrong

An `error:` from `--delete` saying the argument was not found means the word
is not in the current set, often because of a typo or because it was already
removed; the whole `KEY=VALUE` must match. `rpm-ostree kargs` shows the exact
current words to copy from.

`error: Transaction in progress` means another `rpm-ostree` or `bootc`
operation is running; wait until `rpm-ostree status` says `State: idle`.

If a new karg stops the machine booting, the fix is the rollback entry.
Reboot, choose the previous deployment in the GRUB menu, and once inside
delete the argument with `--delete=`. Nothing needs rescuing from a live USB.
The Coach flags `grub2-mkconfig`, `grubby`, and edits to `/etc/default/grub`
under the failed command; `pridwen why` explains why they do nothing here,
and `pridwen explain rpm-ostree` annotates `kargs` and its three actions.

## Try it

1. Type `rpm-ostree kargs` and read the current arguments. Find the `rd.luks.uuid=` word and explain what it does.
2. Type `cat /proc/cmdline` and find the two extra words, `BOOT_IMAGE=` and `ostree=`, that the loader added.
3. Type `ls /boot/loader/entries/` and see one file per deployment. Type `cat` on one and find its `options` line; it is the karg set.
4. On a test machine, type `sudo rpm-ostree kargs --append=systemd.log_level=debug` and read the three-line reply.
5. Type `rpm-ostree status` and find the new pending deployment listed first without a `*`.
6. Type `sudo rpm-ostree cleanup -p` to discard the pending deployment without rebooting, then `rpm-ostree status` to confirm it is gone.
7. Explain in one sentence why editing `/etc/default/grub` would have no effect on Pridwen.

## Remember

- `rpm-ostree kargs` shows the set; `--append=`, `--delete=`, and `--replace=` change it in a new deployment, effective next boot.
- `/proc/cmdline` is what the running kernel actually got; if it differs from `rpm-ostree kargs`, you have not rebooted yet.
- GRUB tools and `/etc/default/grub` do nothing here; entries are generated per deployment, so a bad karg is undone by rollback.
