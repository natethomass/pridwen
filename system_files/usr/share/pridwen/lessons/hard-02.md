# Devices and integrity

Two edges of a machine are easy to forget: the USB ports, where anything plugged in becomes a device the kernel trusts, and the disk, where a quiet change to a system file can stay hidden for months. Both raise the same question: did this change on purpose, or did something else make it? On Pridwen two controls answer it. USBGuard watches the ports, and the immutable image guarantees the system files.

On a job, a USB stick left in a car park is a classic way into a company, and a modified binary under `/usr` is a classic way to stay in. Knowing how Pridwen handles both lets you say, with evidence, what is plugged in and what is on disk. You already know that `/usr` is read-only here and that the whole system arrives as one image; this lesson shows what that buys you.

## Words you'll meet

- **USBGuard**: a service that decides, by policy, whether a newly plugged-in USB device is allowed to work.
- **policy**: a list of rules, one per device, saying allow, block, or reject.
- **learning mode**: how Pridwen ships USBGuard: new devices are allowed and recorded, so you can build a list before enforcing anything.
- **daemon**: a program that runs in the background and answers requests; USBGuard has one, `usbguard-daemon`.
- **integrity**: confidence that a file is exactly what it was when it was installed.
- **AIDE**: a file-integrity tool that takes a snapshot of files and later reports which ones changed.
- **deployment**: one complete version of the system image on disk, the thing you boot into; Pridwen keeps the current one and the previous one.
- **digest**: a checksum of a whole image; two machines with the same digest have the same bytes.
- **immutable**: not changeable in place; on Pridwen `/usr` is replaced by a new image, never edited.

## How it works

USBGuard's daemon talks to the kernel as devices appear. Its commands need root, because the policy decides what hardware the whole machine trusts, so each one starts with `sudo`.

```
{user}@{host}:~$ sudo usbguard list-devices
1: allow id 1d6b:0002 serial "0000:00:14.0" name "xHCI Host Controller" hash "..." with-interface 09:00:00
2: allow id 1d6b:0003 serial "0000:00:14.0" name "xHCI Host Controller" hash "..." with-interface 09:00:00
5: allow id 046d:c52b serial "" name "USB Receiver" hash "..." with-interface { 03:01:01 03:01:02 03:00:00 }
```

Each line is one device. The first number is the device id USBGuard assigned. `allow` is the decision in force. `id 046d:c52b` is the vendor and product code that identifies the model, `name` is what the device calls itself, `hash` is a fingerprint of its descriptors, and `with-interface` lists the kinds of interface it offers (`03:01:01` is a keyboard, `03:01:02` a mouse). A device that says it is a storage stick but also offers a keyboard interface is the classic attack, and this line is where you would see it.

In learning mode every device shows `allow`, which is intended. The point is to collect the real list first. When you are ready to enforce, you turn the current list into a policy.

```
{user}@{host}:~$ sudo usbguard generate-policy > my-devices.conf
{user}@{host}:~$ head -2 my-devices.conf
allow id 1d6b:0002 serial "0000:00:14.0" name "xHCI Host Controller" hash "..." with-interface 09:00:00
allow id 046d:c52b serial "" name "USB Receiver" hash "..." with-interface { 03:01:01 03:01:02 03:00:00 }
```

`generate-policy` prints one `allow` rule per device currently present, and the `>` sends that text into a file instead of the screen. `head -2` shows the first two lines. Installing the file as `/etc/usbguard/rules.conf` and restarting the daemon would block anything not on the list. Do not do that on your daily machine until you have plugged in everything you rely on, including the keyboard, because the rules apply to it too.

The disk side is quieter but stronger. On a traditional system you would install AIDE, take a snapshot of every file under `/usr`, and compare later to find changes. On Pridwen `/usr` is part of a read-only image, so nothing can edit it between boots; a change can only arrive as a whole new deployment that you chose to pull. The guarantee is structural rather than checked after the fact.

```
{user}@{host}:~$ rpm-ostree status
State: idle
Deployments:
* ostree-unverified-registry:ghcr.io/.../pridwen:latest
                   Digest: sha256:8f3a...
                  Version: 0.3.0-m2 (2026-09-07T10:12:40Z)
  ostree-unverified-registry:ghcr.io/.../pridwen:latest
                   Digest: sha256:d6c1...
                  Version: 0.2.0-m1 (2026-09-04T18:02:11Z)
```

The image name and digests are shortened here; yours print in full. The `*` marks the deployment you are booted into. Each one has a digest, so two systems with the same digest have byte-for-byte the same `/usr`. The second entry is the previous version, kept for rollback. When an upgrade has been downloaded but not yet booted, `rpm-ostree db diff` lists exactly which packages changed between the booted deployment and the pending one, which is the kind of answer AIDE gives, but from the image itself.

Where can change still happen? In `/etc`, which holds configuration and is merged across upgrades, and in `/var`, which holds everything that grows: home directories, logs, containers. Those two trees are where a defender looks, and they are much smaller than a whole system.

## When it goes wrong

`IPC connect: service=usbguard: Permission denied` comes from running `usbguard` without `sudo`. The daemon only talks to root, because the policy governs the whole machine. Put `sudo` in front.

`bash: aide: command not found` is exit 127: AIDE is not in the image. On Pridwen the read-only `/usr` gives most of what AIDE would check. If a course insists on it, install it in a Distrobox or on a Range host, where the filesystem is mutable and the tool makes sense.

`rpm-ostree db diff` printing nothing, or saying there is no pending deployment, is normal when nothing new has been downloaded. There is nothing to compare until `bootc upgrade` has staged a new image. `pridwen why` explains any of these after the fact.

## Try it

1. Run `sudo usbguard list-devices` and find the line for your keyboard or mouse. Read its `with-interface` list.
2. Plug in a USB stick, run the command again, and find the new line. Expect `allow`, because this is learning mode.
3. Run `sudo usbguard generate-policy > my-devices.conf` and `wc -l my-devices.conf` to count the rules (`wc -l` counts lines). Read one rule and name each field.
4. Run `rpm-ostree status` and read the digest of the booted deployment. Compare it with the previous one.
5. Run `ls /etc/usbguard/` to see where an enforced policy would live. Do not install one yet.
6. Explain, in one sentence, why a read-only `/usr` gives some of what AIDE would check.

## Remember

- USBGuard in learning mode records every device with `allow`; `generate-policy` turns that record into rules you could enforce later.
- `/usr` on Pridwen cannot change between boots, so file integrity there is a property of the image, not something to check afterwards.
- Change can still happen in `/etc` and `/var`, so those are the trees worth watching.
