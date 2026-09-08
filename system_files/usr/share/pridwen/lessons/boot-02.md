# Deployments and rollback

On a bootc system, what you boot into is a deployment: one complete copy of
the operating system, unpacked from a container image and staged on disk.
Pridwen's image is `ghcr.io/natethomass/pridwen:latest`, built by CI and
signed. An update does not change files under you; it stages a second
deployment and switches to it at the next boot. The boot menu keeps the
current one and the previous one, so a bad update is never more than a
reboot away from undone.

This is the safety net that makes frequent updates comfortable, and it is the
core idea behind image-based systems on real jobs: servers that run the same
bytes as the tested image, and roll back as a unit when something breaks.
Learning to read the deployment list is learning to answer "exactly which
version is this machine running".

## Words you'll meet

- **image**: the container image the whole operating system is built as; `/usr` comes from it read-only.
- **deployment**: one image unpacked on disk and bootable; there are usually two.
- **booted**: the deployment you are running now.
- **staged**: a new deployment written to disk and set to boot next, but not yet used.
- **rollback**: the previous deployment, kept so you can boot it again.
- **digest**: the `sha256:` checksum that names the exact bytes of an image; two images with the same digest are identical.
- **pin**: marking a deployment to be kept through future updates instead of being cleaned up.
- **ostree**: the storage layer under bootc that keeps deployments as trees of files and shares identical files between them.

## How it works

`bootc status` is the first thing to run.

```
{user}@{host}:~$ sudo bootc status
No staged image present
Booted image: ghcr.io/natethomass/pridwen:latest
        Digest: sha256:d6c123f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
       Version: 0.3.0-m2 (2026-09-07 06:41:12 UTC)
Rollback image: ghcr.io/natethomass/pridwen:latest
        Digest: sha256:470f6941b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9
       Version: 0.2.0-m1 (2026-09-04 19:03:40 UTC)
```

The first line says no update is waiting. `Booted image` is the deployment
you are in: the image reference, its digest, and the version stamped at build
time. `Rollback image` is the previous one, still on disk. Both point at the
same `:latest` tag but the digests differ, and the digest is what matters:
it is the exact build from CI. After `sudo bootc upgrade` a third block,
`Staged image`, appears until you reboot.

`rpm-ostree status` shows the same list in the older format many guides use.

```
{user}@{host}:~$ rpm-ostree status
State: idle
Deployments:
* ostree-image-signed:docker://ghcr.io/natethomass/pridwen:latest
                   Digest: sha256:d6c123f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
                  Version: 0.3.0-m2 (2026-09-07T06:41:12Z)

  ostree-image-signed:docker://ghcr.io/natethomass/pridwen:latest
                   Digest: sha256:470f6941b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9
                  Version: 0.2.0-m1 (2026-09-04T19:03:40Z)
```

The `*` marks the booted deployment. The first entry in the list is what
boots next; when they are the same, nothing is pending. `State: idle` means
no operation is running. `ostree-image-signed` says the image's signature
was checked against Pridwen's public key before it was accepted.

The kernel is part of the image. A new kernel arrives only inside a new
deployment, applied at a reboot, never on its own. `uname -r` prints the
running kernel version, and it changes only when the booted deployment does.

```
{user}@{host}:~$ uname -r
6.17.4-200.fc43.x86_64
```

Rolling back is one command plus a reboot. It puts the previous deployment
first in the boot order and keeps the one you were in as the new rollback,
so you can go forward again.

```
{user}@{host}:~$ sudo bootc rollback
Next boot: rollback deployment
{user}@{host}:~$ systemctl reboot
```

`sudo rpm-ostree rollback` does the same. After the reboot `bootc status`
shows the older version as `Booted image`. Your files are untouched either
way: `/var` and `/var/home` are shared by every deployment and never part of
the swap, and `/etc` is merged three ways so your local edits carry across.

If a deployment is known good and you never want it cleaned up, pin it. `0`
is the first deployment in the list, `1` the second.

```
{user}@{host}:~$ sudo ostree admin pin 1
Deployment 1 is now pinned
```

`sudo ostree admin pin --unpin 1` releases it. Between the automatic
rollback entry and a pin, there is always a known-good target to return to.

## When it goes wrong

`error: No rollback deployment found` from `rpm-ostree rollback` means
there is only one deployment on disk, usually right after a fresh install
before the first upgrade. Nothing is wrong; there is simply nothing older to
go back to yet.

`error: Transaction in progress: upgrade` means another `rpm-ostree` or
`bootc` operation is still running. Wait for it, or watch it with
`rpm-ostree status` until `State` returns to `idle`.

`bootc status` answering with a permission error means it needs root on this
version; run `sudo bootc status`. The Coach prints the deployment commands
under any failed `bootc` or `rpm-ostree` line, and `pridwen why` restates how
staged, booted, and rollback fit together. `pridwen explain bootc` annotates
the subcommands.

## Try it

1. Type `sudo bootc status` and identify the `Booted image` and `Rollback image` blocks. Note the two versions.
2. Copy the first twelve characters of the booted digest and compare them with the rollback digest; they should differ.
3. Type `rpm-ostree status` and find the `*` that marks the booted deployment.
4. Type `uname -r` and explain when that number would change.
5. Write down the exact two commands that would undo an update that went wrong, without running them.
6. Type `pridwen explain bootc` and read what `upgrade`, `rollback`, and `status` each do.

## Remember

- A deployment is one image unpacked on disk; `bootc status` shows booted, staged, and rollback with their digests.
- `sudo bootc rollback` then reboot boots the previous deployment; `/var`, home, and merged `/etc` are untouched.
- The kernel comes with the image and changes only with a deployment; `ostree admin pin` keeps a known-good one.
