# Pridwen OS

**A Linux that teaches you to run it.** Immutable, hardened, GNOME on Wayland, and it coaches
you into a sysadmin and security role while you daily-drive it. Named for Arthur's shield.

This repo is the operating system. The whole OS is one container image, described by
[`Containerfile`](Containerfile) and [`build_files/build.sh`](build_files/build.sh), built by
GitHub Actions, pushed to `ghcr.io/natethomass/pridwen`, and turned into installable media by
[bootc-image-builder](https://osbuild.org/docs/bootc/). Installed machines update from the
registry with `bootc upgrade`. This is the [Universal Blue](https://universal-blue.org) pattern.

> Status: **M0 done, M1 Look verified, M2 Coach next.** The image builds, signs, publishes, installs from
> its ISO, and upgrades with `bootc upgrade`. M1 is adding the Pridwen look: wallpapers and
> GNOME defaults first, then Plymouth, GDM, and the first-boot wizard. Roadmap at the bottom.

## Layout

```
Containerfile              the OS, FROM ghcr.io/ublue-os/silverblue-main:gts (Fedora 43)
build_files/build.sh       everything that customises the image
system_files/              files overlaid onto / at build time
disk_config/iso.toml       installer ISO config (Anaconda; no user created, first boot does it)
disk_config/disk.toml      pre-installed disk config (qcow2, vmdk)
pridwen.env                image name, owner, labels
Justfile                   local build recipes (needs a Linux box with podman)
.github/workflows/         build.yml (container image), build-disk.yml (ISO / qcow2 / vmdk)
scripts/                   helpers for signing setup
```

## How updates flow

1. Push to `main` (or the daily 10:05 UTC schedule) runs **Build container image**.
2. It builds, rechunks, tags (`latest`, `latest-<sha>`, `<date>`), and pushes to GHCR.
3. Any installed Pridwen machine runs `sudo bootc upgrade` and reboots into the new build.
4. When you want fresh media, run **Build disk images** from the Actions tab. It pulls
   `:latest` and uploads `anaconda-iso`, `qcow2`, and `vmdk` as workflow artifacts (14 days).

## Installing

**Installer ISO (bare metal, VirtualBox, Proxmox).** Boot the ISO. Anaconda asks for a disk;
tick *Encrypt my data* for LUKS. It creates no user on purpose. First boot runs GNOME Initial
Setup to create your account. (M1 replaces that with the Pridwen welcome wizard.)

**VirtualBox from the vmdk.** Create a new VM: Fedora (64-bit), EFI enabled, 4 GB+ RAM, 2+
CPUs, then *Use an existing virtual hard disk file* and pick `disk.vmdk`. First boot goes
straight to user creation.

**Proxmox from the qcow2.** Upload `disk.qcow2`, then:

```bash
qm create 9000 --name pridwen --memory 4096 --cores 2 --bios ovmf --efidisk0 local-lvm:0 --net0 virtio,bridge=vmbr0
qm importdisk 9000 disk.qcow2 local-lvm
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-1 --boot order=scsi0
```

**Verify after install.**

```bash
grep PRETTY_NAME /etc/os-release       # PRETTY_NAME="Pridwen OS 0.2.0-m1"
sudo bootc status                    # Booted image: ghcr.io/natethomass/pridwen:latest
sudo bootc upgrade --check           # sees newer builds once CI has pushed one
```

## M0 checklist

- [x] Repo, Containerfile on Universal Blue Silverblue, build script, overlay dir
- [x] CI: build, rechunk, tag, push to GHCR; signing step ready (needs the secret below)
- [x] CI: ISO, qcow2, vmdk via bootc-image-builder
- [x] Installer creates no user; first boot creates one
- [x] GHCR package public, signing secret set, images signed
- [x] Boot the ISO in VirtualBox, install, create user, run `bootc status`
- [x] Push a change, wait for CI, `sudo bootc upgrade` on the VM lands the new build

## Image signing

`cosign.pub` in the repo root is the public key. The matching private key must be the
`SIGNING_SECRET` repository secret. The build signs only when that secret exists.

Generate a pair either with cosign (`COSIGN_PASSWORD="" cosign generate-key-pair`) or,
without cosign, with the helper that writes the same format:

```bash
python scripts/gen-cosign-key.py
```

Then paste the contents of `cosign.key` into *Settings → Secrets and variables → Actions →
New repository secret* named `SIGNING_SECRET`. `cosign.key` is gitignored. Never commit it.

## Building locally

Needs a Linux machine (a Pridwen or any bootc VM is ideal) with `podman`, `just`, and `jq`.

```bash
just build              # container image
just build-iso          # installer ISO   -> output/bootiso/install.iso
just build-qcow2        # Proxmox/libvirt -> output/qcow2/disk.qcow2
just build-vmdk         # VirtualBox      -> output/vmdk/disk.vmdk
just run-vm-iso         # boot the ISO in a browser-hosted QEMU
```

## Roadmap

| Milestone | Delivers |
|---|---|
| **M0 Foundation** | This repo. Image builds, publishes, ISO/qcow2/vmdk, updates via bootc. |
| M1 Look | Plymouth boot theme with narrated boot, GDM greeter, Cream Glass day/night, first-boot wizard. |
| M2 Coach | Shell hooks + daemon, rules engine, `pridwen why` / `explain` / `learn` / `quiet`, notifications. |
| M3 Academy | GTK4 skill-tree app, Pridwen Core track, progress store, posture panel. |
| M4 Range | Podman + libvirt lab runner, Rocky 9 targets, checkers, RHCSA scenarios, attack/defend twins. |
| M5 Guide | AI provider layer, context scrubbing, Socratic mode. |
| M6 Posture | Hardening baseline as data, drift detection, a lesson per control. |
| M7 Release | Docs, install guide, public 1.0. |
