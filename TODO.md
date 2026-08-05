# TODO

Work deliberately deferred. Each item says why it waits, so nothing here needs
the conversation it came from.

## Blocking now, not deferred

- [ ] **GitHub Pages source folder.** Settings -> Pages -> Deploy from a branch,
      branch `main`, folder `/docs`. The published site moved into `docs/` and
      the live domain 404s until this is changed. Everything else is pushed.

## Once the data is complete

- [ ] **Google Search Console.** Verify a *domain* property for `boldraven.work`
      with a DNS TXT record at the registrar — that covers http, https, and every
      subdomain at once, where the HTML-file method covers only one exact prefix.
      Then submit `https://boldraven.work/sitemap.xml`.

      Submission mostly buys discovery: the site has no inbound links, so Google
      has no path to find it by crawling. It does not guarantee indexing and has
      no direct effect on ranking.

      The reporting is the real payoff, and it is the feedback loop for the SEO
      content pass below:
      - *Page indexing* — which URLs got indexed and the reason for each that did
        not. `Crawled — currently not indexed` means Google looked and judged the
        page not worth keeping.
      - *Performance* — the actual queries, impressions, and average position.
        This is where you find out whether `naics 111120 cyber liability` surfaces
        the page, and at what rank. Runs about 2–3 days behind live.
      - *URL Inspection* — fetch one page as Googlebot, see what it rendered,
        request a recrawl.

      Expect days to weeks for a new domain, not hours. The ~8,900 `noindex`
      placeholder pages will pile up under `Excluded by 'noindex' tag`; they are
      linked from every policy rail so Google crawls them regardless. That is the
      design working, not a fault to chase.

- [ ] **Bing Webmaster Tools.** Same sitemap, roughly five minutes, and it can
      import the Search Console verification.

- [ ] **Split `docs/data.js`.** The tool at `/` loads the entire dataset in one
      file. Extrapolating from the Cyber Liability files, full coverage lands
      somewhere near 20 MB, which makes the front page unusable on anything but a
      fast connection. The generated pages under `/naics/` do not touch this file,
      so only the lookup tool is affected.

      The fix is a small index (codes and titles only, roughly 60 KB) loaded with
      the page, plus a per-code JSON payload fetched on demand. `build.py` already
      has the data shaped for this. Worth doing well before the data is finished
      rather than after — the projection is rough because only CYB files exist to
      measure, and other policies may run longer.

- [ ] **The per-page SEO content pass.** The structural work is done: every code
      and policy has its own URL, unique title and description, canonical, and
      structured data. What decides whether a page actually ranks is the reason
      copy itself — depth, specificity, and matching how the phrase is really
      searched. Use the Search Console *Performance* report to target this rather
      than guessing.
