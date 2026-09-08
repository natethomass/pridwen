# Flatpak and Distrobox

Flatpak and Distrobox cover almost everything you install day to day on
Pridwen, and neither touches the read-only base image. Flatpak is a way to ship
a desktop application with everything it needs, running in a sandbox. Distrobox
is a way to have a full, ordinary, writable Linux inside a container, sharing
your home directory. They solve different problems, so the skill is knowing
which one fits the thing in your hand.

This matters because the base image staying untouched is what makes Pridwen
updates and rollbacks whole, and it is also how modern desktops and developer
machines work in general: applications in sandboxes, toolchains in containers.
A learner who can install a Flatpak and stand up a Distrobox can get any
software they need without ever weakening the host.

## Words you'll meet

- **sandbox**: a fenced-off space where an app runs with limited access to your files, devices, and network.
- **reverse-DNS id**: an app name built from its web domain backwards, like `org.gnome.Loupe`; Flatpak's real name for an app.
- **remote**: a Flatpak source; Flathub is the only one Pridwen configures.
- **runtime**: a shared bundle of libraries that many Flatpak apps use, installed once.
- **polkit**: the system that asks for your password when an ordinary user does something system-wide.
- **container**: an isolated copy of a Linux userland running on the host's kernel.
- **export**: making a container's app or command appear on the host as if it were installed there.
- **virtualenv**: a private Python environment with its own packages, kept away from the system's.

## How it works

Flatpak apps are found with `flatpak search` and installed by their id. The
first argument to `install` can be the remote name, `flathub`; Pridwen has only
one remote, so it can be left out, but writing it is a good habit for machines
that have several. No `sudo` is needed: a system-wide install asks polkit for
your password once, and `--user` installs into your home and ask nothing.

```
{user}@{host}:~$ flatpak install flathub org.gnome.Loupe
Looking for matches…
        ID                          Branch   Op   Remote    Download
 1. [✓] org.gnome.Loupe             stable   i    flathub   1.2 MB / 1.4 MB
Installation complete.
```

The ID column is the app, Branch is which line of releases, Op `i` means
install, and Download is the size. Once installed, the app is in the GNOME
launcher like any other, and `flatpak run org.gnome.Loupe` starts it from a
terminal. `flatpak list` shows what is installed; `--app` hides the runtimes
so you see only applications.

```
{user}@{host}:~$ flatpak list --app
Name          Application ID        Version   Branch   Installation
Image Viewer  org.gnome.Loupe       49.0      stable   system
{user}@{host}:~$ flatpak list --runtime | head -n 2
Name              Application ID          Version   Branch   Installation
GNOME Platform    org.gnome.Platform      49        49       system
```

Installation says whether it is `system` (for every user) or `user` (only
you). The runtime, `org.gnome.Platform`, is the shared library bundle that
Loupe and other GNOME apps run on; you never install a runtime by hand, it
arrives with the first app that needs it. `flatpak update` refreshes apps and
runtimes together, and `flatpak uninstall org.gnome.Loupe` removes one.
`pridwen explain flatpak` annotates the flags.

Distrobox is for everything that is not a desktop app. Inside the box, `dnf`
on a Fedora image, `apt` on a Debian one, `pip`, `make`, and a compiler all
behave as on an ordinary system, because the box's own `/usr` is writable.
Your home is the same directory inside and out, so a project you edit on the
host is the project you build in the box. The earlier lesson created a box
called `dev` with `distrobox create -n dev -i fedora:43`; `distrobox enter
dev` opens a shell in it, and `exit` leaves.

```
{user}@{host}:~$ distrobox enter dev
📦[{user}@dev ~]$ sudo dnf install -y ripgrep
Installed:
  ripgrep-14.1.1-3.fc43.x86_64
📦[{user}@dev ~]$ pip install --user httpie
Successfully installed httpie-3.2.4
📦[{user}@dev ~]$ exit
```

`-y` answers yes to the install prompt. `pip install --user` puts a Python
tool under your home, which works inside the box because the box's Python is
not the host's. On the host, `pip install` refuses: Fedora marks its system
Python as externally managed, and `/usr` is read-only anyway, so Python
projects belong in a virtualenv (`python3 -m venv .venv` then `source
.venv/bin/activate`) or in a box.

A tool that lives in a box can be made to look native. `distrobox-export
--bin` puts a wrapper on your host PATH that runs the box's command;
`distrobox-export --app` puts a container application in the GNOME launcher.
Both are run from inside the box.

```
📦[{user}@dev ~]$ distrobox-export --bin /usr/bin/rg --export-path {home}/.local/bin
📦[{user}@dev ~]$ exit
{user}@{host}:~$ rg --version
ripgrep 14.1.1
```

`--export-path` says where the wrapper goes; `~/.local/bin` is on your PATH on
Pridwen. From then on `rg` on the host quietly runs inside `dev`. This is where
Python virtualenvs, compilers, and one-off command-line tools belong, kept away
from the host so that nothing you try there can break the base.

## When it goes wrong

`error: No remote refs found similar to 'loupe'` means `flatpak install` was
given a plain word. Run `flatpak search loupe` and use the Application ID.

`error: externally-managed-environment` from `pip install` on the host is
Fedora protecting its own Python. Make a virtualenv, use `pipx install` for a
command-line tool, or install inside a Distrobox.

`Error: no such container: dev` from `distrobox enter` means the box was never
created on this machine or was removed. `distrobox list` shows what exists;
`distrobox create -n dev -i fedora:43` makes it. `pridwen why` explains the
last of these you saw.

## Try it

1. Run `flatpak search loupe`, copy the Application ID, and install it with `flatpak install flathub` and that id.
2. Launch it from the GNOME menu, then from a terminal with `flatpak run` and the id.
3. Run `flatpak list --app` and `flatpak list --runtime` and say which is which.
4. Run `distrobox enter dev` and install `ripgrep` with the box's own `dnf`.
5. Inside the box, run `distrobox-export --bin /usr/bin/rg --export-path ~/.local/bin`, `exit`, and run `rg --version` on the host.
6. On the host, run `pip install httpie`, read the `externally-managed-environment` message, and make a virtualenv instead.

## Remember

- Flatpak is for desktop apps, named by reverse-DNS id, from Flathub, with no `sudo`.
- Distrobox is a writable Linux in a container sharing your home; `dnf`, `pip`, and `make` work there as normal.
- `distrobox-export` makes a box's tool or app appear on the host without touching the base image.
