# Distrobox and daily work

Podman is the engine. Distrobox is the comfortable seat on top of it for everyday work. A Distrobox is a container that shares your home directory, your user account, and your terminal with the host, so it feels like a second Linux installed alongside Pridwen. Inside it, the distribution's own package manager works normally: `dnf install` on a Fedora box, `apt install` on a Debian one. Nothing you install there touches the host image.

This is how mutable tooling lives on an immutable host. Pridwen's `/usr` is read-only and replaced whole at each upgrade, and layering packages onto it with `rpm-ostree install` slows every update. Compilers, language toolchains, one-off command-line tools, and anything a tutorial says to `dnf install` go in a box instead. The host stays clean and can always roll back, and the box can be thrown away and rebuilt in a minute. On a job the same idea appears as a "dev container": the tools travel with the project, not with the machine.

## Words you'll meet

- **Distrobox**: a tool that creates and enters Podman containers set up to share your home and act like a second distribution.
- **box**: one such container, made with `distrobox create` and used with `distrobox enter`.
- **package manager**: the program that installs software from a distribution's repositories; `dnf` on Fedora, `apt` on Debian and Ubuntu.
- **layering**: adding a package to the host image with `rpm-ostree install`; works, but every layered package slows `bootc upgrade`.
- **export**: making a program inside a box appear on the host, as a menu entry or a command.
- **privileged port**: a network port below 1024, which only root may listen on.

## How it works

Create a box from the Fedora image. `-n` names it and `-i` picks the image.

```
{user}@{host}:~$ distrobox create -n dev -i fedora:43
Creating 'dev' using image fedora:43	 [ OK ]
Distrobox 'dev' successfully created.
To enter, run:

distrobox enter dev
```

The first `enter` takes a minute while Distrobox installs its integration inside the box; every later `enter` is instant. The prompt changes to show the box name in place of the host name, which is how you tell where you are.

```
{user}@{host}:~$ distrobox enter dev
Starting container...                   	 [ OK ]
Installing basic packages...            	 [ OK ]
Setting up devpts mounts...             	 [ OK ]
Setting up read-only mounts...          	 [ OK ]
Setting up read-write mounts...         	 [ OK ]
Setting up host's sockets integration...	 [ OK ]
Integrating host's themes, icons, fonts...	 [ OK ]
Setting up package manager exceptions...	 [ OK ]
Setting up dpkg exceptions...           	 [ OK ]
Setting up sudo...                      	 [ OK ]
Setting up user's group list...         	 [ OK ]
Setting up user home...                 	 [ OK ]
Ensuring user's access...               	 [ OK ]

Container Setup Complete!
{user}@dev:~$ pwd
{home}
{user}@dev:~$ sudo dnf install -y ripgrep
{user}@dev:~$ rg --version
ripgrep 14.1.0
{user}@dev:~$ exit
{user}@{host}:~$ rg --version
bash: rg: command not found
```

`pwd` inside the box prints your real home directory: the box shares it, so a file you edit there is the same file on the host. `sudo dnf install -y ripgrep` installs a tool with the box's own package manager (`-y` answers yes to the confirmation), and `sudo` inside the box asks for your normal password. `rg` works inside. After `exit`, back on the host, `rg` is not found, because the program lives in the box's filesystem, not the host's. That is the split working as designed.

To use a box's tool from the host, export it. `distrobox-export` runs inside the box, and `--bin` takes the absolute path of the program there; it writes a small wrapper into `{home}/.local/bin`, which is on your host PATH.

```
{user}@{host}:~$ distrobox enter dev
{user}@dev:~$ distrobox-export --bin /usr/bin/rg
{user}@dev:~$ exit
{user}@{host}:~$ which rg
{home}/.local/bin/rg
{user}@{host}:~$ rg --version
ripgrep 14.1.0
```

`which rg` shows the wrapper, and running it starts the box if needed and runs the real `rg` inside, on the same files. `distrobox-export --app codium` does the same for a graphical program, adding it to the GNOME menu. A box can also run a network service. Rootless containers cannot listen on ports below 1024, so map a service to a high port such as 8080 rather than 80.

```
{user}@{host}:~$ distrobox list
ID           | NAME  | STATUS          | IMAGE
2f1a9c4b7e5d | dev   | Up 12 minutes   | registry.fedoraproject.org/fedora:43
{user}@{host}:~$ distrobox stop dev
{user}@{host}:~$ distrobox rm dev
```

`list` shows every box and whether it is running; `stop` stops one and `rm` deletes it. Deleting a box removes what you installed in it, but not your home directory, so the files are safe. That is why a box is cheap to rebuild and the host is never at risk.

## When it goes wrong

`Error: distrobox named 'dev' already exists.` from `distrobox create` means you already have one by that name. Use `distrobox enter dev`, or pick another name, or `distrobox rm dev` first.

`bash: rg: command not found` on the host after installing in a box is not a failure. The program is inside the box. Enter it, run `distrobox-export --bin /usr/bin/rg`, and try again on the host.

`Error: rootlessport cannot expose privileged port 80, you can add 'net.ipv4.ip_unprivileged_port_start=80' to /etc/sysctl.conf (currently 1024), or choose a larger port number (>= 1024)` means a rootless container tried to listen on a low port. Use `8080` instead. `pridwen why` translates any of these, and `pridwen explain distrobox` walks through the subcommands.

## Try it

1. Run `distrobox create -n dev -i fedora:43` and read the confirmation lines.
2. Run `distrobox enter dev`, wait for `Container Setup Complete!`, and run `pwd` to confirm you are in your own home.
3. Inside, run `sudo dnf install -y ripgrep`, then `rg --version`. Exit and confirm `rg` is not found on the host.
4. Enter again, run `distrobox-export --bin /usr/bin/rg`, exit, and run `which rg` and `rg --version` on the host.
5. Run `distrobox list` and read the `STATUS` column.
6. Explain in one sentence why a compiler belongs in a box rather than layered onto the host with `rpm-ostree install`.

## Remember

- A Distrobox shares your home and user with the host; inside it the box's own `dnf` or `apt` works, and nothing touches the host image.
- `distrobox create -n name -i image`, `distrobox enter name`, and from inside `distrobox-export --bin /usr/bin/tool` to reach it from the host.
- Mutable tooling goes in a box so the host stays clean and rollback-able; layering is the exception, not the rule.
