# Pridwen OS
#
# The whole operating system is this container image. CI builds it, pushes it to
# ghcr.io/natethomass/pridwen, and installed machines pull updates from there with bootc.

# Build context: scripts and overlay files are mounted into the build step, never copied
# into the final image.
FROM scratch AS ctx
COPY build_files /
COPY system_files /system_files
COPY docs /docs

# Base image: Universal Blue Silverblue (Fedora Atomic GNOME + hardware enablement,
# codecs, and a build pipeline that already works).
#   gts    = previous Fedora release (43 today). The stable stream Bluefin ships on.
#   latest = current Fedora release (44 today).
# For NVIDIA hardware, switch to ghcr.io/ublue-os/silverblue-nvidia:gts (M1 will add a variant).
FROM ghcr.io/ublue-os/silverblue-main:gts

# All customisation happens in build_files/build.sh.
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=cache,dst=/var/log \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/build.sh

# Verify the final image is a valid bootc image.
RUN bootc container lint
