#!/usr/bin/env python3
"""Mobile-first performance pass over site/ (run after postprocess builds it).

Never touches mirror/. Every step keeps URLs, layout and photos the same:
 1. scripts   - drops jQuery, Divi, WordPress and plugin scripts; adds /assets/site.js (their replacement);
                tracking tags (GTM, GA4, Clarity, Meta pixel) are kept but run on the first interaction
 2. css       - gathers each page's CSS (inline + local files) into one block, marked for purging
                (tools/purge.mjs keeps only the rules the page uses, minifies and inlines it)
 3. fonts     - Google Fonts link replaced by self-hosted Poppins (font-display: swap)
 4. images    - lazy-loading below the fold, async decoding, preloaded hero, phone-sized hero background
 5. photos    - every JPG/PNG/WebP recompressed in place (same file name, same pixel size unless huge)
"""
import os, re, sys, glob, json, hashlib, html as H, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "site")
BUILD = os.path.join(OUT, "_ev")              # temporary per-page CSS for purge.mjs (removed by it)

SITE_JS = open(os.path.join(HERE, "site.js"), encoding="utf-8").read()
JS_VER = hashlib.md5(SITE_JS.encode()).hexdigest()[:10]

# inline scripts that are tracking tags: kept, but run on first interaction
TRACKER_PAT = re.compile(r"googletagmanager\.com/gtm\.js|gtag\(|clarity\.ms/tag|connect\.facebook\.net/[^'\"]+/fbevents\.js")
TRACKER_SRC = re.compile(r"googletagmanager\.com/gtag/js")
# inline scripts that are dead (Universal Analytics stopped in 2024) or only feed removed WordPress code
DROP_INLINE = re.compile(r"ga\('create'|analytics\.js")
# page scripts that are plain JavaScript and still needed: Quick Quote calculator, blog archive dropdown
KEEP_INLINE = re.compile(r"function do_math|block_core_archives_build_dropdown_script")

FONT_CSS = None


def fonts_css():
    """@font-face for the self-hosted Poppins weights in tools/vendor/fonts."""
    global FONT_CSS
    if FONT_CSS is None:
        out = []
        names = {"poppins": "Poppins", "noto-sans": "Noto Sans"}
        for f in sorted(glob.glob(os.path.join(HERE, "vendor", "fonts", "*-latin-*.woff2"))):
            m = re.search(r"([a-z-]+)-latin-(\d+)-(normal|italic)\.woff2", os.path.basename(f))
            if not m or m.group(1) not in names:
                continue
            out.append("@font-face{font-family:'%s';font-style:%s;font-weight:%s;font-display:swap;src:url(/assets/fonts/%s) format('woff2')}"
                       % (names[m.group(1)], m.group(3), m.group(2), os.path.basename(f)))
        out.append("@font-face{font-family:'Poppins Fallback';src:local('Arial');size-adjust:112.5%;ascent-override:93%;descent-override:31%;line-gap-override:9%}")
        FONT_CSS = "".join(out)
    return FONT_CSS


def local_file(href):
    p = H.unescape(href).split("?")[0].split("#")[0]
    if not p.startswith("/") or p.startswith("//"):
        return None
    f = os.path.join(OUT, p.lstrip("/"))
    return f if os.path.isfile(f) else None


def css_from_file(f):
    return open(f, encoding="utf-8", errors="ignore").read()


