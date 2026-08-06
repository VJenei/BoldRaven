#!/usr/bin/env python3
"""Generate the crawlable static site under docs/.

Called by build.py; not meant to be run on its own.

Every page the site wants a search engine to rank is a real file at a real path.
URL fragments (the old `index.html#111120`) are not separate URLs to a crawler,
so the whole site used to collapse into one indexable page. The layout below
gives each code and each policy its own document:

    /                                    the lookup tool
    /naics/                              sector directory
    /naics/sector/<slug>/                every code in one sector
    /naics/<code>/                       one code, all eight policies
    /naics/<code>/<policy-slug>/         one code, one policy

Pages with no source data yet are still generated, so that every URL on the site
resolves, but they carry `noindex` and stay out of the sitemap until real content
lands. Nothing thin is ever offered to a crawler.
"""

import hashlib
import json
import os
import re

SITE = "https://boldraven.work"
BRAND = "Bold Raven"
AUTHOR = "Vincent Jenei"

# URL segment for each policy. These are part of the public URL space: changing
# one changes a live address, so they only ever get added to, never edited.
POLICY_SLUGS = {
    "CAU": "commercial-auto",
    "GL": "general-liability",
    "PL": "professional-liability",
    "WC": "workers-compensation",
    "CYB": "cyber-liability",
    "BOP": "business-owners-policy",
    "IM": "inland-marine",
    "UMB": "umbrella",
}

# Reason fields, in render order, with their visible label. A list field is
# rendered as bullets and its label is never shown, so "points" carries none.
FIELD_LABELS = [
    ("points", ""),
    ("why_this_business", "WHY"),
    ("loss_scenario", "LOSS"),
    ("rhetorical_question", "ASK"),
]
REASON_SKIP = {"rank", "headline"}
POLICY_SKIP = {"naics_code", "naics_title", "sector", "policy"}

SECTOR_SPLIT = re.compile(r"^(\S+) - (.+)$")


# --------------------------------------------------------------- small helpers

