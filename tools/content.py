"""SEO / AEO content layer (built on top of the migrated pages).

- new guide pages (cost, installation FAQ, LP SmartSide FAQ, LP vs Hardie, LP vs vinyl, affordable replacement)
- the promise band (tagline) and an "answers" link block on key pages
- fixes: Everest does not repair siding and does not install vinyl siding
Facts come from Everest's own pages (policies, project prices) and LP Building Products' published warranty.
"""
import os, re, json, html as H, glob, statistics, datetime

SITE = "https://everestsidingandwindows.com"
PHONE = "(832) 334-2528"
TEL = "tel:+18323342528"
TODAY = datetime.date.today()
UPDATED = TODAY.strftime("%B %Y")

TAGLINE = 'Nobody in Texas installs more LP SmartSide than Everest, <b>so nobody gives you a better price on it.</b>'
TAGLINE_TEXT = "Nobody in Texas installs more LP SmartSide than Everest, so nobody gives you a better price on it."

# ---------------------------------------------------------------- project prices (from Everest's own project pages)
def load_projects(src_dir):
    rows = []
    files = sorted(set(glob.glob(os.path.join(src_dir, "*remodeling-project*", "index.html"))))
    for f in files:
        s = open(f, encoding="utf-8", errors="ignore").read()
        b = s.find('<div id="et-main-area"'); e = s.find("<footer")
        t = H.unescape(re.sub(r"<[^>]+>", "\n", re.sub(r"<script.*?</script>|<style.*?</style>", "", s[b:e], flags=re.S)))
        t = re.sub(r"[ \t]+", " ", t); t = re.sub(r"\n\s*\n+", "\n", t)
        def field(lbl):
            m = re.search(r"\n" + lbl + r"\s*\n(.*?)\n", t); return m.group(1).strip() if m else ""
        title = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        title = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", title.group(1)))).strip() if title else ""
        city = re.search(r"in ([A-Z][A-Za-z .]+?), TX", title)
        slug = os.path.basename(os.path.dirname(f))
        price = field("How much")
        when = field("When")
        if not price.startswith("$"):
            continue
        rows.append(dict(url="/%s/" % slug, title=title, city=city.group(1) if city else "Greater Houston",
                         when=when, project=field("Project"), product=field("Product").rstrip("."), price=price,
                         amount=int(re.sub(r"[^\d]", "", price))))
    return rows


def _month_key(w):
    try:
        return datetime.datetime.strptime(w.strip()[:20], "%B %Y")
    except Exception:
        return datetime.datetime(2000, 1, 1)


def lp_siding_jobs(rows, since=2024):
    out = []
    for r in rows:
        p, pr = r["project"].lower(), r["product"]
        if ("LP" in pr or "SmartSide" in pr) and p.startswith("siding") and "window" not in p and "roof" not in p \
                and _month_key(r["when"]).year >= since:
            out.append(r)
    return sorted(out, key=lambda r: _month_key(r["when"]), reverse=True)


# ---------------------------------------------------------------- shared bits
def btn_quote(label="Get my free quote"):
    return '<a class="ev-btn kbs-apt-btn" href="/contact/">%s</a>' % label


def btn_call():
    return '<a class="ev-btn ev-btn--call" href="%s">Call %s</a>' % (TEL, PHONE)


def promise_band():
    return ('<section class="ev-promise" aria-label="Our price promise"><div class="ev-promise__in">'
            '<p class="ev-promise__line">%s</p>'
            '<p class="ev-promise__sub">Everest is the largest LP SmartSide home remodeler in Texas. That volume is buying power, and we pass it on: '
            '<strong>lowest bid guaranteed, or a $50 gift card</strong>. Fixed price in writing, no change orders, no down payment.</p>'
            '<div class="ev-promise__cta">%s%s</div>'
            '<p class="ev-promise__fine">See what real jobs cost: <a href="/lp-smartside-siding-cost-houston/">LP SmartSide prices from our recent Houston projects</a></p>'
            '</div></section>') % (TAGLINE, btn_quote(), btn_call())


GUIDES = [
    ("/lp-smartside-siding-cost-houston/", "LP SmartSide siding cost in Houston", "Real prices from our recent jobs"),
    ("/affordable-siding-replacement-houston/", "Affordable siding replacement", "How to get the best price without the cheap bid"),
    ("/lp-smartside-installation-faq/", "LP SmartSide installation FAQ", "Timeline, permits, HOA, prep and cleanup"),
    ("/lp-smartside-siding-faq/", "LP SmartSide siding FAQ", "Durability, warranty, paint and care"),
    ("/lp-smartside-vs-hardie-plank/", "LP SmartSide vs. Hardie Plank", "Which one fits your Houston home"),
    ("/lp-smartside-vs-vinyl-siding/", "LP SmartSide vs. vinyl siding", "Why we don't install vinyl"),
]


def related(exclude=""):
    items = "".join('<li><a href="%s">%s<small>%s</small></a></li>' % (u, t, d) for u, t, d in GUIDES if u != exclude)
    return '<ul class="ev-related">%s</ul>' % items


