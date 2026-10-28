// Lighthouse (mobile) + full-page mobile screenshots for a built site/ folder.
// Usage: node lh.mjs <siteDir> <outDir> <port> <path1,path2,...> [--shots]
// Runs in a Vercel Sandbox with Chrome (CHROME_PATH). Not deployed.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import handler from 'serve-handler';
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import puppeteer from 'puppeteer';

const [siteDir, outDir, port, list, flag] = process.argv.slice(2);
const pages = list.split(',');
fs.mkdirSync(outDir, { recursive: true });

const server = http.createServer((req, res) => handler(req, res, {
  public: siteDir, cleanUrls: false, trailingSlash: true, directoryListing: false,
  headers: [{ source: '**/*.@(webp|jpg|jpeg|png|gif|svg|woff|woff2|ttf|css|js)', headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000' }] }],
}));
await new Promise(r => server.listen(Number(port), r));
const base = `http://localhost:${port}`;

const chrome = await chromeLauncher.launch({ chromePath: process.env.CHROME_PATH, chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] });
const results = {};
for (const p of pages) {
  const r = await lighthouse(base + p, { port: chrome.port, output: 'json', logLevel: 'error', onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'], formFactor: 'mobile', screenEmulation: { mobile: true, width: 412, height: 823, deviceScaleFactor: 1.75, disabled: false } });
  const a = r.lhr.audits;
  results[p] = {
    perf: Math.round(r.lhr.categories.performance.score * 100),
    a11y: Math.round(r.lhr.categories.accessibility.score * 100),
    bp: Math.round(r.lhr.categories['best-practices'].score * 100),
    seo: Math.round(r.lhr.categories.seo.score * 100),
    FCP: a['first-contentful-paint'].displayValue, LCP: a['largest-contentful-paint'].displayValue,
    TBT: a['total-blocking-time'].displayValue, CLS: a['cumulative-layout-shift'].displayValue, SI: a['speed-index'].displayValue,
    bytes: a['total-byte-weight'].numericValue,
    lcpEl: (a['largest-contentful-paint-element']?.details?.items?.[0]?.items?.[0]?.node?.snippet || '').slice(0, 200),
    topIssues: Object.values(a).filter(x => x.score !== null && x.score < 0.9 && x.details && (x.details.overallSavingsMs > 100 || x.details.overallSavingsBytes > 20000))
      .map(x => `${x.id}: ${x.displayValue || ''}`).slice(0, 12),
    a11yFails: Object.values(a).filter(x => x.score === 0 && r.lhr.categories.accessibility.auditRefs.some(ar => ar.id === x.id)).map(x => x.id),
  };
  fs.writeFileSync(path.join(outDir, 'lh-' + (p.replace(/\W+/g, '_') || 'home') + '.json'), JSON.stringify(r.lhr));
}
await chrome.kill();
fs.writeFileSync(path.join(outDir, 'scores.json'), JSON.stringify(results, null, 1));
console.log(JSON.stringify(results, null, 1));

if (flag === '--shots') {
  const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
  const errs = [];
  page.on('pageerror', e => errs.push(String(e.message).slice(0, 200)));
  for (const p of pages) {
    await page.goto(base + p, { waitUntil: 'networkidle0', timeout: 60000 });
    await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); } window.scrollTo(0, 0); });
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(outDir, 'shot-' + (p.replace(/\W+/g, '_') || 'home') + '.png'), fullPage: true });
  }
  fs.writeFileSync(path.join(outDir, 'js-errors.json'), JSON.stringify(errs, null, 1));
  await browser.close();
}
server.close();
