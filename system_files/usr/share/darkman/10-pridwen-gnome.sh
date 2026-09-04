#!/bin/sh
# Pridwen day/night switch, run by darkman with "dark" or "light" as $1.
#
# Never crossfade day to night: the midpoint of cream #F2EDE3 and night #111318
# is mud grey and the wallpaper loses all contrast halfway. So the room goes to
# deep night first, the scheme flips there, and the new wallpaper comes up.

# Only act when the user chose "follow the sun" in the welcome wizard (or never chose).
mode="$(dconf read /org/pridwen/look/mode 2>/dev/null)"
case "$mode" in
  "'day'"|"'night'") exit 0 ;;
esac

case "$1" in
  dark)  scheme=prefer-dark; solid='#111318' ;;
  light) scheme=default;     solid='#F2EDE3' ;;
  *)     exit 0 ;;
esac

BG=org.gnome.desktop.background
IF=org.gnome.desktop.interface

# 1. lights down: solid deep night, GNOME fades the wallpaper out to it
gsettings set "$BG" primary-color '#090A0D'
gsettings set "$BG" picture-options 'none'
sleep 0.7

# 2. flip the scheme while the screen is dark
gsettings set "$IF" color-scheme "$scheme"
sleep 0.5

# 3. lights up on the other wallpaper
gsettings set "$BG" primary-color "$solid"
gsettings set "$BG" picture-options 'zoom'