# ---------------------------------------------------------------- per page
def optimize_page(fp):
    s = open(fp, encoding="utf-8", errors="ignore").read()
    if "<head" not in s:
        return
    head_end = s.find("</head>")
    had_faq_script = 'kbs-faqs .et_pb_toggle:first-child' in s

    # ---- 1. scripts
    trackers = []

    def script(m):
        tag, attrs, body = m.group(0), m.group(1), m.group(2)
        src = re.search(r'\bsrc=["\']([^"\']+)', attrs)
        typ = (re.search(r'\btype=["\']([^"\']+)', attrs) or [None, ""])[1].lower()
        if typ in ("application/ld+json", "speculationrules"):
            return tag
        if src:
            if TRACKER_SRC.search(src.group(1)):
                trackers.append('<script type="text/ev-delay" data-src="%s"></script>' % H.escape(H.unescape(src.group(1)), quote=True))
            return ""
        if DROP_INLINE.search(body):
            return ""
        if KEEP_INLINE.search(body) and "jQuery" not in body:
            return tag
        if TRACKER_PAT.search(body):
            trackers.append('<script type="text/ev-delay">%s</script>' % body)
            return ""
        lk = re.search(r"var et_link_options_data\s*=\s*(\[.*?\]);", body, re.S)
        if lk:
            return "<script>window.EV_LINKS=%s;</script>" % lk.group(1)
        return ""
    s = re.sub(r"<script\b([^>]*)>(.*?)</script>", script, s, flags=re.S | re.I)

    # ---- 2. css: collect every stylesheet and <style> in document order
    parts = []

    def css_tag(m):
        tag = m.group(0)
        if tag.lower().startswith("<style"):
            body = re.sub(r"^<style[^>]*>|</style>$", "", tag, flags=re.I | re.S)
            parts.append(body)
            return "\x00"
        href = re.search(r'href=["\']([^"\']+)', tag)
        rel = (re.search(r'rel=["\']([^"\']+)', tag) or [None, ""])[1].lower()
        as_ = (re.search(r'\bas=["\']([^"\']+)', tag) or [None, ""])[1].lower()
        if not href:
            return tag
        h = href.group(1)
        is_css = rel == "stylesheet" or (rel == "preload" and as_ == "style")
        if not is_css:
            if rel in ("dns-prefetch", "preconnect") and ("fonts.g" in h or "translate" in h):
                return ""
            return tag
        if "fonts.googleapis.com" in h or "cdnjs.cloudflare.com" in h:
            return ""                                   # Poppins self-hosted below; datepicker CSS unused
        f = local_file(h)
        if f:
            parts.append(css_from_file(f))
        return "\x00" if f else ""
    s = re.sub(r"<style\b[^>]*>.*?</style>|<link\b[^>]*>", css_tag, s, flags=re.S | re.I)
    # remove the noscript copies of stylesheet links Divi adds
    s = re.sub(r"<noscript>\s*(?:<link[^>]*>\s*)+</noscript>", "", s, flags=re.I)

    # WordPress-only head links: feeds, oEmbed, REST API, shortlink, generator
    s = re.sub(r'<link\b[^>]*rel=["\'](?:alternate|shortlink|EditURI|pingback|https://api\.w\.org/)["\'][^>]*(?:rss\+xml|oembed|application/json|shortlink|api\.w\.org|xmlrpc|wp-json|/feed/)?[^>]*>',
               lambda m: "" if re.search(r'rss\+xml|oembed|json|shortlink|api\.w\.org|xmlrpc|wp-json|/feed/|EditURI|pingback', m.group(0), re.I) else m.group(0), s, flags=re.I)
    s = re.sub(r'<meta\b[^>]*name=["\']generator["\'][^>]*>', "", s, flags=re.I)

    # accordions start closed (what Divi's script did on load), done in HTML so nothing jumps
    def faqs_closed(src):
        out, pos = [], 0
        for m in re.finditer(r'class="[^"]*\bet_pb_accordion\b[^"]*\bkbs-faqs\b[^"]*"', src):
            nxt = re.compile(r'class="([^"]*\bet_pb_accordion_item\b[^"]*)\bet_pb_toggle_open\b').search(src, m.end())
            if not nxt or nxt.start() < pos:
                continue
            out.append(src[pos:nxt.start()]); out.append('class="' + nxt.group(1) + 'et_pb_toggle_close'); pos = nxt.end()
        out.append(src[pos:])
        return "".join(out)
    if had_faq_script:      # only pages that had that script
        s = faqs_closed(s)
    # blog filter plugin (portfolio): items were hidden until Filterizr ran
    s = re.sub(r'(<div\b[^>]*?)\s*style="opacity:\s*0;?"([^>]*class="[^"]*\b(?:filtr-item|bfg_theme_1)\b)', r'\1\2', s)
    s = re.sub(r'(<div\b[^>]*class="[^"]*\b(?:filtr-item|bfg_theme_1)\b[^"]*"[^>]*?)\s*style="opacity:\s*0;?"', r'\1', s)
    s = re.sub(r'class="post-box ', 'class="post-box lazyimg ', s)
    nfig = [0]
    def lazy_fig(m):
        nfig[0] += 1
        if nfig[0] <= 2:
            return m.group(0)
        return '%s data-ev-bg="%s"' % (m.group(1), m.group(2))
    s = re.sub(r'(<figure class="snip\d+[^"]*")\s*style="background-image:\s*url\(([^)]+)\)"', lazy_fig, s)

    # YouTube: thumbnail + play button; the player (about 1 MB) loads on tap
    def yt(m):
        tag = m.group(0)
        src = H.unescape(re.search(r'src=["\']([^"\']+)', tag).group(1))
        vid = re.search(r"youtube(?:-nocookie)?\.com/embed/([\w-]{6,})", src)
        if not vid:
            return tag
        title = re.search(r'title=["\']([^"\']*)', tag)
        title = title.group(1) if title else "YouTube video"
        w_ = re.search(r'width=["\'](\d+)', tag); h_ = re.search(r'height=["\'](\d+)', tag)
        ratio = "%s/%s" % (w_.group(1), h_.group(1)) if w_ and h_ else "16/9"
        play = "https://www.youtube.com/embed/%s?autoplay=1&rel=0" % vid.group(1)
        return ('<div class="ev-yt" data-src="%s" data-title="%s" style="aspect-ratio:%s">'
                '<img loading="lazy" decoding="async" src="https://i.ytimg.com/vi/%s/hqdefault.jpg" alt="%s">'
                '<button type="button" class="ev-yt-play" aria-label="Play video: %s"></button></div>'
                % (H.escape(play, quote=True), title, ratio, vid.group(1), title, title))
    s = re.sub(r"<iframe\b[^>]*youtube(?:-nocookie)?\.com/embed/[^>]*>\s*</iframe>", yt, s, flags=re.I)

    # Divi "multi view" (different image/text per device), resolved in HTML: no JS, no layout shift
    def mv_img(m):
        tag = m.group(0)
        raw = re.search(r'data-et-multi-view="([^"]+)"', tag)
        try:
            data = json.loads(H.unescape(raw.group(1)))
            attrs = data["schema"]["attrs"]
        except Exception:
            return tag
        img = re.sub(r'\s*data-et-multi-view(?:-load-[a-z]+-hidden)?="[^"]*"', "", tag)
        srcs = ""
        for dev, mq in (("phone", "(max-width:767px)"), ("tablet", "(max-width:980px)")):
            a = attrs.get(dev)
            if a and (a.get("srcset") or a.get("src")):
                srcs += '<source media="%s" srcset="%s"%s>' % (mq, H.escape(a.get("srcset") or a["src"], quote=True),
                                                            (' sizes="%s"' % H.escape(a["sizes"], quote=True)) if a.get("sizes") else "")
        return "<picture>%s%s</picture>" % (srcs, img) if srcs else img
    s = re.sub(r"<img\b[^>]*data-et-multi-view=[^>]*>", mv_img, s)

    def mv_content(m):
        open_tag, inner = m.group(1), m.group(3)
        raw = re.search(r'data-et-multi-view="([^"]+)"', open_tag)
        try:
            content = json.loads(H.unescape(raw.group(1)))["schema"]["content"]
        except Exception:
            return m.group(0)
        clean = re.sub(r'\s*data-et-multi-view(?:-load-[a-z]+-hidden)?="[^"]*"', "", open_tag)
        d_ = content.get("desktop", inner); t_ = content.get("tablet", d_); p_ = content.get("phone", t_)
        if d_ == t_ == p_:
            return clean + d_ + "</div>"
        parts = []
        if p_ != t_:
            parts.append('<div class="ev-mv ev-mv-p">%s</div>' % p_)
            parts.append('<div class="ev-mv ev-mv-t">%s</div>' % t_ if t_ != d_ else "")
        elif t_ != d_:
            parts.append('<div class="ev-mv ev-mv-pt">%s</div>' % t_)
        parts.append('<div class="ev-mv %s">%s</div>' % ("ev-mv-d" if t_ != d_ else "ev-mv-td", d_))
        return clean + "".join(parts) + "</div>"
    s = re.sub(r'(<div\b[^>]*data-et-multi-view="[^"]*"[^>]*>)((.*?))</div>(?=\s*</div>)', mv_content, s, flags=re.S)

    # ---- 3. carousel layout before JS (no layout shift): slides per view from data-breakpoints
    extra = [fonts_css(), STATIC_CSS]
    n = [0]

    def carousel(m):
        attrs = m.group(1)
        bp = re.search(r'data-breakpoints="([\d|]+)"', attrs)
        gap = re.search(r'data-spacing="(\d+)"', attrs)
        if not bp:
            return m.group(0)
        n[0] += 1
        cls = "ev-c%d" % n[0]
        p = [int(x or 1) for x in bp.group(1).split("|")] + [1, 1]
        g = int(gap.group(1)) if gap else 0
        rule = lambda k: ".%s>.swiper-wrapper>*{flex:0 0 calc((100%% - %dpx)/%d);margin-right:%dpx}" % (cls, g * (k - 1), k, g)
        extra.append("%s@media(min-width:768px){%s}@media(min-width:981px){%s}" % (rule(p[2] or 1), rule(p[1] or 1), rule(p[0] or 1)))
        new = re.sub(r'class="swiper-container', 'class="swiper-container ' + cls, m.group(0), count=1)
        return new
    s = re.sub(r'<div ([^>]*class="swiper-container[^"]*"[^>]*)>', carousel, s)

    # ---- 4. images
    hero = hero_preload(parts)
    count = [0]

    def img(m):
        tag = m.group(0)
        count[0] += 1
        in_header = count[0] <= HEADER_IMGS[0]
        if "loading=" not in tag and not in_header:
            tag = tag.replace("<img ", '<img loading="lazy" ', 1)
        if "decoding=" not in tag:
            tag = tag.replace("<img ", '<img decoding="async" ', 1)
        return tag
    HEADER_IMGS[0] = header_img_count(s)
    s = re.sub(r"<img\b[^>]*>", img, s, flags=re.I)
    # iframes (maps, video) load when scrolled near
    s = re.sub(r"<iframe(?![^>]*loading=)(?![^>]*googletagmanager)", '<iframe loading="lazy"', s, flags=re.I)

    # ---- assemble head
    css_id = hashlib.md5(fp.encode()).hexdigest()[:12]
    os.makedirs(BUILD, exist_ok=True)
    open(os.path.join(BUILD, css_id + ".css"), "w", encoding="utf-8").write("\n".join(parts) + "\n" + "".join(extra))
    head_bits = ""
    head_bits += '<link rel="preload" href="/assets/fonts/poppins-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>'
    head_bits += hero
    head_bits += "<!--EV-CSS:%s-->" % css_id
    head_bits += '<script defer src="/assets/site.js?v=%s"></script>' % JS_VER
    s = s.replace("\x00", "", 0)
    first = s.find("\x00")
    s = s.replace("\x00", "")
    if first >= 0 and first < s.find("</head>"):
        s = s[:first] + head_bits + s[first:]
    else:
        s = s.replace("</head>", head_bits + "</head>", 1)
    if trackers:
        s = s.replace("</body>", "".join(trackers) + "</body>", 1)
    s = re.sub(r"\n\s*\n+", "\n", s)
    open(fp, "w", encoding="utf-8").write(s)


