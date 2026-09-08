# Software on an image-based system

Pridwen does not install software the way a traditional Fedora does. On a
traditional system, a package manager called `dnf` downloads packages and
writes their files into `/usr`, one at a time, over years, until no two
machines are quite alike. On Pridwen the whole base system, everything under
`/usr`, is one container image built in one place, and it is mounted read-only
on your machine. `dnf` has nowhere to write, so it is not the tool here. That
is not a limitation you work around; it is the design.

This matters because a base that never accumulates one-off changes is a base
that can be replaced whole and rolled back whole. Every Pridwen machine runs
the same tested image, an update is one new image, and a bad update is one
reboot away from undone. In return you learn to ask a question that
traditional systems never made you ask: what kind of software is this, and
which layer does it belong in.

## Words you'll meet

- **image**: a complete, prebuilt copy of the operating system, made once and shipped to many machines.
- **immutable**: cannot be changed in place; here, `/usr` is read-only while the system runs.
- **bootc**: the tool that fetches a new image and switches the machine to it at the next boot.
- **deployment**: one image installed on the disk; the booted one, a staged one, and a rollback one can coexist.
- **Flatpak**: a format for desktop applications that bundles what they need and runs them in a sandbox.
- **Flathub**: the public Flatpak store; the only source Pridwen has configured.
- **Distrobox**: a container with a full mutable Linux inside that shares your home directory.
- **layering**: adding an RPM package on top of the image with `rpm-ostree install`; the last resort.

## How it works

Start by seeing the image you are running. `rpm-ostree status` lists the
deployments on this machine.

```
{user}@{host}:~$ rpm-ostree status
State: idle
Deployments:
● ostree-image-signed:docker://ghcr.io/natethomass/pridwen:latest
                   Digest: sha256:9f3a1c…e2b7
                  Version: 0.3.0-m2 (2026-09-07T08:12:04Z)
```

The dot marks the booted deployment. The long line is the image name: it lives
at `ghcr.io/natethomass/pridwen`, and `latest` is the tag your machine follows.
Digest is the exact build, a checksum of its contents, so two machines with the
same digest are byte-for-byte the same. Version is the human-readable label.
Because this is the whole base, there is no package to install "into" it.

Now try the reflex that every tutorial teaches, and read what happens.

```
{user}@{host}:~$ sudo dnf install ripgrep
sudo: dnf: command not found
```

`dnf` is not even present, because it could not do anything useful. Instead
there are three clean places for software, chosen by what the software is.

Desktop applications come from Flatpak. A Flatpak bundles the libraries an app
needs and runs it in a sandbox, a fenced-off space with limited access to your
files and devices. Apps are named by a reverse-DNS id, a name like
`org.inkscape.Inkscape` built from the project's web domain backwards, and
they come from Flathub, the only remote Pridwen configures. No root is needed.

```
{user}@{host}:~$ flatpak search inkscape
Name        Description                 Application ID          Version   Branch  Remotes
Inkscape    Vector Graphics Editor      org.inkscape.Inkscape   1.4.2     stable  flathub
```

Read the Application ID column: that id, not the word "inkscape", is what
`flatpak install` wants.

Command-line tools and development environments live in a Distrobox. It is a
container, an isolated copy of another Linux, running on the same kernel as
your host, and it shares your home directory, so files you edit inside it are
the same files. Inside, `dnf` works normally because the container's `/usr` is
writable. `create` makes one, `-n` names it, `-i` picks the image to build it
from, and `enter` drops you into a shell inside it.

```
{user}@{host}:~$ distrobox create -n dev -i fedora:43
Creating 'dev' using image fedora:43
Distrobox 'dev' successfully created.
{user}@{host}:~$ distrobox enter dev
📦[{user}@dev ~]$ sudo dnf install ripgrep
```

The prompt changes to show you are in `dev`. The `sudo` inside asks for your
own password, and anything you install here stays inside the box; the host
image is untouched, and if the box ever breaks, `distrobox rm dev` and start
again. This is the right home for compilers, Python environments, and any
tool you want to try.

Anything that must be part of the host itself, a kernel module, a driver, a
system service, is layered onto the image with `sudo rpm-ostree install name`.
Layering builds a new deployment with the package added, and it takes effect
after a reboot. It is the last resort, because every layered package must be
re-applied on top of each new image, which slows updates and moves you away
from the tested base. Most days you reach for Flatpak or Distrobox and never
touch the host image at all.

The mental shift is from "install a package into a mutable system" to "choose
the right layer". A graphical editor is a Flatpak. A command-line tool is a
Distrobox. A driver is a layer. `pridwen explain rpm-ostree` and `pridwen
explain flatpak` annotate the commands as you meet them.

## When it goes wrong

`sudo: dnf: command not found` on the host is the immutable model, not a
broken install. Ask which layer the software belongs in and use `flatpak`,
`distrobox`, or `rpm-ostree` instead; `pridwen why` prints the same choice.

`error: No remote refs found similar to 'inkscape'` from `flatpak install`
means a plain word was given where an application id belongs. Run `flatpak
search inkscape` and copy the Application ID column.

`Error: creating container storage: ... no space left on device` from
`distrobox create` means `/var`, where container images live, is full. `podman
system prune` removes unused images, and the Storage node covers `df`.

## Try it

1. Run `rpm-ostree status` and read the image name, the Version, and the first few characters of the Digest.
2. Run `sudo dnf install ripgrep` on the host and read the `command not found` line as the system explaining itself.
3. Run `flatpak search` for an app you use and read its reverse-DNS Application ID.
4. Run `distrobox create -n dev -i fedora:43`, then `distrobox enter dev`, and `sudo dnf install ripgrep` inside.
5. Type `exit` to leave the box and run `rg --version` on the host; expect `command not found`, because the tool lives in the box.
6. Say which of the three layers you would use for a GUI editor, a compiler, and a Wi-Fi driver, and why.

## Remember

- The base is a read-only image; `dnf` is not on the host because it would have nowhere to write.
- Desktop apps are Flatpaks from Flathub; CLI tools go in a Distrobox; only host-level things are layered with `rpm-ostree install`.
- Choosing the right layer is what keeps the base identical to the tested image and lets it roll back whole.
