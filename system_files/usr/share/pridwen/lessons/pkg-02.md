# Flatpak and Distrobox

Flatpak and Distrobox cover almost everything you install day to day, and
neither touches the read-only base. They solve different problems, so it helps
to know which fits.

Flatpak ships graphical applications with their dependencies bundled and run in
a sandbox. Apps are named by reverse-DNS id like `org.gnome.Loupe`, found with
`flatpak search`, and installed from Flathub, the only remote Pridwen configures.
It needs no sudo: system installs ask polkit and `--user` installs ask nothing.

```
$ flatpak install flathub org.gnome.Loupe
$ flatpak list --app
$ distrobox enter dev
[dev]$ pip install --user httpie
```

Distrobox gives you a full mutable Linux inside a container that shares your home
directory, so files you edit appear on the host. Inside it, `dnf`, `apt`, `pip`
and `make` all behave as on an ordinary system. `distrobox-export --app name`
puts a container app in the GNOME launcher, and `distrobox-export --bin` puts a
command on your host PATH. This is where Python virtualenvs, compilers and
one-off CLI tools belong, kept away from the host so nothing you try there can
break the base.

## Try it

1. Install a Flatpak app from Flathub and launch it from the GNOME menu.
2. Run `flatpak list` and tell apps apart from runtimes.
3. Enter a Distrobox and install a CLI tool with the box's own package manager.
4. Export that tool with `distrobox-export --bin` and run it from the host.
