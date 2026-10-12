/* Teacher comparison: selection rules and the comparison dialog. */
/* compare */
function tg(id){if(sel.includes(id))sel=sel.filter(x=>x!=id);else{if(sel.length&&g(sel[0]).s!==g(id).s)return toast('فقط اساتید یک درس رو می‌شه مقایسه کرد');if(sel.length>=2)return toast('حداکثر ۲ استاد');sel.push(id)}refresh()}
function refresh(){renderCards();if(cur)renderProfile(cur);$('bar').classList.toggle('on',sel.length>0);$('bt').textContent=fa(sel.length)+' استاد انتخاب شده';$('bn').textContent=sel.map(i=>g(i).n).join('، ')}
function showCmp(ids){const c=ids.map(g).filter(Boolean).slice(0,2);if(c.length<2)return toast('حداقل ۲ استاد انتخاب کن');
 if(c[0].s!==c[1].s)return toast('فقط اساتید یک درس رو می‌شه مقایسه کرد');
 const [a,b]=c,LB=['پیشنهاد بچه‌ها','امتیاز از ۵','تعداد نظر'];
 const rows=[['سبک تدریس',t=>t.st||'—'],['سطح مناسب',t=>t.lv||'—'],['مدرک',t=>t.b?t.b.edu.split('\n')[0]:'—'],['سابقه',t=>t.b?t.b.exp:'—']];
 $('cmp').innerHTML=`<div class="lgs">${c.map((t,i)=>`<div class="lg"><span class="tav" style="border:3px solid ${COL[i]}">${av(t)}</span><b style="color:${COL[i]}">${t.n}</b></div>`).join('')}</div>
 <div class="rings">${mets(a,b).map((m,i)=>`<div class="rc"><span class="sv" style="color:${COL[0]}">${m.v[0]}</span><div class="rsvg">${sring(m.f[0],m.f[1],11)}</div><span class="sv" style="color:${COL[1]}">${m.v[1]}</span><b class="rl">${LB[i]}</b></div>`).join('')}</div>
 <table><thead><tr><th></th>${c.map((t,i)=>`<th><span style="color:${COL[i]}">●</span> ${t.n}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr><td><b>${r[0]}</b></td>${c.map(t=>`<td>${r[1](t)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;$('ov').classList.add('on')}
