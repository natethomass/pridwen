#!/bin/bash
# Pridwen OS image build.
# Runs inside the Containerfile RUN step. /ctx holds build_files/ and system_files/.

set -ouex pipefail

PRIDWEN_VERSION="0.2.1-m1"
IMAGE_REF="ghcr.io/natethomass/pridwen"

### 1. Overlay files from system_files/ onto /
cp -avf "/ctx/system_files"/. /

### 2. Packages
# Fedora and RPM Fusion repos are already enabled on Universal Blue main images.
# gnome-initial-setup is what creates the first user on first boot, because the
# installer deliberately creates none (Omarchy-style). Keep it installed.
dnf5 install -y \
    gnome-initial-setup \
    zsh \
    tmux \
    fastfetch \
    plymouth-plugin-script \
    plymouth-plugin-label \
    darkman \
    python3-gobject \
    gnome-desktop4 \
    virtualbox-guest-additions
# gnome-desktop4: GnomeDesktop typelib for the wizard (locales, keyboard layouts).
# virtualbox-guest-additions: userspace only; the kernel already has vboxguest/vboxsf.

# Fedora's corner watermark extension has no place on a Pridwen desktop.
dnf5 remove -y gnome-shell-extension-background-logo || true

### 3. Identity
# Keep ID=fedora: tooling keys on it. Brand everything else.
sed -i \
    -e 's|^NAME=.*|NAME="Pridwen OS"|' \
    -e "s|^PRETTY_NAME=.*|PRETTY_NAME=\"Pridwen OS ${PRIDWEN_VERSION}\"|" \
    -e 's|^VARIANT=.*|VARIANT="Pridwen"|' \
    -e 's|^VARIANT_ID=.*|VARIANT_ID=pridwen|' \
    -e 's|^HOME_URL=.*|HOME_URL="https://github.com/natethomass/pridwen"|' \
    -e 's|^SUPPORT_URL=.*|SUPPORT_URL="https://github.com/natethomass/pridwen/issues"|' \
    -e 's|^BUG_REPORT_URL=.*|BUG_REPORT_URL="https://github.com/natethomass/pridwen/issues"|' \
    -e 's|^LOGO=.*|LOGO=pridwen|' \
    /usr/lib/os-release
grep -q "^LOGO=" /usr/lib/os-release || echo "LOGO=pridwen" >> /usr/lib/os-release

mkdir -p /usr/share/pridwen
echo "${PRIDWEN_VERSION}" > /usr/share/pridwen/VERSION

### 4. Image info for Universal Blue tooling (ujust, update notifier)
FEDORA_VERSION="$(. /usr/lib/os-release && echo "${VERSION_ID}")"
mkdir -p /usr/share/ublue-os
cat > /usr/share/ublue-os/image-info.json <<EOF
{
  "image-name": "pridwen",
  "image-flavor": "main",
  "image-vendor": "natethomass",
  "image-ref": "ostree-unverified-registry:${IMAGE_REF}",
  "image-tag": "latest",
  "base-image-name": "silverblue",
  "fedora-version": "${FEDORA_VERSION}"
}
EOF

### 5. Look (M1)
# Compile the dconf defaults in /etc/dconf/db/distro.d into the distro database.
# Fedora's /etc/dconf/profile/user already reads system-db:distro.
dconf update
# Register the mark with the icon cache so Settings > About and GDM can find it.
gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true

# Greeter and lock screen: rewrite GNOME Shell's theme gresource with the Cream
# Glass override (GDM cannot load extensions, so this is the only way in).
/ctx/gdm-theme.sh

# Boot splash: /etc/plymouth/plymouthd.conf selects the pridwen theme. The initramfs
# carries its own copy of the theme, so regenerate it (same recipe as Bazzite/Bluefin).
plymouth-set-default-theme pridwen
chmod 0755 /usr/share/darkman/*.sh
KVER="$(dnf5 repoquery --installed --queryformat='%{evr}.%{arch}' kernel | head -n1)"
echo "Regenerating initramfs for kernel ${KVER}"
export DRACUT_NO_XATTR=1
dracut --no-hostonly --kver "${KVER}" --reproducible --zstd -v --add ostree \
    -f "/usr/lib/modules/${KVER}/initramfs.img"
chmod 0600 "/usr/lib/modules/${KVER}/initramfs.img"

# First boot: the Pridwen wizard runs inside GDM's initial-setup session instead of
# GNOME Initial Setup (drop-in on gnome-initial-setup.service). The existing-user
# first-login pass is not wanted.
chmod 0755 /usr/libexec/pridwen-firstboot
systemctl --global mask gnome-initial-setup-first-login.service

# Narrated boot lines and the day/night switcher.
systemctl enable pridwen-narrate-disks.service pridwen-narrate-network.service pridwen-narrate-desktop.service
systemctl --global enable darkman.service

### 6. Services
systemctl enable podman.socket
