/* Everest static site script — replaces jQuery, Divi, Divi Essential and the WordPress plugins.
   Rebuilds only what the pages use: mobile menu, consultation popup, tabs, toggles/accordions,
   sliders/carousels, before/after, gallery lightbox, scroll-to-top, clickable blurbs, phone mask,
   EN/ES (Google Translate on demand), forms (posted to /api/lead), and tracking loaded on first interaction. */
(function () {
  'use strict';
  var d = document, w = window;
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); };
  var on = function (el, ev, fn, opt) { el.addEventListener(ev, fn, opt || false); };
  var reduce = w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function fadeIn(el) { el.style.display = 'block'; el.style.opacity = 0; requestAnimationFrame(function () { el.style.transition = 'opacity .3s'; el.style.opacity = 1; }); }
  function fadeOut(el) { el.style.transition = 'opacity .3s'; el.style.opacity = 0; setTimeout(function () { el.style.display = 'none'; }, 300); }
  function slide(el, open) {
    if (reduce) { el.style.display = open ? 'block' : 'none'; return; }
    el.style.overflow = 'hidden'; el.style.display = 'block';
    var h = el.scrollHeight;
    el.style.transition = 'none'; el.style.height = open ? '0px' : h + 'px';
    requestAnimationFrame(function () {
      el.style.transition = 'height .3s ease'; el.style.height = open ? h + 'px' : '0px';
      setTimeout(function () { el.style.height = ''; el.style.overflow = ''; el.style.transition = ''; if (!open) el.style.display = 'none'; }, 320);
    });
  }

  /* ---------- mobile menu (Divi builds #mobile_menuN from the desktop menu) ---------- */
  function mobileMenus() {
    $$('.et_pb_menu, .et_pb_fullwidth_menu').forEach(function (m, i) {
      var nav = $('.mobile_nav', m), src = $('.et-menu-nav > ul', m);
      if (!nav || !src || $('.et_mobile_menu', nav)) return;
      var ul = d.createElement('ul');
      ul.id = 'mobile_menu' + (i + 1);
      ul.className = 'et_mobile_menu';
      ul.innerHTML = src.innerHTML;
      $$('li', ul).forEach(function (li) {
        li.removeAttribute('id');
        if (li.classList.contains('menu-item-has-children')) {
          var t = d.createElement('span'); t.className = 'open-sub'; li.insertBefore(t, li.firstChild);
        }
      });
      ul.style.display = 'none';
      nav.appendChild(ul);
      var bar = $('.mobile_menu_bar', nav);
      if (bar) { bar.setAttribute('role', 'button'); bar.setAttribute('aria-label', 'Menu'); bar.setAttribute('aria-expanded', 'false'); bar.tabIndex = 0; }
      on(nav, 'click', function (e) {
        if (e.target.closest('.open-sub')) { e.preventDefault(); e.stopPropagation(); e.target.closest('li').classList.toggle('open'); return; }
        if (e.target.closest('.et_mobile_menu a')) {
          var a = e.target.closest('a');
          if (a.getAttribute('href') === '#') { e.preventDefault(); a.parentNode.classList.toggle('open'); }
          return;
        }
        if (e.target.closest('.et_mobile_menu')) return;
        var open = nav.classList.contains('closed');
        nav.classList.toggle('opened', open); nav.classList.toggle('closed', !open);
        if (bar) bar.setAttribute('aria-expanded', open ? 'true' : 'false');
        slide(ul, open);
      });
      on(nav, 'keydown', function (e) { if ((e.key === 'Enter' || e.key === ' ') && e.target === bar) { e.preventDefault(); bar.click(); } });
      on(d, 'click', function (e) {
        if (nav.classList.contains('opened') && !e.target.closest('.mobile_nav')) {
          nav.classList.remove('opened'); nav.classList.add('closed'); if (bar) bar.setAttribute('aria-expanded', 'false'); slide(ul, false);
        }
      });
    });
    // touch devices: first tap on a desktop parent item opens its dropdown
    $$('.et-menu .menu-item-has-children > a').forEach(function (a) {
      on(a, 'click', function (e) { if (a.getAttribute('href') === '#') e.preventDefault(); });
    });
  }

  /* ---------- consultation popup ---------- */
  function popup() {
    var box = $('#kbs-appointment-form');
    if (!box) return;
    $$('.kbs-popup-box > .et_pb_column').forEach(function (c) {
      if (!$('.close', c)) { var x = d.createElement('div'); x.className = 'close'; x.setAttribute('role', 'button'); x.setAttribute('aria-label', 'Close'); x.tabIndex = 0; c.appendChild(x); }
    });
    on(d, 'click', function (e) {
      var trigger = e.target.closest('.kbs-apt-btn, .kbs_action-bar .et_pb_promo_button');
      if (trigger) {
        e.preventDefault();
        fadeIn(box);
        var first = $('input[type="text"], input[type="email"]', box);
        if (first) setTimeout(function () { try { first.focus({ preventScroll: true }); } catch (x) {} }, 320);
        return;
      }
      var popupOpen = $$('.kbs-popup-box').filter(function (p) { return p.style.display === 'block'; });
      if (!popupOpen.length) return;
      if (e.target.closest('.kbs-popup-box .close') || !e.target.closest('.kbs-popup-box .et_pb_column')) popupOpen.forEach(fadeOut);
    });
    on(d, 'keydown', function (e) {
      if (e.key === 'Escape') $$('.kbs-popup-box').forEach(function (p) { if (p.style.display === 'block') fadeOut(p); });
    });
  }

  /* ---------- tabs ---------- */
  function tabs() {
    $$('.et_pb_tabs').forEach(function (t) {
      var ctl = $$('.et_pb_tabs_controls > li', t), panes = $$('.et_pb_all_tabs > .et_pb_tab', t);
      ctl.forEach(function (li, i) {
        var a = $('a', li);
        if (a) { a.setAttribute('role', 'tab'); a.setAttribute('aria-selected', li.classList.contains('et_pb_tab_active') ? 'true' : 'false'); }
        on(li, 'click', function (e) {
          e.preventDefault();
          ctl.forEach(function (x, j) { x.classList.toggle('et_pb_tab_active', j === i); var xa = $('a', x); if (xa) xa.setAttribute('aria-selected', j === i ? 'true' : 'false'); });
          panes.forEach(function (p, j) { p.classList.toggle('et_pb_active_content', j === i); p.style.display = j === i ? 'block' : 'none'; });
        });
      });
    });
  }

  /* ---------- toggles & accordions ---------- */
  function toggles() {
    $$('.et_pb_toggle').forEach(function (t) {
      var title = $('.et_pb_toggle_title', t), body = $('.et_pb_toggle_content', t);
      if (!title || !body) return;
      title.setAttribute('role', 'button'); title.tabIndex = 0;
      title.setAttribute('aria-expanded', t.classList.contains('et_pb_toggle_open') ? 'true' : 'false');
      function set(el, open) {
        var b = $('.et_pb_toggle_content', el), tt = $('.et_pb_toggle_title', el);
        el.classList.toggle('et_pb_toggle_open', open); el.classList.toggle('et_pb_toggle_close', !open);
        if (tt) tt.setAttribute('aria-expanded', open ? 'true' : 'false');
        slide(b, open);
      }
      function toggle() {
        var open = !t.classList.contains('et_pb_toggle_open');
        var acc = t.closest('.et_pb_accordion');
        if (acc) {
          if (!open) return;   // accordions keep one item open, like Divi
          $$('.et_pb_toggle', acc).forEach(function (o) { if (o !== t && o.classList.contains('et_pb_toggle_open')) set(o, false); });
        }
        set(t, open);
      }
      on(title, 'click', toggle);
      on(title, 'keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
    });
    // open the toggle a URL hash points to (e.g. /faqs/#siding-faqs)
    if (location.hash.length > 1) { try { var el = $(location.hash); if (el) setTimeout(function () { el.scrollIntoView(); }, 50); } catch (x) {} }
  }

  /* ---------- carousels (Divi Essential swiper) ---------- */
  function perView(bp) {
    var p = String(bp || '1|1|1').split('|').map(Number);
    var vw = w.innerWidth;
    return Math.max(1, vw >= 981 ? p[0] : vw >= 768 ? (p[1] || p[0]) : (p[2] || p[1] || p[0]));
  }
  function carousels() {
    $$('.swiper-container').forEach(function (c) {
      var wrap = $('.swiper-wrapper', c);
      if (!wrap) return;
      var slides = Array.prototype.slice.call(wrap.children);
      if (!slides.length) return;
      var gap = Number(c.getAttribute('data-spacing') || 0);
      var auto = c.getAttribute('data-autoplay') === '1' || c.getAttribute('data-autoplay') === 'on';
      var delay = Math.max(1500, Number(c.getAttribute('data-delay') || 3000));
      var idx = 0, n = 1, timer = null;
      c.classList.add('ev-carousel');
      wrap.style.display = 'flex'; wrap.style.transition = reduce ? 'none' : 'transform .4s ease'; wrap.style.willChange = 'transform';
      function layout() {
        n = perView(c.getAttribute('data-breakpoints'));
        var width = (c.clientWidth - gap * (n - 1)) / n;
        slides.forEach(function (s, i) { s.style.flex = '0 0 ' + width + 'px'; s.style.width = width + 'px'; s.style.marginRight = (i < slides.length - 1 ? gap : 0) + 'px'; s.classList.add('swiper-slide'); });
        go(Math.min(idx, Math.max(0, slides.length - n)));
      }
      function go(i) {
        var max = Math.max(0, slides.length - n);
        idx = i > max ? 0 : i < 0 ? max : i;
        var x = slides[idx] ? slides[idx].offsetLeft - slides[0].offsetLeft : 0;
        wrap.style.transform = 'translate3d(' + (-x) + 'px,0,0)';
        slides.forEach(function (s, j) { var vis = j >= idx && j < idx + n; s.setAttribute('aria-hidden', vis ? 'false' : 'true'); });
      }
      function play() { if (auto && !reduce && slides.length > n) { stop(); timer = setInterval(function () { go(idx + 1); }, delay); } }
      function stop() { if (timer) clearInterval(timer); timer = null; }
      // arrows if the module has them
      var mod = c.closest('.et_pb_module_inner') || c.parentNode;
      var prev = mod && mod.parentNode ? $('[class*="arrows"] [class*="prev"], .swiper-button-prev', mod.parentNode) : null;
      var next = mod && mod.parentNode ? $('[class*="arrows"] [class*="next"], .swiper-button-next', mod.parentNode) : null;
      if (prev) on(prev, 'click', function (e) { e.preventDefault(); go(idx - 1); play(); });
      if (next) on(next, 'click', function (e) { e.preventDefault(); go(idx + 1); play(); });
      // swipe
      var sx = null;
      on(c, 'touchstart', function (e) { sx = e.touches[0].clientX; stop(); }, { passive: true });
      on(c, 'touchend', function (e) { if (sx === null) return; var dx = e.changedTouches[0].clientX - sx; if (Math.abs(dx) > 40) go(idx + (dx < 0 ? 1 : -1)); sx = null; play(); }, { passive: true });
      if (c.getAttribute('data-pauseonhover')) { on(c, 'mouseenter', stop); on(c, 'mouseleave', play); }
      var rt; on(w, 'resize', function () { clearTimeout(rt); rt = setTimeout(layout, 150); });
      layout(); play();
    });
  }

  /* ---------- Divi slider (rotating hero titles etc.) ---------- */
  function sliders() {
    $$('.et_pb_slider').forEach(function (s) {
      var slides = $$('.et_pb_slides > .et_pb_slide', s);
      if (slides.length < 2) return;
      var m = s.className.match(/et_slider_speed_(\d+)/), speed = m ? Number(m[1]) : 7000;
      var i = Math.max(0, slides.findIndex(function (x) { return x.classList.contains('et-pb-active-slide'); }));
      function show(k) {
        slides[i].classList.remove('et-pb-active-slide');
        i = (k + slides.length) % slides.length;
        slides[i].classList.add('et-pb-active-slide');
        var ctl = $$('.et-pb-controllers a', s); ctl.forEach(function (a, j) { a.classList.toggle('et-pb-active-control', j === i); });
      }
      $$('.et-pb-controllers a', s).forEach(function (a, j) { on(a, 'click', function (e) { e.preventDefault(); show(j); }); });
      var pv = $('.et-pb-arrow-prev', s), nx = $('.et-pb-arrow-next', s);
      if (pv) on(pv, 'click', function (e) { e.preventDefault(); show(i - 1); });
      if (nx) on(nx, 'click', function (e) { e.preventDefault(); show(i + 1); });
      if (s.classList.contains('et_slider_auto') && !reduce) setInterval(function () { if (!d.hidden) show(i + 1); }, speed);
    });
    // fullwidth gallery sliders: show one image at a time with arrows
    $$('.et_pb_gallery_fullwidth').forEach(function (g) {
      var items = $$('.et_pb_gallery_item', g);
      if (items.length < 2) return;
      var i = 0;
      items.forEach(function (it, j) { it.style.display = j ? 'none' : 'block'; });
      function show(k) { items[i].style.display = 'none'; i = (k + items.length) % items.length; items[i].style.display = 'block'; }
      var pv = $('.et-pb-arrow-prev', g), nx = $('.et-pb-arrow-next', g);
      if (pv) on(pv, 'click', function (e) { e.preventDefault(); show(i - 1); });
      if (nx) on(nx, 'click', function (e) { e.preventDefault(); show(i + 1); });
    });
  }

  /* ---------- before / after ---------- */
  function beforeAfter() {
    $$('.dnxte_bf_img').forEach(function (b) {
      var box = b.parentNode, a = $('.dnxte_af_img', box);
      if (!a || box.classList.contains('ev-ba')) return;
      box.classList.add('ev-ba', 'twentytwenty-container');
      var pos = Number(box.getAttribute('data-offset') || 0.5) * 100;
      var bl = box.getAttribute('data-before-label') || 'Before', al = box.getAttribute('data-after-label') || 'After';
      var h = d.createElement('div'); h.className = 'ev-ba-handle twentytwenty-handle'; h.innerHTML = '<span class="twentytwenty-left-arrow"></span><span class="twentytwenty-right-arrow"></span>';
      var lb = d.createElement('div'); lb.className = 'ev-ba-label ev-ba-before'; lb.textContent = bl;
      var la = d.createElement('div'); la.className = 'ev-ba-label ev-ba-after'; la.textContent = al;
      var r = d.createElement('input'); r.type = 'range'; r.min = 0; r.max = 100; r.value = pos; r.className = 'ev-ba-range'; r.setAttribute('aria-label', 'Drag to compare before and after');
      box.appendChild(lb); box.appendChild(la); box.appendChild(h); box.appendChild(r);
      function set(p) { b.style.clipPath = 'inset(0 ' + (100 - p) + '% 0 0)'; h.style.left = p + '%'; }
      on(r, 'input', function () { set(Number(r.value)); });
      set(pos);
    });
  }

  /* ---------- gallery lightbox ---------- */
  function lightbox() {
    var links = $$('.et_pb_gallery_image a[href$=".webp"], .et_pb_gallery_image a[href$=".jpg"], .et_pb_gallery_image a[href$=".png"], .et_pb_lightbox_image, a.swipebox, .et_pb_image a[href$=".webp"], .et_pb_image a[href$=".jpg"]');
    if (!links.length) return;
    var ov = null, list = [], cur = 0;
    function build() {
      ov = d.createElement('div'); ov.className = 'ev-lightbox'; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true');
      ov.innerHTML = '<button class="ev-lb-close" aria-label="Close">&times;</button><button class="ev-lb-prev" aria-label="Previous">&#8249;</button><img alt=""><button class="ev-lb-next" aria-label="Next">&#8250;</button>';
      d.body.appendChild(ov);
      on(ov, 'click', function (e) {
        if (e.target.closest('.ev-lb-prev')) show(cur - 1);
        else if (e.target.closest('.ev-lb-next')) show(cur + 1);
        else if (e.target.tagName !== 'IMG') close();
      });
      on(d, 'keydown', function (e) { if (!ov.classList.contains('open')) return; if (e.key === 'Escape') close(); if (e.key === 'ArrowLeft') show(cur - 1); if (e.key === 'ArrowRight') show(cur + 1); });
    }
    function show(i) { cur = (i + list.length) % list.length; var img = $('img', ov); img.src = list[cur].href; var t = $('img', list[cur]); img.alt = t ? t.alt : ''; }
    function close() { ov.classList.remove('open'); d.documentElement.style.overflow = ''; }
    links.forEach(function (a) {
      on(a, 'click', function (e) {
        e.preventDefault();
        if (!ov) build();
        var g = a.closest('.et_pb_gallery, .et_pb_module') || d;
        list = links.filter(function (x) { return g.contains(x); });
        ov.querySelector('.ev-lb-prev').style.display = ov.querySelector('.ev-lb-next').style.display = list.length > 1 ? '' : 'none';
        show(list.indexOf(a)); ov.classList.add('open'); d.documentElement.style.overflow = 'hidden';
      });
    });
  }

  /* ---------- scroll to top, clickable blurbs, hash offset ---------- */
  function misc() {
    var top = $('.et_pb_scroll_top');
    if (top) {
      var tick = false;
      on(w, 'scroll', function () { if (tick) return; tick = true; requestAnimationFrame(function () { var v = w.scrollY > 800; top.classList.toggle('et-visible', v); top.classList.toggle('et-hidden', !v); tick = false; }); }, { passive: true });
      on(top, 'click', function (e) { e.preventDefault(); w.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' }); });
    }
    (w.EV_LINKS || []).forEach(function (o) {
      $$('.' + o['class']).forEach(function (el) {
        el.style.cursor = 'pointer';
        on(el, 'click', function (e) { if (e.target.closest('a')) return; if (o.target === '_blank') w.open(o.url, '_blank', 'noopener'); else location.href = o.url; });
      });
    });
    // phone mask on "contact" inputs: (999) 999-9999
    $$('input.contact').forEach(function (i) {
      on(i, 'input', function () {
        var v = i.value.replace(/\D/g, '').slice(0, 10), out = v;
        if (v.length > 6) out = '(' + v.slice(0, 3) + ') ' + v.slice(3, 6) + '-' + v.slice(6);
        else if (v.length > 3) out = '(' + v.slice(0, 3) + ') ' + v.slice(3);
        else if (v.length) out = '(' + v;
        i.value = out;
      });
    });
    $$('input.form_date').forEach(function (i) { i.type = 'date'; });
  }

  /* ---------- EN / ES (Google Translate, loaded only when asked) ---------- */
  function translate() {
    var pending = null;
    w.googleTranslateElementInit = function () {
      new w.google.translate.TranslateElement({ pageLanguage: 'en', autoDisplay: false }, 'google_translate_element');
      var tries = 0, t = setInterval(function () {
        var sel = $('#google_translate_element select');
        if (sel && sel.options.length > 1) { clearInterval(t); if (pending) pick(pending); }
        if (++tries > 50) clearInterval(t);
      }, 100);
    };
    function pick(lang) {
      var sel = $('#google_translate_element select');
      if (!sel) { pending = lang; return; }
      for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].text.indexOf(lang) > -1) { sel.value = sel.options[i].value; sel.dispatchEvent(new Event('change', { bubbles: true })); return; }
      }
      if (lang === 'English') {   // back to the original page
        var f = $('iframe.goog-te-banner-frame, iframe.skiptranslate');
        d.cookie = 'googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        d.cookie = 'googtrans=; path=/; domain=.' + location.hostname + '; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        if (f || d.documentElement.classList.contains('translated-ltr')) location.reload();
      }
    }
    on(d, 'click', function (e) {
      var a = e.target.closest('.lang-select');
      if (!a) return;
      e.preventDefault();
      var lang = a.getAttribute('data-lang');
      if (!w.google || !w.google.translate) {
        pending = lang;
        if (!$('#ev-gt')) { var s = d.createElement('script'); s.id = 'ev-gt'; s.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit'; d.body.appendChild(s); }
      } else pick(lang);
    });
  }

  /* ---------- forms: Contact Form 7 markup, posted to /api/lead ---------- */
  function forms() {
    var started = Date.now();
    var SKIP = /^(_wpcf7|_wpcf7cf|wpcf7cfpdf_|redirect_nonce|g-recaptcha)/;
    var THANKS = { '236': '/thank-you/', '3991': '/thank-you/', '8978': '/thank-you-survey-form/', '10287': '/thank-you-lp/' };
    $$('form.wpcf7-form').forEach(function (f) {
      if ($('input[name="_gotcha"]', f)) return;
      var trap = d.createElement('input');
      trap.type = 'text'; trap.name = '_gotcha'; trap.tabIndex = -1; trap.autocomplete = 'off'; trap.setAttribute('aria-hidden', 'true');
      trap.style.cssText = 'position:absolute!important;left:-9999px!important;width:1px;height:1px;opacity:0';
      f.appendChild(trap);
      f.setAttribute('action', '/api/lead');
      var wrap = f.closest('.wpcf7'); if (wrap) { wrap.classList.remove('no-js'); wrap.classList.add('js'); }
    });
    function status(form, s) {
      form.classList.remove('init', 'submitting', 'sent', 'failed', 'invalid', 'spam');
      form.classList.add(s); form.setAttribute('data-status', s);
    }
    function output(form, msg, ok) {
      var o = $('.wpcf7-response-output', form);
      if (!o) { o = d.createElement('div'); o.className = 'wpcf7-response-output'; form.appendChild(o); }
      o.textContent = msg; o.setAttribute('aria-hidden', 'false'); o.setAttribute('role', ok ? 'status' : 'alert');
    }
    function tip(el, msg) {
      el.classList.add('wpcf7-not-valid'); el.setAttribute('aria-invalid', 'true');
      var s = d.createElement('span'); s.className = 'wpcf7-not-valid-tip ev-tip'; s.setAttribute('aria-hidden', 'true'); s.textContent = msg;
      el.parentNode.insertBefore(s, el.nextSibling);
    }
    function visible(el) { return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length); }
    function validate(form) {
      $$('.ev-tip', form).forEach(function (t) { t.parentNode.removeChild(t); });
      $$('.wpcf7-not-valid', form).forEach(function (x) { x.classList.remove('wpcf7-not-valid'); x.setAttribute('aria-invalid', 'false'); });
      var first = null;
      $$('[aria-required="true"], .wpcf7-validates-as-required', form).forEach(function (el) {
        if (!visible(el) || el.disabled) return;
        if (!String(el.value || '').trim()) { tip(el, 'Please fill out this field.'); first = first || el; }
      });
      $$('input[type="email"]', form).forEach(function (el) {
        var v = String(el.value || '').trim();
        if (v && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) && !el.classList.contains('wpcf7-not-valid')) { tip(el, 'Please enter a valid email address.'); first = first || el; }
      });
      if (first) { try { first.focus(); } catch (x) {} }
      return !first;
    }
    function collect(form) {
      var data = {};
      Array.prototype.forEach.call(form.elements, function (el) {
        if (!el.name || el.disabled || SKIP.test(el.name) || el.type === 'submit' || el.type === 'button') return;
        if ((el.type === 'checkbox' || el.type === 'radio') && !el.checked) return;
        var key = el.name.replace(/\[\]$/, '');
        if (el.name.slice(-2) === '[]') (data[key] = data[key] || []).push(el.value); else data[key] = el.value;
      });
      return data;
    }
    on(d, 'submit', function (e) {
      var form = e.target && e.target.closest ? e.target.closest('form.wpcf7-form') : null;
      if (!form) return;
      e.preventDefault();
      if (form.classList.contains('submitting')) return;
      if (!validate(form)) { status(form, 'invalid'); output(form, 'One or more fields have an error. Please check and try again.', false); return; }
      var formId = ($('input[name="_wpcf7"]', form) || {}).value || '';
      var unit = ($('input[name="_wpcf7_unit_tag"]', form) || {}).value || '';
      var btn = $('[type="submit"]', form);
      status(form, 'submitting'); if (btn) btn.disabled = true;
      fetch('/api/lead', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ form_id: formId, page: location.href, elapsed_ms: Date.now() - started, fields: collect(form) }) })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok && j.ok, j: j }; }); })
        .then(function (res) {
          if (btn) btn.disabled = false;
          if (!res.ok) { status(form, 'failed'); output(form, (res.j && res.j.error) || 'Sorry, the form could not be sent. Please call (832) 334-2528.', false); return; }
          status(form, 'sent'); output(form, 'Thank you for your message. It has been sent.', true);
          var detail = { contactFormId: formId, unitTag: unit, apiResponse: { status: 'mail_sent' } };
          try { form.dispatchEvent(new CustomEvent('wpcf7mailsent', { bubbles: true, detail: detail })); } catch (x) {}
          (w.dataLayer = w.dataLayer || []).push({ event: 'form_submit_success', form_id: formId });
          try { form.reset(); } catch (x) {}
          if (THANKS[formId]) setTimeout(function () { location.href = THANKS[formId]; }, 300);
        })
        .catch(function () { if (btn) btn.disabled = false; status(form, 'failed'); output(form, 'Sorry, the form could not be sent. Please call (832) 334-2528.', false); });
    });
  }

  /* ---------- tracking: run the original tags on first interaction ---------- */
  function delayed() {
    var done = false, evs = ['pointerdown', 'keydown', 'touchstart', 'scroll', 'mousemove', 'wheel'];
    function run() {
      if (done) return; done = true;
      evs.forEach(function (ev) { w.removeEventListener(ev, run, { passive: true }); });
      $$('script[type="text/ev-delay"]').forEach(function (old) {
        var s = d.createElement('script');
        for (var i = 0; i < old.attributes.length; i++) { var at = old.attributes[i]; if (at.name !== 'type') s.setAttribute(at.name, at.value); }
        if (old.getAttribute('data-src')) { s.src = old.getAttribute('data-src'); s.async = true; }
        else s.text = old.text;
        old.parentNode.replaceChild(s, old);
      });
    }
    evs.forEach(function (ev) { w.addEventListener(ev, run, { passive: true }); });
  }

  function init() {
    [mobileMenus, popup, tabs, toggles, carousels, sliders, beforeAfter, lightbox, misc, translate, forms, delayed].forEach(function (f) {
      try { f(); } catch (e) { if (w.console) console.error('site.js', f.name, e); }
    });
  }
  if (d.readyState === 'loading') on(d, 'DOMContentLoaded', init); else init();
})();
