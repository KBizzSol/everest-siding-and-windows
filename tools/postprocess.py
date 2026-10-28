#!/usr/bin/env python3
"""Turn the raw WordPress mirror (mirror/) into the deployable static site (site/).

Phase 1 = straight migration, nothing redesigned:
- keeps every original URL (folder/index.html, trailing slash)
- rewrites internal links to root-relative paths (canonical, og:url and JSON-LD stay absolute)
- removes WordPress-only head links that would 404 on static hosting (REST API, oEmbed, RSD, pingback)
- fixes found in the audit (phone links, utility pages noindexed, unreferenced uploads removed)
- writes sitemap_index.xml + page/post sitemaps (Yoast file names), robots.txt (AI crawlers allowed), llms.txt and llms-full.txt
"""
import os, re, sys, shutil, html, glob, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llms  # noqa: E402
import content  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "mirror")
OUT = os.path.join(REPO, "site")
DOM = "everestsidingandwindows.com"
SITE = "https://" + DOM
TODAY = datetime.date.today().isoformat()
DOM_RE = r'(?:www\.)?' + re.escape(DOM)
ASSET_EXT = r'\.(?:css|js|webp|png|jpe?g|gif|svg|woff2?|ttf|eot|otf|mp4|webm|ico|json|pdf)'

# ---------------------------------------------------------------- copy + rename
def copy_tree():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT, ignore=shutil.ignore_patterns("_urls.txt"))
    # strip wget query-suffixes from file names: x.css?ver=1.css -> x.css
    for d, _, files in os.walk(OUT):
        for f in files:
            if "?" in f:
                clean = f.split("?")[0]
                src, dst = os.path.join(d, f), os.path.join(d, clean)
                if not os.path.exists(dst):
                    os.rename(src, dst)
                else:
                    os.remove(src)
    # "/page.html" twins wget may create for "/page/" alongside "/page/index.html"
    for fp in glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True):
        if not fp.endswith("index.html") and os.path.isdir(fp[:-5]) and os.path.exists(os.path.join(fp[:-5], "index.html")):
            os.remove(fp)

# ---------------------------------------------------------------- url rewriting
def to_root(url, file_dir):
    """Return a root-relative URL for an internal reference, else None."""
    u = url.strip()
    if not u or u.lower().startswith(("#", "data:", "mailto:", "tel:", "javascript:", "sms:")):
        return None
    u = u.replace("\\/", "/")
    if re.search(r"""['"`]\s*\+|\+\s*['"`]|\$\{|^'|'$""", u):
        return None  # JavaScript string building (e.g. href="' + file + '"), not a URL
    m = re.match(r'^(?:https?:)?//' + DOM_RE + r'(/.*)?$', u, re.I)
    if m:
        path = m.group(1) or "/"
    elif re.match(r'^(?:[a-z]+:)?//', u, re.I):
        return None  # other domain
    elif u.startswith("/"):
        path = u
    else:
        rel = os.path.relpath(file_dir, OUT)
        rel = "" if rel == "." else rel
        path = "/" + os.path.normpath(os.path.join(rel, u)).replace("\\", "/")
        if u.endswith("/") and not path.endswith("/"):
            path += "/"
        if path == "/.":
            path = "/"
    frag = ""
    if "#" in path:
        path, frag = path.split("#", 1)
        frag = "#" + frag
    for sep in ("%3F", "%3f"):
        if sep in path:
            path = path.split(sep)[0]
    query = ""
    if "?" in path:
        path, query = path.split("?", 1)
        if re.search(ASSET_EXT + "$", path, re.I) or path.startswith(("/wp-content", "/wp-includes")):
            query = ""
        else:
            query = "?" + query
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    path = re.sub(r"/{2,}", "/", path)
    return path + query + frag


def rewrite_attr_urls(s, file_dir):
    def attr(m):
        name, q, val = m.group(1), m.group(2), m.group(3)
        if name.lower().endswith("srcset"):
            parts = []
            for p in val.split(","):
                bits = p.strip().split()
                if not bits:
                    continue
                r = to_root(bits[0], file_dir)
                parts.append(" ".join([r or bits[0]] + bits[1:]))
            return f'{name}={q}{", ".join(parts)}{q}'
        r = to_root(html.unescape(val), file_dir)
        return f'{name}={q}{html.escape(r, quote=False) if r else val}{q}'
    return re.sub(r'\b(href|src|srcset|data-src|data-srcset|data-lazy-src|data-lazy-srcset|data-bg|data-link|poster|action)=(["\'])(.*?)\2',
                  attr, s, flags=re.S)


def rewrite_css_urls(s, file_dir):
    def u(m):
        q, val = m.group(1), m.group(2)
        r = to_root(val, file_dir)
        return f'url({q}{r}{q})' if r else m.group(0)
    return re.sub(r'url\((["\']?)([^"\')]+)\1\)', u, s)


