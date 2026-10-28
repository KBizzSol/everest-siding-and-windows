// Keeps only the CSS each page uses, minifies it and inlines it where optimize.py left <!--EV-CSS:id-->.
// Usage: node tools/purge.mjs site   (needs: npm i --no-save purgecss lightningcss)
import fs from 'node:fs';
import path from 'node:path';
import { PurgeCSS } from 'purgecss';
import { transform } from 'lightningcss';

const OUT = path.resolve(process.argv[2] || 'site');
const BUILD = path.join(OUT, '_ev');
const siteJs = fs.readFileSync(path.join(OUT, 'assets', 'site.js'), 'utf8');

// classes/states added at runtime by site.js or Google Translate, kept even if not in the HTML
const safelist = {
  standard: ['mobile_nav', 'opened', 'closed', 'open-sub', 'open', 'et_pb_toggle_open', 'et_pb_toggle_close', 'et_pb_tab_active',
    'et_pb_active_content', 'et-pb-active-slide', 'et-pb-active-control', 'et_pb_sticky', 'et-visible', 'et-hidden', 'swiper-slide',
    'sent', 'failed', 'invalid', 'submitting', 'spam', 'init', 'js', 'no-js', 'close', 'translated-ltr', 'translated-rtl',
    'wpcf7-not-valid', 'wpcf7-not-valid-tip', 'wpcf7-response-output', 'current-menu-item',
    /^ev-/, /^twentytwenty/, /^goog-/, /^skiptranslate/, /^et_mobile_menu/],
  deep: [/et_mobile_menu/, /mobile_nav/, /ev-lightbox/, /kbs-popup-box/, /ev-ba/],
  greedy: [/et_pb_sticky/, /opened/, /open-sub/, /et_pb_toggle_open/, /et_pb_tab_active/, /wpcf7-not-valid/],
};

function walk(d, acc = []) {
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f);
    const st = fs.statSync(p);
    if (st.isDirectory()) { if (p !== BUILD) walk(p, acc); }
    else if (f.endsWith('.html')) acc.push(p);
  }
  return acc;
}

const pages = walk(OUT);
let before = 0, after = 0, done = 0;
const cache = new Map();
const failed = [];   // identical (css, html-class-set) pairs are common across posts

async function one(fp) {
  let html = fs.readFileSync(fp, 'utf8');
  const m = html.match(/<!--EV-CSS:([a-f0-9]+)-->/);
  if (!m) return;
  const cssFile = path.join(BUILD, m[1] + '.css');
  const css = fs.readFileSync(cssFile, 'utf8');
  before += css.length;
  const classes = [...new Set((html.match(/class=["'][^"']*["']/g) || []).join(' ').split(/[\s"'=]+/))].sort().join(' ');
  const key = css.length + ':' + css.slice(0, 200) + ':' + classes.length + ':' + classes;
  let out = cache.get(key);
  if (!out) {
    const clean = (code, minify) => transform({ filename: 'p.css', code: Buffer.from(code), minify, errorRecovery: true }).code.toString();
    let normalized;
    try { normalized = clean(css, false); } catch (e) { normalized = css; }   // repairs WordPress CSS syntax slips
    try {
      const res = await new PurgeCSS().purge({
        content: [{ raw: html, extension: 'html' }, { raw: siteJs, extension: 'js' }],
        css: [{ raw: normalized }],
        safelist,
        fontFace: false, keyframes: false, variables: false,
      });
      out = clean(res.map(r => r.css).join('\n'), true);
    } catch (e) {
      failed.push(path.relative(OUT, fp) + ': ' + String(e.message || e).split('\n')[0]);
      out = clean(normalized, true);                                          // still works, just bigger
    }
    cache.set(key, out);
  }
  out = out.replace(/(['"]?)Poppins\1\s*,/g, (m, q) => `${q}Poppins${q},'Poppins Fallback',`);   // metric-matched fallback
  after += out.length;
  html = html.replace(m[0], '<style id="ev-css">' + out.replace(/<\/style/gi, '<\\/style') + '</style>');
  fs.writeFileSync(fp, html);
  done++;
}

const queue = pages.slice();
await Promise.all(Array.from({ length: 4 }, async () => { while (queue.length) await one(queue.shift()); }));
fs.rmSync(BUILD, { recursive: true, force: true });
if (failed.length) console.log('  purge fell back to full CSS on:', failed.slice(0, 10));
console.log(`  purge: ${done} pages, avg css ${(before / Math.max(done, 1) / 1024).toFixed(0)} KB -> ${(after / Math.max(done, 1) / 1024).toFixed(0)} KB`);
