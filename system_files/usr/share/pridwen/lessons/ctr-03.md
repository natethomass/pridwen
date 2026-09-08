# Volumes, labels, and services

A container's filesystem is disposable: when the container is removed, whatever it wrote is gone. That is a feature for a throwaway shell and a problem for a database. To keep data you attach storage from outside, either a host directory or a volume Podman manages. On Pridwen there is one more step most tutorials skip, because SELinux is enforcing here: the storage has to carry a label the container is allowed to read, or the kernel refuses, and the refusal looks like an ordinary permission error.

The second half of this lesson is running a container as a service that starts at boot and survives a reboot, the way `docker-compose` is used elsewhere. Pridwen's way is a Quadlet, a short file that systemd turns into a real unit, so the container gets the same journal, status, and dependency handling as every other service on the machine. You already know that a service unit has `systemctl status` and a journal; this lesson gives a container those things.

## Words you'll meet

- **bind mount**: a host directory made visible inside a container at a path you choose, with `-v host:container`.
- **volume**: storage that Podman creates and manages for you, named rather than pathed, with `podman volume create`.
- **SELinux label**: the security context every file carries; a process may only touch files whose label its policy allows.
- **relabel**: changing a file's label; `:Z` and `:z` on a mount ask Podman to do it.
- **Quadlet**: a `.container` file that describes a container in systemd's own format; systemd generates a service unit from it.
- **generator**: the part of systemd that reads Quadlet files at `daemon-reload` and writes the units.
- **transient**: created at runtime and not stored; a generated unit is transient in this sense.

## How it works

Start with a bind mount and the label. Make a directory on the host, then mount it into a container with `-v ./data:/data`, and add `:Z` so Podman relabels it privately for this container.

```
{user}@{host}:~$ mkdir -p {home}/data && echo hello > {home}/data/note.txt
{user}@{host}:~$ podman run --rm -v {home}/data:/data:Z fedora:43 ls -l /data
total 4
-rw-r--r--. 1 root root 6 Sep  7 10:05 note.txt
```

The container ran `ls -l /data` and saw the file, owned by root because your uid maps to root inside. The `:Z` (capital) gave the directory a label unique to this container. `:z` (lower case) gives it a shared label, so several containers can use the same directory. Now the same command without the suffix.

```
{user}@{host}:~$ podman run --rm -v {home}/data:/data fedora:43 ls -l /data
ls: cannot open directory '/data': Permission denied
```

Nothing about ownership changed, yet the container is refused. SELinux confines containers to files labelled for containers, and your home directory's files are labelled for you, so the kernel denied the read. Pridwen keeps SELinux enforcing on purpose: if a container is compromised, this same rule stops it reading the rest of your home. `sudo ausearch -m AVC -ts recent` shows the denial as an `avc: denied { read }` record naming `container_t` and `user_home_t`, which is the audit system saying exactly what happened.

Managed volumes avoid the question, because Podman creates them already labelled for containers.

```
{user}@{host}:~$ podman volume create appdata
appdata
{user}@{host}:~$ podman run --rm -v appdata:/var/lib/app fedora:43 sh -c 'echo saved > /var/lib/app/state'
{user}@{host}:~$ podman run --rm -v appdata:/var/lib/app fedora:43 cat /var/lib/app/state
saved
{user}@{host}:~$ podman volume inspect appdata | grep Mountpoint
          "Mountpoint": "{home}/.local/share/containers/storage/volumes/appdata/_data",
```

The first container wrote a file, exited and was removed, and the second container read it: the volume outlived both. `volume inspect` shows where the data really lives, under your own container storage, so `podman volume ls` and `podman volume rm` are how you manage it, and a home backup includes it.

Now the service. A Quadlet lives in `{home}/.config/containers/systemd/` for your user, or `/etc/containers/systemd/` for the system, and its name becomes the service name.

```
{user}@{host}:~$ mkdir -p {home}/.config/containers/systemd
{user}@{host}:~$ cat > {home}/.config/containers/systemd/web.container <<'EOF'
[Unit]
Description=A small web server

[Container]
Image=docker.io/library/nginx:alpine
PublishPort=8080:80
Volume=appdata:/usr/share/nginx/html:Z

[Install]
WantedBy=default.target
EOF
{user}@{host}:~$ systemctl --user daemon-reload
{user}@{host}:~$ systemctl --user start web.service
{user}@{host}:~$ systemctl --user status web.service | head -3
* web.service - A small web server
     Loaded: loaded ({home}/.config/containers/systemd/web.container; generated)
     Active: active (running) since Mon 2026-09-07 10:12:33 UTC; 4s ago
```

`[Container]` is the Quadlet section: `Image` is the image, `PublishPort=8080:80` maps host port 8080 to the container's 80 (a high host port, because rootless containers cannot take 80), and `Volume` mounts the volume with the label suffix. `WantedBy=default.target` makes it start at login. `daemon-reload` runs the generator, which writes `web.service`; the `Loaded` line says `generated`, and `Active: active (running)` means the container is up. `journalctl --user -u web.service` shows its log lines like any service. Because it is a generated unit you do not `enable` it: the `[Install]` section in the `.container` file does that job, and the unit is regenerated on every reload.

## When it goes wrong

`ls: cannot open directory '/data': Permission denied` inside a container, on a directory you can plainly read on the host, is the SELinux label. Add `:Z` to the `-v` argument, or use a managed volume. `pridwen why` will point at the denial in the audit log.

`Failed to start web.service: Unit web.service not found.` means the generator did not produce the unit. Either you have not run `systemctl --user daemon-reload` since writing the file, or the file has an error. `/usr/libexec/podman/quadlet -dryrun -user` prints the units it would generate and names any line it cannot parse.

`Error: statfs {home}/data: no such file or directory` from `podman run -v` means the host side of a bind mount does not exist. Podman does not create it for you; `mkdir -p` it first. `pridwen explain podman` lists the `-v` suffixes.

## Try it

1. Create `{home}/data` with a file in it, then run the `ls -l /data` container with `:Z` and expect the file listed.
2. Run it again without `:Z` and expect `Permission denied`. Run `sudo ausearch -m AVC -ts recent | tail -2` and find `container_t`.
3. Create a volume with `podman volume create appdata`, write a file into it from one container, and read it back from another.
4. Write `web.container` as above, run `systemctl --user daemon-reload`, then `start web.service`, and expect `active (running)` in status.
5. Run `curl -s http://localhost:8080/ | head -3` (`-s` hides the progress meter) and expect HTML from the container.
6. Run `systemctl --user stop web.service`, then move the `.container` file away, reload, and confirm `web.service` is gone from `systemctl --user list-units --all`.

## Remember

- A bind mount on Pridwen needs `:Z` (private) or `:z` (shared) or SELinux denies it; managed volumes from `podman volume create` are labelled already.
- A container's own filesystem is disposable; anything worth keeping goes in a volume or a mount.
- A Quadlet `.container` file plus `systemctl --user daemon-reload` turns a container into a real service with status and a journal.
