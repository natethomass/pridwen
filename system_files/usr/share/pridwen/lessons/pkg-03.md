# Deployments, layering, and updates

An image-based system does not have a package database that slowly changes
over time. It has deployments: whole copies of the operating system image
installed side by side on the disk, one of which is booted. On Pridwen the tool
that manages them is `bootc`, with `rpm-ostree` alongside it for the older,
package-shaped tasks. Updating means fetching a new image and adding it as a
deployment; nothing about the running system changes until you reboot.

This matters because it is the whole reason Pridwen can be hardened and
still be safe to update: every update is one tested image, the one you are on
stays on disk, and a bad update is one reboot away from undone. At work this
is how fleets of servers and edge devices are increasingly run, and knowing
the words deployment, staged, and rollback puts you ahead of most first-year
admins.

## Words you'll meet

- **deployment**: one complete image installed on disk and bootable; several can coexist.
- **booted**: the deployment you are running right now, marked with a dot in status output.
- **staged**: a deployment that has been downloaded and prepared and will be booted next time.
- **rollback**: the previous deployment, kept so you can boot back into it.
- **digest**: the checksum that names one exact build of an image.
- **layering**: adding an RPM package on top of the image so it is present in every future deployment.
- **pin**: marking a deployment so cleanup never removes it.
- **3-way merge**: how `/etc` is carried across updates, keeping your edits while taking the new defaults.

## How it works

`bootc status` shows the deployments as bootc sees them, and `rpm-ostree
status` shows the same ones with more detail. Look at the machine before an
update.

```
{user}@{host}:~$ bootc status
Current staged image: <none>
Current booted image: ghcr.io/natethomass/pridwen:latest
    Image version: 0.3.0-m2 (2026-09-07T08:12:04Z)
    Image digest: sha256:9f3a1c…e2b7
Current rollback image: ghcr.io/natethomass/pridwen:latest
    Image version: 0.2.0-m1 (2026-09-04T19:40:11Z)
    Image digest: sha256:41d0be…77c3
```

Three slots. Staged is `<none>`, so nothing is waiting. Booted is the image
you are on, with its version and digest. Rollback is the previous one, kept
on disk. Both have the same name because your machine follows the `latest`
tag of `ghcr.io/natethomass/pridwen`; the digest is what tells them apart.

Now check for an update. `bootc upgrade` asks the registry whether `latest`
points at a newer digest and, if so, downloads it and stages it. It needs
root because it writes a new deployment to the disk.

```
{user}@{host}:~$ sudo bootc upgrade
Fetching ghcr.io/natethomass/pridwen:latest
Queued for next boot: ghcr.io/natethomass/pridwen:latest
  Version: 0.3.1-m2
  Digest: sha256:c08d5e…19af
{user}@{host}:~$ bootc status | head -n 3
Current staged image: ghcr.io/natethomass/pridwen:latest
    Image version: 0.3.1-m2 (2026-09-07T11:02:37Z)
    Image digest: sha256:c08d5e…19af
```

`Queued for next boot` is the key phrase: the new image is staged, the running
system is untouched, and the next reboot boots into it while the one you are
on becomes the rollback. If there is nothing new, `bootc upgrade` says `No
changes in ghcr.io/natethomass/pridwen:latest` and stages nothing. `pridwen
explain bootc` annotates the subcommands.

After the reboot, if something is wrong, `sudo bootc rollback` swaps the
order so the previous deployment boots next, and one more reboot puts you back
where you were. `rpm-ostree rollback` does the same thing. Across all of this,
`/usr` is replaced whole, but your files survive: `/var`, which holds your
home directory and containers, is never part of the image, and `/etc` is
carried over by a 3-way merge that keeps the lines you changed and takes the
image's new defaults for the rest.

Layering is the way to put an RPM package on the host itself, for things that
must be part of the base, such as a driver or a system service. It rebuilds
the deployment with the package added and, like an upgrade, takes effect at
the next boot. Use it as the last resort: every layered package has to be
applied again on top of each new image, which slows every update and moves you
away from the tested base. Prefer a Flatpak for apps and a Distrobox for tools.

```
{user}@{host}:~$ sudo rpm-ostree install tmux
Checking out tree 9f3a1c6... done
Resolving dependencies... done
Importing packages... done
Added:
  tmux-3.5a-2.fc43.x86_64
Changes queued for next boot. Run "systemctl reboot" to start a reboot
{user}@{host}:~$ rpm-ostree status | head -n 8
State: idle
Deployments:
  ostree-image-signed:docker://ghcr.io/natethomass/pridwen:latest
                   Digest: sha256:9f3a1c…e2b7
                  Version: 0.3.0-m2 (2026-09-07T08:12:04Z)
                    Diff: 1 added
          LayeredPackages: tmux
```

`Changes queued for next boot` again. In `rpm-ostree status` the new entry
sits at the top without a dot, because it is pending, and the LayeredPackages
line lists what was added. For a simple package with no services,
`--apply-live` makes it usable now as well; `sudo rpm-ostree uninstall tmux`
removes the layer. `rpm-ostree status` after a layering shows the pending
entry; `rpm-ostree` keeps the list of layered packages and re-applies it to
every upgrade, which is exactly the cost mentioned above.

Deployments are cleaned up automatically, so only booted, staged, and rollback
normally exist. To keep a known-good one longer, pin it: `sudo ostree admin pin
0` pins the deployment at index 0, the first in the list, and `--unpin`
releases it. This is what you do before a risky change on a server.

This is the model behind Pridwen's whole update story. CI builds a new image
and pushes it to `ghcr.io/natethomass/pridwen`; your machine pulls it, stages
it, and keeps the one you are on as a fallback.

## When it goes wrong

`error: This command requires root privileges` from `bootc upgrade` or
`rpm-ostree install` means a write to the deployments was attempted without
`sudo`. `bootc status` and `rpm-ostree status` read without root; changes need
it.

`error: Packages not found: tmx` from `rpm-ostree install` means no package
of that name exists in the Fedora repositories. Check the spelling with
`rpm-ostree search tmux`, or `flatpak search` if it is a desktop app.

`error: Transaction in progress: upgrade` means another rpm-ostree or bootc
operation is still running, usually an automatic update check. Wait for it,
or `rpm-ostree status` shows `State: busy` until it finishes. `pridwen why`
explains whichever you just met.

## Try it

1. Run `bootc status` and read the booted image's Version and the first characters of its Digest; note whether Staged says `<none>`.
2. Run `rpm-ostree status` and match its dotted entry to the booted line from bootc.
3. Run `sudo bootc upgrade` and read whether it queued a new image or reported no changes.
4. Run `sudo rpm-ostree install tmux`, then `rpm-ostree status`, and find the pending entry with `LayeredPackages: tmux`.
5. Run `sudo rpm-ostree uninstall tmux` to drop the layer again, and confirm the pending entry is gone.
6. Say out loud what `sudo bootc rollback` followed by a reboot would do to the three slots.

## Remember

- Deployments are whole images side by side: booted, staged for next boot, and rollback; `bootc status` shows all three.
- `sudo bootc upgrade` stages a new image and the reboot switches; `sudo bootc rollback` and a reboot undo it.
- Layering with `rpm-ostree install` is the last resort; it lands at the next boot and slows every future update.
