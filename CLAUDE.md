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
  ~3-4 GiB each, 14-day retention, no checksum file in the artifact. An ISO is a snapshot
  of `:latest` at build time, so the order is always push → container build green → disk
  build. The plan job refuses to build unless the image's
  `org.opencontainers.image.revision` label equals HEAD (`-f allow-stale=true` bypasses).
- Anaconda writes its own `/etc/hostname` ("fedora") and that local edit survives every
  `bootc upgrade` (3-way /etc merge keeps local changes), so the kickstart `%post` sets it.
  Systems installed from an older ISO need a one-time `sudo hostnamectl hostname pridwen`.
- Installer look: the Anaconda boot image is Fedora's, not ours, so branding is dropped in
  by a kickstart `%pre` written by `scripts/gen-installer-branding.py` (pixmaps + CSS at
  `/run/install/product/`, which Anaconda loads above its own stylesheet). The `%pre` is
  Python because the installer image has no `base64` binary. Kickstart text sits in a TOML
  basic string: no backslashes, no triple double-quotes. The summary hub header is `#nav-box`
  (Anaconda's rule only targets AnacondaSpokeWindow). Anaconda's tty2 shell is reachable with
  Ctrl+Alt+F2 sent via `VBoxManage controlvm ... keyboardputscancode 1d 38 3c bc b8 9d`.
- build.yml ignores `disk_config/**`, `scripts/**` and `build-disk.yml`; only Containerfile,
  Justfile, build_files, system_files and build.yml rebuild the image. Rechunking drops OCI
  labels, so the Justfile re-applies them (metadata-only build) after `ostree-rechunk`.
- Test VM: VirtualBox 7.2 "Pridwen M0" at `C:\Users\natet\VMs\Pridwen M0\` (EFI, 4 GB,
  2 CPU, 40 GB VDI, VMSVGA). ISO at `C:\Users\natet\VMs\pridwen\pridwen-0.1.0-m0-amd64.iso`.
  Host has Hyper-V active so VirtualBox uses its slower backend; acceptable.
- Fixes that were needed: `sigstore/cosign-installer` has no floating `v4` tag (pinned
  v4.1.2); silverblue-main declares no default root filesystem, so
  `system_files/usr/lib/bootc/install/50-pridwen.toml` sets btrfs and `build-disk.yml`
  passes `rootfs: btrfs`.
- Known M0 leftovers for M1: hostname is still "fedora"; desktop is stock Fedora wallpaper
  and branding; VirtualBox guest additions not installed (no shared clipboard).

## M1 status: VERIFIED (2026-09-04)

Four slices, each a commit on main. Verify the same way as M0: CI green, `bootc upgrade` in
the VM, look. Slice 4 needs a fresh install (new ISO) because it only runs when no user exists.

1. **Look basics** (7e22e82): Cream Glass wallpapers rendered by `scripts/gen-wallpapers.py`
   from the mode.ts tokens; dconf distro defaults (`system_files/etc/dconf/db/distro.d`);
   hostname `pridwen`; shield mark as os-release LOGO. Version 0.2.0-m1.
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

Verified in the M0 VM after `bootc upgrade` to the slice 1-4 image (2026-09-04): Plymouth
theme renders in VirtualBox (mark, rail, narration line); cream wallpaper, weekday clock,
favourites all present; greeter got dark scheme, logo, pill entry but NOT the night wallpaper
or the frosted card. Fixed in 45958ab: St resolves a bare path in `url()` relative to the
stylesheet inside the gresource, so use `url("file:///...")`; and the user-card rule needs the
stock three-class selector chain to win. Also removed Fedora's corner watermark extension
(`gnome-shell-extension-background-logo`) in 9d25995. Both verified after the next upgrade.

Two VMs now: "Pridwen M0" (installed from the M0 ISO, upgraded since) and "Pridwen M1"
(fresh, for the wizard test). ISOs in `C:\Users\natet\VMs\pridwen\`.

First fresh-install test of the wizard (2026-09-04): account created, password set, PAM
session opened, then `TypeError: on_session_opened() takes 3 positional arguments but 4
were given`: GdmGreeter::session-opened carries (service_name, session_id). Fixed; all GDM
signal handlers now take *rest. The wizard also got a failure path (status + "Go to the
login screen"), a 25 s watchdog, and journal logging. To re-run the wizard on an installed
system without reinstalling: `sudo rpm-ostree kargs --append=gnome.initial-setup=1`, reboot
(GDM forces initial setup from the kernel cmdline); remove the karg afterwards.

Wizard re-test on "Pridwen M1" after `bootc upgrade` to 470f694 (2026-09-04): second user
created, PAM session opened, landed on the desktop with no watermark. Slice 4 verified.
Fresh install from `pridwen-0.2.0-m1c-amd64.iso` (run 33915470966, image d6c123f) in VM
"Pridwen M1 fresh" (2026-09-04): branded Anaconda (night sidebar gradient, Chief mark, night
header, "PRIDWEN OS 43 INSTALLATION"), Plymouth narration, wizard, desktop, prompt
`user@pridwen`, no watermark. Only polish left in the installer: the keyboard-layout badge
label was cream on white; fixed in 6253b15, lands in the next ISO.

Known gaps for later (not blocking M2): Shell top-bar styling (needs user-theme extension);
language and keyboard pages in the wizard; Guide connection page is informational only until
M5; VirtualBox guest additions; Anaconda's blue progress bar and buttons are GTK Adwaita
literals, not themable from the product CSS. The "recording worth posting" is the owner's call.

## M2 status (2026-09-04, in progress)

Design: `docs/coach.md` (installed at `/usr/share/doc/pridwen/coach.md`). Read it before
touching rules or the daemon. Slices:

1. **Coach core** (cda3f45): `pridwend` (GLib, per-user, `$XDG_RUNTIME_DIR/pridwen/coach.sock`),
   bash and zsh hooks in `/usr/share/pridwen/shell/`, C client `pridwen-coach-send` (built by
   gcc in build.sh, gcc removed after), rules engine with probes, SQLite store
   `~/.local/share/pridwen/pridwen.db`, CLI `pridwen why|explain|learn|quiet|status`, Dispatch
   via libnotify. Python package lives at `/usr/lib/pridwen/pridwen/` (no RPM/COPR yet).
2. **Content**: `tree.yaml` (29 nodes), `rules/<node>.yaml` (~200), `nudges.yaml`,
   `lessons/<id>.md` (87), `explain/<cmd>.yaml` (30). Written by a subagent from the schema.
3. **Verify in VM** (2026-09-04, image dfb7d81 on "Pridwen M1 fresh"): owner confirmed the hook
   prints hints after failures and `pridwen why/explain/status` work. Driven from the host:
   `why` rendered a rule's why text and translated a real AVC (bootupd -> systemd-homed;
   now gated so unrelated denials are only mentioned), `quiet 1h/off` works, daemon runs at
   ~19 MB. Found and fixed a false positive (web-traversal fired on `cd /etc/passwd`).
   Still to exercise: the ten-sudo nudge (needs the owner's password), notification actions.

Decisions: bash stays the default login shell (zsh hook shipped too); rules match the
command with a leading sudo stripped (`not_sudo` distinguishes); output is never captured,
probes look at the system instead; secrets are scrubbed before storage.

## The mark

The Pridwen mark is "Chief": a heater shield with a chevron cut out, chosen by the owner on
2026-09-04 from five candidates (https://claude.ai/code/artifact/0ba21e5d-7680-4f56-8998-4f7e94f60adb).
`scripts/pridwen_mark.py` is the single source of the geometry and writes the hicolor icons
(`pridwen.svg` = cream mark on a night tile, `pridwen-symbolic.svg` = currentColor mark).
`scripts/gen-plymouth-assets.py` imports it for the boot frames and the GDM login logo.
Never redraw the shield by hand anywhere else.

## Useful references

- Universal Blue image template (this repo's ancestor): https://github.com/ublue-os/image-template
- bootc-image-builder config (kickstart, installer modules, types): https://osbuild.org/docs/bootc/
- ublue image versions (which Fedora `gts`/`latest` map to): https://github.com/ublue-os/main/blob/main/image-versions.yaml
- Owner's related product: the $97 RHEL Compliance Lab (RHCSA track connects to it).
