// Receives the site's forms (posted by /assets/forms.js) and emails them through FormSubmit.
// Consultation (form 236), contact (3991) and survey (8978) all go to the office inbox.
const TO = 'info@everestsidingandwindows.com';
const FORM_NAMES = { '236': 'Free consultation', '3991': 'Contact page', '8978': 'Customer satisfaction survey' };

const LABELS = {
  fullname: 'Name', emailaddress: 'Email', phonenumber: 'Phone', address: 'Address', city: 'City', zipcode: 'ZIP',
  services: 'Services', howcanwehelp: 'How can we help', hear: 'Heard about us from', promotionalemails: 'Promotional emails',
};

module.exports = async (req, res) => {
  if (req.method !== 'POST') { res.status(405).json({ ok: false }); return; }
  let b = req.body || {};
  if (typeof b === 'string') { try { b = JSON.parse(b); } catch (e) { b = {}; } }
  const f = (b.fields && typeof b.fields === 'object') ? b.fields : {};
  const formId = String(b.form_id || '');
  // hidden trap field and too-fast submits: flag instead of dropping (autofill can trip the trap)
  const maybeSpam = !!f._gotcha || (Number(b.elapsed_ms) > 0 && Number(b.elapsed_ms) < 2500);
  delete f._gotcha;

  const name = String(f.fullname || f.customername || '').trim();
  if (formId !== '8978' && (!name || !(f.emailaddress || f.phonenumber))) {
    res.status(400).json({ ok: false, error: 'Please fill in your name and an email or phone number.' }); return;
  }

  const lead = {};
  for (const [k, v] of Object.entries(f)) {
    const val = Array.isArray(v) ? v.join(', ') : String(v);
    if (val.trim() === '') continue;
    lead[LABELS[k] || k] = val.slice(0, 5000);
  }
  lead.Form = FORM_NAMES[formId] || ('Form ' + formId);
  lead.Page = String(b.page || '').slice(0, 500);
  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.headers['x-real-ip'] || '';
  lead['IP address'] = ip;
  lead['IP location'] = [req.headers['x-vercel-ip-city'], req.headers['x-vercel-ip-country-region'], req.headers['x-vercel-ip-country']]
    .filter(Boolean).map(decodeURIComponent).join(', ');
  lead.Browser = req.headers['user-agent'] || '';
  lead._subject = `${maybeSpam ? '[Possible spam] ' : ''}${FORM_NAMES[formId] || 'Website form'}: ${name || 'no name'}${f.city ? ' (' + f.city + ')' : ''}`;
  if (f.emailaddress) lead._replyto = String(f.emailaddress);

  try {
    await require('./_send')(TO, lead);
    res.status(200).json({ ok: true });
  } catch (e) {
    console.error('lead error', e.message);
    res.status(502).json({ ok: false, error: 'Sorry, the form could not be sent. Please call (832) 334-2528.' });
  }
};
