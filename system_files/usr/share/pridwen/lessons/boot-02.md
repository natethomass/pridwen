# Deployments and rollback

On a bootc system, what you boot into is a deployment, a specific image staged on
disk. The boot menu offers the current one and the previous one, so a bad update
is never more than a reboot away from undone. This is the safety net that makes
frequent updates comfortable.

`rpm-ostree status` and `bootc status` list the deployments, marking which is
booted and which is set for next boot. Each shows the image reference and a
digest, the exact bytes it came from. The kernel came with the image, so a new
kernel arrives only through an update and a reboot, never on its own.

```
$ bootc status
$ rpm-ostree status
State: idle
Deployments:
* ghcr.io/natethomass/pridwen:latest (booted)
  ghcr.io/natethomass/pridwen:latest (rollback)
```

Rolling back is `sudo rpm-ostree rollback` (or `bootc rollback`) plus a reboot,
which puts the previous deployment first in the boot order. If you have a
deployment you never want cleaned up, `sudo ostree admin pin N` keeps it, and
`--unpin` releases it. Between the rollback entry and a pin, you always have a
known-good target to return to.

## Try it

1. Run `bootc status` and identify the booted and rollback deployments.
2. Read the image digest and connect it to a build from CI.
3. Describe the exact steps to undo an update that went wrong.
4. Run `uname -r` and explain when that kernel version would change.
