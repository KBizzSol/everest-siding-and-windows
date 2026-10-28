// Shared helper: email a lead through FormSubmit (same setup as kbizz-website).
// Files starting with "_" are not public routes.
module.exports = async function sendLead(to, lead) {
  const r = await fetch('https://formsubmit.co/ajax/' + to, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Origin: 'https://everestsidingandwindows.com',
      Referer: 'https://everestsidingandwindows.com/contact/',
    },
    body: JSON.stringify({ _template: 'table', _captcha: 'false', ...lead }),
  });
  const txt = await r.text().catch(() => '');
  let j = {};
  try { j = JSON.parse(txt); } catch (e) {}
  if (!r.ok || String(j.success) === 'false') throw new Error(`formsubmit ${r.status}: ${(j.message || txt).slice(0, 300)}`);
  return true;
};