HEADER_IMGS = [0]


def header_img_count(s):
    """Images above the fold that must not be lazy: header logos + images in the first content section."""
    end = s.find("</header>")
    n = len(re.findall(r"<img\b", s[:end])) if end > 0 else 0
    first = re.search(r'<div class="et_pb_section et_pb_section_0[ "]', s[end:] if end > 0 else s)
    if first:
        start = (end if end > 0 else 0) + first.start()
        nxt = re.search(r'<div class="et_pb_section et_pb_section_1[ "]', s[start:])
        stop = start + nxt.start() if nxt else start + 20000
        n += len(re.findall(r"<img\b", s[start:stop]))
    return n


HERO_DONE = {}


def hero_preload(parts):
    """Find the first section's background image, make a phone-sized copy, preload it."""
    css = "\n".join(parts)
    m = re.search(r"div\.et_pb_section\.et_pb_section_0\{[^}]*?url\((/wp-content/uploads/[^)]+)\)", css) or \
        re.search(r"\.et_pb_section_0(?:\.et_pb_section)?\{[^}]*?background-image:[^}]*?url\((/wp-content/uploads/[^)]+)\)", css)
    if not m:
        return ""
    url = m.group(1).strip("'\"")
    small = phone_variant(url)
    if not small:
        return '<link rel="preload" as="image" href="%s" fetchpriority="high">' % url
    PHONE_BG.append((url, small))
    return '<link rel="preload" as="image" href="%s" media="(max-width:767px)" fetchpriority="high">' % small


