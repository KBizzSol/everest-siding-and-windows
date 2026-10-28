// Evaluate a JS expression on a page in two builds. Usage: node probe.mjs <dirA> <dirB> <path> "<js expr>"
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import puppeteer from 'puppeteer';
const [dirA, dirB, page, expr] = process.argv.slice(2);
const serve = (dir, port) => new Promise(r => http.createServer((req, res) => {
  let f = path.join(dir, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(f).isDirectory()) f = path.join(f, 'index.html'); } catch (e) {}
  fs.readFile(f, (e, b) => { if (e) { res.statusCode = 404; return res.end(); } const t = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.webp': 'image/webp' }[path.extname(f)]; if (t) res.setHeader('Content-Type', t); res.end(b); });
}).listen(port, r));
await serve(dirA, 8093); await serve(dirB, 8094);
const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
for (const port of [8093, 8094]) {
  const p = await browser.newPage();
  await p.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
  await p.goto(`http://localhost:${port}${page}`, { waitUntil: 'load', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));
  console.log(port === 8093 ? 'ORIG:' : 'NEW: ', JSON.stringify(await p.evaluate(expr)).slice(0, 1500));
  await p.close();
}
await browser.close(); process.exit(0);
