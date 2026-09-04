# Volumes, labels, and services

Containers are ephemeral by design; to keep data you attach storage, and on an
SELinux system you have to label it so the container may read it. Getting the
mount right is the detail that trips people up.

A bind mount maps a host directory into the container with `-v host:container`.
Without a label suffix, SELinux may deny access, and it looks like a plain
permission error inside. Add `:Z` to relabel the source privately for this
container, or `:z` to share it among containers. Managed volumes created with
`podman volume create` are already labelled.

```
$ podman run --rm -v ./data:/data:Z fedora:43 ls /data
$ podman volume create appdata
$ podman run --rm -v appdata:/var/lib/app fedora:43 true
```

For a container that should run like a service and survive reboots, the Pridwen
way is a Quadlet: a `.container` file under `/etc/containers/systemd/` (or
`~/.config/containers/systemd/`) that systemd turns into a unit at boot. After
writing or editing one, `systemctl daemon-reload` regenerates the unit. This
replaces `docker-compose` for persistent services, giving you the same journal,
status and dependency handling as any other systemd unit.

## Try it

1. Run a container with a `:Z` bind mount and confirm it can read the directory.
2. Repeat without the `:Z` on an enforcing host and read the denial.
3. Create a named volume and mount it into a container.
4. Write a minimal Quadlet `.container` file and reload systemd to generate its unit.
