// Viewport screenshots (not full page) at given scroll offsets, phone + desktop, as small JPEGs for review.
// Usage: node shots.mjs <siteDir> <outDir> <path> <w> <y1,y2,...>
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import puppeteer from 'puppeteer';
const [dir, out, page, w = '390', ys = '0'] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const port = 8100 + Math.floor(Math.random() * 800);
const T = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.woff2': 'font/woff2', '.jpg': 'image/jpeg', '.png': 'image/png' };
const srv = http.createServer((req, res) => {
  let f = path.join(dir, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(f).isDirectory()) f = path.join(f, 'index.html'); } catch (e) {}
  fs.readFile(f, (e, b) => { if (e) { res.statusCode = 404; return res.end(); } if (T[path.extname(f)]) res.setHeader('Content-Type', T[path.extname(f)]); res.end(b); });
});
await new Promise(r => srv.listen(port, r));
const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
const p = await browser.newPage();
const W = Number(w);
await p.setViewport({ width: W, height: W < 768 ? 844 : 900, isMobile: W < 768, hasTouch: W < 768 });
await p.setRequestInterception(true);
p.on('request', q => /googletagmanager|google-analytics|clarity\.ms|facebook|translate\.google|maps\.google|youtube/.test(q.url()) ? q.respond({ status: 200, body: '' }) : q.continue());
await p.goto(`http://localhost:${port}${page}`, { waitUntil: 'load', timeout: 60000 });
await p.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 700) { scrollTo(0, y); await new Promise(r => setTimeout(r, 30)); } });
await new Promise(r => setTimeout(r, 1200));
const name = (page.replace(/\W+/g, '_') || 'home') + '-' + W;
for (const y of ys.split(',').map(Number)) {
  await p.evaluate(y => scrollTo(0, y), y); await new Promise(r => setTimeout(r, 350));
  await p.screenshot({ path: path.join(out, `${name}-${y}.jpg`), type: 'jpeg', quality: 55 });
}
console.log(name, 'height', await p.evaluate(() => document.body.scrollHeight));
await browser.close(); srv.close(); process.exit(0);
