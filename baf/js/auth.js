/* Phone login (SMS code) and the review form. */
const GRADES = ['دانش\u200cآموز پایه دهم', 'دانش\u200cآموز پایه یازدهم', 'دانش\u200cآموز پایه دوازدهم', 'فارغ\u200cالتحصیل'];
let pending = null, rf = null, cdTimer = null, curPhone = '';

function onAuthChange() { const b = $('loginBtn'); if (b) b.textContent = loggedIn() ? 'خروج' : 'ورود' }
function authClick() { if (loggedIn()) { setToken(null); onAuthChange(); toast('از حساب خارج شدی') } else openLogin() }
function reviewFromNav() { if (cur) openReview(cur); else toast('برای ثبت نظر، اول صفحه‌ی استاد را باز کن') }

function stopCd() { clearInterval(cdTimer); cdTimer = null }
function openModal(html) { stopCd(); $('modal').innerHTML = html; $('ov2').classList.add('on'); const f = $('modal').querySelector('input,textarea,select'); if (f) f.focus() }
function closeModal() { stopCd(); pending = null; rf = null; $('ov2').classList.remove('on') }
const lerr = m => { const e = $('lerr'); if (e) e.textContent = m };
const setBusy = (id, b) => { const x = $(id); if (x) x.disabled = b };

/* ---- login ---- */
function openLogin(phone = '') {
    openModal(`<h3>ورود با شماره موبایل</h3><p class="mut">کد تأیید به شماره‌ات پیامک می‌شود.</p>
 <label class="fl">شماره موبایل<input id="lphone" type="tel" inputmode="numeric" autocomplete="tel" dir="ltr" placeholder="09121234567" value="${esc(phone)}"></label>
 <div class="ferr" id="lerr" role="alert"></div>
 <button class="b1 wide" id="lgo" onclick="sendCode()">ارسال کد</button>
 <button class="b2 wide" onclick="closeModal()">بستن</button>`);
}
async function sendCode() {
    const phone = $('lphone').value.trim();
    if (!phone) return lerr('شماره موبایل را وارد کن.');
    setBusy('lgo', true); lerr('');
    try { const d = await API.requestCode(phone); curPhone = phone; codeStep(d.retryAfter || 60) }
    catch (e) { lerr(e.message); setBusy('lgo', false) }
}
function codeStep(sec) {
    openModal(`<h3>کد تأیید</h3><p class="mut">کد ۶ رقمی ارسال‌شده به ${esc(curPhone)} را وارد کن.</p>
 <label class="fl">کد تأیید<input id="lcode" inputmode="numeric" maxlength="6" autocomplete="one-time-code" dir="ltr"></label>
 <div class="ferr" id="lerr" role="alert"></div>
 <button class="b1 wide" id="lgo" onclick="verify()">ورود</button>
 <button class="b2 wide" id="lresend" onclick="resend()" disabled>ارسال دوباره</button>
 <button class="more-btn" onclick="openLogin(curPhone)">تغییر شماره</button>`);
    startCd(sec);
}
function startCd(sec) {
    stopCd(); let n = sec;
    const tick = () => { const b = $('lresend'); if (!b) { stopCd(); return } b.disabled = n > 0; b.textContent = n > 0 ? 'ارسال دوباره (' + fa(n) + ')' : 'ارسال دوباره'; if (n-- <= 0) stopCd() };
    tick(); cdTimer = setInterval(tick, 1000);
}
async function resend() {
    setBusy('lresend', true); lerr('');
    try { const d = await API.requestCode(curPhone); startCd(d.retryAfter || 60) }
    catch (e) { lerr(e.message); startCd(5) }
}
async function verify() {
    const code = $('lcode').value.trim();
    if (!code) return lerr('کد را وارد کن.');
    setBusy('lgo', true); lerr('');
    try {
        const d = await API.verifyCode(curPhone, code);
        setToken(d.accessToken); onAuthChange();
        const p = pending; closeModal(); toast('وارد شدی');
        if (p && p.type === 'review') openReview(p.id);
    } catch (e) { lerr(e.message); setBusy('lgo', false) }
}

