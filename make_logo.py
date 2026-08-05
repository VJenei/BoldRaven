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
    icon/og-image.png                   1200x630 social card, mark + wordmark

Everything is written into docs/icon/, which is the published site root.

The page background is #292831 and the mark is #fbbbad, so a transparent icon
would vanish against a light browser tab bar. Everything except logo-mark.png is
therefore composited onto a solid #292831 square.
"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

ROOT = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(ROOT, "docs", "icon")
MASTER = os.path.join(ICON_DIR, "logo.png")

BG = (41, 40, 49)           # #292831
TITLE = (238, 134, 149)     # #ee8695

# Facebook, LinkedIn, Slack and X all crop social cards to 1.91:1.
OG_SIZE = (1200, 630)
OG_WORDMARK = "BOLD RAVEN"
OG_TRACKING = 0.62          # em, matching .wordmark in styles.css

# Any bold monospace face is close enough to the site's type. The bundled
# Pillow default is the fallback so the build never depends on system fonts.
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\consolab.ttf",
    r"C:\Windows\Fonts\consola.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
]

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

# Corner radius as a fraction of the icon width, matching the usual rounded
# square convention. Applied ONLY to the favicons, which browsers draw exactly
# as supplied. The touch icon and the manifest icons are left square on purpose:
# iOS and Android apply their own mask, and a pre-rounded icon shows a second
# rounded edge inside theirs.
RADIUS = 0.22

# The mask is drawn large and scaled down so the curve is smooth at 16px.
SUPERSAMPLE = 8


def rounded_mask(size):
    big = size * SUPERSAMPLE
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, big - 1, big - 1), radius=round(big * RADIUS), fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def render(master, size, fill, rounded=False):
    """Centre the mark on a solid square of the given size."""
    canvas = Image.new("RGBA", (size, size), BG + (255,))
    width = max(1, round(size * fill))
    height = max(1, round(master.height * width / master.width))
    art = master.resize((width, height), Image.LANCZOS)
    canvas.paste(art, ((size - width) // 2, (size - height) // 2), art)
    if rounded:
        canvas.putalpha(rounded_mask(size))
    return canvas


def load_font(size):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, ValueError):
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:          # Pillow older than 10.1: bitmap default only
        return ImageFont.load_default()


def draw_tracked(draw, font, text, tracking, centre_x, top):
    """Draw text letter by letter so it carries the wordmark's tracking."""
    widths = [draw.textlength(char, font=font) for char in text]
    gap = font.size * tracking
    total = sum(widths) + gap * (len(text) - 1)
    x = centre_x - total / 2.0
    for char, width in zip(text, widths):
        draw.text((x, top), char, font=font, fill=TITLE)
        x += width + gap


def render_og(master):
    """The 1200x630 card every page points at with og:image."""
    width, height = OG_SIZE
    canvas = Image.new("RGB", OG_SIZE, BG)

    art_width = round(width * 0.26)
    art_height = max(1, round(master.height * art_width / master.width))
    art = master.resize((art_width, art_height), Image.LANCZOS)

    font = load_font(round(height * 0.062))
    block = art_height + round(height * 0.085) + font.size
    top = (height - block) // 2

    canvas.paste(art, ((width - art_width) // 2, top), art)
    draw_tracked(ImageDraw.Draw(canvas), font, OG_WORDMARK, OG_TRACKING,
                 width / 2.0, top + art_height + round(height * 0.085))
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
        ("favicon-96x96.png", 96, FILL_FAVICON, True),
        ("apple-touch-icon.png", 180, FILL_TOUCH, False),
        ("web-app-manifest-192x192.png", 192, FILL_MASKABLE, False),
        ("web-app-manifest-512x512.png", 512, FILL_MASKABLE, False),
    ]
    for name, size, fill, rounded in targets:
        path = os.path.join(ICON_DIR, name)
        render(master, size, fill, rounded).save(path, "PNG", optimize=True)
        report(path)

    og_path = os.path.join(ICON_DIR, "og-image.png")
    render_og(master).save(og_path, "PNG", optimize=True)
    report(og_path)

    ico_path = os.path.join(ICON_DIR, "favicon.ico")
    render(master, 256, FILL_FAVICON, True).save(
        ico_path, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    report(ico_path)


if __name__ == "__main__":
    main()
