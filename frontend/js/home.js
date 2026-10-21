/* Home page: subject filters, sorting and search (all done by the server). */
const SORTS = [['pop', 'محبوب‌ترین‌ها'], ['cnt', 'بیشترین نظرات ثبت‌شده'], ['zero', 'تدریس از صفر']];
let dt; function flt() { clearTimeout(dt); dt = setTimeout(() => loadList(true), 150) }

function pick(k, l) { subj = subj === k && k !== 'همه' ? 'همه' : k; subjL = subj === 'همه' ? 'همه' : l; openMore = false; renderChips(); loadList(true) }
function onChipClick(e) {
    const b = e.target.closest('button'); if (!b) return;
    if (b.dataset.pick !== undefined) return pick(b.dataset.pick, b.dataset.label);
    if (b.dataset.more) {
        openMore = !openMore;
        if (openMore && !G.length) loadSubjects().then(renderChips).catch(() => toast('خطا در دریافت فهرست درس‌ها'));
        return renderChips();
    }
    if (b.dataset.s2) { s2 = s2 === b.dataset.s2 ? '' : b.dataset.s2; renderChips(); loadList(true) }
}
function renderChips() {
    $('chips').innerHTML = TOP.map(s => `<button class="chip ${s === subj ? 'on' : ''}" data-pick="${esc(s)}" data-label="${esc(s)}">${esc(s)}</button>`).join('') + `<button class="chip ${(!TOP.includes(subj) || openMore) ? 'on' : ''}" data-more="1">${!TOP.includes(subj) ? esc(subjL) + ' ' : ''}⋯</button>`;
    $('more').className = 'more' + (openMore ? ' on' : '');
    $('more').innerHTML = G.map(([h, a]) => `<h4>${esc(h)}</h4><div class="wrap">${a.map(([l, k]) => `<button class="chip ${k === subj ? 'on' : ''}" data-pick="${esc(k)}" data-label="${esc(l)}">${esc(l)}</button>`).join('')}</div>`).join('');
    $('chips2').innerHTML = SORTS.map(([k, l]) => `<button class="chip ${s2 === k ? 'on' : ''}" data-s2="${k}">${l}</button>`).join('');
}

function listParams(page) {
    return { subject: subj === 'همه' ? '' : subj, q: $('q').value.trim(), sort: s2 === 'pop' ? 'popular' : s2 === 'cnt' ? 'reviews' : 'default', scratch: s2 === 'zero' ? 1 : '', page, pageSize: PG };
}
async function loadList(reset) {
    if (listCtrl) listCtrl.abort();
    const ctrl = listCtrl = new AbortController();
    const page = reset ? 1 : L.page + 1;
    if (reset) L = { items: [], total: 0, page: 0, loading: true, error: '' };
    else { L.loading = true; L.error = '' }
    renderCards();
    try {
        const d = await API.teachers(listParams(page), ctrl.signal);
        if (ctrl !== listCtrl) return;
        const items = d.items.map(c => reg(mapCard(c)));
        L = { items: reset ? items : L.items.concat(items), total: d.total, page: d.page, loading: false, error: '' };
    } catch (e) {
        if (e instanceof ApiAbort || ctrl !== listCtrl) return;
        L.loading = false; L.error = e.message || 'خطا در دریافت اطلاعات؛ دوباره تلاش کن.';
    }
    renderCards();
}

const cardHtml = t => `<article class="card"><div class="av">${av(t)}</div><div class="info"><h3>${esc(t.n)}</h3><div class="mut">استاد ${esc(t.s)} کنکور</div><div class="rt">${rt(t)}</div><div class="tg">${t.tags.map(x => `<span>${esc(x)}</span>`).join('')}</div><div class="row"><a class="b1" href="#/t/${t.id}">مشاهده پروفایل</a><button class="b2 ${sel.includes(t.id) ? 'on' : ''}${sel.length && !sel.includes(t.id) && g(sel[0]).s !== t.s ? ' dis' : ''}" onclick="tg(${t.id})">${sel.includes(t.id) ? '✓ انتخاب شد' : '+ مقایسه'}</button></div></div></article>`;
const skelHtml = n => Array.from({ length: n }, () => '<article class="card sk"><div class="av"></div><div class="info"><div class="skl w60"></div><div class="skl w40"></div><div class="skl w80"></div></div></article>').join('');

function renderCards() {
    const a = L.items, rest = L.total - a.length;
    $('cnt').textContent = L.page ? fa(L.total) + ' استاد' : '';
    $('grid').innerHTML = L.loading && !a.length ? skelHtml(6) : a.map(cardHtml).join('');
    $('empty').style.display = !L.loading && !L.error && L.page && !a.length ? 'block' : 'none';
    $('err').style.display = L.error ? 'block' : 'none'; $('errmsg').textContent = L.error;
    const lm = $('loadmore');
    lm.style.display = (L.loading && a.length) || (!L.loading && !L.error && rest > 0) ? 'block' : 'none';
    lm.disabled = L.loading;
    lm.textContent = L.loading ? 'در حال بارگذاری...' : 'نمایش بیشتر (' + fa(rest) + ' استاد دیگر)';
}