# Podman, not Docker

Pridwen ships Podman for containers. Its command line matches Docker closely, so
`podman run`, `podman ps` and `podman build` all behave as you would expect, and
it reads the same images. The difference is underneath: Podman is rootless and
daemonless.

Rootless means a container runs as your user, mapped into a range of subordinate
uids, so root inside the container is not root on the host. Daemonless means
there is no background service to start or secure; each `podman` command runs on
its own. Together these confine a container to your account rather than giving it
a path to host root.

```
$ podman run --rm -it fedora:43 bash
[root@ctr /]# id
uid=0(root) ...
[root@ctr /]# exit
$ podman ps -a
```

Inside the container you may be root, but on the host that maps to your
unprivileged range, which you can see with `podman unshare cat /proc/self/uid_map`.
`--rm` cleans up the container on exit; without it, `podman ps -a` shows it
stopped, ready to reuse. If a tool insists on a Docker socket, `systemctl --user
enable --now podman.socket` provides a compatible one, but most of the time you
will not need it. The rootless model is the security reason Pridwen chose Podman.

## Try it

1. Run `podman run --rm -it fedora:43 bash` and check `id` inside it.
2. Exit and list the container history with `podman ps -a`.
3. Pull an image with `podman pull` and list images with `podman images`.
4. Explain what rootless means for a container that is compromised.