PHONE_BG = []


def phone_variant(url):
    """bg.webp -> bg-ev768.webp (768px wide), created once."""
    if url in HERO_DONE:
        return HERO_DONE[url]
    f = os.path.join(OUT, url.lstrip("/"))
    if not os.path.isfile(f):
        HERO_DONE[url] = None
        return None
    try:
        from PIL import Image
        im = Image.open(f)
        if im.width <= 900:
            HERO_DONE[url] = None
            return None
        root, ext = os.path.splitext(url)
        small = root + "-ev768" + ext
        dst = os.path.join(OUT, small.lstrip("/"))
        if not os.path.exists(dst):
            h = round(im.height * 768 / im.width)
            sm = im.convert("RGB").resize((768, h), Image.LANCZOS)
            if ext.lower() == ".webp":
                sm.save(dst, "WEBP", quality=70, method=6)
            elif ext.lower() in (".jpg", ".jpeg"):
                sm.save(dst, "JPEG", quality=72, optimize=True, progressive=True)
            else:
                sm.save(dst, optimize=True)
        HERO_DONE[url] = small
        return small
    except Exception as e:
        print("  hero variant failed", url, e)
        HERO_DONE[url] = None
        return None


# styles that replace what Divi's JavaScript used to do at runtime
STATIC_CSS = (
    # sticky header (Divi sticky module) without JS
    "header.et-l--header{position:sticky;top:0;z-index:99}"
    "#page-container{overflow-y:visible!important;overflow-x:clip}"
    # gallery grids are revealed by Divi JS
    ".et_pb_gallery_grid .et_pb_gallery_item{display:block}"
    # carousels: slides in a row before/after JS
    ".ev-carousel,.swiper-container{overflow:hidden;position:relative}"
    ".swiper-container>.swiper-wrapper{display:flex}"
    # before/after
    ".ev-ba{position:relative;overflow:hidden;line-height:0}.ev-ba .dnxte_af_img img,.ev-ba .dnxte_bf_img img{width:100%;height:auto;display:block}"
    ".ev-ba .dnxte_bf_img{position:absolute;inset:0;z-index:2}.ev-ba .dnxte_af_img{position:relative;z-index:1}"
    ".ev-ba-handle{position:absolute;top:0;bottom:0;width:4px;margin-left:-2px;background:#fff;z-index:4;pointer-events:none;box-shadow:0 0 6px rgba(0,0,0,.35)}"
    ".ev-ba-handle:after{content:'';position:absolute;top:50%;left:50%;width:38px;height:38px;margin:-19px 0 0 -19px;border:3px solid #fff;border-radius:50%;background:rgba(0,0,0,.25)}"
    ".ev-ba-range{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:ew-resize;z-index:5;margin:0}"
    ".ev-ba-label{position:absolute;top:50%;transform:translateY(-50%);z-index:3;background:rgba(255,255,255,.2);color:#fff;padding:0 18px;line-height:38px;font-size:13px;letter-spacing:.1em;text-transform:uppercase}"
    ".ev-ba-before{left:10px}.ev-ba-after{right:10px}"
    # lightbox
    ".ev-lightbox{position:fixed;inset:0;background:rgba(0,0,0,.88);display:none;align-items:center;justify-content:center;z-index:100000}"
    ".ev-lightbox.open{display:flex}.ev-lightbox img{max-width:92vw;max-height:86vh;width:auto;height:auto}"
    ".ev-lightbox button{position:absolute;background:none;border:0;color:#fff;font-size:44px;line-height:1;cursor:pointer;padding:12px}"
    ".ev-lb-close{top:8px;right:12px}.ev-lb-prev{left:6px;top:50%;transform:translateY(-50%)}.ev-lb-next{right:6px;top:50%;transform:translateY(-50%)}"
    # videos (fitvids)
    ".et_pb_video_box iframe,.fluid-width-video-wrapper iframe{width:100%;aspect-ratio:16/9;height:auto}"
    # form messages
    ".wpcf7 form .wpcf7-response-output:empty{display:none}"
    # blog filter plugin: no loader, items visible
    ".blog_loader{display:none!important}.bfg_theme_1{opacity:1!important}.filtr-container{display:flex;flex-wrap:wrap}"
    "html{scroll-padding-top:120px}"
    # YouTube preview
    ".ev-yt{position:relative;width:100%;background:#000;cursor:pointer;overflow:hidden}.ev-yt img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}"
    ".ev-yt-play{position:absolute;left:50%;top:50%;width:68px;height:48px;margin:-24px 0 0 -34px;border:0;border-radius:12px;background:#f00;cursor:pointer}"
    ".ev-yt-play:after{content:'';position:absolute;left:27px;top:14px;border-style:solid;border-width:10px 0 10px 17px;border-color:transparent transparent transparent #fff}"
    ".ev-yt iframe{position:absolute;inset:0;width:100%;height:100%;border:0}"
    # device-specific content (Divi multi view)
    ".ev-mv-p,.ev-mv-t,.ev-mv-pt{display:none}@media(max-width:767px){.ev-mv-p,.ev-mv-pt{display:block}.ev-mv-t,.ev-mv-td,.ev-mv-d{display:none}}"
    "@media(min-width:768px) and (max-width:980px){.ev-mv-t,.ev-mv-pt,.ev-mv-td{display:block}.ev-mv-p,.ev-mv-d{display:none}}"
    "#et-main-area .et_builder_inner_content>.et_pb_section:not(:first-child):not(.et_pb_section_0){content-visibility:auto;contain-intrinsic-size:auto 900px}"
    ".et-l--footer .et_builder_inner_content>.et_pb_section{content-visibility:visible}"
)


