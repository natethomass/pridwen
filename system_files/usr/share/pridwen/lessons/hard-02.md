# Devices and integrity

Two more baseline controls guard the physical and the on-disk edges of the
machine: USBGuard for what you plug in, and the immutable image itself for what
lives on disk. Both are about limiting change to what you intended.

USBGuard can block USB devices by policy. Pridwen ships it in learning mode, so
new devices are allowed and recorded rather than blocked, which lets you build a
picture before you enforce anything. `sudo usbguard list-devices` shows what has
been seen, and `sudo usbguard generate-policy` turns the current set into rules
you could then enforce.

```
$ sudo usbguard list-devices | tail
$ sudo usbguard generate-policy > my-devices.conf
```

The disk side is quieter but stronger. On a traditional host you would run a
file-integrity tool like AIDE to detect changes under `/usr`. On Pridwen `/usr`
is a read-only image that cannot change between boots, so the guarantee is
structural rather than checked after the fact. `rpm-ostree db diff` shows exactly
what a deployment contains, and any drift would be in `/etc` or `/var`, which is
where a defender looks. Together these mean surprises come from a small, known
set of places.

## Try it

1. Run `sudo usbguard list-devices` and find a device you have plugged in.
2. Generate a policy from your current devices and read a rule from it.
3. Run `rpm-ostree db diff` and see how the image is described.
4. Explain why an immutable `/usr` gives some of what AIDE would check.
