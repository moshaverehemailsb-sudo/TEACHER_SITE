/* App entry: router, theme toggle, toast, init. */
/* router, theme, toast */
function route(){const m=location.hash.match(/#\/t\/(\d+)/);cur=m?+m[1]:null;if(cur&&!g(cur)){location.hash='#/';return}document.title=cur?g(cur).n+' | باف':'باف | پیدا کردن استاد';$('home').style.display=cur?'none':'block';$('profile').style.display=cur?'block':'none';if(cur)renderProfile(cur);scrollTo(0,0)}
addEventListener('hashchange',route);
function theme(){const d=document.documentElement;d.dataset.theme=d.dataset.theme==='dark'?'light':'dark'}
let tt;function toast(m){const e=$('toast');e.textContent=m;e.style.display='block';clearTimeout(tt);tt=setTimeout(()=>e.style.display='none',2200)}
addEventListener('keydown',e=>{if(e.key==='Escape')$('ov').classList.remove('on')});
lay();play();renderChips();renderCards();route();
