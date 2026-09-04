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

## M0 status (as of 2026-09-04)

Done locally: repo, Containerfile, build.sh, both workflows, disk configs, Justfile, README,
cosign key pair generated (`scripts/gen-cosign-key.py`, verified round-trip).

**Not done, blocked in the previous (non-interactive) session.** These need interactive
approval, so do them here first, in order:

1. Install tooling if missing: `winget install GitHub.cli` and `winget install Sigstore.Cosign`.
   Then `gh auth login` (the owner does this in the terminal; browser flow).
2. Create the repo and push: `gh repo create natethomass/pridwen --public --source . --push`
   (remote `origin` is already set to https://github.com/natethomass/pridwen.git).
3. Watch the first "Build container image" run: `gh run watch`. Fix anything red.
4. Make the GHCR package public (web UI: Packages → pridwen → Package settings → Change
   visibility). Required for installs and for the disk-image workflow to pull.
5. Set the signing secret: `gh secret set SIGNING_SECRET < cosign.key`. Re-run the build so
   the image is signed.
6. Run "Build disk images": `gh workflow run build-disk.yml -f platform=amd64`, then download
   the artifacts: `gh run download -n pridwen-anaconda-iso-amd64`.
7. Boot the ISO in VirtualBox (EFI on, 4 GB, 2 CPU), install, create the user on first boot,
   run `sudo bootc status`. Then push a trivial change, wait for CI, `sudo bootc upgrade` in
   the VM. That closes M0.

Known unverified: the workflow YAML was checked by eye only (no PyYAML on the host). The
bootc-image-builder action's exact input names came from the ublue image-template as of
2026-09; if it errors, fetch its README and adjust.

## Useful references

- Universal Blue image template (this repo's ancestor): https://github.com/ublue-os/image-template
- bootc-image-builder config (kickstart, installer modules, types): https://osbuild.org/docs/bootc/
- ublue image versions (which Fedora `gts`/`latest` map to): https://github.com/ublue-os/main/blob/main/image-versions.yaml
- Owner's related product: the $97 RHEL Compliance Lab (RHCSA track connects to it).
