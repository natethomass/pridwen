# Pridwen OS — project brief for Claude

Read this first. It replaces re-deriving context from the conversation.

## What this is

Pridwen OS is an immutable, hardened Fedora Atomic desktop (GNOME on Wayland) that teaches
sysadmin and cybersecurity skills while being a full daily driver. Named for Arthur's shield.
Standalone product; promoted by the owner's TechFitDad channel, not branded as it.

The whole OS is one container image: `Containerfile` + `build_files/build.sh`, built by GitHub
Actions, pushed to `ghcr.io/natethomass/pridwen`, turned into ISO/qcow2/vmdk by
bootc-image-builder. This is the Universal Blue pattern (Bluefin, Bazzite).

Full concept doc (architecture, teaching layer, hardening, cert tracks, M0–M7 plan):
https://claude.ai/code/artifact/fde7ace6-f138-4e68-82a7-7d6aa6f2823c

## Locked decisions (do not re-ask)

- Base: `ghcr.io/ublue-os/silverblue-main:gts` (gts = Fedora 43 today, latest = 44). Rocky 9 is
  the lab target ("Range"), not the base. Rocky has no immutable desktop.
- Desktop: GNOME only, Wayland everywhere including GDM.
- Immutable (bootc). Apps via Flatpak, mutable tooling via Distrobox/Podman.
- Installer creates NO user (Omarchy-style). First boot creates one. M1 replaces GNOME Initial
  Setup with a Pridwen welcome wizard.
- Look: "Cream Glass" day/night. Cream `#F2EDE3` canvas, ink `#24211D`, slate `#5F7E9B`
  (chrome), sage `#6E9E7A` (earned/ok), clay `#B9714E` (caution). Night canvas `#111318`.
  Never crossfade day→night (midpoint is mud); fade through deep night.
- Teaching: push and pull. Subsystems: Coach (`pridwen-shell`, shell hooks + daemon `pridwend`),
  Dispatch (notifications), Academy (GTK4/libadwaita skill-tree app), Range (Podman/libvirt
  labs with checkers), Guide (AI that explains, never executes; BYO key or local model),
  Posture (hardening baseline as data, every control is a lesson).
- Tracks: Pridwen Core, RHCSA (lead with this), Linux+, Security+, Red Team Fundamentals.
- Hardened by default: LUKS2, SELinux enforcing, firewalld drop zone, auditd, sshd off,
  wheel-only sudo, USBGuard learn mode, sysctl hardening, Flathub-only, DNS over TLS. Not
  fapolicyd / full STIG on the desktop.
- CLI verb is `pridwen`. Packages are `pridwen-*`. Learning data stays local (SQLite).

## Conventions

- Keep this repo OUT of OneDrive. File locks break builds.
- Commit as `natethomass <nrthomas13@gmail.com>` (repo-local config already set).
- Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Never commit `cosign.key`. It is gitignored. `cosign.pub` is committed.
- Windows host, PowerShell/Git Bash. No podman here: container builds happen in GitHub
  Actions; boot tests happen in VirtualBox (and later Proxmox).
- Keep `ID=fedora` in os-release; brand NAME/PRETTY_NAME/VARIANT_ID only.
- Prefer small, verifiable steps: push, watch CI, boot the artifact, report exactly what
  happened. Don't claim a build works until CI is green and the VM booted.

## Milestones

| | Delivers | Done when |
|---|---|---|
| **M0 Foundation** | This repo, CI image build, ISO/qcow2/vmdk | Installs in VirtualBox; `bootc upgrade` pulls a new build |
| M1 Look | Plymouth narrated boot, GDM greeter, Shell + libadwaita theme, adaptive wallpapers, sunrise/sunset switch, first-boot wizard | Power-on-to-desktop recording worth posting |
| M2 Coach | `pridwend`, zsh/bash hooks, YAML rules engine (~200 rules), `pridwen why/explain/learn/quiet`, SELinux denial translation, Dispatch | A beginner survives a week of failed commands with the coach alone |
| M3 Academy | GTK4 app, tree data model, progress store, Core track (20 missions), journal, posture panel | Core track completable end to end |
| M4 Range | Scenario runner, Podman + libvirt targets, Rocky images, checkers, 24 scenarios, `pridwen enter rocky` | RHCSA track completable; attack/defend twins on one network |
| M5 Guide | Provider layer, context scrubbing, Socratic mode | Works with a cloud key and offline with a local model |
| M6 Posture | Baseline as data, defaults applied at build, drift detection, lesson per control | Fresh install passes its own posture check |
| M7 Release | Docs site, install guide, releases, partial Linux+/Sec+ tracks | Public 1.0 |

## M0 status: DONE (2026-09-04)

