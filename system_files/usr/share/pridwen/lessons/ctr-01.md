# Podman, not Docker

A container is a process, or a small group of them, running on your kernel but seeing its own private copy of a filesystem, its own process list, and its own network. It is not a virtual machine: there is no second kernel, which is why a container starts in a second and a virtual machine takes a minute. Containers are how most software is shipped and run on servers today, and on Pridwen they are also how you get software the immutable host does not carry.

Pridwen ships Podman rather than Docker. The commands are the same, `podman run`, `podman ps`, `podman build`, and it pulls the same images from the same registries, so anything written for Docker works. What differs is underneath, and the difference is a security decision: Podman runs a container as you, with no background service, so a container that goes wrong can only do what your account can do. You already know from the packages node that `/usr` is read-only and that mutable tooling lives elsewhere; this node is where that elsewhere begins.

## Words you'll meet

- **container**: an isolated process with its own filesystem view, sharing the host's kernel.
- **image**: the read-only filesystem a container starts from, downloaded from a registry.
- **registry**: a server that stores images, such as `registry.fedoraproject.org` or `docker.io`.
- **Podman**: the container engine on Pridwen, a drop-in for the `docker` command.
- **rootless**: running the container as your ordinary user rather than as root.
- **daemonless**: no always-on background service; each `podman` command does its own work and exits.
- **uid**: the number that identifies a user to the kernel; yours is probably `1000`, root's is `0`.
- **subordinate uids**: a range of extra uids reserved for your account, which a rootless container uses for the users inside it.

## How it works

Start a throwaway container from the Fedora image. `run` creates and starts a container, `--rm` removes it when it exits, `-it` gives it an interactive terminal (`-i` keeps input open, `-t` allocates a terminal), `fedora:43` is the image and tag, and `bash` is the command to run inside.

```
{user}@{host}:~$ podman run --rm -it fedora:43 bash
Resolved "fedora" as an alias (/etc/containers/registries.conf.d/000-shortnames.conf)
Trying to pull registry.fedoraproject.org/fedora:43...
Getting image source signatures
Copying blob 4a1e2b3c9d8f done
Copying config 7b2c9e0a1d done
Writing manifest to image destination
[root@2f1a9c4b7e5d /]# id
uid=0(root) gid=0(root) groups=0(root)
[root@2f1a9c4b7e5d /]# exit
{user}@{host}:~$
```

The first lines are the pull: the short name `fedora` was resolved to the Fedora registry, and the image's layers (blobs) were downloaded once and cached. Then the prompt changes to `[root@2f1a9c4b7e5d /]#`: you are inside, the random hostname is the container id, and `id` says you are root there. Typing `exit` ends bash, which ends the container, and `--rm` deletes it.

Root inside is not root outside, and you can see the mapping. `podman unshare` runs a command inside the user namespace Podman uses, and `/proc/self/uid_map` shows how uids are translated.

```
{user}@{host}:~$ podman unshare cat /proc/self/uid_map
         0       1000          1
         1     100000      65536
```

Each line is a range: uid inside, uid outside, how many. The first says uid `0` inside is your own uid `1000` outside. The second says uids `1` to `65536` inside are the subordinate range starting at `100000` outside, which is reserved for you in `/etc/subuid`. So a process that is "root" in the container is really you, and a service user inside is really uid `100000` and up, an account that owns nothing on the host. Even if a program inside the container breaks out of its filesystem, the kernel sees an ordinary user.

Containers you run without `--rm` stay around after they stop. `ps` lists running containers and `-a` includes stopped ones.

```
{user}@{host}:~$ podman run -it fedora:43 bash -c 'echo hello'
hello
{user}@{host}:~$ podman ps -a
CONTAINER ID  IMAGE                                   COMMAND         CREATED        STATUS                    PORTS  NAMES
9e8d7c6b5a4f  registry.fedoraproject.org/fedora:43    bash -c echo...  8 seconds ago  Exited (0) 7 seconds ago         eager_wright
```

Read the columns. `CONTAINER ID` is the short id, `IMAGE` is the full image name, `COMMAND` is what it ran, `STATUS` says it exited with code `0` seven seconds ago, and `NAMES` is a random name Podman gave it because you did not pass `--name`. `podman rm eager_wright` deletes it; `podman start -ai eager_wright` would run it again with the same filesystem.

Images live in a local store. `pull` downloads one without running it, and `images` lists what you have.

```
{user}@{host}:~$ podman pull docker.io/library/alpine:3.20
{user}@{host}:~$ podman images
REPOSITORY                            TAG         IMAGE ID      CREATED       SIZE
registry.fedoraproject.org/fedora     43          7b2c9e0a1d3f  2 weeks ago   170 MB
docker.io/library/alpine              3.20        1d34ffeaf190  3 months ago  8.1 MB
```

Writing the registry into the name, `docker.io/library/alpine`, is safer than the short `alpine`, because a short name is looked up across several registries and could match the wrong one.

Some tools insist on talking to a Docker socket. `systemctl --user enable --now podman.socket` provides a compatible one at `$XDG_RUNTIME_DIR/podman/podman.sock`, still rootless, but most of the time you will not need it.

## When it goes wrong

`bash: docker: command not found` is exit 127. There is no Docker here; type `podman` in its place. Every subcommand you know works the same way.

`Error: initializing source docker://registry.fedoraproject.org/fedora:99: reading manifest 99 in registry.fedoraproject.org/fedora: manifest unknown` means the tag does not exist. Tags are versions; check the registry's page for the ones it offers, and use `fedora:43` or `fedora:latest`.

`Error: short-name "myimage" did not resolve to an alias and no unqualified-search registries are defined` means Podman could not tell which registry you meant. Give the full name, such as `docker.io/library/myimage`. `pridwen why` explains any of these after the fact, and `pridwen explain podman` walks through the flags used here.

## Try it

1. Run `podman run --rm -it fedora:43 bash`, then `id` inside, and expect `uid=0(root)`. Type `exit`.
2. Run `podman ps -a` and expect an empty list, because `--rm` cleaned up.
3. Run `podman run -it fedora:43 bash -c 'echo hello'` without `--rm`, then `podman ps -a`, and find it with `Exited (0)`. Remove it with `podman rm` and its name.
4. Run `podman unshare cat /proc/self/uid_map` and say which host uid a container's root really is.
5. Run `podman pull docker.io/library/alpine:3.20` and then `podman images` to see both images and their sizes.
6. Run `podman run --rm fedora:99 true` and read the `manifest unknown` error.

## Remember

- `podman` takes the same commands as `docker`: `run`, `ps -a`, `images`, `pull`, `rm`.
- Rootless means root inside the container is your own uid outside, and other users inside map to a subordinate range that owns nothing on the host.
- `--rm` cleans up on exit; without it, stopped containers stay in `podman ps -a` until you remove them.
