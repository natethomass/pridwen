# Distrobox and daily work

Podman is the engine; Distrobox is the comfortable seat on top of it for
interactive work. A Distrobox is a container that shares your home directory and
integrates with the host, so it feels like a second Linux you can install
anything into without touching the base image.

Inside a box, the distribution's own package manager works normally, so `dnf` on
a Fedora box or `apt` on a Debian one installs whatever you need. Files you edit
live in your shared home, so they are visible on the host too. This is where
compilers, language toolchains and one-off CLI tools belong.

```
$ distrobox create -n dev -i fedora:43
$ distrobox enter dev
[dev]$ sudo dnf install -y ripgrep
[dev]$ exit
$ distrobox-export --bin ~/.local/bin/rg   # or export an app
```

`distrobox-export` bridges the box to the host: `--app name` puts a graphical
program in the GNOME menu, and `--bin path` puts a command on your host PATH.
Ports below 1024 are not bindable rootless by default, so map services to high
ports like 8080. Keeping messy, mutable tooling inside a box is what lets the host
stay clean and rollback-able, which is the whole point of the split.

## Try it

1. Create and enter a Fedora Distrobox.
2. Install a CLI tool inside it with the box's package manager.
3. Export that tool to the host with `distrobox-export --bin` and run it outside.
4. Explain why development toolchains belong in a box rather than layered on the host.