/* ---- review form ---- */
function openReview(id) {
    const t = g(id); if (!t) return;
    if (!loggedIn()) { pending = { type: 'review', id }; return openLogin() }
    rf = { id, stars: 0, rec: null };
    openModal(`<h3>ثبت نظر درباره‌ی استاد ${esc(t.n)}</h3>
 <label class="fl">وضعیت تحصیلی<select id="rgrade">${GRADES.map(x => `<option value="${esc(x)}">${esc(x)}</option>`).join('')}</select></label>
 <div class="fl">امتیاز<div class="starin" id="rstars" role="radiogroup" aria-label="امتیاز">${[1, 2, 3, 4, 5].map(n => `<button type="button" class="st" data-n="${n}" role="radio" aria-checked="false" aria-label="${fa(n)} ستاره">★</button>`).join('')}</div></div>
 <div class="fl">این استاد را توصیه می‌کنی؟<div class="yn"><button type="button" class="b2" data-rec="1">بله</button><button type="button" class="b2" data-rec="0">خیر</button></div></div>
 <label class="fl">متن نظر<textarea id="rbody" maxlength="1000" rows="5" placeholder="تجربه‌ات را بنویس..."></textarea><span class="mut" id="rcount">${fa(0)} / ${fa(1000)}</span></label>
 <div class="ferr" id="rerr" role="alert"></div>
 <button class="b1 wide" id="rgo" onclick="submitReview()">ثبت نظر</button>
 <button class="b2 wide" onclick="closeModal()">بستن</button>`);
}
function paintStars() { document.querySelectorAll('#rstars .st').forEach(b => { b.classList.toggle('on', +b.dataset.n <= rf.stars); b.setAttribute('aria-checked', String(+b.dataset.n === rf.stars)) }) }
function paintRec() { document.querySelectorAll('#modal [data-rec]').forEach(b => b.classList.toggle('on', (b.dataset.rec === '1') === rf.rec)) }
function onModalClick(e) {
    if (!rf) return;
    const s = e.target.closest('.st'); if (s) { rf.stars = +s.dataset.n; paintStars(); return }
    const r = e.target.closest('[data-rec]'); if (r) { rf.rec = r.dataset.rec === '1'; paintRec() }
}
function onModalInput(e) { if (e.target.id === 'rbody') { const c = $('rcount'); if (c) c.textContent = fa(e.target.value.length) + ' / ' + fa(1000) } }
function onModalKey(e) { if (e.key === 'Enter' && e.target.tagName === 'INPUT') { const b = $('lgo'); if (b && !b.disabled) { e.preventDefault(); b.click() } } }

async function submitReview() {
    const fail = m => { const x = $('rerr'); if (x) x.textContent = m };
    const body = $('rbody').value.trim(), id = rf.id;
    fail('');
    if (!rf.stars) return fail('امتیاز را انتخاب کن.');
    if (rf.rec === null) return fail('مشخص کن این استاد را توصیه می‌کنی یا نه.');
    if (!body) return fail('متن نظر را بنویس.');
    setBusy('rgo', true);
    try {
        const d = await API.postReview(id, { reviewerLabel: $('rgrade').value, stars: rf.stars, recommends: rf.rec, body });
        $('modal').innerHTML = `<h3>ممنون از نظرت</h3><p class="mut">${esc(d.message || 'نظر شما پس از بررسی نمایش داده می‌شود.')}</p><button class="b1 wide" onclick="closeModal()">بستن</button>`;
    } catch (e) {
        if (e.status === 401) { pending = { type: 'review', id }; toast('نشست تمام شد؛ دوباره وارد شو'); return openLogin() }
        fail(e.message); setBusy('rgo', false);
    }
}