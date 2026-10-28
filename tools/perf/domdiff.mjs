// Compare module sizes/visibility between two builds of the same page (mobile 390px).
// Usage: node domdiff.mjs <dirA> <dirB> <path> [portA] [portB]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer';

const [dirA, dirB, page, pa = '8091', pb = '8092'] = process.argv.slice(2);
function serve(dir, port) {
  return new Promise(r => http.createServer((req, res) => {
    let f = path.join(dir, decodeURIComponent(req.url.split('?')[0]));
    try { if (fs.statSync(f).isDirectory()) f = path.join(f, 'index.html'); } catch (e) {}
    fs.readFile(f, (err, buf) => { if (err) { res.statusCode = 404; return res.end(); }
      const t = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.webp': 'image/webp' }[path.extname(f)];
      if (t) res.setHeader('Content-Type', t); res.end(buf); });
  }).listen(Number(port), r));
}
await serve(dirA, pa); await serve(dirB, pb);
const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
async function snap(port) {
  const p = await browser.newPage();
  await p.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
  await p.goto(`http://localhost:${port}${page}`, { waitUntil: 'networkidle0', timeout: 60000 });
  await p.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); } scrollTo(0, 0); });
  await new Promise(r => setTimeout(r, 700));
  const out = await p.evaluate(() => {
    const res = {};
    document.querySelectorAll('[class*="et_pb_section_"],[class*="et_pb_row_"],[class*="et_pb_module"],[class*="et_pb_column_"]').forEach(el => {
      const key = [...el.classList].filter(c => /_\d+(_tb_(header|footer|body))?$/.test(c)).join('.') || null;
      if (!key) return;
      const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
      res[key] = { w: Math.round(r.width), ff: cs.fontFamily.slice(0, 24) + ' ' + cs.fontWeight + ' ' + cs.fontSize + '/' + cs.lineHeight, h: Math.round(r.height), y: Math.round(r.top + scrollY), vis: cs.display !== 'none' && cs.visibility !== 'hidden' && cs.opacity !== '0',
        bg: cs.backgroundImage.replace(/https?:\/\/localhost:\d+/g, '').slice(0, 60), txt: (el.innerText || '').slice(0, 40).replace(/\s+/g, ' ') };
    });
    return res;
  });
  await p.close();
  return out;
}
const A = await snap(pa), B = await snap(pb);
const rows = [];
for (const k of Object.keys(A)) {
  const a = A[k], b = B[k];
  if (!b) { rows.push(`MISSING in B: ${k} h=${a.h} "${a.txt}"`); continue; }
  if (Math.abs(a.h - b.h) > 6 || a.vis !== b.vis || (a.bg !== b.bg && !(a.bg.includes('ev768') || b.bg.includes('ev768'))))
    rows.push(`${k}: h ${a.h}->${b.h} w ${a.w}->${b.w}${a.ff !== b.ff ? ' font [' + a.ff + '] -> [' + b.ff + ']' : ''} vis ${a.vis}->${b.vis}${a.bg !== b.bg ? ' bg ' + a.bg + ' -> ' + b.bg : ''} "${a.txt}"`);
}
console.log(`${page}: ${rows.length} differences`);
// print only the outermost differing items first (sections/rows), then modules
rows.sort((x, y) => (x.includes('section') ? 0 : x.includes('row') ? 1 : 2) - (y.includes('section') ? 0 : y.includes('row') ? 1 : 2));
console.log(rows.filter(r => !/section_|row_|column_/.test(r.split(':')[0])).slice(0, 14).join('\n'));
await browser.close();
process.exit(0);
