/* Teacher profile page: bio, courses, rivals, reviews (loaded from the API). */
const BL = [['👥', 'سبک کلاس', 'cls'], ['📝', 'روش تدریس', 'way'], ['🎯', 'سطح مناسب', 'lvl'], ['❓', 'حل تست و تمرین', 'tst'], ['🎓', 'مدرک و تحصیلات', 'edu'], ['⏳', 'سابقه تدریس', 'exp'], ['💡', 'نکته', 'note']];
const BACK = '<a class="back" href="#/">‹ بازگشت به اساتید</a>';
const PROF_SKELETON = '<div class="cover"><div class="ph"><div class="av"></div><div style="flex:1"><div class="skl w60"></div><div class="skl w40"></div></div></div></div><div class="sec"><div class="skl w80"></div><div class="skl w60"></div><div class="skl w40"></div></div>';
let profSeq = 0;

async function loadProfile(id) {
    const seq = ++profSeq;
    PD[id] = { loading: true }; renderProfile(id);
    const [pr, rr, vr] = await Promise.allSettled([API.teacher(id), API.reviews(id, 1), API.rivals(id)]);
    if (seq !== profSeq) return;
    if (pr.status === 'rejected') {
        const e = pr.reason;
        if (e && e.code === 'TEACHER_NOT_FOUND') { toast('استاد پیدا نشد'); location.hash = '#/'; return }
        PD[id] = { error: (e && e.message) || 'خطا در دریافت اطلاعات؛ دوباره تلاش کن.' }; renderProfile(id); return;
    }
    const t = mapProfile(pr.value);
    PD[id] = {
        t, courses: mapCourses(pr.value.courses),
        reviews: rr.status === 'fulfilled' ? { items: rr.value.items.map(mapReview), total: rr.value.total, page: rr.value.page } : null,
        reviewsErr: rr.status === 'rejected' ? rr.reason.message : '',
        rivals: vr.status === 'fulfilled' ? vr.value.items.map(c => reg(mapCard(c))) : null
    };
    if (cur === id) document.title = t.n + ' | باف';
    renderProfile(id);
}
async function moreReviews(id) {
    const d = PD[id]; if (!d || !d.reviews || d.busy) return;
    d.busy = true; renderProfile(id);
    try {
        const rv = await API.reviews(id, d.reviews.page + 1);
        d.reviews.items = d.reviews.items.concat(rv.items.map(mapReview)); d.reviews.page = rv.page; d.reviews.total = rv.total;
    } catch (e) { toast(e.message) }
    d.busy = false; if (cur === id) renderProfile(id);
}

function bioHtml(t) {
    const b = t.b; if (!b) return '<p>معرفی این استاد به‌زودی اضافه می‌شود.</p>';
    const R = r => b[r[2]] ? `<div class="br"><b>${r[0]} ${r[1]}</b><p>${esc(b[r[2]])}</p></div>` : '';
    return `<div class="bio">${R(BL[0])}<div class="full">${BL.slice(1).map(R).join('')}</div></div>`
}
function coursesHtml(d) { const c = d.courses || []; return `<div class="sec"><h3>دوره‌های استاد</h3>${c.length ? c.map(x => `<div class="cr"><div class="sh2"><b>${esc(x[0])}</b><button class="more-btn" onclick="toast('صفحه‌ی دوره به‌زودی')">مشاهده ←</button></div><p>${esc(x[1])}</p></div>`).join('') : '<p>دوره‌های این استاد به‌زودی اضافه می‌شود.</p>'}</div>` }
function rivalsHtml(d) {
    let body;
    if (!d.rivals) body = '<p class="mut">خطا در دریافت اساتید رقیب.</p>';
    else if (!d.rivals.length) body = '<p class="mut">استاد رقیبی پیدا نشد.</p>';
    else body = `<div class="sc">${d.rivals.map(x => `<div class="mn" onclick="location.hash='#/t/${x.id}'"><i>${av(x)}</i>${esc(x.n)}<small>${x.c ? '⭐ ' + fa(x.r) : esc(x.s)}</small><u class="${sel.includes(x.id) ? 'on' : ''}" onclick="event.stopPropagation();tg(${x.id})">${sel.includes(x.id) ? '✓' : '+'}</u></div>`).join('')}</div><div class="mut">برای مقایسه روی + بزن.</div>`;
    return `<div class="sec"><h3>اساتید رقیب</h3>${body}</div>`;
}
function reviewsHtml(d, t) {
    const rv = d.reviews; let list;
    if (!rv) list = `<p class="mut">${esc(d.reviewsErr || 'خطا در دریافت نظرها.')}</p>`;
    else list = rv.items.map(r => `<div class="rv"><b>${esc(r.w)}</b> <s>${stars(r.s)}</s><p>${esc(r.t)}</p></div>`).join('') + (rv.items.length < rv.total ? `<button class="b2" style="margin-top:10px" onclick="moreReviews(${t.id})">${d.busy ? 'در حال بارگذاری...' : 'نمایش نظرهای بیشتر'}</button>` : '');
    return `<div class="sec"><div class="sh2"><h3>نظرات دانش‌آموزان</h3></div><div class="sum"><big>${t.c ? fa(t.r) : '—'}</big><div><s style="color:#f0a800;text-decoration:none">${'★'.repeat(Math.round(t.r || 0))}</s><div class="mut">${t.c ? 'بر اساس ' + fa(t.c) + ' نظر' : 'هنوز نظری ثبت نشده؛ اولین نفر باش ✍️'}</div></div></div>${list}</div>`;
}

function renderProfile(id) {
    const d = PD[id], el = $('profile');
    if (!d || d.loading) { el.innerHTML = BACK + PROF_SKELETON; return }
    if (d.error) { el.innerHTML = BACK + `<div class="empty" style="display:block">${esc(d.error)}<br><button class="b2" style="margin-top:8px" onclick="loadProfile(${id})">تلاش دوباره</button></div>`; return }
    const t = d.t;
    el.innerHTML = `${BACK}
 <div class="cover"><div class="ph"><div class="av">${av(t)}</div><div><h1>استاد ${esc(t.n)}</h1><div class="mut">مدرس ${esc(t.s)} کنکور</div><div class="tg" style="margin-top:6px">${[t.st, t.lv].filter(Boolean).map(x => `<span>${esc(x)}</span>`).join('')}</div></div></div>
 <div class="stats">${t.c ? `<span>⭐ <b>${fa(t.r)}</b></span><span>💬 <b>${fa(t.c)}</b> نظر</span><span>👍 <b>${pv(t.rec, '٪')}</b> پیشنهاد</span>` : '<span>هنوز نظری ثبت نشده</span>'}</div></div>
 <div class="act"><button class="b1" onclick="openReview(${id})">✍ ثبت نظر</button><button class="b2 ${sel.includes(id) ? 'on' : ''}" onclick="tg(${id})">${sel.includes(id) ? '✓ در مقایسه' : '+ مقایسه'}</button></div>
 <div class="sec ${OB[t.id] ? 'open' : ''}"><div class="sh2"><h3>درباره‌ی استاد</h3>${t.b ? `<button class="more-btn" onclick="OB[${t.id}]=!OB[${t.id}];renderProfile(${t.id})">${OB[t.id] ? 'کمتر' : 'بیشتر ...'}</button>` : ''}</div>${bioHtml(t)}</div>${coursesHtml(d)}${rivalsHtml(d)}${reviewsHtml(d, t)}`;
}