def answers_block():
    return ('<section class="ev-answers" aria-label="Siding answers"><div class="ev-answers__in">'
            '<h2>Straight answers before you call</h2><p>Prices from real jobs, the install process and how LP SmartSide compares.</p>%s'
            '</div></section>') % related()


# ---------------------------------------------------------------- fixes to existing pages
VINYL_PAGES = {
    "/can-you-paint-vinyl-siding/", "/how-long-does-vinyl-siding-last/", "/thinking-diy-for-your-siding-installation-think-again/",
    "/siding-maintenance-tips-how-to-keep-your-siding-looking-great/", "/buyers-guide-to-exterior-siding/",
    "/how-much-does-it-cost-to-get-a-new-siding/", "/how-much-does-siding-cost-for-a-2000-sq-ft-house/",
}
VINYL_NOTE = ('<div class="ev-note" role="note"><strong>Good to know:</strong> Everest Siding and Windows does not sell, install or repair vinyl siding. '
              'We replace it, most often with LP SmartSide engineered wood. '
              '<a href="/lp-smartside-vs-vinyl-siding/">See how LP SmartSide compares to vinyl</a>.</div>')
ANSWER_PAGES = {"/", "/faqs/", "/lp-smartside-in-houston-tx/", "/siding-in-houston-tx/", "/hardieplank-in-houston-tx/",
                "/quick-quote/", "/cost-vs-value/", "/payment-options/", "/services/"}
PROMISE_PAGES = {"/lp-smartside-in-houston-tx/", "/siding-in-houston-tx/", "/quick-quote/", "/payment-options/", "/promotions/"}


def _before_footer(s, block):
    i = s.find('<footer class="et-l et-l--footer">')
    return s[:i] + block + s[i:] if i > 0 else s


def page_fixes(s, path):
    # repair wording that implied Everest repairs siding
    s = s.replace("for quick maintenance tips and siding repair, give our experts at Everest Siding and Windows a call",
                  "for siding replacement on your property, give our experts at Everest Siding and Windows a call")
    s = re.sub(r"hire a professional contractor to fix the problem\.?\s*Hiring a professional will ensure that your siding repairs are effective\.",
               "talk to a professional. Everest does not do spot repairs; if the damage is widespread, we can replace the siding with new LP SmartSide.", s)
    # vinyl articles: clear notice right under the first heading of the article
    if path in VINYL_PAGES and "ev-note" not in s:
        m = re.search(r"</h1>", s)
        if m:
            s = s[:m.end()] + VINYL_NOTE + s[m.end():]
    # homepage: the tagline band right after the hero
    if path == "/" and "ev-promise" not in s:
        m = re.search(r'<div class="et_pb_section et_pb_section_1[ "]', s)
        if m:
            s = s[:m.start()] + promise_band() + s[m.start():]
    elif path in PROMISE_PAGES and "ev-promise" not in s:
        s = _before_footer(s, promise_band())
    if path in ANSWER_PAGES and "ev-answers" not in s:
        s = _before_footer(s, answers_block())
    return s


# ---------------------------------------------------------------- new pages
def faq_html(items):
    return '<div class="ev-faq">%s</div>' % "".join(
        '<details%s><summary>%s</summary><div class="ev-a">%s</div></details>' % (" open" if i == 0 else "", q, a)
        for i, (q, a) in enumerate(items))


def faq_schema(items):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": H.unescape(re.sub(r"<[^>]+>", "", q)),
         "acceptedAnswer": {"@type": "Answer", "text": H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", a))).strip()}}
        for q, a in items]}