Verified end to end in VirtualBox: ISO installs (LUKS, no user), gnome-initial-setup creates
the user, `bootc status` shows `ghcr.io/natethomass/pridwen:latest`, and after a version
bump push + CI, `sudo bootc upgrade` + reboot moved PRETTY_NAME from 0.1.0-m0 to 0.1.1-m0
with the old image kept as rollback. Next milestone: M1 Look.

Operational notes (keep):
- Tooling: gh 2.100.0 and cosign 3.1.3 via winget. cosign is NOT on PATH; run it as
  `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Sigstore.Cosign_Microsoft.Winget.Source_8wekyb3d8bbwe\cosign-windows-amd64.exe`.
  gh scopes: repo, workflow, read:org, gist (no read:packages, so `gh api` on packages 403s;
  query ghcr.io anonymously). Run gh inside the repo or pass `-R natethomass/pridwen`.
- Container build: ~11-14 min, triggered by any push except README/docs/CLAUDE.md/LICENSE/
  .vscode/.claude. Workflow file changes always trigger. Images are signed; verify with
  `cosign verify --key cosign.pub --insecure-ignore-tlog=true ghcr.io/natethomass/pridwen:latest`.
- GHCR package is public (inherited from the public repo).
- Disk images: `gh workflow run build-disk.yml -f platform=amd64`, ~15 min, artifacts
  ~3-4 GiB each, 14-day retention, no checksum file in the artifact.
- Test VM: VirtualBox 7.2 "Pridwen M0" at `C:\Users\natet\VMs\Pridwen M0\` (EFI, 4 GB,
  2 CPU, 40 GB VDI, VMSVGA). ISO at `C:\Users\natet\VMs\pridwen\pridwen-0.1.0-m0-amd64.iso`.
  Host has Hyper-V active so VirtualBox uses its slower backend; acceptable.
- Fixes that were needed: `sigstore/cosign-installer` has no floating `v4` tag (pinned
  v4.1.2); silverblue-main declares no default root filesystem, so
  `system_files/usr/lib/bootc/install/50-pridwen.toml` sets btrfs and `build-disk.yml`
  passes `rootfs: btrfs`.
- Known M0 leftovers for M1: hostname is still "fedora"; desktop is stock Fedora wallpaper
  and branding; VirtualBox guest additions not installed (no shared clipboard).

## M1 status (2026-09-04, in progress)

Four slices, each a commit on main. Verify the same way as M0: CI green, `bootc upgrade` in
the VM, look. Slice 4 needs a fresh install (new ISO) because it only runs when no user exists.

1. **Look basics** (7e22e82): Cream Glass wallpapers rendered by `scripts/gen-wallpapers.py`
   from the mode.ts tokens; dconf distro defaults (`system_files/etc/dconf/db/distro.d`);
   hostname `pridwen`; placeholder shield mark as os-release LOGO. Version 0.2.0-m1.
2. **Boot and sun** (24e13d5): Plymouth script theme `pridwen` (assets from
   `scripts/gen-plymouth-assets.py`), initramfs regenerated with dracut at build,
   three `pridwen-narrate-*` units send plain-English lines via `plymouth display-message`,
   darkman follows the sun and `usr/share/darkman/10-pridwen-gnome.sh` fades through deep
   night. Deviation from the concept doc: Esc still shows Plymouth's raw details view (that
   toggle is inside plymouthd, script themes cannot intercept it), so narration is always on
   under the rail instead.
3. **Greeter** (c4b81a2): `build_files/gdm-theme.sh` rewrites gnome-shell-theme.gresource
   with `gdm-override.css` (glib2-devel installed for the step, removed after); gdm.d dconf.
   Rules are appended overrides, so unknown selectors are harmless.
4. **Welcome wizard** (a63ce98): `/usr/libexec/pridwen-firstboot` (PyGObject/libadwaita)
   replaces the GIS binary through a drop-in on the user unit `gnome-initial-setup.service`;
   GDM's initial-setup session, user, polkit rules and copy worker are reused. Creates the
   admin user via AccountsService, writes choices to dconf (`/org/pridwen/learner/track`,
   `/org/pridwen/look/mode`), writes `~/.config/gnome-initial-setup-done` and
   `~/gnome-initial-setup-uid`, then logs in through libgdm (`gdm-password`).

Known gaps for later: Shell top-bar styling (needs user-theme extension); language and
keyboard pages in the wizard; Guide connection page is informational only until M5; the
mark is a placeholder pending the owner's sign-off; VirtualBox has no guest additions.

## Useful references

- Universal Blue image template (this repo's ancestor): https://github.com/ublue-os/image-template
- bootc-image-builder config (kickstart, installer modules, types): https://osbuild.org/docs/bootc/
- ublue image versions (which Fedora `gts`/`latest` map to): https://github.com/ublue-os/main/blob/main/image-versions.yaml
- Owner's related product: the $97 RHEL Compliance Lab (RHCSA track connects to it).
