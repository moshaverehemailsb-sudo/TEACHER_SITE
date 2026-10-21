/* App entry: router, theme toggle, toast, init. */
function route() {
    const m = location.hash.match(/#\/t\/(\d+)/); cur = m ? +m[1] : null;
    $('home').style.display = cur ? 'none' : 'block'; $('profile').style.display = cur ? 'block' : 'none';
    document.title = cur ? 'استاد | باف' : 'باف | پیدا کردن استاد';
    if (cur) loadProfile(cur);
    scrollTo(0, 0);
}
addEventListener('hashchange', route);
function theme() { const d = document.documentElement; d.dataset.theme = d.dataset.theme === 'dark' ? 'light' : 'dark' }
let tt; function toast(m) { const e = $('toast'); e.textContent = m; e.style.display = 'block'; clearTimeout(tt); tt = setTimeout(() => e.style.display = 'none', 2600) }
addEventListener('keydown', e => { if (e.key === 'Escape') { $('ov').classList.remove('on'); closeModal() } });

function init() {
    ['chips', 'more', 'chips2'].forEach(id => $(id).addEventListener('click', onChipClick));
    $('modal').addEventListener('click', onModalClick);
    $('modal').addEventListener('input', onModalInput);
    $('modal').addEventListener('keydown', onModalKey);
    onAuthChange();
    renderChips(); renderCards(); route();
    loadList(true);
    loadSubjects().then(renderChips).catch(() => toast('خطا در دریافت فهرست درس‌ها'));
    loadPopular().then(renderCarousel).catch(() => { });
    if (loggedIn()) API.me().catch(() => { });
}
init();