def rewrite_js_absolute(s):
    # JSON-escaped absolute asset URLs inside inline scripts: https:\/\/site.com\/wp-content\/...
    return re.sub(r'https?:\\/\\/' + DOM_RE.replace('\\.', '\\.') + r'\\/(wp-content|wp-includes)', r'\\/\1', s)

# ---------------------------------------------------------------- head
def clean_head(s):
    pats = [r'<link rel=["\']alternate["\'][^>]*(?:oembed|application/json)[^>]*>',
            r'<link rel=["\']https://api\.w\.org/["\'][^>]*>',
            r'<link rel=["\']EditURI["\'][^>]*>', r'<link rel=["\']pingback["\'][^>]*>']
    for p in pats:
        s = re.sub(p, "", s, flags=re.I)
    return s


def protect_ld(s):
    store = []
    def keep(m):
        store.append(m.group(0))
        return f"<!--LD{len(store)-1}-->"
    # JSON-LD and canonical/og/hreflang tags keep their absolute URLs
    s = re.sub(r'<script type=["\']application/ld\+json["\'][^>]*>.*?</script>'
               r'|<link[^>]+rel=["\'](?:canonical|alternate|shortlink)["\'][^>]*>'
               r'|<meta[^>]+(?:property|name)=["\'](?:og:|twitter:|msapplication)[^>]*>', keep, s, flags=re.S | re.I)
    return s, store


def restore_ld(s, store):
    for i, block in enumerate(store):
        s = s.replace(f"<!--LD{i}-->", block)
    return s


def process_html(fp, page_path):
    s = open(fp, encoding="utf-8", errors="ignore").read()
    s, keep = protect_ld(s)
    s = clean_head(s)
    d = os.path.dirname(fp)
    s = rewrite_attr_urls(s, d)
    s = re.sub(r'(<style[^>]*>)(.*?)(</style>)', lambda m: m.group(1) + rewrite_css_urls(m.group(2), d) + m.group(3), s, flags=re.S)
    s = re.sub(r'style=(["\'])(.*?)\1', lambda m: f'style={m.group(1)}{rewrite_css_urls(m.group(2), d)}{m.group(1)}', s, flags=re.S)
    s = rewrite_js_absolute(s)
    s = restore_ld(s, keep)
    s = audit_fixes(s, page_path)
    s = content.page_fixes(s, page_path)
    open(fp, "w", encoding="utf-8").write(s)


# ---------------------------------------------------------------- audit fixes
# Utility pages reached only after a form or from a customer email: keep the URL, keep them out of search.
NOINDEX = {"/thank-you-survey-form/", "/customer-satisfaction-survey/"}


def audit_fixes(s, page_path):
    # broken phone links in a few posts: href="Tel:+1-..." and href="http://Tel:+1-..."
    s = re.sub(r'href=(["\'])(?:https?://)?tel:\+?1?-?\(?(\d{3})\)?[-. ]?(\d{3})[-. ]?(\d{4})\1',
               r'href=\1tel:+1\2\3\4\1', s, flags=re.I)
    if page_path in NOINDEX:
        if re.search(r'<meta name=["\']robots["\']', s):
            s = re.sub(r'(<meta name=["\']robots["\'] content=["\'])[^"\']*', r'\1noindex, follow', s, count=1)
        else:
            s = s.replace("</head>", '<meta name="robots" content="noindex, follow" />\n</head>', 1)
    return s


def prune_unreferenced():
    """Delete files in uploads that no page, stylesheet or script references. Writes tools/junk-removed.txt."""
    text = []
    for f in glob.glob(os.path.join(OUT, "**", "*"), recursive=True):
        if os.path.isfile(f) and re.search(r"\.(html|css|js|xml|txt|json)$", f):
            text.append(open(f, encoding="utf-8", errors="ignore").read())
    text = urllib_unquote("".join(text))
    removed = []
    for f in glob.glob(os.path.join(OUT, "wp-content", "uploads", "**", "*"), recursive=True):
        if os.path.isfile(f) and os.path.basename(f) not in text:
            removed.append(os.path.relpath(f, OUT)); os.remove(f)
    open(os.path.join(HERE, "junk-removed.txt"), "w").write("\n".join(sorted(removed)) + ("\n" if removed else ""))
    print("  unreferenced uploads removed:", len(removed))


def urllib_unquote(s):
    import urllib.parse
    return urllib.parse.unquote(s)


def process_css(fp):
    s = open(fp, encoding="utf-8", errors="ignore").read()
    s2 = rewrite_css_urls(s, os.path.dirname(fp))
    if s2 != s:
        open(fp, "w", encoding="utf-8").write(s2)

