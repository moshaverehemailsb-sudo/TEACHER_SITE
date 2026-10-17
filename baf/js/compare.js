/* Teacher comparison: selection rules and the comparison dialog (data from the API). */
function tg(id) { if (sel.includes(id)) sel = sel.filter(x => x != id); else { if (sel.length && g(sel[0]).s !== g(id).s) return toast('فقط اساتید یک درس رو می‌شه مقایسه کرد'); if (sel.length >= 2) return toast('حداکثر ۲ استاد'); sel.push(id) } refresh() }
function refresh() { renderCards(); if (cur) renderProfile(cur); $('bar').classList.toggle('on', sel.length > 0); $('bt').textContent = fa(sel.length) + ' استاد انتخاب شده'; $('bn').textContent = sel.map(i => g(i).n).join('، ') }

let cmpSeq = 0;
async function showCmp(ids) {
    const a = ids[0], b = ids[1];
    if (!a || !b || a === b) return toast('حداقل ۲ استاد انتخاب کن');
    const ta = g(a), tb = g(b);
    if (ta && tb && ta.s !== tb.s) return toast('فقط اساتید یک درس رو می‌شه مقایسه کرد');
    const seq = ++cmpSeq;
    $('cmp').innerHTML = '<p class="mut" style="text-align:center;padding:24px 0">در حال بارگذاری...</p>';
    $('ov').classList.add('on');
    try {
        const d = await API.compare(a, b);
        if (seq !== cmpSeq) return;
        renderCompare(d);
    } catch (e) {
        if (seq !== cmpSeq) return;
        $('ov').classList.remove('on'); toast(e.message);
    }
}
function renderCompare(d) {
    const c = [d.a, d.b].map(x => ({ ...reg(mapCard(x)), edu: x.education, exp: x.experience }));
    const [a, b] = c, LB = ['پیشنهاد بچه‌ها', 'امتیاز از ۵', 'تعداد نظر'];
    const rows = [['سبک تدریس', t => t.st || '—'], ['سطح مناسب', t => t.lv || '—'], ['مدرک', t => t.edu ? t.edu.split('\n')[0] : '—'], ['سابقه', t => t.exp || '—']];
    $('cmp').innerHTML = `<div class="lgs">${c.map((t, i) => `<div class="lg"><span class="tav" style="border:3px solid ${COL[i]}">${av(t)}</span><b style="color:${COL[i]}">${esc(t.n)}</b></div>`).join('')}</div>
 <div class="rings">${mets(a, b).map((m, i) => `<div class="rc"><span class="sv" style="color:${COL[0]}">${m.v[0]}</span><div class="rsvg">${sring(m.f[0], m.f[1], 11)}</div><span class="sv" style="color:${COL[1]}">${m.v[1]}</span><b class="rl">${LB[i]}</b></div>`).join('')}</div>
 <table><thead><tr><th></th>${c.map((t, i) => `<th><span style="color:${COL[i]}">●</span> ${esc(t.n)}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr><td><b>${r[0]}</b></td>${c.map(t => `<td>${esc(r[1](t))}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}