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
GitHub → Actions → **Mirror live site** → Run workflow (or change `tools/.mirror-trigger` and push). It mirrors, fetches any missing assets, rebuilds `site/` and commits. Vercel redeploys automatically.

## Rebuild after editing
```
python3 tools/postprocess.py
git add -A && git commit -m "Update site" && git push   # Vercel redeploys automatically
```
To change an original page, edit the file in `mirror/`, then rebuild.

## Phase 1 (migration) — what changed vs. WordPress
- **Nothing visible.** Layout, URLs, menus, header, footer, images, Yoast meta and schema are unchanged.
- Internal links point to local root-relative paths; canonical, og and JSON-LD URLs stay absolute.
- WordPress-only head links (REST API, oEmbed, RSD, pingback) were removed because they would 404.
- `sitemap_index.xml`, `page-sitemap.xml`, `post-sitemap.xml` and `robots.txt` are generated from the built pages.
- WordPress system URLs (`/wp-admin/`, `/wp-login.php`, `/xmlrpc.php`, `/wp-json/`, feeds) redirect in `vercel.json`.

## Confirm before pointing the domain here
- **Consultation form:** the WordPress form handler doesn't exist on static hosting. Connect a form service (e.g. Formspree) or a Vercel function before the DNS switch so leads keep arriving.
- **EN/ES switcher:** check the Spanish pages work on the Vercel preview.
- Then add `everestsidingandwindows.com` in Vercel → Project → Domains and update DNS. Do this only after `mirror/` is final, because the live WordPress site is the mirror's source.

## Phase 2 (next)
Speed, image compression, accessibility, SEO/AEO and design improvements, as on Bay Colony.
