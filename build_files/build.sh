#!/bin/bash
# Pridwen OS image build.
# Runs inside the Containerfile RUN step. /ctx holds build_files/ and system_files/.

set -ouex pipefail

PRIDWEN_VERSION="0.1.1-m0"
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
    fastfetch

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
    /usr/lib/os-release

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

### 5. Services
systemctl enable podman.socket