# ---------------------------------------------------------------- sitemap + robots
def page_paths():
    out = []
    for fp in glob.glob(os.path.join(OUT, "**", "index.html"), recursive=True):
        rel = os.path.relpath(os.path.dirname(fp), OUT)
        p = "/" if rel == "." else "/" + rel.replace("\\", "/") + "/"
        if p.startswith(("/wp-", "/feed/", "/comments/")) or "/feed/" in p or re.search(r"/page/\d+/$", p):
            continue
        s = open(fp, encoding="utf-8", errors="ignore").read()
        if re.search(r'<meta name=["\']robots["\'] content=["\'][^"\']*noindex', s):
            continue
        out.append(p)
    return sorted(out, key=lambda p: (p != "/", p))


def lastmod(p):
    fp = os.path.join(OUT, p.strip("/"), "index.html") if p != "/" else os.path.join(OUT, "index.html")
    s = open(fp, encoding="utf-8", errors="ignore").read()
    ds = re.findall(r'article:modified_time" content="(\d{4}-\d\d-\d\d)', s) + re.findall(r'"dateModified":\s*"(\d{4}-\d\d-\d\d)', s)
    ds = [d for d in ds if d <= TODAY]
    return max(ds) if ds else TODAY


def is_post(p):
    fp = os.path.join(OUT, p.strip("/"), "index.html") if p != "/" else os.path.join(OUT, "index.html")
    s = open(fp, encoding="utf-8", errors="ignore").read(200000)
    return bool(re.search(r'og:type" content="article"', s) and re.search(r'\bsingle-post\b', s))


def write_seo_files():
    paths = page_paths()
    groups = {"post-sitemap.xml": [p for p in paths if is_post(p)]}
    groups["page-sitemap.xml"] = [p for p in paths if p not in groups["post-sitemap.xml"]]
    index = []
    for name, ps in groups.items():
        if not ps:
            continue
        mods = {p: lastmod(p) for p in ps}
        urls = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{mods[p]}</lastmod></url>" for p in ps)
        open(os.path.join(OUT, name), "w").write(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
        index.append(f"<sitemap><loc>{SITE}/{name}</loc><lastmod>{max(mods.values())}</lastmod></sitemap>")
    open(os.path.join(OUT, "sitemap_index.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(index) + "</sitemapindex>\n")
    bots = ["Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot",
            "Claude-User", "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot", "Applebot-Extended",
            "Amazonbot", "DuckAssistBot"]
    robots = "".join(f"User-agent: {b}\nAllow: /\nDisallow: /wp-admin/\n\n" for b in bots)
    robots += "User-agent: *\nAllow: /\nDisallow: /wp-admin/\n\nSitemap: " + SITE + "/sitemap_index.xml\n"
    open(os.path.join(OUT, "robots.txt"), "w").write(robots)
    # llms.txt + llms-full.txt (AI assistants / answer engines)
    posts = set(groups["post-sitemap.xml"])
    info = {}
    for p in paths:
        fp = os.path.join(OUT, p.strip("/"), "index.html") if p != "/" else os.path.join(OUT, "index.html")
        h = open(fp, encoding="utf-8", errors="ignore").read()
        clean = lambda x: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        d = re.search(r'<meta name=["\']description["\'] content=["\']([^"\']*)', h)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        info[p] = dict(title=clean(t.group(1)).replace(" - Everest Siding and Windows", "") if t else "",
                       desc=clean(d.group(1)) if d else "", h1=clean(h1.group(1)) if h1 else "",
                       text=llms.page_text(h), lastmod=lastmod(p), group=llms.group(p, p in posts))
    open(os.path.join(OUT, "llms.txt"), "w").write(llms.llms_txt(paths, info))
    open(os.path.join(OUT, "llms-full.txt"), "w").write(llms.llms_full(paths, info))
    print("  llms groups:", {g: sum(1 for v in info.values() if v["group"] == g) for g in llms.GROUP_ORDER})
    print("  sitemap urls:", len(paths), {k: len(v) for k, v in groups.items()})


def main():
    print("copy"); copy_tree()
    n = 0
    for fp in glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(fp, OUT).replace("\\", "/")
        page_path = "/" + rel[: -len("index.html")] if rel.endswith("index.html") else "/" + rel
        process_html(fp, page_path); n += 1
    for fp in glob.glob(os.path.join(OUT, "**", "*.css"), recursive=True):
        process_css(fp)
    print("  html files:", n)
    print("guides"); content.build_pages(OUT, SRC, os.path.join(OUT, "faqs", "index.html"))
    print("prune"); prune_unreferenced()
    print("seo files"); write_seo_files()
    if os.environ.get("EV_NO_OPTIMIZE") != "1":
        import optimize, subprocess
        optimize.main()
        node_mods = os.path.join(HERE, "node_modules", "purgecss")
        if os.path.isdir(node_mods):
            subprocess.run(["node", os.path.join(HERE, "purge.mjs"), OUT], check=True)
        else:
            raise SystemExit("purgecss missing: run `npm ci --prefix tools` (or set EV_NO_OPTIMIZE=1 for an unoptimized build)")


if __name__ == "__main__":
    main()
