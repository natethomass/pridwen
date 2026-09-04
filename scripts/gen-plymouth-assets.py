#!/usr/bin/env python3
"""Render the image assets for the Pridwen Plymouth boot theme.

Plymouth script themes can only show bitmaps, so the mark's "draw in" is a
sequence of frames: the shield revealed top to bottom with a soft edge.
Colours: cream on the night canvas (the boot screen is always night).
The mark itself comes from scripts/pridwen_mark.py.

Usage: python scripts/gen-plymouth-assets.py [outdir]
Writes into system_files/usr/share/plymouth/themes/pridwen/ by default.
Needs Pillow and numpy.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pridwen_mark import CREAM, render_mark  # noqa: E402

SS = 4  # supersampling for clean edges
MARK = 192  # mark box in px
FRAMES = 24


def shield_outline_mask():
    """The Chief mark in cream, oversampled; reveal() and down() work on this."""
    return render_mark(MARK * SS, CREAM, ss=1)


def reveal(im, t):
    """Reveal `im` top to bottom; t in [0,1]; soft 12% edge."""
    big = im.size[1]
    y = np.arange(big)[:, None] / big
    edge = 0.12
    a = np.clip((t * (1 + edge) - y) / edge, 0, 1)
    arr = np.asarray(im).astype(np.float32)
    arr[..., 3] *= a
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def down(im):
    return im.resize((im.size[0] // SS, im.size[1] // SS), Image.LANCZOS)


def rounded_bar(w, h, colour, alpha):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=h * SS // 2, fill=colour + (alpha,))
    return down(im)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "system_files/usr/share/plymouth/themes/pridwen")
    out.mkdir(parents=True, exist_ok=True)
    mark = shield_outline_mask()
    for i in range(FRAMES):
        t = (i + 1) / FRAMES
        down(reveal(mark, t)).save(out / f"mark-{i:02d}.png")
    down(mark).save(out / "mark.png")
    rounded_bar(420, 4, CREAM, 36).save(out / "rail-track.png")
    rounded_bar(420, 4, CREAM, 255).save(out / "rail-fill.png")
    # password bullets and a small cursor block
    b = Image.new("RGBA", (10 * SS, 10 * SS), (0, 0, 0, 0))
    ImageDraw.Draw(b).ellipse((0, 0, 10 * SS - 1, 10 * SS - 1), fill=CREAM + (255,))
    down(b).save(out / "bullet.png")
    rounded_bar(260, 36, CREAM, 22).save(out / "entry.png")
    # GDM login-screen logo (org.gnome.login-screen logo): a quiet 72px mark.
    logo_dir = out.parent.parent.parent / "pridwen"  # /usr/share/pridwen
    logo_dir.mkdir(parents=True, exist_ok=True)
    down(mark).resize((72, 72), Image.LANCZOS).save(logo_dir / "login-logo.png")
    print(f"wrote {FRAMES} mark frames + rail, bullet, entry to {out}; login-logo.png to {logo_dir}")


if __name__ == "__main__":
    main()
