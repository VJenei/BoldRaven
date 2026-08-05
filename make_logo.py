#!/usr/bin/env python3
"""Derive the on-site logo mark from the source artwork.

    python make_logo.py

The source logo is pure black with a coral beak, which is invisible against the
#292831 page background. This recolours it into the site palette and trims the
transparent margin so it can be sized precisely in CSS.

    body -> #fbbbad   (same tone as body text)
    beak -> #ee8695   (same tone as headings)

Run this again if icon/LogoOriginal.png ever changes.
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(ROOT, "icon", "LogoOriginal.png")
OUTPUT = os.path.join(ROOT, "icon", "logo-mark.png")

BODY = (251, 187, 173)      # #fbbbad
BEAK = (238, 134, 149)      # #ee8695

# A pixel is part of the beak when it is clearly warmer than it is cool.
WARM_THRESHOLD = 40

# Rendered at 256px wide, so 512 keeps it sharp on high-density displays.
TARGET_WIDTH = 512


def main():
    if not os.path.isfile(SOURCE):
        sys.exit("Source artwork not found at " + SOURCE)

    image = Image.open(SOURCE).convert("RGBA")

    box = image.getbbox()
    if box:
        image = image.crop(box)

    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            pixels[x, y] = (BEAK if r - b > WARM_THRESHOLD else BODY) + (a,)

    target_height = max(1, round(height * TARGET_WIDTH / width))
    image = image.resize((TARGET_WIDTH, target_height), Image.LANCZOS)
    image.save(OUTPUT, "PNG", optimize=True)

    size_kb = os.path.getsize(OUTPUT) / 1024.0
    print("wrote %s  %dx%d  %.1f KB" % (
        os.path.relpath(OUTPUT, ROOT), image.width, image.height, size_kb))


if __name__ == "__main__":
    main()
