# Bold Raven

Static, zero-backend NAICS insurance lookup. Type a 6-digit code, press Enter, read
the policy-by-policy reasoning.

Live at [boldraven.work](https://boldraven.work).

Copyright (c) 2026 Vincent Jenei. All rights reserved. See [LICENSE](LICENSE).

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Both views (root input, code display). |
| `styles.css` | Palette and layout. |
| `app.js` | All behaviour. No dependencies. |
| `data.js` | Generated. Every code, title, and policy payload. |
| `build.py` | Regenerates `data.js` from the `NAICS/` tree. |
| `make_logo.py` | Regenerates `icon/logo-mark.png` from the source artwork. |
| `icon/` | Favicon suite, web app manifest, and the derived on-site mark. |
| `NAICS/` | Source data. One folder per code, 8 policy files each. |

## Rebuilding data

Run this after editing anything under `NAICS/`. Nothing else needs to change.

```bash
python build.py
```

It walks every `<code> - <title>` folder, reads the eight `<code><POLICY>.txt` files,
skips empty ones, and writes `data.js`. It exits non-zero and names the file if any
JSON fails to parse.

## The logo

`icon/logo.png` is the master artwork: the raven in `#fbbbad` with an `#ee8695`
beak, on transparency. Every other image is generated from it.

```bash
python make_logo.py
```

That writes `logo-mark.png` (transparent, used on the page) plus the favicon,
touch icon, and manifest icons. The icons are composited onto solid `#292831`
because a `#fbbbad` mark on transparency disappears against a light browser tab
bar. The manifest icons are inset to 66% width so Android's maskable safe zone
cannot clip the wingtips.

Edit `icon/logo.png` and rerun the script to change the branding everywhere.

## Running locally

Open `index.html` directly, or serve the folder:

```bash
python -m http.server 8731
```

Then visit `http://127.0.0.1:8731/`.

## Deploying to GitHub Pages

The repository root is the site root. Push the repo, then in **Settings -> Pages**
set the source to **Deploy from a branch**, branch `main`, folder `/ (root)`.

## Keys

| Key | Action |
| --- | --- |
| Any digit | Types into the input. Digits that cannot lead to a real code are rejected. |
| `Enter` | Opens the code. Incomplete or invalid shakes and clears. |
| `Tab` / `Shift+Tab` | Next / previous policy. |
| `<-` `->` | Next / previous policy. |
| `1`-`8` | Jump directly to a policy. |
| `Home` / `End` | First / last policy. |
| `Esc` | Back to the root page with an empty input. |

## Notes

- No network requests after page load. `data.js` is loaded once with the page.
- Policies with no content render as `NO DATA` and are dimmed in the rail.
- The renderer is schema-driven: `why_this_business`, `loss_scenario`, and
  `rhetorical_question` are labelled `WHY`, `LOSS`, and `ASK`. Any other field in a
  reason is still rendered, labelled from its key. Adding fields later needs no code
  change.
- A code page is linkable: `index.html#111110`.
