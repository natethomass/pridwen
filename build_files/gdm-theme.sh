#!/bin/bash
# Pridwen greeter, lock-screen and top-bar styling.
#
# GDM runs GNOME Shell and cannot load extensions, so the only way to restyle it
# is to rewrite the shell's theme gresource. This extracts every resource,
# appends the Cream Glass override to each stylesheet, and recompiles the bundle
# in place. glib2-devel provides the tools and is removed again afterwards.
set -euo pipefail

GRES=/usr/share/gnome-shell/gnome-shell-theme.gresource
OVERRIDE=/ctx/gdm-override.css
SHELL_OVERRIDE=/ctx/shell-override.css

dnf5 install -y glib2-devel

WORK="$(mktemp -d)"
cd "$WORK"
mkdir -p src
# Extract every resource, preserving its path under src/.
gresource list "$GRES" | while read -r res; do
    mkdir -p "src/$(dirname "$res")"
    gresource extract "$GRES" "$res" > "src/$res"
done

# Append the override to every stylesheet variant (gnome-shell.css, -dark, -light,
# high-contrast, and gdm.css where present).
count=0
while read -r css; do
    printf '\n\n/* --- Pridwen Cream Glass (build_files/gdm-override.css) --- */\n' >> "$css"
    cat "$OVERRIDE" >> "$css"
    printf '\n\n/* --- Pridwen Cream Glass shell chrome (build_files/shell-override.css) --- */\n' >> "$css"
    cat "$SHELL_OVERRIDE" >> "$css"
    count=$((count + 1))
done < <(find src -name 'gnome-shell*.css')
echo "gdm-theme: patched ${count} stylesheet(s)"

# Rebuild the manifest from what we extracted and compile.
{
    echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo '<gresources>'
    echo '  <gresource prefix="/">'
    (cd src && find . -type f | sed 's|^\./||' | sort | while read -r f; do
        echo "    <file>${f}</file>"
    done)
    echo '  </gresource>'
    echo '</gresources>'
} > theme.gresource.xml

glib-compile-resources --sourcedir=src --target="${GRES}.new" theme.gresource.xml
mv -f "${GRES}.new" "$GRES"
chmod 0644 "$GRES"
echo "gdm-theme: $(gresource list "$GRES" | wc -l) resources in rebuilt bundle"

cd /
rm -rf "$WORK"
dnf5 remove -y glib2-devel
