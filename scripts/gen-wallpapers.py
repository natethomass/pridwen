#!/usr/bin/env python3
"""Render the Pridwen Cream Glass wallpapers.

Day and night are the same composition with every colour swapped: a soft
diagonal canvas gradient, three large blurred blobs that drift in the motion
graphics but sit still here, and a fine grain so the flat fields don't band.
Tokens are copied verbatim from the TechFitDad Cream Glass system (mode.ts).

Usage: python scripts/gen-wallpapers.py [outdir]
Writes pridwen-day.png and pridwen-night.png at 3840x2160.
Needs Pillow and numpy.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 3840, 2160

DAY = {
    "canvas": (242, 237, 227),
    "canvas_deep": (231, 223, 209),
    "ink": (36, 33, 29),
    "blobs": [(216, 205, 186), (227, 214, 194), (220, 210, 198)],
    "blob_opacity": 0.75,
    "grain": 0.05,
}
NIGHT = {
    "canvas": (17, 19, 24),
    "canvas_deep": (9, 10, 13),
    "ink": (240, 237, 231),
    "blobs": [(44, 50, 78), (28, 44, 62), (52, 38, 62)],
    "blob_opacity": 0.90,
    "grain": 0.07,
}

# (x%, y%, radius px at 1920 wide) from Glass.tsx <Canvas>; scaled to 4K below.
BLOBS = [(22, 24, 620), (78, 34, 560), (50, 82, 700)]
SCALE = W / 1920
BLUR = 90 * SCALE


def gradient(c0, c1):
    """165deg linear gradient across the frame (top-left canvas to bottom-right deep)."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    ang = np.deg2rad(165)
    # CSS angle: 0deg = to top, 90deg = to right. Direction vector:
    dx, dy = np.sin(ang), -np.cos(ang)
    t = (x - W / 2) * dx + (y - H / 2) * dy
    t = (t - t.min()) / (t.max() - t.min())
    c0 = np.array(c0, np.float32)
    c1 = np.array(c1, np.float32)
    return c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]


def render(tokens):
    base = gradient(tokens["canvas"], tokens["canvas_deep"])

    # Blobs: blur an alpha mask per blob and composite its solid colour through it.
    # (Blurring an RGBA layer would bleed transparent black into the edges and
    # draw dark halos around every blob.)
    out = base
    for (px, py, r), colour in zip(BLOBS, tokens["blobs"]):
        cx, cy, rr = px / 100 * W, py / 100 * H, r * SCALE / 2
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(BLUR))
        alpha = np.asarray(mask).astype(np.float32)[..., None] / 255.0 * tokens["blob_opacity"]
        out = out * (1 - alpha) + np.array(colour, np.float32)[None, None, :] * alpha

    # Grain: sparse ink dots, same idea as the 3px radial-gradient tile.
    rng = np.random.default_rng(2026)
    dots = (rng.random((H, W)) < (1 / 9)).astype(np.float32)[..., None]
    ink = np.array(tokens["ink"], np.float32)[None, None, :]
    out = out * (1 - dots * tokens["grain"]) + ink * dots * tokens["grain"]

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def main():
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else "system_files/usr/share/backgrounds/pridwen")
    outdir.mkdir(parents=True, exist_ok=True)
    for name, tokens in (("day", DAY), ("night", NIGHT)):
        img = render(tokens)
        path = outdir / f"pridwen-{name}.png"
        img.save(path, optimize=True)
        print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
