(() => {
const d = document, $ = (s, e = d) => e.querySelector(s), $$ = (s, e = d) => [...e.querySelectorAll(s)];
d.documentElement.classList.add('js');
const f = {status: 'all', tech: 'all', cls: 'all', page: 'all', el: '', q: ''};
const tab = name => {
  if (!$(`section[data-tab="${name}"]`)) name = 'overview';
  $$('section[data-tab]').forEach(s => s.classList.toggle('active', s.dataset.tab === name));
  $$('.tabs a').forEach(a => a.setAttribute('aria-selected', a.dataset.tab === name));
  if (location.hash.slice(1) !== name) history.replaceState(null, '', '#' + name);
};
const reset = () => { Object.assign(f, {status: 'all', tech: 'all', cls: 'all', page: 'all', el: '', q: ''});
  const q = $('#q'); if (q) q.value = ''; };
const apply = () => {
  const rows = $$('tbody.t'); let n = 0;
  rows.forEach(b => {
    const ok = (f.status === 'all' || b.dataset.status === f.status)
      && (f.tech === 'all' || b.dataset.tech === f.tech) && (f.cls === 'all' || b.dataset.cls === f.cls)
      && (f.page === 'all' || b.dataset.page === f.page)
      && (!f.el || b.dataset.els.split(' ').includes(f.el)) && (!f.q || b.dataset.q.includes(f.q));
    b.hidden = !ok; if (ok) n++;
  });
  $('#count').textContent = `Showing ${n} of ${rows.length}`;
  $$('.chips[data-filter] button').forEach(x => x.classList.toggle('on', f[x.parentElement.dataset.filter] === x.dataset.v));
  const ae = $('#active-el'); ae.hidden = !f.el; $('span', ae).textContent = f.el;
};
const open = (b, yes) => {
  b.classList.toggle('open', yes); $('tr.detail', b).hidden = !yes;
  $('.toggle', b).setAttribute('aria-expanded', yes);
  const slot = $('.shot-slot', b), img = slot && $('#shot-' + slot.dataset.shot);
  if (yes && img && !slot.firstChild) slot.appendChild(img.cloneNode());
};
const showTests = () => { tab('tests'); apply(); };
d.addEventListener('click', e => {
  const t = e.target, a = t.closest('a,button,td[data-el],th[data-sort],img.shot,tr.main');
  if (!a) return;
  if (a.matches('.tabs a')) { e.preventDefault(); tab(a.dataset.tab); return; }
  if (a.matches('img.shot')) { a.classList.toggle('big'); return; }
  if (a.matches('[data-open]')) { e.preventDefault(); reset(); showTests();
    const b = $(`tbody.t[data-id="${a.dataset.open}"]`); open(b, true); b.scrollIntoView({block: 'center'}); return; }
  if (a.matches('[data-el]')) { e.preventDefault(); reset(); f.el = a.dataset.el;
    if (a.dataset.tech) f.tech = a.dataset.tech; showTests(); return; }
  if (a.matches('[data-go]')) { e.preventDefault(); if (a.dataset.status) { reset(); f.status = a.dataset.status; }
    if (a.dataset.go === 'tests') showTests(); else tab(a.dataset.go);
    if (a.getAttribute('href')) $(a.getAttribute('href')).scrollIntoView(); return; }
  if (a.matches('.chips[data-filter] button')) { f[a.parentElement.dataset.filter] = a.dataset.v; apply(); return; }
  if (a.matches('#active-el button')) { f.el = ''; apply(); return; }
  if (a.matches('#reset')) { reset(); apply(); return; }
  if (a.matches('#expand')) { const all = $$('tbody.t:not([hidden])'), yes = all.some(b => !b.classList.contains('open'));
    all.forEach(b => open(b, yes)); a.textContent = yes ? 'Collapse all' : 'Expand all'; return; }
  if (a.matches('.chips[data-cov] button,.chips[data-kind] button')) {
    $$('button', a.parentElement).forEach(x => x.classList.toggle('on', x === a));
    if (a.parentElement.matches('[data-cov]'))
      $$('tr.cov').forEach(r => r.hidden = a.dataset.v !== 'all' && r.dataset.state !== a.dataset.v);
    else filterEls(); return; }
  if (a.matches('th[data-sort]')) { sort(a); return; }
  if (a.matches('tr.main,.toggle')) { const b = a.closest('tbody.t'); open(b, !b.classList.contains('open')); }
});
d.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('td[data-el]')) e.target.click(); });
const q = $('#q'); q.addEventListener('input', () => { f.q = q.value.trim().toLowerCase(); apply(); });
const filterEls = () => {
  const k = ($('.chips[data-kind] button.on') || {}).dataset?.v || 'all', s = $('#eq').value.trim().toLowerCase();
  $$('tr.el').forEach(r => r.hidden = (k !== 'all' && r.dataset.kind !== k) || (s && !r.dataset.q.includes(s)));
};
$('#eq').addEventListener('input', filterEls);
const sort = th => {
  const key = th.dataset.sort, asc = th.getAttribute('aria-sort') !== 'ascending';
  $$('th[data-sort]').forEach(x => x.removeAttribute('aria-sort'));
  th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
  const num = key === 'priority' || key === 'time', table = th.closest('table');
  $$('tbody.t', table).sort((x, y) => {
    const a = x.dataset[key], b = y.dataset[key];
    const c = num ? parseFloat(a) - parseFloat(b) : a.localeCompare(b);
    return asc ? c : -c;
  }).forEach(b => table.appendChild(b));
};
window.addEventListener('hashchange', () => tab(location.hash.slice(1)));
tab(location.hash.slice(1) || 'overview'); apply();
})();
