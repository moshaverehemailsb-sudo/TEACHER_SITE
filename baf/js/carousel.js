/* Rotating popular-comparisons carousel (data from the API). */
const stage = $('stage');
function renderCarousel() {
    stage.querySelectorAll('.pc').forEach(e => e.remove());
    $('popsec').style.display = P.length ? '' : 'none';
    if (!P.length) { clearInterval(timer); return }
    stage.insertAdjacentHTML('beforeend', P.map((p, i) => { const a = g(p[0]), b = g(p[1]); return `<article class="pc" role="button" tabindex="0" onkeydown="if(event.key==='Enter')carClick(${i})" onclick="carClick(${i})"><span class="pl">${esc(p[2])}</span><div class="pp"><div class="pe"><i style="box-shadow:0 0 0 2px ${COL[0]}">${av(a)}</i><b style="color:${COL[0]}">${esc(a.n)}</b><small>${esc(a.s)}</small></div><span class="vs">VS</span><div class="pe"><i style="box-shadow:0 0 0 2px ${COL[1]}">${av(b)}</i><b style="color:${COL[1]}">${esc(b.n)}</b><small>${esc(b.s)}</small></div></div><div class="pr">${mets(a, b).map(m => `<div class="mr"><span style="color:${COL[0]}">${m.v[0]}</span><div class="ms">${sring(m.f[0], m.f[1], 13)}</div><span style="color:${COL[1]}">${m.v[1]}</span><small>${m.l}</small></div>`).join('')}</div></article>` }).join(''));
    ci = 0; lay(); play();
}
function lay() {
    const n = P.length, big = stage.clientWidth >= 800, step = big ? 300 : Math.min(185, stage.clientWidth * .33);
    [...stage.querySelectorAll('.pc')].forEach((c, i) => {
        let o = i - ci; if (o > n / 2) o -= n; if (o < -n / 2) o += n; const a = Math.abs(o);
        c.style.transform = `translateX(calc(-50% + ${-o * step}px)) translateZ(${-a * 100}px) rotateY(${o * (big ? 22 : 28)}deg) scale(${big ? (a ? .78 - (a - 1) * .1 : 1.22) : 1 - a * .07})`;
        c.style.opacity = a > 2 ? 0 : 1 - a * .3; c.style.zIndex = 10 - a; c.style.pointerEvents = a > 2 ? 'none' : 'auto'; c.classList.toggle('mid', o === 0)
    })
}
function go(d) { if (!P.length) return; ci = (ci + d + P.length) % P.length; lay() }
function carClick(i) { if (i === ci) showCmp(P[i]); else { ci = i; lay() } }
function play() { clearInterval(timer); if (!P.length || matchMedia('(prefers-reduced-motion:reduce)').matches) return; timer = setInterval(() => go(1), 3800) }
let x0 = null; stage.addEventListener('pointerdown', e => { x0 = e.clientX; clearInterval(timer) });
stage.addEventListener('pointerup', e => { if (x0 !== null && Math.abs(e.clientX - x0) > 40) go(e.clientX < x0 ? -1 : 1); x0 = null; play() });
stage.addEventListener('mouseenter', () => clearInterval(timer)); stage.addEventListener('mouseleave', play);
addEventListener('resize', lay);