# ---------------------------------------------------------------- photos
def compress_images():
    """Recompress uploads in place: same file name and format; cap very large images at 1920px wide."""
    from PIL import Image
    cache_f = os.path.join(HERE, ".imgcache.json")
    try:
        cache = json.load(open(cache_f))
    except Exception:
        cache = {}
    before = after = n = 0
    for f in glob.glob(os.path.join(OUT, "wp-content", "uploads", "**", "*"), recursive=True):
        ext = os.path.splitext(f)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp") or "-ev768" in f:
            continue
        raw = open(f, "rb").read()
        key = hashlib.md5(raw).hexdigest()
        rel = os.path.relpath(f, OUT)
        before += len(raw)
        if cache.get(rel) == key:              # already optimized output
            after += len(raw)
            continue
        try:
            im = Image.open(f)
            im.load()
            if getattr(im, "is_animated", False):
                after += len(raw); continue
            if im.width > 1920:
                im = im.resize((1920, round(im.height * 1920 / im.width)), Image.LANCZOS)
            import io
            buf = io.BytesIO()
            if ext == ".webp":
                im.save(buf, "WEBP", quality=75, method=4)
            elif ext in (".jpg", ".jpeg"):
                im.convert("RGB").save(buf, "JPEG", quality=76, optimize=True, progressive=True)
            else:
                if im.mode in ("RGBA", "LA", "P"):
                    im.save(buf, "PNG", optimize=True)
                else:
                    im.convert("RGB").save(buf, "PNG", optimize=True)
            data = buf.getvalue()
            if len(data) < len(raw) * 0.95:
                open(f, "wb").write(data)
                raw = data
                n += 1
            cache[rel] = hashlib.md5(raw).hexdigest()
            after += len(raw)
        except Exception as e:
            after += len(raw)
    json.dump(cache, open(cache_f, "w"), indent=0, sort_keys=True)
    print("  photos recompressed: %d, %.1f MB -> %.1f MB" % (n, before / 1e6, after / 1e6))


