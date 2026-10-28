// Clicks through every rebuilt interaction on the optimized build (mobile 390px).
// Usage: node interact.mjs <siteDir>
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import puppeteer from 'puppeteer';
const dir = process.argv[2];
await new Promise(r => http.createServer((req, res) => {
  let f = path.join(dir, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(f).isDirectory()) f = path.join(f, 'index.html'); } catch (e) {}
  fs.readFile(f, (e, b) => { if (e) { res.statusCode = 404; return res.end(); } const t = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.webp': 'image/webp' }[path.extname(f)]; if (t) res.setHeader('Content-Type', t); res.end(b); });
}).listen(8095, r));
const base = 'http://localhost:8095';
const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
const results = [];
const ok = (name, pass, info = '') => results.push(`${pass ? 'PASS' : 'FAIL'}  ${name}${info ? '  (' + info + ')' : ''}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function open(p, w = 390) {
  const page = await browser.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  await page.setViewport({ width: w, height: 844, isMobile: w < 768, hasTouch: w < 768 });
  await page.setRequestInterception(true);
  page.on('request', req => {
    if (req.url().endsWith('/api/lead')) return req.respond({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
    if (/googletagmanager|google-analytics|clarity\.ms|facebook\.net|translate\.google/.test(req.url())) return req.respond({ status: 200, contentType: 'text/javascript', body: '' });
    req.continue();
  });
  await page.goto(base + p, { waitUntil: 'load', timeout: 60000 });
  await sleep(800);
  page._errs = errs;
  return page;
}

try {
  // home: menu, popup, tabs, carousel, before/after, tracking delay
  let p = await open('/');
  ok('home: no JS errors', p._errs.length === 0, p._errs.join(' | ').slice(0, 200));
  ok('home: trackers waiting (not loaded before interaction)', await p.evaluate(() => document.querySelectorAll('script[type="text/ev-delay"]').length > 0));
  await p.tap('.mobile_menu_bar'); await sleep(500);
  ok('mobile menu opens', await p.evaluate(() => { const m = document.querySelector('.et_mobile_menu'); return !!m && getComputedStyle(m).display !== 'none' && m.offsetHeight > 100 && document.querySelector('.mobile_nav').classList.contains('opened'); }));
  ok('mobile menu has all items', await p.evaluate(() => document.querySelectorAll('#mobile_menu1 > li').length === document.querySelectorAll('#menu-main-menu > li').length));
  await p.evaluate(() => document.querySelector('.et_mobile_menu .open-sub').click()); await sleep(200);
  ok('mobile submenu toggle', await p.evaluate(() => !!document.querySelector('.et_mobile_menu li.open')));
  await p.tap('.mobile_menu_bar'); await sleep(500);
  ok('mobile menu closes', await p.evaluate(() => document.querySelector('.mobile_nav').classList.contains('closed')));
  ok('trackers run after interaction', await p.evaluate(() => document.querySelectorAll('script[type="text/ev-delay"]').length === 0 && !!document.querySelector('script[src*="googletagmanager"]')));
  const hasApt = await p.evaluate(() => !!document.querySelector('.kbs-apt-btn, .kbs_action-bar .et_pb_promo_button'));
  if (hasApt) {
    await p.evaluate(() => document.querySelector('.kbs-apt-btn, .kbs_action-bar .et_pb_promo_button').click()); await sleep(500);
    ok('consultation popup opens', await p.evaluate(() => getComputedStyle(document.querySelector('#kbs-appointment-form')).display === 'block'));
    await p.evaluate(() => document.querySelector('#kbs-appointment-form .close').click()); await sleep(500);
    ok('consultation popup closes', await p.evaluate(() => getComputedStyle(document.querySelector('#kbs-appointment-form')).display === 'none'));
  } else ok('consultation popup trigger present', false);
  if (await p.$('.et_pb_tabs_controls li')) {
    await p.evaluate(() => document.querySelectorAll('.et_pb_tabs_controls li')[1].click()); await sleep(200);
    ok('service tabs switch', await p.evaluate(() => document.querySelectorAll('.et_pb_tabs_controls li')[1].classList.contains('et_pb_tab_active') && getComputedStyle(document.querySelectorAll('.et_pb_all_tabs > .et_pb_tab')[1]).display !== 'none' && getComputedStyle(document.querySelectorAll('.et_pb_all_tabs > .et_pb_tab')[0]).display === 'none'));
  }
  ok('carousels laid out', await p.evaluate(() => [...document.querySelectorAll('.swiper-container')].every(c => c.classList.contains('ev-carousel'))));
  ok('before/after sliders built', await p.evaluate(() => document.querySelectorAll('.ev-ba .ev-ba-range').length >= 1 && [...document.querySelectorAll('.dnxte_before_after')].every(x => x.offsetHeight > 100)));
  await p.evaluate(() => { const r = document.querySelector('.ev-ba-range'); r.value = 20; r.dispatchEvent(new Event('input')); });
  ok('before/after drag works', await p.evaluate(() => document.querySelector('.ev-ba .dnxte_bf_img').style.clipPath.includes('80%')));
  await p.evaluate(() => document.querySelector('.lang-select[data-lang="Spanish"]').click()); await sleep(300);
  ok('ES button loads Google Translate on demand', await p.evaluate(() => !!document.querySelector('#ev-gt')));
  await p.close();

  // FAQ toggles
  p = await open('/faqs/');
  ok('faq: no JS errors', p._errs.length === 0, p._errs.join(' | ').slice(0, 200));
  await p.evaluate(() => document.querySelector('.et_pb_toggle .et_pb_toggle_title').click()); await sleep(450);
  ok('faq toggle opens', await p.evaluate(() => { const t = document.querySelector('.et_pb_toggle'); return t.classList.contains('et_pb_toggle_open') && t.querySelector('.et_pb_toggle_content').offsetHeight > 10; }));
  await p.evaluate(() => document.querySelectorAll('.et_pb_accordion')[0].querySelectorAll('.et_pb_toggle_title')[1].click()); await sleep(450);
  ok('accordion closes the other item', await p.evaluate(() => { const a = document.querySelectorAll('.et_pb_accordion')[0].querySelectorAll('.et_pb_toggle'); return !a[0].classList.contains('et_pb_toggle_open') && a[1].classList.contains('et_pb_toggle_open'); }));
  await p.close();

  // contact form -> /api/lead -> /thank-you/
  p = await open('/contact/');
  await p.evaluate(() => { const f = document.querySelector('form.wpcf7-form'); f.querySelector('[type=submit]').click(); });
  await sleep(300);
  ok('form: empty submit shows field errors', await p.evaluate(() => document.querySelectorAll('.wpcf7-not-valid-tip').length > 0));
  await p.evaluate(() => {
    const f = document.querySelector('form.wpcf7-form');
    f.querySelectorAll('[aria-required="true"], .wpcf7-validates-as-required').forEach(el => { el.value = el.type === 'email' ? 'test@example.com' : el.name === 'zipcode' ? '77429' : el.name === 'phonenumber' ? '8325551234' : 'Test'; });
  });
  let posted = null;
  p.on('request', r => { if (r.url().endsWith('/api/lead')) posted = r.postData(); });
  await Promise.all([p.waitForNavigation({ timeout: 8000 }).catch(() => null), p.evaluate(() => document.querySelector('form.wpcf7-form [type=submit]').click())]);
  ok('form posts to /api/lead with fields', !!posted && /"fullname":"Test"/.test(posted) && /"form_id":"3991"|"form_id":"236"/.test(posted), (posted || '').slice(0, 120));
  ok('form redirects to /thank-you/', p.url().endsWith('/thank-you/'), p.url());
  await p.close();

  // popup form on home submits too
  p = await open('/');
  await p.evaluate(() => document.querySelector('.kbs-apt-btn, .kbs_action-bar .et_pb_promo_button')?.click()); await sleep(400);
  await p.evaluate(() => { const f = document.querySelector('#kbs-appointment-form form'); f.querySelectorAll('[aria-required="true"], .wpcf7-validates-as-required').forEach(el => { el.value = el.type === 'email' ? 'a@b.co' : 'Test'; }); });
  posted = null; p.on('request', r => { if (r.url().endsWith('/api/lead')) posted = r.postData(); });
  await Promise.all([p.waitForNavigation({ timeout: 8000 }).catch(() => null), p.evaluate(() => document.querySelector('#kbs-appointment-form form [type=submit]').click())]);
  ok('popup consultation form submits', !!posted && p.url().endsWith('/thank-you/'), p.url());
  await p.close();

  // gallery slider + lightbox + multi-view (LP page)
  p = await open('/lp-smartside-in-houston-tx/');
  ok('lp: no JS errors', p._errs.length === 0, p._errs.join(' | ').slice(0, 200));
  ok('gallery slider has arrows + dots', await p.evaluate(() => !!document.querySelector('.et_pb_gallery_fullwidth .et-pb-slider-arrows') && !!document.querySelector('.et_pb_gallery_fullwidth .et-pb-controllers')));
  ok('phone image swapped (multi-view)', await p.evaluate(() => document.querySelector('.et_pb_image_11 img').getAttribute('src').includes('LP-SmartSide-Colors.jpg')));
  await p.close();
  p = await open('/about/');
  ok('about: phone History text shown', await p.evaluate(() => [...document.querySelectorAll('.et_pb_text_inner')].some(e => /Everest was formed/.test(e.textContent) && e.offsetHeight > 200)));
  await p.close();

  // portfolio filter
  p = await open('/portfolio/');
  ok('portfolio items visible', await p.evaluate(() => [...document.querySelectorAll('.filtr-item')].filter(x => x.offsetHeight > 50).length >= 6));
  await p.evaluate(() => document.querySelectorAll('.simplefilter li[data-multifilter]')[1].click()); await sleep(200);
  ok('portfolio filter hides others', await p.evaluate(() => { const it = [...document.querySelectorAll('.filtr-item')]; return it.some(x => x.style.display === 'none') && it.some(x => x.style.display !== 'none'); }));
  await p.close();

  // quick quote calculator
  p = await open('/quick-quote/');
  ok('quick quote calculator present', await p.evaluate(() => typeof window.do_math === 'function'));
  await p.close();

  // desktop: sticky header + dropdown CSS
  p = await open('/', 1366);
  await p.evaluate(() => scrollTo(0, 1500)); await sleep(300);
  ok('desktop: header sticks on scroll', await p.evaluate(() => Math.round(document.querySelector('header.et-l--header').getBoundingClientRect().top) === 0));
  ok('desktop: stuck header gets teal background', await p.evaluate(() => getComputedStyle(document.querySelector('.et_pb_section_0_tb_header')).backgroundColor === 'rgb(231, 248, 248)'));
  ok('desktop: no JS errors', p._errs.length === 0, p._errs.join(' | ').slice(0, 200));
  await p.close();
} catch (e) { results.push('ERROR ' + e.message); }
console.log(results.join('\n'));
console.log(`${results.filter(r => r.startsWith('PASS')).length}/${results.length} passed`);
await browser.close(); process.exit(0);
