# Everest Siding and Windows — migration audit (Oct 27, 2026)

## Result: clean
No malware, no injected spam, no hidden links, no rogue redirects.

| Check | What was scanned | Result |
|---|---|---|
| Malware / injected code | All 203 pages and 35 JS files: `eval`/packed code, `atob`/`unescape` tricks, long `fromCharCode` strings, code appended to jQuery/Divi files | None found |
| Spam content | Pharma, casino, adult, loan and essay-mill keywords (whole words) | None. Earlier hits were false matches inside base64 image data |
| Hidden links | Off-screen / `display:none` blocks wrapping outbound links | None |
| Redirects | Meta-refresh and JavaScript location redirects | None |
| Third-party scripts | Every external `<script>` and `<iframe>` host | Only Google (Tag Manager, Analytics, reCAPTCHA, Maps), YouTube and cdnjs (date picker and input mask for the form) |
| Outbound links | Every external `<a href>` domain | All legitimate: K Bizz footer credit, Google Maps reviews, YouTube, Tomball / Cy-Fair / Houston NW chambers, NOAA, Remodeling magazine |
| Plugins in use | Folders under `wp-content/plugins` | Contact Form 7, CF7 Conditional Fields, Divi Essential, Blog Filter Premium, Link Whisper, PixelYourSite — all known, legitimate plugins |
| Broken internal links / assets | Every `href`, `src`, `srcset` and CSS `url()` | None, except 5 Glyphicons font files that the live site doesn't serve either (harmless) |
| Junk / unused files | Uploads not referenced by any page, CSS or JS | None (the mirror only downloads referenced files) |
| Test / placeholder pages | Slugs like test, sample, draft, copy; "lorem ipsum" text | No test pages. One placeholder section (see "Needs a decision") |

## Fixed
- **Broken phone links** in 5 blog posts (`Tel:+1-832...` and `http://Tel:+1-832...`) now use `tel:+18323342528`.
- **Survey pages kept out of Google:** `/thank-you-survey-form/` and `/customer-satisfaction-survey/` are now `noindex, follow` and out of the sitemap. URLs unchanged.
- **Build bug:** the link rewriter had altered a Divi script (`href="' + file + '"`), which broke Divi's stylesheet de-duplication. Fixed in `tools/postprocess.py`.
- **WordPress system URLs** (`/wp-admin/`, `/wp-login.php`, `/xmlrpc.php`, `/wp-json/`, feeds) redirect to the site (`vercel.json`).

## Kept as on the live site
- `/siding-remodeling-project-in-houston-tx/` is `noindex, nofollow` on WordPress. Kept that way and left out of the sitemap.

## Needs a decision
1. **FAQ page, Outdoor Living section** just says "Coming Soon!", and the menu links to it (`/faqs/#outdoor-faqs`). Either write 4–6 real FAQs or remove the section and the menu link.
2. **Consultation form** (on every page) still posts to WordPress, which won't exist after the DNS switch. Connect Formspree or a Vercel function before pointing the domain here.

## Numbers
- 203 pages (190 from the sitemaps + blog/portfolio pagination and 2 posts not in the sitemap), every URL identical to WordPress
- 189 URLs in the new sitemap (pagination and 3 noindex pages excluded)
- 1,850 files, ~250 MB served from `site/`