def esc(text):
    """Escape for HTML text and double-quoted attributes."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def slugify(text):
    text = str(text).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def clip(text, limit=158):
    """Trim to a whole word, for meta descriptions."""
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    space = cut.rfind(" ")
    if space > limit * 0.6:
        cut = cut[:space]
    return cut.rstrip(" .,;:") + "…"


def branded(title):
    """Append the brand only when it still fits a search result.

    Google truncates titles around 600px, roughly 60 characters. Past that the
    brand is cut off anyway and only costs room the industry name needs.
    """
    suffix = " | " + BRAND
    return title + suffix if len(title) + len(suffix) <= 62 else title


def ld_json(obj):
    """Serialise structured data so it cannot break out of its script tag."""
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def split_label(label):
    """'11 - Agriculture, Forestry...' -> ('11', 'Agriculture, Forestry...')."""
    match = SECTOR_SPLIT.match(str(label))
    return (match.group(1), match.group(2)) if match else ("", str(label))


def reasons_of(policy):
    preferred = policy.get("reasons_ranked_by_importance")
    if isinstance(preferred, list):
        return preferred
    for value in policy.values():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value
    return []


def label_for(key):
    return key.replace("_", " ").upper()


# ------------------------------------------------------------------- lastmod

class Stamps:
    """Per-URL first-seen and last-changed dates, keyed by content hash.

    A sitemap `lastmod` that moves every time the site is rebuilt teaches a
    crawler to ignore the field. Dates here only advance when the rendered
    content actually changes, so they stay worth reading.
    """

    def __init__(self, path, today):
        self.path = path
        self.today = today
        try:
            with open(path, encoding="utf-8") as handle:
                self.state = json.load(handle)
        except (OSError, ValueError):
            self.state = {}
        self.seen = {}

    def stamp(self, url, content):
        digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:16]
        previous = self.state.get(url)
        if previous and previous.get("hash") == digest:
            entry = {"hash": digest,
                     "first": previous.get("first", self.today),
                     "last": previous.get("last", self.today)}
        else:
            entry = {"hash": digest,
                     "first": previous.get("first", self.today) if previous else self.today,
                     "last": self.today}
        self.seen[url] = entry
        return entry

    def get(self, url):
        return self.seen.get(url) or {"first": self.today, "last": self.today}

    def save(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self.seen, handle, indent=1, sort_keys=True)
            handle.write("\n")


# ---------------------------------------------------------------------- head

def head(title, description, path, indexable, extra_ld=None, og_type="website"):
    """The shared <head>. `path` is the canonical path, always with a trailing slash."""
    url = SITE + path
    robots = ("index,follow,max-snippet:-1,max-image-preview:large,"
              "max-video-preview:-1") if indexable else "noindex,follow"
    lines = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="dark">',
        '<meta name="theme-color" content="#292831">',
        '<title>%s</title>' % esc(title),
        '<meta name="description" content="%s">' % esc(description),
        '<meta name="author" content="%s">' % esc(AUTHOR),
        '<meta name="robots" content="%s">' % robots,
        '<link rel="canonical" href="%s">' % esc(url),
        '<link rel="icon" href="/icon/favicon.ico" sizes="any">',
        '<link rel="icon" type="image/png" sizes="96x96" href="/icon/favicon-96x96.png">',
        '<link rel="apple-touch-icon" sizes="180x180" href="/icon/apple-touch-icon.png">',
        '<link rel="manifest" href="/icon/site.webmanifest">',
        '<meta property="og:type" content="%s">' % og_type,
        '<meta property="og:site_name" content="%s">' % BRAND,
        '<meta property="og:locale" content="en_US">',
        '<meta property="og:url" content="%s">' % esc(url),
        '<meta property="og:title" content="%s">' % esc(title),
        '<meta property="og:description" content="%s">' % esc(description),
        '<meta property="og:image" content="%s/icon/og-image.png">' % SITE,
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="%s">' % BRAND,
        '<meta name="twitter:card" content="summary_large_image">',
        '<link rel="stylesheet" href="/styles.css">',
    ]
    if extra_ld:
        lines.append('<script type="application/ld+json">%s</script>' % ld_json(extra_ld))
    lines.append('</head>')
    return "\n".join(lines)


def crumbs(trail):
    """Visible breadcrumb plus the matching BreadcrumbList graph node.

    `trail` is a list of (label, path). The last entry is the current page.
    """
    parts = []
    items = []
    for position, (label, path) in enumerate(trail, start=1):
        if position == len(trail):
            parts.append('<span aria-current="page">%s</span>' % esc(label))
        else:
            parts.append('<a href="%s">%s</a>' % (esc(path), esc(label)))
        items.append({"@type": "ListItem", "position": position,
                      "name": str(label), "item": SITE + path})
    html = '<nav class="crumbs" aria-label="Breadcrumb">%s</nav>' % (
        '<span class="sep">/</span>'.join(parts))
    return html, {"@type": "BreadcrumbList", "itemListElement": items}


def site_footer():
    return (
        '<footer class="doc-foot">'
        '<a href="/">%s</a>'
        '<span>&copy; 2026 %s</span>'
        '<span>All rights reserved</span>'
        '</footer>' % (BRAND, esc(AUTHOR))
    )


def publisher_node():
    return {
        "@type": "Organization",
        "@id": SITE + "/#organization",
        "name": BRAND,
        "url": SITE + "/",
        "logo": {"@type": "ImageObject",
                 "url": SITE + "/icon/web-app-manifest-512x512.png",
                 "width": 512, "height": 512},
    }


def website_node():
    return {
        "@type": "WebSite",
        "@id": SITE + "/#website",
        "name": BRAND,
        "url": SITE + "/",
        "inLanguage": "en",
        "publisher": {"@id": SITE + "/#organization"},
    }


# ------------------------------------------------------------------ fragments

def rail(code, policies, present, active=None):
    """The eight-policy sidebar, as real links."""
    out = ['<nav class="rail" aria-label="Policies">']
    for position, (abbr, name, slug) in enumerate(policies, start=1):
        classes = "rail-item"
        if abbr not in present:
            classes += " empty"
        if abbr == active:
            classes += " active"
        href = "/naics/%s/%s/" % (code, slug)
        current = ' aria-current="page"' if abbr == active else ""
        out.append(
            '<a class="%s" href="%s"%s>'
            '<span class="idx">%d</span>'
            '<span class="abbr">%s</span>'
            '<span class="name">%s</span></a>'
            % (classes, href, current, position, esc(abbr), esc(name)))
    out.append('</nav>')
    return "\n".join(out)


def render_fields(pairs):
    if not pairs:
        return ""
    out = ['<dl class="fields">']
    for label, value in pairs:
        out.append('<dt>%s</dt><dd>%s</dd>' % (esc(label), esc(value)))
    out.append('</dl>')
    return "\n".join(out)


def render_points(values):
    return '<ul class="points">%s</ul>' % "".join(
        "<li>%s</li>" % esc(item) for item in values if item not in (None, ""))


def render_reason(reason, position):
    """A list value becomes a bullet list; a scalar becomes a labelled row.

    Blocks come out in field order, so consecutive scalars stay in one <dl>
    and a list breaks out of it.
    """
    rank = reason.get("rank", position)
    headline = reason.get("headline", "")

    ordered = [(key, label, reason.get(key)) for key, label in FIELD_LABELS]
    seen = {key for key, _label in FIELD_LABELS}
    for key, value in reason.items():
        if key in seen or key in REASON_SKIP:
            continue
        ordered.append((key, label_for(key), value))

    blocks = []
    pending = []
    for _key, label, value in ordered:
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            if pending:
                blocks.append(render_fields(pending))
                pending = []
            blocks.append(render_points(value))
            continue
        if isinstance(value, dict):
            value = json.dumps(value, ensure_ascii=False)
        pending.append((label, value))
    if pending:
        blocks.append(render_fields(pending))

    return (
        '<li class="reason">'
        '<div class="reason-head">'
        '<span class="rank">%02d</span>'
        '<h2>%s</h2>'
        '</div>%s</li>' % (int(rank) if str(rank).isdigit() else position,
                           esc(headline), "\n".join(blocks))
    )


# ---------------------------------------------------------------- page bodies

def policy_page(code, record, abbr, name, slug, policies, stamps, today):
    title_text = record["title"]
    sector_label = record["sector"]
    sector_num, sector_name = split_label(sector_label)
    sector_path = "/naics/sector/%s/" % slugify(sector_label)
    path = "/naics/%s/%s/" % (code, slug)
    present = set(record["policies"])
    policy = record["policies"].get(abbr)
    reasons = reasons_of(policy) if policy else []
    indexable = bool(reasons)

    page_title = "NAICS %s %s Insurance | %s" % (code, name, title_text)
    if indexable:
        lead = reasons[0].get("headline", "")
        description = clip("%s for NAICS %s, %s: %s" % (name, code, title_text, lead))
    else:
        page_title = "NAICS %s %s | %s" % (code, name, title_text)
        description = clip("%s coverage notes for NAICS %s, %s. Not yet published."
                           % (name, code, title_text))

    trail = [(BRAND, "/"), ("NAICS", "/naics/"),
             ("%s %s" % (sector_num, sector_name), sector_path),
             (code, "/naics/%s/" % code), (name, path)]
    crumb_html, crumb_ld = crumbs(trail)

    graph = [publisher_node(), website_node(), crumb_ld]
    if indexable:
        entry = stamps.state.get(SITE + path) or {}
        graph.append({
            "@type": "Article",
            "@id": SITE + path + "#article",
            "headline": clip("%s Insurance for NAICS %s: %s" % (name, code, title_text), 110),
            "description": description,
            "url": SITE + path,
            "inLanguage": "en",
            "datePublished": entry.get("first", today),
            "dateModified": entry.get("last", today),
            "author": {"@type": "Person", "name": AUTHOR},
            "publisher": {"@id": SITE + "/#organization"},
            "isPartOf": {"@id": SITE + "/#website"},
            "image": SITE + "/icon/og-image.png",
            "about": {"@type": "Thing",
                      "name": "NAICS %s — %s" % (code, title_text),
                      "identifier": code},
        })
    ld = {"@context": "https://schema.org", "@graph": graph}

    body = [
        head(page_title, description, path, indexable, ld, og_type="article"),
        '<body>',
        '<main class="code-view doc">',
        crumb_html,
        '<header class="code-head">',
        '<span class="code-number">%s</span>' % code,
        '<p class="code-title"><a href="/naics/%s/">%s</a></p>' % (code, esc(title_text)),
        '</header>',
        '<div class="code-body">',
        rail(code, policies, present, active=abbr),
        '<section class="panel">',
        '<div class="policy-head"><h1>%s Insurance for NAICS %s</h1>'
        '<span class="abbr">%s</span></div>' % (esc(name), code, esc(abbr)),
    ]

    if indexable:
        body.append(
            '<p class="lede">Ranked reasons a business in NAICS %s, %s, needs %s '
            'coverage. Each reason is specific to how this industry actually loses '
            'money, and ends with the question to ask before the objection comes '
            'up.</p>' % (code, esc(title_text), esc(name)))
        extras = [(label_for(key), value) for key, value in policy.items()
                  if key not in POLICY_SKIP
                  and not isinstance(value, (dict, list))
                  and value not in (None, "")]
        if extras:
            body.append(render_fields(extras))
        body.append('<ol class="reasons">')
        for position, reason in enumerate(reasons, start=1):
            body.append(render_reason(reason, position))
        body.append('</ol>')
    else:
        body.append('<p class="empty-state">No data</p>')
        body.append(
            '<p class="lede">The %s analysis for NAICS %s is not published yet. '
            'The policies marked below already have one.</p>'
            % (esc(name.lower()), code))

    body += [
        '</section>',
        '</div>',
        '<nav class="pager" aria-label="Related">',
        '<a href="/naics/%s/">All policies for %s</a>' % (code, code),
        '<a href="%s">%s %s</a>' % (esc(sector_path), sector_num, esc(sector_name)),
        '</nav>',
        '<p class="keyhint"><b>1&#8211;8</b> policy <b>&#8592; &#8594;</b> move '
        '<b>ESC</b> home</p>',
        site_footer(),
        '</main>',
        '<script src="/page.js" defer></script>',
        '</body>',
        '</html>',
        '',
    ]
    return "\n".join(body), indexable


def code_page(code, record, policies, neighbours):
    title_text = record["title"]
    sector_label = record["sector"]
    sector_num, sector_name = split_label(sector_label)
    sector_path = "/naics/sector/%s/" % slugify(sector_label)
    path = "/naics/%s/" % code
    present = {abbr for abbr, payload in record["policies"].items()
               if reasons_of(payload)}
    indexable = bool(present)

    page_title = branded("NAICS %s Insurance Requirements — %s" % (code, title_text))
    if indexable:
        named = ", ".join(name for abbr, name, _ in policies if abbr in present)
        description = clip("Why a %s business needs each commercial policy. "
                           "Published: %s." % (title_text.lower(), named))
    else:
        description = clip("NAICS %s, %s. Commercial insurance analysis in progress."
                           % (code, title_text))

    trail = [(BRAND, "/"), ("NAICS", "/naics/"),
             ("%s %s" % (sector_num, sector_name), sector_path), (code, path)]
    crumb_html, crumb_ld = crumbs(trail)
    ld = {"@context": "https://schema.org",
          "@graph": [publisher_node(), website_node(), crumb_ld]}

    body = [
        head(page_title, description, path, indexable, ld),
        '<body>',
        '<main class="code-view doc">',
        crumb_html,
        '<header class="code-head">',
        '<span class="code-number">%s</span>' % code,
        '<h1 class="code-title">%s</h1>' % esc(title_text),
        '</header>',
        '<div class="code-body">',
        rail(code, policies, present),
        '<section class="panel">',
        '<p class="lede">Eight commercial policies, and the specific reason a '
        'business in NAICS %s, %s, needs each one. Pick a policy to read the '
        'ranked reasoning.</p>' % (code, esc(title_text)),
        '<ul class="dir-list">',
    ]
    for abbr, name, slug in policies:
        has = abbr in present
        count = len(reasons_of(record["policies"][abbr])) if has else 0
        note = "%d reason%s" % (count, "" if count == 1 else "s") if has else "No data"
        body.append(
            '<li%s><a href="/naics/%s/%s/"><span class="dir-name">%s '
            'Insurance for NAICS %s</span><span class="dir-note">%s</span></a></li>'
            % ("" if has else ' class="empty"', code, slug, esc(name), code, note))
    body.append('</ul>')
    body.append('</section>')
    body.append('</div>')

    body.append('<nav class="pager" aria-label="Nearby codes">')
    previous_code, next_code = neighbours
    if previous_code:
        body.append('<a href="/naics/%s/">&#8592; %s</a>' % (previous_code, previous_code))
    body.append('<a href="%s">%s %s</a>' % (esc(sector_path), sector_num, esc(sector_name)))
    if next_code:
        body.append('<a href="/naics/%s/">%s &#8594;</a>' % (next_code, next_code))
    body.append('</nav>')
    body += [site_footer(), '</main>', '</body>', '</html>', '']
    return "\n".join(body), indexable


def sector_page(sector_label, codes, records, policies):
    sector_num, sector_name = split_label(sector_label)
    path = "/naics/sector/%s/" % slugify(sector_label)
    live = [code for code in codes
            if any(reasons_of(payload) for payload in records[code]["policies"].values())]
    indexable = bool(live)

    page_title = branded("NAICS Sector %s Insurance by Code — %s"
                         % (sector_num, sector_name))
    description = clip("Every NAICS code in sector %s (%s) and the commercial "
                       "insurance each one needs. %d codes, %d with published analysis."
                       % (sector_num, sector_name, len(codes), len(live)))

    trail = [(BRAND, "/"), ("NAICS", "/naics/"),
             ("%s %s" % (sector_num, sector_name), path)]
    crumb_html, crumb_ld = crumbs(trail)
    ld = {"@context": "https://schema.org",
          "@graph": [publisher_node(), website_node(), crumb_ld]}

    body = [
        head(page_title, description, path, indexable, ld),
        '<body>',
        '<main class="code-view doc">',
        crumb_html,
        '<header class="code-head">',
        '<span class="code-number">%s</span>' % esc(sector_num),
        '<h1 class="code-title">%s</h1>' % esc(sector_name),
        '</header>',
        '<section class="panel wide">',
        '<p class="lede">%d six-digit codes in this sector. %d have published '
        'coverage analysis.</p>' % (len(codes), len(live)),
    ]

    subsector = None
    open_list = False
    for code in codes:
        record = records[code]
        if record["subsector"] != subsector:
            if open_list:
                body.append('</ul>')
            subsector = record["subsector"]
            sub_num, sub_name = split_label(subsector)
            body.append('<h2 class="group">%s <span>%s</span></h2>'
                        % (esc(sub_num), esc(sub_name)))
            body.append('<ul class="dir-list">')
            open_list = True

        published = [(abbr, name, slug) for abbr, name, slug in policies
                     if reasons_of(record["policies"].get(abbr) or {})]
        links = "".join(
            '<a class="chip" href="/naics/%s/%s/">%s</a>' % (code, slug, esc(abbr))
            for abbr, _, slug in published)
        body.append(
            '<li%s><a href="/naics/%s/"><span class="dir-code">%s</span>'
            '<span class="dir-name">%s</span></a>%s</li>'
            % ("" if published else ' class="empty"', code, code,
               esc(record["title"]),
               '<span class="chips">%s</span>' % links if links else ""))
    if open_list:
        body.append('</ul>')

    body += ['</section>',
             '<nav class="pager" aria-label="Related">'
             '<a href="/naics/">All NAICS sectors</a></nav>',
             site_footer(), '</main>', '</body>', '</html>', '']
    return "\n".join(body), indexable


def naics_index_page(sectors, records, order):
    path = "/naics/"
    total = sum(len(codes) for codes in sectors.values())
    live = sum(1 for record in records.values()
               if any(reasons_of(payload) for payload in record["policies"].values()))
    page_title = branded("NAICS Code Directory — Insurance by Industry")
    description = clip("Every NAICS code, grouped by sector, with the specific "
                       "commercial insurance reasoning for each. %d codes across "
                       "%d sectors." % (total, len(sectors)))

    trail = [(BRAND, "/"), ("NAICS", path)]
    crumb_html, crumb_ld = crumbs(trail)
    ld = {"@context": "https://schema.org",
          "@graph": [publisher_node(), website_node(), crumb_ld,
                     {"@type": "CollectionPage",
                      "@id": SITE + path + "#page",
                      "url": SITE + path,
                      "name": page_title,
                      "description": description,
                      "inLanguage": "en",
                      "isPartOf": {"@id": SITE + "/#website"}}]}

    body = [
        head(page_title, description, path, True, ld),
        '<body>',
        '<main class="code-view doc">',
        crumb_html,
        '<header class="code-head">',
        '<span class="code-number">NAICS</span>',
        '<h1 class="code-title">Code Directory</h1>',
        '</header>',
        '<section class="panel wide">',
        '<p class="lede">%d six-digit codes across %d sectors. %d have published '
        'coverage analysis. Pick a sector, then a code, then a policy.</p>'
        % (total, len(sectors), live),
        '<ul class="dir-list">',
    ]
    for label in order:
        codes = sectors[label]
        sector_num, sector_name = split_label(label)
        published = sum(1 for code in codes
                        if any(reasons_of(payload)
                               for payload in records[code]["policies"].values()))
        body.append(
            '<li%s><a href="/naics/sector/%s/">'
            '<span class="dir-code">%s</span>'
            '<span class="dir-name">%s</span>'
            '<span class="dir-note">%d codes &middot; %d published</span></a></li>'
            % ("" if published else ' class="empty"', slugify(label),
               esc(sector_num), esc(sector_name), len(codes), published))
    body += ['</ul>', '</section>', site_footer(), '</main>', '</body>', '</html>', '']
    return "\n".join(body), True


def not_found_page():
    description = "That page does not exist. Look up a NAICS code instead."
    body = [
        head("Not Found | " + BRAND, description, "/404.html", False),
        '<body>',
        '<main class="code-view doc">',
        '<header class="code-head">',
        '<span class="code-number">404</span>',
        '<h1 class="code-title">Not Found</h1>',
        '</header>',
        '<section class="panel">',
        '<p class="lede">No page at that address.</p>',
        '<nav class="pager"><a href="/">Look up a code</a>'
        '<a href="/naics/">Browse every NAICS code</a></nav>',
        '</section>',
        site_footer(), '</main>', '</body>', '</html>', '',
    ]
    return "\n".join(body)


# ------------------------------------------------------------------- writing

def write_if_changed(path, content, written):
    written.add(os.path.normcase(os.path.abspath(path)))
    try:
        with open(path, encoding="utf-8") as handle:
            if handle.read() == content:
                return False
    except OSError:
        pass
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return True


def prune(root, written):
    """Delete generated files that this run did not produce, then empty dirs."""
    removed = 0
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            if os.path.normcase(os.path.abspath(full)) not in written:
                os.remove(full)
                removed += 1
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        if not dirnames and not filenames and dirpath != root:
            os.rmdir(dirpath)
    return removed


# ---------------------------------------------------------------------- build

def build(records, policies, docs_dir, state_path, today):
    """Write every page. `records` is {code: {title, sector, subsector, policies}}."""
    naics_dir = os.path.join(docs_dir, "naics")
    stamps = Stamps(state_path, today)
    written = set()
    changed = 0
    sitemap = []

    # Sectors in numeric code order, codes in numeric order within each.
    sectors = {}
    for code in sorted(records):
        sectors.setdefault(records[code]["sector"], []).append(code)
    order = sorted(sectors, key=lambda label: split_label(label)[0])

    def emit(path_url, disk_path, html, indexable):
        nonlocal changed
        if write_if_changed(disk_path, html, written):
            changed += 1
        entry = stamps.stamp(SITE + path_url, html)
        if indexable:
            sitemap.append((SITE + path_url, entry["last"]))

    # Directory and sector hubs.
    html, indexable = naics_index_page(sectors, records, order)
    emit("/naics/", os.path.join(naics_dir, "index.html"), html, indexable)

    for label in order:
        html, indexable = sector_page(label, sectors[label], records, policies)
        emit("/naics/sector/%s/" % slugify(label),
             os.path.join(naics_dir, "sector", slugify(label), "index.html"),
             html, indexable)

    # Code hubs and policy pages.
    for label in order:
        codes = sectors[label]
        for position, code in enumerate(codes):
            record = records[code]
            neighbours = (codes[position - 1] if position else None,
                          codes[position + 1] if position + 1 < len(codes) else None)
            html, indexable = code_page(code, record, policies, neighbours)
            emit("/naics/%s/" % code,
                 os.path.join(naics_dir, code, "index.html"), html, indexable)

            for abbr, name, slug in policies:
                html, indexable = policy_page(code, record, abbr, name, slug,
                                              policies, stamps, today)
                emit("/naics/%s/%s/" % (code, slug),
                     os.path.join(naics_dir, code, slug, "index.html"),
                     html, indexable)

    removed = prune(naics_dir, written)

    # The home page is hand-maintained, but it still belongs in the sitemap.
    home = os.path.join(docs_dir, "index.html")
    if os.path.isfile(home):
        with open(home, encoding="utf-8") as handle:
            entry = stamps.stamp(SITE + "/", handle.read())
        sitemap.insert(0, (SITE + "/", entry["last"]))

    stamps.save()

    if len(sitemap) > 45000:
        raise SystemExit("sitemap has %d URLs; split it before it hits the "
                         "50,000 limit" % len(sitemap))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lastmod in sitemap:
        lines.append('<url><loc>%s</loc><lastmod>%s</lastmod></url>' % (esc(url), lastmod))
    lines += ['</urlset>', '']
    write_if_changed(os.path.join(docs_dir, "sitemap.xml"), "\n".join(lines), set())

    robots = "\n".join([
        "User-agent: *",
        "Allow: /",
        "",
        "Sitemap: %s/sitemap.xml" % SITE,
        "",
    ])
    write_if_changed(os.path.join(docs_dir, "robots.txt"), robots, set())
    write_if_changed(os.path.join(docs_dir, "404.html"), not_found_page(), set())
    write_if_changed(os.path.join(docs_dir, ".nojekyll"), "", set())

    return {"pages": len(written), "changed": changed, "removed": removed,
            "indexable": len(sitemap)}