def page_shell_parts(title, desc, path, crumb, h1, lede, answer, body, faqs, extra_schema=None, promise=True):
    url = SITE + path
    graph = [
        {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": title, "description": desc,
         "inLanguage": "en-US", "dateModified": TODAY.isoformat(), "isPartOf": {"@id": SITE + "/#website"},
         "about": {"@type": "Product", "name": "LP SmartSide engineered wood siding", "brand": {"@type": "Brand", "name": "LP Building Products"}},
         "publisher": {"@id": SITE + "/#localbusiness"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": crumb, "item": url}]},
        {"@type": ["LocalBusiness", "HomeAndConstructionBusiness"], "@id": SITE + "/#localbusiness", "name": "Everest Siding and Windows",
         "url": SITE + "/", "telephone": "+1-832-334-2528", "email": "info@everestsidingandwindows.com", "slogan": TAGLINE_TEXT,
         "image": SITE + "/wp-content/uploads/everest-logo.webp", "priceRange": "$$",
         "address": {"@type": "PostalAddress", "streetAddress": "11424 Spring Cypress Rd Unit A1", "addressLocality": "Tomball",
                     "addressRegion": "TX", "postalCode": "77377", "addressCountry": "US"},
         "areaServed": [{"@type": "City", "name": c} for c in AREAS]},
    ]
    if faqs:
        graph.append(faq_schema(faqs))
    graph += extra_schema or []
    ld = '<script type="application/ld+json">%s</script>' % json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    main = ('<div class="ev-page"><header class="ev-hero"><div class="ev-hero__in">'
            '<nav class="ev-crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span>%s</span></nav>'
            '<h1>%s</h1><p class="ev-lede">%s</p><p class="ev-meta">Updated %s by the Everest Siding and Windows team, Tomball, TX</p>'
            '<div class="ev-answer"><p>%s</p></div></div></header>'
            '<div class="ev-body"><div class="ev-body__in">%s%s<h2>More answers</h2>%s</div></div></div>%s') % (
        crumb, h1, lede, UPDATED, answer, body,
        ('<h2 id="faq">Frequently asked questions</h2>' + faq_html(faqs)) if faqs else "", related(path),
        promise_band() if promise else "")
    return main, ld


AREAS = ["Houston", "Katy", "Cypress", "Spring", "Sugar Land", "Tomball", "Magnolia", "The Woodlands", "Conroe", "Kingwood",
         "Humble", "Hockley", "Jersey Village", "Pinehurst", "Montgomery", "Richmond", "Huntsville", "Willis"]

# shared answers (Everest policies, from its own pages)
A_FIXED = ("No. Everest gives you a fixed price in writing with a strict no-change-order policy. If we find rotted sheathing or other surprises "
           "behind the old siding, fixing them is already in your price.")
A_DOWN = "No down payment. You pay when the project is finished and you are satisfied with it."
A_REPAIR = ("No. Everest does not do siding repairs or patch jobs. We install new siding and replace full walls or whole homes, "
            "because a patch on aging siding rarely matches and the next weak spot is usually right beside it.")
A_VINYL = ("No. We do not sell, install or repair vinyl siding. We install LP SmartSide engineered wood and James Hardie (Hardie Plank) fiber cement, "
           "and we often replace vinyl with LP SmartSide. <a href=\"/lp-smartside-vs-vinyl-siding/\">Here is why.</a>")
A_WARRANTY = ("LP SmartSide siding and trim carry LP's 50-year prorated limited warranty, with a 100% labor and material remedy for the first five years. "
              "On top of that, Everest backs every installation with its own Lifetime Labor Warranty.")
A_TIME = "Most siding replacements take 5 to 12 business days, depending on the size of the home, the number of stories and the weather."
A_AREA = ("Greater Houston: Houston, Katy, Cypress, Spring, Sugar Land, Tomball, Magnolia, The Woodlands, Conroe, Kingwood, Humble, Hockley, "
          "Jersey Village, Pinehurst, Montgomery, Richmond, Huntsville, Willis and nearby communities. Not sure about your address? "
          "<a href=\"/service-areas/\">Check our service areas</a> or call " + PHONE + ".")
A_FIN = ("Yes. Everest can help you finance the project with an unsecured home improvement loan based on your credit, not your home's equity. "
         "You can apply online and often hear back the same day, you are not bound to the loan until you are satisfied with the finished work, "
         "and you can pay it off early with no penalty. We also take cash, checks and all major credit cards. <a href=\"/payment-options/\">Payment options</a>")
A_PERMIT = "Yes. Everest handles HOA approval when it is needed and pulls permits where they apply, so you don't have to."


def build_pages(OUT, src_dir, shell_path):
    shell = open(shell_path, encoding="utf-8").read()
    rows = load_projects(src_dir)
    jobs = lp_siding_jobs(rows)
    amounts = [r["amount"] for r in jobs] or [0]
    med = int(statistics.median(amounts))
    whole = [a for a in amounts if a >= 10000] or amounts
    lo, hi = min(whole), max(whole)
    n_all_lp = len([r for r in rows if "LP" in r["product"] or "SmartSide" in r["product"]])
    def money(n): return "${:,}".format(int(n))

    pages = {}

    # 1. cost guide -------------------------------------------------------
    table = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td class="ev-num"><a href="%s">%s</a></td></tr>' % (
        H.escape(r["when"]), H.escape(r["city"]), H.escape(r["product"]), r["url"], r["price"]) for r in jobs)
    faqs = [
        ("How much does LP SmartSide siding cost in Houston?",
         "On our recent Houston-area jobs, replacing siding with LP SmartSide cost a median of %s. Most projects ran %s to %s; "
         "smaller jobs, like one side of a house or a garage, cost less. Your price depends on wall area, stories, trim, soffit and fascia, "
         "and whether you add paint upgrades or gutters." % (money(med), money(lo), money(hi))),
        ("Why do siding quotes vary so much?",
         "Quotes differ in what they include. Check that each one covers tear-off and disposal, replacing rotted sheathing, house wrap, "
         "trim, soffit and fascia, caulking, paint and cleanup. Everest's quote is itemized and fixed, so the number you sign is the number you pay."),
        ("Will the price go up if you find rot behind my old siding?", A_FIXED),
        ("Do I have to pay a deposit?", A_DOWN),
        ("Can I finance my siding?", A_FIN),
        ("Is LP SmartSide cheaper than Hardie Plank?",
         "It often costs less to install because LP SmartSide is lighter and comes in 16-foot lengths, which means fewer seams and less labor. "
         "Material prices change, so we quote both when you are deciding. <a href=\"/lp-smartside-vs-hardie-plank/\">LP SmartSide vs. Hardie Plank</a>"),
        ("Does Everest offer a price guarantee?",
         "Yes. Everest guarantees the lowest bid, or gives you a $50 gift card. Ask your consultant how the guarantee works for your quote."),
        ("Is the estimate free?", "Yes. Estimates are free and come with no obligation. We measure the home and give you a written, itemized price."),
    ]
    body = ('<h2>What our recent LP SmartSide jobs cost</h2>'
            '<div class="ev-stats"><div><b>%s</b><span>median price, %d LP SmartSide siding jobs since 2024</span></div>'
            '<div><b>%s&ndash;%s</b><span>range on most jobs (partial-wall jobs under $10,000 excluded)</span></div>'
            '<div><b>%d</b><span>LP SmartSide projects in our public portfolio</span></div></div>'
            '<p>These are real Everest projects, published with their prices in our <a href="/portfolio/">portfolio</a>. '
            'Each includes tear-off of the old siding, new LP SmartSide, trim and paint as described on the project page.</p>'
            '<div class="ev-table-wrap"><table class="ev-table"><caption>LP SmartSide siding replacements by Everest, newest first. Siding-only jobs; '
            'projects that also replaced windows or roofs are left out.</caption><thead><tr><th>Completed</th><th>City</th><th>Product</th>'
            '<th class="ev-num">Price</th></tr></thead><tbody>%s</tbody></table></div>'
            '<h2>What changes the price</h2>'
            '<h3>Wall area and stories</h3><p>Siding is priced by the area covered. Two-story walls need more labor and staging than a single story.</p>'
            '<h3>Profile and texture</h3><p>LP SmartSide comes as lap siding (6, 8 and 12 inch), board and batten, panels and shakes. '
            'Mixing profiles, like lap on the body and board and batten on the gables, adds cutting and trim work.</p>'
            '<h3>Trim, soffit and fascia</h3><p>Replacing trim, soffit and fascia with LP SmartSide at the same time gives you one material and one warranty '
            'around the whole house, and it is cheaper than coming back later.</p>'
            '<h3>What we find under the old siding</h3><p>Houston humidity rots sheathing behind failed siding. With Everest, that repair is already in your fixed price.</p>'
            '<h3>Paint and extras</h3><p>Most of our jobs are painted with Sherwin-Williams Emerald exterior paint. Seamless gutters, '
            'new windows or a roof at the same time change the total.</p>'
            '<h2>How Everest prices a job</h2>'
            '<ol class="ev-steps"><li><strong>Free on-site measure</strong>We measure every wall and look at trim, soffit and fascia.</li>'
            '<li><strong>Written, itemized quote</strong>Product, profile, color, paint and what is included, line by line.</li>'
            '<li><strong>Fixed price</strong>No change orders. Rot we find behind the old siding is already covered.</li>'
            '<li><strong>Pay at the end</strong>No down payment. You pay when the job is done and you are satisfied.</li></ol>'
            % (money(med), len(jobs), money(lo), money(hi), n_all_lp, table))
    pages["/lp-smartside-siding-cost-houston/"] = dict(
        title="LP SmartSide Siding Cost in Houston (Real %d Prices) - Everest Siding and Windows" % TODAY.year,
        desc="What LP SmartSide siding costs in Houston, from %d recent Everest jobs: median %s. Fixed prices, no down payment, lowest bid guaranteed." % (len(jobs), money(med)),
        crumb="LP SmartSide siding cost", h1="LP SmartSide siding cost in Houston",
        lede="Real prices from our recent LP SmartSide jobs around Houston, what moves the number, and how to compare quotes.",
        answer="<strong>Short answer:</strong> on %d LP SmartSide siding replacements we completed since 2024, the median price was <strong>%s</strong>. "
               "Most jobs ran %s to %s. Every Everest quote is fixed: no change orders, no down payment, and the lowest bid guaranteed." % (len(jobs), money(med), money(lo), money(hi)),
        body=body, faqs=faqs,
        extra=[{"@type": "Service", "name": "LP SmartSide siding replacement", "serviceType": "Siding installation and replacement",
                "provider": {"@id": SITE + "/#localbusiness"}, "areaServed": AREAS,
                "offers": {"@type": "AggregateOffer", "priceCurrency": "USD", "lowPrice": min(amounts), "highPrice": max(amounts), "offerCount": len(jobs)}}])

    # 2. affordable replacement -------------------------------------------
    faqs = [
        ("What is the most affordable way to replace siding in Houston?",
         "Replace everything that is failing in one project, with one crew and one fixed price. Piecemeal jobs cost more over time because each "
         "visit repeats setup, and patches on aging siding rarely last. LP SmartSide gives you the look of cedar for less installed cost than many "
         "fiber cement jobs, and it is lighter and faster to install."),
        ("Do you match or beat other quotes?",
         "Everest guarantees the lowest bid, or gives you a $50 gift card. Bring your other quotes to the consultation and make sure they include the same "
         "scope: tear-off, rot replacement, house wrap, trim, soffit, fascia and paint."),
        ("Is a cheap siding bid a good deal?",
         "Often not. The cheapest bids usually leave out rot replacement, house wrap or paint, then add them as change orders once the old siding is off. "
         "Everest's price is fixed in writing before we start."),
        ("Do you do siding repairs to save money?", A_REPAIR),
        ("Do you install vinyl siding?", A_VINYL),
        ("Do I need a down payment?", A_DOWN),
        ("Can I finance siding replacement?", A_FIN),
        ("Will new siding lower my energy bills?",
         "Every Everest siding job adds Low-E house wrap under the new siding, which helps keep summer heat out. How much you save depends on your home, "
         "insulation and windows."),
    ]
    body = ('<h2>Where the money goes</h2><p>On a typical siding replacement, most of the cost is labor and the parts you never see: tear-off, '
            'disposal, replacing rotted sheathing, house wrap, flashing and caulking. The cheapest bid usually saves money in exactly those places.</p>'
            '<h2>Six ways to pay less without buying twice</h2><ol class="ev-steps">'
            '<li><strong>Compare the same scope</strong>Line up quotes on tear-off, rot replacement, wrap, trim, soffit, fascia and paint.</li>'
            '<li><strong>Get the price fixed in writing</strong>A fixed price with no change orders is the cheapest price you can actually count on.</li>'
            '<li><strong>Do the whole house at once</strong>One mobilization, one crew, one warranty. Spot jobs repeat setup costs.</li>'
            '<li><strong>Pick LP SmartSide lap</strong>8-inch lap in cedar texture is our most common choice and keeps cutting waste low.</li>'
            '<li><strong>Don\'t pay up front</strong>With Everest you pay at the end, so your money stays yours until the job is right.</li>'
            '<li><strong>Use the guarantee</strong>Lowest bid guaranteed, or a $50 gift card.</li></ol>'
            '<p>See what our customers actually paid in the <a href="/lp-smartside-siding-cost-houston/">LP SmartSide cost guide</a>.</p>')
    pages["/affordable-siding-replacement-houston/"] = dict(
        title="Affordable Siding Replacement in Houston, TX - Everest Siding and Windows",
        desc="How to get the best price on siding replacement in Houston: fixed prices, no change orders, no down payment and the lowest bid guaranteed.",
        crumb="Affordable siding replacement", h1="Affordable siding replacement in Houston",
        lede="The best price is the one that doesn't change after the old siding comes off. Here is how to get it.",
        answer="<strong>Short answer:</strong> compare quotes on the same scope, insist on a fixed written price, and replace failing siding in one project. "
               "Everest installs LP SmartSide with no change orders, no down payment and the lowest bid guaranteed, or a $50 gift card.",
        body=body, faqs=faqs, extra=[])

    # 3. installation FAQ -------------------------------------------------
    faqs = [
        ("How long does LP SmartSide installation take?", A_TIME),
        ("What happens on install day?",
         "Our crew protects your landscaping, removes the old siding, inspects and replaces any rotted sheathing, wraps the walls in Low-E house wrap, "
         "flashes windows and doors, installs the LP SmartSide siding and trim, caulks the joints and paints. We clean up every day."),
        ("Do I need to be home during installation?", "No. Most homeowners keep a normal schedule. Your project manager checks the work daily and keeps you updated."),
        ("Do you pull permits and handle HOA approval?", A_PERMIT),
        ("What if you find rot behind the old siding?", A_FIXED),
        ("Can you install LP SmartSide over my old siding?",
         "We remove the old siding first. That is the only way to find and replace rotted sheathing and to put house wrap and flashing where they belong."),
        ("Do you paint LP SmartSide after installation?",
         "Yes. LP SmartSide comes primed, and we paint it, usually with Sherwin-Williams Emerald exterior paint in the color you choose. "
         "Soffit and fascia are painted to match."),
        ("Who installs my siding?",
         "Everest does not hand projects to untrained or self-taught crews. Our installers are trained on the products they install, "
         "and a project manager inspects the work every day."),
        ("Can it rain during installation?", "Light rain usually doesn't stop work. Heavy storms can pause a day; we wrap open walls so they stay protected."),
        ("Do you also replace soffit, fascia and gutters?",
         "Yes. Many of our siding jobs include LP SmartSide soffit and fascia and new seamless gutters, so the whole exterior is finished at once."),
        ("What warranty covers the installation?", A_WARRANTY),
        ("How do I get started?", "Call " + PHONE + " or request a free consultation. We measure your home and give you a written, fixed price."),
    ]
    body = ('<h2>The installation, step by step</h2><ol class="ev-steps">'
            '<li><strong>Free consultation and measure</strong>We look at every wall, trim board, soffit and fascia and show you profiles and colors.</li>'
            '<li><strong>Fixed written price</strong>Itemized and final. No change orders.</li>'
            '<li><strong>HOA approval and permits</strong>We handle both where they apply.</li>'
            '<li><strong>Tear-off and inspection</strong>Old siding comes off; rotted sheathing is replaced at no extra cost.</li>'
            '<li><strong>Low-E house wrap and flashing</strong>Every wall gets wrapped; windows and doors are flashed.</li>'
            '<li><strong>LP SmartSide siding and trim</strong>Installed to LP\'s installation instructions, which keeps your warranty valid.</li>'
            '<li><strong>Caulk and paint</strong>Usually Sherwin-Williams Emerald exterior paint.</li>'
            '<li><strong>Walkthrough, then payment</strong>You pay when the job is finished and you are satisfied.</li></ol>')
    pages["/lp-smartside-installation-faq/"] = dict(
        title="LP SmartSide Installation FAQ (Houston) - Everest Siding and Windows",
        desc="LP SmartSide installation in Houston, answered: how long it takes, what happens on install day, permits, HOA, rot, paint and warranty.",
        crumb="LP SmartSide installation FAQ", h1="LP SmartSide installation, answered",
        lede="What happens from the first measurement to the final walkthrough when Everest installs LP SmartSide on your home.",
        answer="<strong>Short answer:</strong> most LP SmartSide replacements take 5 to 12 business days. Everest removes the old siding, replaces any rotted "
               "sheathing at no extra cost, adds Low-E house wrap, installs and paints the new siding, handles permits and HOA approval, and you pay at the end.",
        body=body, faqs=faqs,
        extra=[{"@type": "HowTo", "name": "How Everest installs LP SmartSide siding", "totalTime": "P12D",
                "step": [{"@type": "HowToStep", "position": i + 1, "name": n} for i, n in enumerate(
                    ["Free consultation and measure", "Fixed written price", "HOA approval and permits", "Tear-off and inspection",
                     "Low-E house wrap and flashing", "LP SmartSide siding and trim", "Caulk and paint", "Walkthrough, then payment"])]}])

    # 4. LP SmartSide FAQ -------------------------------------------------
    faqs = [
        ("What is LP SmartSide siding?",
         "LP SmartSide is engineered wood siding made by LP Building Products. Wood strands are treated through LP's SmartGuard process with binders, "
         "waxes and zinc borate and bonded under a water-resistant overlay, so it resists rot, fungal decay and termites while looking like real cedar."),
        ("Is LP SmartSide good for Houston's humidity and storms?",
         "Yes, which is why it is most of what we install. The SmartGuard treatment resists moisture, rot and termites, and LP SmartSide is more "
         "impact-resistant than fiber cement against hail and wind-blown debris."),
        ("How long does LP SmartSide last?",
         "LP backs its siding with a 50-year prorated limited warranty. With paint maintained and water kept off the walls, it is built to last decades."),
        ("What warranty does LP SmartSide have?", A_WARRANTY),
        ("What styles does LP SmartSide come in?",
         "Lap siding (6, 8 and 12 inch), board and batten, panel siding, shakes, plus matching trim, soffit and fascia. Most come in a cedar texture or smooth."),
        ("Does LP SmartSide need to be painted?",
         "It comes primed for paint or prefinished from the factory. Everest paints it after installation, usually with Sherwin-Williams Emerald exterior paint."),
        ("How do I care for LP SmartSide?",
         "Look it over once a year, wash it with a soft brush and mild soap, keep sprinklers and gutters from soaking the walls, touch up paint chips "
         "and recaulk joints when needed. Don't use a pressure washer on it. <a href=\"/caring-for-your-lp-smartside-siding/\">Care guide</a>"),
        ("Is LP SmartSide real wood?", "It is engineered wood: real wood strands, treated and pressed into boards. It cuts and looks like wood but resists rot and pests."),
        ("Does LP SmartSide help with energy efficiency?",
         "The siding itself is not insulation, but every Everest siding job adds Low-E house wrap behind it, which helps reflect summer heat."),
        ("Do you repair LP SmartSide?", A_REPAIR),
        ("Do you install vinyl siding instead?", A_VINYL),
        ("Is Everest certified to install LP SmartSide?",
         "Everest is the largest LP SmartSide home remodeler in Texas and holds LP's BuildSmart Master level (2025). "
         "<a href=\"/credentials/\">See our credentials</a>."),
    ]
    body = ('<h2>Why we install so much of it</h2><p>Houston is hard on siding: long humid summers, heavy rain, termites and hail. '
            'LP SmartSide stands up to all four, it looks like cedar, and it comes in 16-foot lengths, so walls have fewer seams. '
            'That combination is why it is the siding most of our customers choose.</p>'
            '<h2>LP SmartSide at a glance</h2><div class="ev-table-wrap"><table class="ev-table ev-compare"><tbody>'
            '<tr><td>Material</td><td>Engineered wood with SmartGuard treatment (binders, waxes, zinc borate)</td></tr>'
            '<tr><td>Resists</td><td>Moisture, rot, fungal decay, termites, impact from hail and debris</td></tr>'
            '<tr><td>Lengths</td><td>Up to 16 feet, for fewer seams</td></tr>'
            '<tr><td>Styles</td><td>Lap (6, 8, 12 in), board and batten, panel, shakes, trim, soffit, fascia</td></tr>'
            '<tr><td>Finish</td><td>Primed for paint, or prefinished</td></tr>'
            '<tr><td>Manufacturer warranty</td><td>50-year prorated limited; 100% labor and material remedy in years 1&ndash;5</td></tr>'
            '<tr><td>Everest warranty</td><td>Lifetime Labor Warranty on the installation</td></tr></tbody></table></div>')
    pages["/lp-smartside-siding-faq/"] = dict(
        title="LP SmartSide Siding FAQ: Houston Homeowners' Questions - Everest",
        desc="LP SmartSide siding questions answered for Houston homes: what it is, how long it lasts, warranty, styles, paint, care and humidity.",
        crumb="LP SmartSide siding FAQ", h1="LP SmartSide siding FAQ",
        lede="What Houston homeowners ask us most about LP SmartSide engineered wood siding, answered by the crew that installs it every week.",
        answer="<strong>Short answer:</strong> LP SmartSide is treated engineered wood siding that looks like cedar and resists moisture, rot, termites and hail. "
               "It carries LP's 50-year prorated limited warranty, and Everest adds a Lifetime Labor Warranty on the install.",
        body=body, faqs=faqs, extra=[])

    # 5. LP vs Hardie -----------------------------------------------------
    faqs = [
        ("Which is better for Houston, LP SmartSide or Hardie Plank?",
         "Both perform well here, and Everest installs both. LP SmartSide is lighter, more impact-resistant, comes in longer 16-foot boards and carries a "
         "longer manufacturer warranty. Hardie Plank is fiber cement, which does not burn. Most of our customers choose LP SmartSide."),
        ("Is LP SmartSide cheaper than James Hardie?",
         "LP SmartSide usually costs less to install because it is lighter and faster to work with. We quote both so you can compare the same scope."),
        ("Which has the better warranty?",
         "LP SmartSide siding and trim carry a 50-year prorated limited warranty with a 100% labor and material remedy for the first five years. "
         "LP's own comparison lists James Hardie siding at 30 years and trim at 15. Both get Everest's Lifetime Labor Warranty."),
        ("Which holds up better to hail?", "LP SmartSide. Engineered wood flexes under impact where fiber cement can crack or chip."),
        ("Can I mix LP SmartSide and Hardie on one house?",
         "We can, and we have, for example Hardie soffit and fascia with LP SmartSide walls. Usually one material for the whole house is simpler and keeps one warranty."),
        ("Do you install vinyl too?", A_VINYL),
    ]
    body = ('<h2>Side by side</h2><div class="ev-table-wrap"><table class="ev-table ev-compare"><thead><tr><th></th><th>LP SmartSide</th><th>James Hardie (Hardie Plank)</th></tr></thead><tbody>'
            '<tr><td>Material</td><td>Treated engineered wood</td><td>Fiber cement</td></tr>'
            '<tr><td>Weight</td><td>Lighter, easier to handle</td><td>Heavier</td></tr>'
            '<tr><td>Impact (hail, debris)</td><td>Flexes, resists cracking</td><td>Can crack or chip</td></tr>'
            '<tr><td>Board length</td><td>Up to 16 ft</td><td>Typically 12 ft</td></tr>'
            '<tr><td>Fire</td><td>Wood-based; not fire-resistant on its own</td><td>Non-combustible</td></tr>'
            '<tr><td>Manufacturer warranty</td><td>50-year prorated; labor and material remedy in years 1&ndash;5</td><td>30 years on siding, 15 on trim (per LP\'s comparison)</td></tr>'
            '<tr><td>Everest installs it</td><td>Yes, most of our jobs</td><td>Yes</td></tr></tbody></table></div>'
            '<p>Warranty terms from <a href="https://lpcorp.com/resources/product-literature/competitive-comparison/lp-smartside-warranty-comparison" rel="noopener">LP Building Products</a>. '
            'Always read the current manufacturer warranty for your exact product.</p>'
            '<h2>How to choose</h2><p>If hail, weight on older framing and a wood look matter most, choose LP SmartSide. If you want a non-combustible '
            'cladding, choose Hardie Plank. Either way you get the same fixed price, no down payment and Lifetime Labor Warranty from Everest. '
            'See <a href="/hardieplank-in-houston-tx/">Hardie Plank in Houston</a> and <a href="/lp-smartside-in-houston-tx/">LP SmartSide in Houston</a>.</p>')
    pages["/lp-smartside-vs-hardie-plank/"] = dict(
        title="LP SmartSide vs. Hardie Plank for Houston Homes - Everest Siding and Windows",
        desc="LP SmartSide vs. James Hardie fiber cement in Houston: weight, hail, board length, fire and warranty compared by a contractor that installs both.",
        crumb="LP SmartSide vs. Hardie Plank", h1="LP SmartSide vs. Hardie Plank",
        lede="We install both. Here is how they compare on a Houston home, and how to pick.",
        answer="<strong>Short answer:</strong> LP SmartSide is lighter, more impact-resistant, comes in longer boards and has a longer manufacturer warranty. "
               "Hardie Plank is fiber cement and does not burn. For most Houston homes we recommend LP SmartSide.",
        body=body, faqs=faqs, extra=[])

    # 6. LP vs vinyl ------------------------------------------------------
    faqs = [
        ("Does Everest install vinyl siding?", A_VINYL),
        ("Why choose LP SmartSide over vinyl?",
         "LP SmartSide looks like real wood, is far stiffer and more impact-resistant, and can be painted any color, again and again. "
         "Vinyl is thin plastic that can crack in impact and warp under concentrated heat, such as sunlight reflected off windows."),
        ("Is vinyl siding cheaper than LP SmartSide?",
         "Vinyl usually costs less up front. LP SmartSide costs more, but lasts, can be repainted to change the look, and carries a 50-year prorated limited warranty. "
         "<a href=\"/lp-smartside-siding-cost-houston/\">See real LP SmartSide prices</a>."),
        ("Can you replace my vinyl siding with LP SmartSide?",
         "Yes. We remove the vinyl, check and replace any rotted sheathing, add Low-E house wrap and install and paint LP SmartSide. "
         "One recent example is <a href=\"/siding-remodeling-project-in-cleveland-tx/\">this Cleveland, TX home</a>."),
        ("Do you repair vinyl siding?", A_REPAIR),
    ]
    body = ('<h2>Side by side</h2><div class="ev-table-wrap"><table class="ev-table ev-compare"><thead><tr><th></th><th>LP SmartSide</th><th>Vinyl siding</th></tr></thead><tbody>'
            '<tr><td>Material</td><td>Treated engineered wood</td><td>PVC plastic</td></tr>'
            '<tr><td>Look</td><td>Deep cedar grain or smooth, like painted wood</td><td>Plastic sheen, visible overlaps</td></tr>'
            '<tr><td>Impact</td><td>Stiff, resists hail and debris</td><td>Can crack, especially when old</td></tr>'
            '<tr><td>Heat</td><td>Stable</td><td>Can warp under concentrated heat</td></tr>'
            '<tr><td>Color</td><td>Paint any color, repaint later</td><td>Color set at the factory</td></tr>'
            '<tr><td>Everest installs it</td><td>Yes</td><td>No</td></tr></tbody></table></div>'
            '<h2>Why we stopped short of vinyl</h2><p>We build our business on siding we can stand behind for decades with a Lifetime Labor Warranty. '
            'For Houston\'s heat, storms and humidity, that means LP SmartSide and Hardie Plank, not vinyl.</p>')
    pages["/lp-smartside-vs-vinyl-siding/"] = dict(
        title="LP SmartSide vs. Vinyl Siding: Why We Don't Install Vinyl - Everest",
        desc="LP SmartSide engineered wood vs. vinyl siding for Houston homes: look, hail, heat, paint and warranty. Everest does not install vinyl siding.",
        crumb="LP SmartSide vs. vinyl siding", h1="LP SmartSide vs. vinyl siding",
        lede="Everest does not install vinyl siding. Here is what we install instead, and why.",
        answer="<strong>Short answer:</strong> Everest doesn't sell, install or repair vinyl siding. We replace it with LP SmartSide, which looks like real wood, "
               "stands up better to hail and heat, can be repainted and carries a 50-year prorated limited warranty.",
        body=body, faqs=faqs, extra=[])

    # ---- write pages from the shell
    for path, p in pages.items():
        main, ld = page_shell_parts(p["title"], p["desc"], path, p["crumb"], p["h1"], p["lede"], p["answer"], p["body"], p["faqs"], p["extra"])
        s = shell
        s = re.sub(r"<title>.*?</title>", "<title>%s</title>" % H.escape(p["title"], quote=False), s, count=1, flags=re.S)
        s = re.sub(r'<meta name="description" content="[^"]*"\s*/?>', '<meta name="description" content="%s" />' % H.escape(p["desc"]), s, count=1)
        if '<meta name="description"' not in s:
            s = s.replace("</title>", '</title><meta name="description" content="%s" />' % H.escape(p["desc"]), 1)
        s = re.sub(r'<meta name=["\']robots["\'][^>]*>', '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />', s, count=1)
        s = re.sub(r'<link rel="canonical" href="[^"]*"\s*/?>', '<link rel="canonical" href="%s" />' % (SITE + path), s, count=1)
        s = re.sub(r'(<meta property="og:url" content=")[^"]*', r"\g<1>" + SITE + path, s)
        s = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + H.escape(p["title"]), s)
        s = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + H.escape(p["desc"]), s)
        s = re.sub(r'(<meta name="twitter:(?:title|description)" content=")[^"]*', lambda m: m.group(1) + H.escape(p["desc"]), s)
        s = re.sub(r'<meta property="article:modified_time" content="[^"]*"', '<meta property="article:modified_time" content="%sT08:00:00+00:00"' % TODAY.isoformat(), s)
        s = re.sub(r'<script type=["\']application/ld\+json["\'][^>]*>.*?</script>', "", s, flags=re.S)
        s = s.replace("</head>", ld + "</head>", 1)
        a = s.find('<div class="entry-content">'); b = s.find("</article>")
        s = s[:a] + '<div class="entry-content">' + main + "</div>" + s[b:]
        s = re.sub(r"<body([^>]*)class=\"", r'<body\1class="ev-guide ', s, count=1)
        d = os.path.join(OUT, path.strip("/"))
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(s)
    print("  new guide pages:", len(pages), "| LP jobs since 2024:", len(jobs), "median", money(med))
    return list(pages)
