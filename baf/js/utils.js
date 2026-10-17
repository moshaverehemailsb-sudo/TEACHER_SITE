/* Shared helpers: formatting, escaping, avatars, comparison metrics and the split ring SVG. */
const $=id=>document.getElementById(id),fa=n=>Number(n).toLocaleString('fa-IR');
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl=u=>typeof u==='string'&&/^(assets\/|https:\/\/)[^\s"'<>]+$/.test(u)?u:'';
const g=id=>TM.get(Number(id));
const av=t=>{const u=safeUrl(t.img);return u?`<img src="${esc(u)}" alt="">`:esc(t.e)};
const COL=['#1f9d57','#2f80ed'];
const stars=n=>{const k=Math.max(0,Math.min(5,Math.round(Number(n)||0)));return '★'.repeat(k)+'☆'.repeat(5-k)};
const mets=(a,b)=>{const mx=Math.max(a.c||0,b.c||0)||1;return [{l:'پیشنهاد',f:[(a.rec||0)/100,(b.rec||0)/100],v:[pv(a.rec,'٪'),pv(b.rec,'٪')]},{l:'امتیاز',f:[(a.r||0)/5,(b.r||0)/5],v:[pv(a.r),pv(b.r)]},{l:'تعداد نظر',f:[(a.c||0)/mx,(b.c||0)/mx],v:[pv(a.c),pv(b.c)]}]};
function sring(f1,f2,sw){const r=50,C=2*Math.PI*r;
 const arc=(f,flip,col)=>f>0?`<circle class="rg" cx="60" cy="60" r="${r}" fill="none" stroke="${col}" stroke-width="${sw}" stroke-linecap="round" transform="${flip?'translate(120 0) scale(-1 1) ':''}rotate(90 60 60)" style="--c:${C.toFixed(1)};--d:${(C/2*Math.min(1,f)).toFixed(1)}"/>`:'';
 return `<svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="${r}" fill="none" stroke="var(--line)" stroke-width="${sw}"/>${arc(f1,true,COL[0])}${arc(f2,false,COL[1])}</svg>`}
const pv=(x,u='')=>x==null?'—':fa(x)+u,rt=t=>t.c?`<s>★</s> <b>${fa(t.r)}</b> <span>(${fa(t.c)} نظر)</span>`:'<span>هنوز نظری ثبت نشده</span>';