# Deployments, layering, and updates

An image-based system does not have a package database that changes over time.
It has deployments: whole images, one of which is booted. `rpm-ostree status`
and `bootc status` list them, usually the running image, anything staged for the
next boot, and the previous image kept for rollback.

Updating fetches a new image and stages it; it does not change the running
system until you reboot. Because the old deployment stays on disk, a bad update
is one reboot away from undone. Layering adds packages on top of the image, and
they also arrive at the next boot unless you ask for `--apply-live`.

```
$ sudo bootc upgrade
$ bootc status
$ sudo rpm-ostree install tmux
$ rpm-ostree status   # tmux shows as a layered package, pending reboot
```

This is the model behind Pridwen's whole update story. CI builds a new image and
pushes it to `ghcr.io/natethomass/pridwen`; your machine pulls it, stages it, and
keeps the one you are on as a fallback. Rolling back is `rpm-ostree rollback`
plus a reboot, and pinning a known-good deployment with `ostree admin pin` keeps
it from being cleaned up.

## Try it

1. Run `rpm-ostree status` and identify the booted and rollback entries.
2. Run `sudo bootc upgrade` and read whether a new image was staged.
3. Layer a small package and find it listed as pending in `rpm-ostree status`.
4. Describe what `rpm-ostree rollback` plus a reboot would do.
