#!/usr/bin/env python3
"""Generate every logo and icon asset from the master artwork.

    python make_logo.py

Master: icon/logo.png  (transparent, already in the site palette)

Outputs
    icon/logo-mark.png                  transparent, for the page itself
    icon/favicon-96x96.png              solid background
    icon/favicon.ico                    solid background, 16/32/48
    icon/apple-touch-icon.png           solid background, iOS-safe inset
    icon/web-app-manifest-192x192.png   solid background, maskable-safe inset
    icon/web-app-manifest-512x512.png   solid background, maskable-safe inset

The page background is #292831 and the mark is #fbbbad, so a transparent icon
would vanish against a light browser tab bar. Everything except logo-mark.png is
therefore composited onto a solid #292831 square.
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

ROOT = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(ROOT, "icon")
MASTER = os.path.join(ICON_DIR, "logo.png")

BG = (41, 40, 49)           # #292831

# Rendered at 132px wide on the page, so 512 stays sharp when zoomed.
MARK_WIDTH = 512

# Fraction of the icon width taken up by the mark.
#   0.90  favicons are shown as-is, so fill the square.
#   0.78  iOS rounds the corners of the touch icon.
#   0.66  Android maskable icons only guarantee a centred circle of 80%
#         diameter. A 1.33:1 mark fits inside that circle at 64% width, so
#         0.66 keeps the wingtips clear of any mask shape.
FILL_FAVICON = 0.90
FILL_TOUCH = 0.78
FILL_MASKABLE = 0.66


def render(master, size, fill):
    """Centre the mark on a solid square of the given size."""
    canvas = Image.new("RGBA", (size, size), BG + (255,))
    width = max(1, round(size * fill))
    height = max(1, round(master.height * width / master.width))
    art = master.resize((width, height), Image.LANCZOS)
    canvas.paste(art, ((size - width) // 2, (size - height) // 2), art)
    return canvas


def report(path):
    print("  %-34s %.1f KB" % (
        os.path.relpath(path, ROOT), os.path.getsize(path) / 1024.0))


def main():
    if not os.path.isfile(MASTER):
        sys.exit("Master artwork not found at " + MASTER)

    master = Image.open(MASTER).convert("RGBA")
    box = master.getbbox()
    if box:
        master = master.crop(box)

    # Transparent mark for the page.
    mark_height = max(1, round(master.height * MARK_WIDTH / master.width))
    mark = master.resize((MARK_WIDTH, mark_height), Image.LANCZOS)
    mark_path = os.path.join(ICON_DIR, "logo-mark.png")
    mark.save(mark_path, "PNG", optimize=True)
    report(mark_path)

    targets = [
        ("favicon-96x96.png", 96, FILL_FAVICON),
        ("apple-touch-icon.png", 180, FILL_TOUCH),
        ("web-app-manifest-192x192.png", 192, FILL_MASKABLE),
        ("web-app-manifest-512x512.png", 512, FILL_MASKABLE),
    ]
    for name, size, fill in targets:
        path = os.path.join(ICON_DIR, name)
        render(master, size, fill).save(path, "PNG", optimize=True)
        report(path)

    ico_path = os.path.join(ICON_DIR, "favicon.ico")
    render(master, 256, FILL_FAVICON).save(
        ico_path, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    report(ico_path)


if __name__ == "__main__":
    main()