def phone_backgrounds():
    """Point phones at the small hero copies (added to each page's CSS before purging)."""
    rules = []
    for big, small in sorted(set(PHONE_BG)):
        rules.append((big, small))
    return rules


ICON_FONTS = {
    # family -> (original file used by the site, subset name)
    "ETmodules": ("wp-content/themes/Divi/core/admin/fonts/modules/all/modules.ttf", "assets/fonts/etmodules-ev.woff2"),
    "FontAwesome-solid": ("wp-content/themes/Divi/core/admin/fonts/fontawesome/fa-solid-900.ttf", "assets/fonts/fa-solid-ev.woff2"),
    "FontAwesome-regular": ("wp-content/themes/Divi/core/admin/fonts/fontawesome/fa-regular-400.ttf", "assets/fonts/fa-regular-ev.woff2"),
    "FontAwesome-brands": ("wp-content/themes/Divi/core/admin/fonts/fontawesome/fa-brands-400.ttf", "assets/fonts/fa-brands-ev.woff2"),
}
ICON_DONE = {}


def used_icon_codepoints():
    """Every codepoint an icon could use: CSS content values, data-icon attributes, text of icon elements."""
    cps = set()
    for f in glob.glob(os.path.join(OUT, "**", "*.css"), recursive=True) + glob.glob(os.path.join(BUILD, "*.css")):
        t = open(f, encoding="utf-8", errors="ignore").read()
        for v in re.findall(r'content:\s*(?:"([^"]*)"|\'([^\']*)\')', t):
            for ch in re.sub(r"\\([0-9a-fA-F]{1,6})\s?", lambda m: chr(int(m.group(1), 16)), v[0] or v[1]):
                cps.add(ord(ch))
    for f in glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True):
        t = open(f, encoding="utf-8", errors="ignore").read()
        for v in re.findall(r'data-icon(?:-[a-z]+)?=["\']([^"\']*)["\']', t):
            cps.update(ord(c) for c in H.unescape(v))
        for v in re.findall(r'class="[^"]*\b(?:et-pb-icon|et_pb_font_icon|fa|fas|far|fab)\b[^"]*"[^>]*>([^<]{1,8})<', t):
            cps.update(ord(c) for c in H.unescape(v))
    cps.update(range(0x20, 0x7F))           # ASCII (Divi maps some icons to letters)
    return cps


