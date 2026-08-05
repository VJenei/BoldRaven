# Bold Raven

Static, zero-backend NAICS insurance lookup. Type a 6-digit code, press Enter, read
the policy-by-policy reasoning.

Live at [boldraven.work](https://boldraven.work).

Copyright (c) 2026 Vincent Jenei. All rights reserved. See [LICENSE](LICENSE).

## Layout

Source lives at the repository root. Everything that gets published lives in
`docs/`, which is the site root on GitHub Pages.

| Path | Purpose |
| --- | --- |
| `NAICS/` | Source data. One folder per code, 8 policy files each. |
| `build.py` | Regenerates `docs/data.js` and every page under `docs/naics/`. |
| `pages.py` | Page templates and the sitemap. Called by `build.py`. |
| `make_logo.py` | Regenerates every icon from `docs/icon/logo.png`. |
| `.seo-state.json` | Generated. Per-URL first-seen and last-changed dates. Commit it. |
| `docs/index.html` | The lookup tool. Both views (root input, code display). |
| `docs/styles.css` | Palette and layout, shared by the tool and the pages. |
| `docs/app.js` | The tool's behaviour. No dependencies. |
| `docs/page.js` | Keyboard navigation for the generated pages. |
| `docs/data.js` | Generated. Every code, title, and policy payload. |
| `docs/naics/**` | Generated. One page per code and per policy. |
| `docs/sitemap.xml` | Generated. Every indexable URL. |
| `docs/robots.txt`, `docs/404.html`, `docs/.nojekyll` | Generated. |
| `docs/icon/` | Favicon suite, manifest, on-site mark, social card. |
| `docs/CNAME` | The custom domain. |

## URLs

A URL fragment is not a separate page to a search engine, so the old
`index.html#111110` scheme put the entire site behind one indexable URL. Every code
and every policy is now a real file:

| URL | Page |
| --- | --- |
| `/` | The lookup tool. |
| `/naics/` | Sector directory. |
| `/naics/sector/11-agriculture-forestry-fishing-and-hunting/` | Every code in a sector. |
| `/naics/111120/` | One code, all eight policies. |
| `/naics/111120/cyber-liability/` | One code, one policy. |

The policy slugs are `commercial-auto`, `general-liability`, `professional-liability`,
`workers-compensation`, `cyber-liability`, `business-owners-policy`, `inland-marine`,
and `umbrella`. They are public addresses, so add to them, never rename them.

The tool at `/` still renders instantly from memory, but it pushes these real paths
into the address bar instead of a fragment. A shared or reloaded link therefore lands
on the crawlable page. Old `#111110` links still work and are rewritten on arrival.

## Rebuilding

Run this after editing anything under `NAICS/`. Nothing else needs to change.

```bash
python build.py
```

It walks every `<code> - <title>` folder, reads the eight `<code><POLICY>.txt` files,
skips empty ones, writes `docs/data.js`, then regenerates every page, the sitemap,
`robots.txt`, and `404.html`. Files no longer produced are deleted. It exits non-zero
and names the file if any JSON fails to parse.

Pages for codes and policies with no data yet are still generated, so that every URL
resolves, but they carry `noindex` and stay out of the sitemap. A page becomes
indexable the moment its source file has content. Nothing thin is ever offered to a
crawler.

`.seo-state.json` records a content hash per URL so `lastmod` only advances when a
page actually changes. A `lastmod` that moved on every build would teach crawlers to
ignore the field. Commit the file; deleting it resets every date to the build date.

## The logo

`docs/icon/logo.png` is the master artwork: the raven in `#fbbbad` with an `#ee8695`
beak, on transparency. Every other image is generated from it.

```bash
python make_logo.py
```

That writes `logo-mark.png` (transparent, used on the page), the favicon, touch icon,
manifest icons, and `og-image.png` (the 1200x630 social card). Everything except
`logo-mark.png` is composited onto solid `#292831`, because a `#fbbbad` mark on
transparency disappears against a light browser tab bar. The manifest icons are inset
to 66% width so Android's maskable safe zone cannot clip the wingtips.

Only the favicons get rounded corners, because browsers draw them exactly as
supplied. `apple-touch-icon.png` and the manifest icons stay square: iOS and Android
apply their own mask, and a pre-rounded icon shows a second rounded edge inside
theirs.

Edit `docs/icon/logo.png` and rerun the script to change the branding everywhere.

## Running locally

The site uses root-absolute paths (`/styles.css`, `/naics/...`), so it needs a server
rather than `file://`. Serve `docs/`:

```bash
python -m http.server 8731 --directory docs
```

Then visit `http://127.0.0.1:8731/`.

## Deploying to GitHub Pages

`docs/` is the site root. In **Settings -> Pages** set the source to **Deploy from a
branch**, branch `main`, folder `/docs`.

## Keys

The same keys work in the tool and on the generated pages, except `Tab`, `Home` and
`End`, which are left alone on the pages so ordinary link navigation still works.

| Key | Action |
| --- | --- |
| Any digit | Types into the input. Digits that cannot lead to a real code are rejected. |
| `Enter` | Opens the code. Incomplete or invalid shakes and clears. |
| `Tab` / `Shift+Tab` | Next / previous policy. Tool only. |
| `<-` `->` | Next / previous policy. |
| `1`-`8` | Jump directly to a policy. |
| `Home` / `End` | First / last policy. Tool only. |
| `Esc` | Back to the root page with an empty input. |

## Notes

- The tool makes no network requests after page load. `data.js` is loaded once with
  the page. At full coverage that file lands around 25 MB, so it will need splitting
  into per-code payloads well before then.
- Policies with no content render as `NO DATA` and are dimmed in the rail.
- The renderer is schema-driven: `why_this_business`, `loss_scenario`, and
  `rhetorical_question` are labelled `WHY`, `LOSS`, and `ASK`. Any other field in a
  reason is still rendered, labelled from its key. Adding fields later needs no code
  change. The generated pages follow the same rules.
- The generated pages reuse `styles.css`, so the tool and the pages stay identical in
  appearance without a second stylesheet.
