/* Home page: subject filters, sorting, search results. */
function pick(k,l){subj=subj===k&&k!=='همه'?'همه':k;subjL=subj==='همه'?'همه':l;openMore=false;shown=PG;renderChips();renderCards()}
function renderChips(){
 $('chips').innerHTML=TOP.map(s=>`<button class="chip ${s===subj?'on':''}" onclick="pick('${s}','${s}')">${s}</button>`).join('')+`<button class="chip ${(!TOP.includes(subj)||openMore)?'on':''}" onclick="openMore=!openMore;renderChips()">${!TOP.includes(subj)?subjL+' ':''}⋯</button>`;
 $('more').className='more'+(openMore?' on':'');
 $('more').innerHTML=G.map(([h,a])=>`<h4>${h}</h4><div class="wrap">${a.map(([l,k])=>`<button class="chip ${k===subj?'on':''}" onclick="pick('${k}','${l}')">${l}</button>`).join('')}</div>`).join('');
 $('chips2').innerHTML=[['pop','محبوب‌ترین‌ها'],['cnt','بیشترین نظرات ثبت‌شده'],['zero','تدریس از صفر']].map(([k,l])=>`<button class="chip ${s2===k?'on':''}" onclick="s2=s2==='${k}'?'':'${k}';shown=PG;renderChips();renderCards()">${l}</button>`).join('')}
function renderCards(){const q=$('q').value.trim();
 const a=T.filter(t=>(subj==='همه'||t.s===subj)&&(s2!=='zero'||t.st==='آموزش از پایه')&&(!q||nz(t.n+' '+t.s+' '+t.st+' '+t.tags.join(' ')).includes(nz(q))));
 if(s2==='pop')a.sort((x,y)=>y.rec-x.rec||y.r-x.r);if(s2==='cnt')a.sort((x,y)=>y.c-x.c);
 $('cnt').textContent=fa(a.length)+' استاد';const lm=$('loadmore');lm.style.display=a.length>shown?'block':'none';lm.textContent='نمایش بیشتر ('+fa(a.length-shown)+' استاد دیگر)';$('empty').style.display=a.length?'none':'block';
 $('grid').innerHTML=a.slice(0,shown).map(t=>`<article class="card"><div class="av">${av(t)}</div><div class="info"><h3>${t.n}</h3><div class="mut">استاد ${t.s} کنکور</div><div class="rt">${rt(t)}</div><div class="tg">${t.tags.map(x=>`<span>${x}</span>`).join('')}</div><div class="row"><a class="b1" href="#/t/${t.id}">مشاهده پروفایل</a><button class="b2 ${sel.includes(t.id)?'on':''}${sel.length&&!sel.includes(t.id)&&g(sel[0]).s!==t.s?' dis':''}" onclick="tg(${t.id})">${sel.includes(t.id)?'✓ انتخاب شد':'+ مقایسه'}</button></div></div></article>`).join('')}
