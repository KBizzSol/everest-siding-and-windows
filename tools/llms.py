"""llms.txt / llms-full.txt for AI assistants and answer engines.

Every fact in FACTS comes from the live site (home, contact, about, payment options, service areas, FAQs).
Update it here if the business details change.
"""
import re, html

SITE = "https://everestsidingandwindows.com"

FACTS = """# Everest Siding and Windows

> Family-owned exterior remodeling contractor in the Greater Houston area since 2015: LP SmartSide and James Hardie siding installation and replacement, window replacement, roofing (GAF and Malarkey), covered patios and outdoor living, plus add-on services. Showroom in Tomball, TX. Bills itself as the largest LP SmartSide home remodeler in Texas.

## Key facts
- Address: 11424 Spring Cypress Rd Unit A1, Tomball, TX 77377
- Phone: (832) 334-2528
- Email: info@everestsidingandwindows.com
- Showroom hours: Monday-Friday 9am-5pm, by appointment only
- Founded: 2015; multi-generation, family owned and operated
- Free, no-obligation estimates and consultations
- Pricing: 100% guaranteed pricing with a no-change-order policy (what is quoted is what is paid)
- Lowest bid guaranteed, or a $50 gift card
- Warranty: Everest's own Lifetime Labor Warranty on every project, on top of manufacturer warranties (e.g. LP SmartSide 5/50-year limited)
- Payment: cash, check, all major credit cards, and financing (unsecured home improvement loans, same-day decisions, no early repayment penalty)
- Installers: Everest does not subcontract to untrained crews
- Typical siding replacement: 5 to 12 business days
- Residential focus; light commercial by request

## What Everest does not do
- No siding repairs (installation and full replacement only)
- No sale of materials (not a distributor or supplier)
- Window replacement minimum: 3 windows

## Products and partners
- Siding: LP SmartSide engineered wood, James Hardie (HardiePlank) fiber cement
- Paint: Sherwin-Williams
- Windows: NT Window, MI Windows and Doors, Simonton
- Roofing: GAF (Timberline HDZ), Malarkey (Emerald Pro and Certified Residential Contractor)
- Memberships: NARI (National Association of the Remodeling Industry), Tomball, Cy-Fair and Houston Northwest chambers of commerce

## Service area
Houston, Conroe, Cypress, Hockley, Humble, Huntsville, Jersey Village, Katy, Kingwood, Magnolia, Montgomery, Pinehurst, Richmond, Spring, Sugar Land, The Woodlands, Tomball and Willis, TX
"""

GROUP_ORDER = ["Home", "Services", "Pricing and payment", "Company", "Service areas", "Project gallery", "Articles and guides", "Other"]
OTHER_SLUGS = {"privacy-policy"}

SERVICE_SLUGS = {"services", "add-ons-services"}
PRICING_SLUGS = {"quick-quote", "cost-vs-value", "payment-options", "promotions"}
COMPANY_SLUGS = {"about", "credentials", "giving-back", "contact", "faqs", "service-areas", "portfolio", "blog"}


def group(p, is_post):
    slug = p.strip("/")
    if p == "/":
        return "Home"
    article = re.match(r"(how|what|why|is|are|can|does|should|winterizing)-", slug)
    if slug in SERVICE_SLUGS or (slug.endswith("-in-houston-tx") and not article and "project" not in slug):
        return "Services"
    if slug in PRICING_SLUGS:
        return "Pricing and payment"
    if slug in COMPANY_SLUGS:
        return "Company"
    if re.match(r"(siding-contractor-in|home-remodeling-company|siding-installation|home-improvement-(contractor|company))-", slug):
        return "Service areas"
    if "remodeling-project" in slug:
        return "Project gallery"
    if slug in OTHER_SLUGS:
        return "Other"
    return "Articles and guides"   # blog posts and article-style pages


def page_text(s):
    """Readable main-content text of a Divi page (no header, menus, forms, footer)."""
    b = s.find('<div id="et-main-area"')
    e = s.find('<footer')
    body = s[b if b > 0 else 0: e if e > 0 else None]
    body = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<form\b.*?</form>|<nav\b.*?</nav>|<!--.*?-->", " ", body, flags=re.S)
    body = re.sub(r"</(p|li|h[1-6]|tr|div|br)>|<br\s*/?>", "\n", body)
    body = re.sub(r"<[^>]+>", " ", body)
    lines, seen = [], set()
    for l in body.split("\n"):
        l = re.sub(r"\s+", " ", html.unescape(l)).strip()
        if len(l) > 2 and l not in seen:   # drop repeated blocks (CTAs, phone lines)
            seen.add(l); lines.append(l)
    return "\n".join(lines)


def llms_txt(paths, info):
    out = [FACTS]
    for g in GROUP_ORDER:
        ps = [p for p in paths if info[p]["group"] == g]
        if g in ("Articles and guides", "Project gallery"):
            ps.sort(key=lambda p: info[p]["lastmod"], reverse=True)
        if not ps:
            continue
        out.append(f"\n## {g}")
        for p in ps:
            i = info[p]
            desc = f": {i['desc']}" if i["desc"] else ""
            out.append(f"- [{i['h1'] or i['title']}]({SITE}{p}){desc}")
    out.append(f"\n## Optional\n- [Full text of every page]({SITE}/llms-full.txt)\n- [XML sitemap]({SITE}/sitemap_index.xml)")
    return "\n".join(out) + "\n"


def llms_full(paths, info):
    out = [FACTS, "\n# Pages\n"]
    for g in GROUP_ORDER:
        for p in [p for p in paths if info[p]["group"] == g]:
            i = info[p]
            text = i["text"]
            text = text[:8000] + ("\n[...]" if len(text) > 8000 else "")
            out.append(f"\n---\n\n## {i['h1'] or i['title']}\nURL: {SITE}{p}\nUpdated: {i['lastmod']}\n"
                       + (f"Summary: {i['desc']}\n" if i["desc"] else "") + f"\n{text}\n")
    return "\n".join(out)