def subset_icon_fonts():
    try:
        from fontTools import subset
    except ImportError:
        print("  icon font subsetting skipped (pip install fonttools brotli)")
        return
    cps = used_icon_codepoints()
    for fam, (src, dst) in ICON_FONTS.items():
        f = os.path.join(OUT, src)
        if not os.path.isfile(f):
            continue
        out = os.path.join(OUT, dst)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]; opts.notdef_outline = True
        try:
            font = subset.load_font(f, opts)
            sub = subset.Subsetter(opts); sub.populate(unicodes=sorted(cps)); sub.subset(font)
            subset.save_font(font, out, opts)
            ICON_DONE[src.rsplit(".", 1)[0]] = "/" + dst
            print("  icon font %s: %d KB -> %d KB" % (fam, os.path.getsize(f) // 1024, os.path.getsize(out) // 1024))
        except Exception as e:
            print("  icon font %s failed: %s" % (fam, e))


def swap_icon_fonts_in_css():
    """Point @font-face rules at the subset woff2 (kept first in src so browsers pick it)."""
    if not ICON_DONE:
        return
    for f in glob.glob(os.path.join(BUILD, "*.css")):
        t = open(f, encoding="utf-8").read()
        def face(m):
            body = m.group(0)
            for stem, new in ICON_DONE.items():
                if "/" + stem + "." in body or stem.split("/")[-1] + ".woff" in body:
                    body = re.sub(r"src:[^;}]*;?", "", body)
                    body = body.replace("{", "{src:url(%s) format('woff2');" % new, 1)
                    break
            return body
        t2 = re.sub(r"@font-face\s*\{[^}]*\}", face, t)
        if t2 != t:
            open(f, "w", encoding="utf-8").write(t2)


def main():
    print("optimize")
    compress_images()
    shutil.rmtree(BUILD, ignore_errors=True)
    pages = glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True)
    for fp in pages:
        if os.sep + "_ev" + os.sep in fp:
            continue
        PHONE_BG.clear()
        optimize_page(fp)
        if PHONE_BG:
            css_id = hashlib.md5(fp.encode()).hexdigest()[:12]
            with open(os.path.join(BUILD, css_id + ".css"), "a", encoding="utf-8") as fh:
                for big, small in PHONE_BG:
                    # same selector + !important as Divi's rule, phones only, gradient kept
                    css = open(os.path.join(BUILD, css_id + ".css"), encoding="utf-8").read()
                    for m in re.finditer(r"(div\.et_pb_section\.et_pb_section_0\{background-image:)([^}]*?)url\(" + re.escape(big) + r"\)([^}]*)\}", css):
                        fh.write("@media only screen and (max-width:767px){%s%surl(%s)%s}}" % (m.group(1), m.group(2), small, m.group(3)))
    os.makedirs(os.path.join(OUT, "assets", "fonts"), exist_ok=True)
    subset_icon_fonts()
    swap_icon_fonts_in_css()
    open(os.path.join(OUT, "assets", "site.js"), "w", encoding="utf-8").write(SITE_JS)
    for f in glob.glob(os.path.join(HERE, "vendor", "fonts", "*.woff2")):
        shutil.copy(f, os.path.join(OUT, "assets", "fonts", os.path.basename(f)))
    print("  pages:", len(pages))


if __name__ == "__main__":
    main()
