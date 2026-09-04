# Software on an image-based system

Pridwen does not install software the way a traditional Fedora does. The base
system is a container image mounted read-only at `/usr`, so `dnf` has nowhere to
write and is not the tool here. Instead there are three clean places for
software, chosen by what the software is.

Desktop applications come from Flatpak, sandboxed and drawn from Flathub.
Command-line tools and development environments live in a Distrobox, a mutable
container that shares your home and where `dnf` works normally. Anything that
must be part of the host itself is layered onto the image with
`rpm-ostree install`, which takes effect after a reboot.

```
$ flatpak search inkscape
$ distrobox create -n dev -i fedora:43
$ distrobox enter dev
[dev]$ sudo dnf install ripgrep
```

The mental shift is from "install a package into a mutable system" to "choose
the right layer". Most days you reach for Flatpak or Distrobox and never touch
the host image at all. That separation is what lets the whole OS roll back to a
known-good state, because the base never accumulates one-off changes.

## Try it

1. Run `flatpak search` for an app you use and read its reverse-DNS id.
2. Create and enter a Distrobox, then `sudo dnf install` a small tool inside it.
3. Run `rpm-ostree status` and read the image name and digest.
4. Explain which of the three layers you would use for a GUI editor, and why.
