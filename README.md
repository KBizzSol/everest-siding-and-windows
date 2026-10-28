# Everest Siding and Windows — static site (Vercel)

An exact static copy of the current everestsidingandwindows.com (WordPress), with the same layout and the **same URLs**. Vercel serves the `site/` folder.

## Folders
| Folder | What it is |
|---|---|
| `mirror/` | Raw copy of the live WordPress site (every sitemap URL plus a crawl, with CSS, JS, images). Source of truth once WordPress is retired. |
| `site/` | The deployed site, generated from `mirror/` by `tools/postprocess.py`. |
| `tools/` | Mirror and build scripts. |
| `.github/workflows/` | `mirror.yml` re-mirrors the live site and rebuilds `site/`; `build.yml` rebuilds `site/` only. |

## Re-mirror the live site
SiteGround's anti-bot captcha blocks GitHub's runners, so the mirror is made in a **Vercel Sandbox** (Vercel's network gets through): clone this repo there, run `tools/mirror.sh` plus `tools/scan_missing.py` / `tools/fetch_missing.py`, tar `mirror/`, serve it, put the URL in `tools/.mirror-url` and push. The **Import mirror from URL** workflow downloads it, rebuilds `site/` and commits; Vercel redeploys automatically.

(`mirror.yml` still works for hosts that don't block GitHub.)

## Rebuild after editing
```
python3 tools/postprocess.py
git add -A && git commit -m "Update site" && git push   # Vercel redeploys automatically
```
To change an original page, edit the file in `mirror/`, then rebuild.

See **AUDIT.md** for the malware/spam/link audit and what was fixed.

## Phase 1 (migration) — what changed vs. WordPress
- **Nothing visible.** Layout, URLs, menus, header, footer, images, Yoast meta and schema are unchanged.
- Internal links point to local root-relative paths; canonical, og and JSON-LD URLs stay absolute.
- WordPress-only head links (REST API, oEmbed, RSD, pingback) were removed because they would 404.
- `sitemap_index.xml`, `page-sitemap.xml`, `post-sitemap.xml` and `robots.txt` are generated from the built pages. `robots.txt` explicitly allows search and AI crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended and others).
- `llms.txt` (business facts + every page, grouped) and `llms-full.txt` (full text of every page) for AI assistants. Business facts live in `tools/llms.py`.
- WordPress system URLs (`/wp-admin/`, `/wp-login.php`, `/xmlrpc.php`, `/wp-json/`, feeds) redirect in `vercel.json`.

## Confirm before pointing the domain here
- **Consultation form:** now posts to `/api/lead` (see Phase 2). Click the FormSubmit activation email the first time a lead arrives.
- **EN/ES switcher:** check the Spanish pages work on the Vercel preview.
- Then add `everestsidingandwindows.com` in Vercel → Project → Domains and update DNS. Do this only after `mirror/` is final, because the live WordPress site is the mirror's source.


## Phase 2 — mobile performance (static, no WordPress code)
The build now strips everything WordPress and serves plain static pages. `tools/postprocess.py` runs `tools/optimize.py` and `tools/purge.mjs` after the copy step (needs `npm i --prefix tools` and `pip install pillow fonttools brotli`; GitHub Actions does this).

**Removed from every page:** jQuery, jQuery Migrate, Divi's scripts (scripts.min.js, sticky, magnific popup, salvattore, fitvids...), Divi Essential (swiper, sliders, before/after), Contact Form 7 + reCAPTCHA, CF7 Conditional Fields, PixelYourSite (no pixel configured), Link Whisper, WordPress polyfills/hooks/i18n, the dead Universal Analytics tag, Google Fonts, the date picker, WordPress REST/oEmbed/feed head links.

**Replaced by `/assets/site.js` (~10 KB):** mobile menu, consultation popup, service tabs, FAQ toggles/accordions, review + logo carousels, Divi sliders and gallery sliders, before/after sliders, gallery lightbox, portfolio filter + search, sticky header, scroll-to-top, clickable blurbs, phone mask, EN/ES (Google Translate loads only when tapped), YouTube previews (player loads on tap), forms.

**Forms:** every Contact Form 7 form posts to `/api/lead` (Vercel function, FormSubmit → info@everestsidingandwindows.com), then fires the same `wpcf7mailsent` event and redirects to the same thank-you pages, so tracking keeps working. Spam: hidden trap field + too-fast check (flagged, not dropped). FormSubmit sends a one-time activation email to the inbox on the first lead.

**Tracking:** both GTM containers, GA4, Microsoft Clarity and the Meta pixel are unchanged, but start on the visitor's first scroll/tap/keypress.

**CSS:** each page's CSS (inline + files) is gathered, purged to the rules that page uses, minified and inlined (no render-blocking requests). Sections below the fold use `content-visibility:auto`.

**Fonts:** Poppins (7 weights) and Noto Sans self-hosted as woff2 with `font-display:swap`; above-the-fold weights preloaded; metric-matched fallback; Divi and Font Awesome icon fonts subset to the icons used (89/199/33/133 KB → 15/29/9/27 KB).

**Photos:** same files, same names and pixel sizes (capped at 1920px wide), recompressed: 168 MB → 56 MB. Below-the-fold images lazy-load; the hero gets a 768px phone copy (`*-ev768.webp`), preloaded.

**Checks (tools/perf/, run in a Vercel Sandbox with Chrome):** `lh.mjs` (Lighthouse mobile + screenshots), `domdiff.mjs` (every Divi section/module size and visibility vs. the original), `interact.mjs` (31 click-through tests: menu, popup, tabs, toggles, sliders, before/after, lightbox, filter, forms → thank-you, tracking delay, translate, sticky header).

Lighthouse mobile, local test server (before → after): home 26 → 97, LP SmartSide 15 → 99, blog post 28 → 100, FAQ 100, contact 99, service area 100, Malarkey 99, portfolio 96. Layout shift 0 on all of them.

## Phase 3 — SEO / AEO content and design (branch `seo`)
**Content (`tools/content.py`)** — built on top of the copied pages at build time, so `mirror/` stays the untouched original.
- Six new guide pages, each with a direct "short answer" up top (what AI answers quote), question-style headings, tables, an FAQ in `<details>` and FAQPage + BreadcrumbList + LocalBusiness schema:
  - `/lp-smartside-siding-cost-houston/`: real prices from Everest's own published project pages (LP SmartSide siding-only jobs since 2024: count, median, range, full table). Recomputed on every build from the portfolio.
  - `/affordable-siding-replacement-houston/`: best price without the cheap bid (fixed price, no change orders, no down payment, lowest bid guarantee, financing).
  - `/lp-smartside-installation-faq/`: step-by-step install + 12 questions (HowTo schema).
  - `/lp-smartside-siding-faq/`: 12 product questions.
  - `/lp-smartside-vs-hardie-plank/` and `/lp-smartside-vs-vinyl-siding/`: comparison tables.
- Tagline band ("Nobody in Texas installs more LP SmartSide than Everest, so nobody gives you a better price on it.") on the homepage under the hero and before the footer on the LP SmartSide, siding, quick quote, payment and promotions pages.
- "Straight answers" link block to the guides on the home, FAQ, LP SmartSide, siding, Hardie, quick quote, cost vs. value, payment and services pages.
- Repair and vinyl: Everest does not repair siding and does not install vinyl siding. Two sentences that implied repairs were reworded; seven vinyl articles get a notice under the title pointing to the LP vs. vinyl page. URLs unchanged.
- `llms.txt` lists the guides first and states no repairs, no vinyl, no down payment, the tagline and where real prices are published.

**Design (`tools/ev.css`)** — layered over Divi on every page.
- Headlines in Archivo (condensed signage style, self-hosted variable font); body stays Poppins.
- Buttons: "free quote" in action green #2E7D3E with a board-edge shadow (white text passes contrast; the old #52AC62 did not), "call" in white with an ink outline and phone icon, other links as quiet outline buttons. Same everywhere, keyboard focus ring.
- Mobile bottom bar: call (ink) | free consultation (green), full width, safe-area aware.
- Promise band: ink background with LP lap-siding shadow lines; two columns on desktop.

**Sources used for competitor research:** Mr. Happy House cost guide and LP vs. Hardie article, All Over TX Roofing cost page, Texas Home Exteriors (LP BuildSmart Platinum), Allied Siding & Windows (Hardie contractor pages), LP warranty comparison (lpcorp.com), Fixr LP SmartSide buyer's guide.
