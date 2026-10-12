/* Teacher profile page: bio, courses, rivals, reviews. */
const BL=[['👥','سبک کلاس','cls'],['📝','روش تدریس','way'],['🎯','سطح مناسب','lvl'],['❓','حل تست و تمرین','tst'],['🎓','مدرک و تحصیلات','edu'],['⏳','سابقه تدریس','exp'],['💡','نکته','note']];
function bioHtml(t){const b=t.b;if(!b)return '<p>معرفی این استاد به‌زودی اضافه می‌شود.</p>';
 const R=r=>b[r[2]]?`<div class="br"><b>${r[0]} ${r[1]}</b><p>${b[r[2]]}</p></div>`:'';
 return `<div class="bio">${R(BL[0])}<div class="full">${BL.slice(1).map(R).join('')}</div></div>`}
function coursesHtml(t){const c=CR[t.id];return `<div class="sec"><h3>دوره‌های استاد</h3>${c?c.map(x=>`<div class="cr"><div class="sh2"><b>${x[0]}</b><button class="more-btn" onclick="toast('صفحه‌ی دوره به‌زودی')">مشاهده ←</button></div><p>${x[1]}</p></div>`).join(''):'<p>دوره‌های این استاد به‌زودی اضافه می‌شود.</p>'}</div>`}
/* profile */
function renderProfile(id){const t=g(id);if(!t)return;
 const sim=T.filter(x=>x.id!==id&&x.s===t.s).sort((a,b)=>b.r-a.r);
 $('profile').innerHTML=`<a class="back" href="#/">‹ بازگشت به اساتید</a>
 <div class="cover"><div class="ph"><div class="av">${av(t)}</div><div><h1>استاد ${t.n}</h1><div class="mut">مدرس ${t.s} کنکور</div><div class="tg" style="margin-top:6px">${[t.st,t.lv].filter(Boolean).map(x=>`<span>${x}</span>`).join('')}</div></div></div>
 <div class="stats">${t.c?`<span>⭐ <b>${fa(t.r)}</b></span><span>💬 <b>${fa(t.c)}</b> نظر</span><span>👍 <b>${pv(t.rec,'٪')}</b> پیشنهاد</span>`:'<span>هنوز نظری ثبت نشده</span>'}</div></div>
 <div class="act"><button class="b1" onclick="toast('فرم ثبت نظر به‌زودی')">✍ ثبت نظر</button><button class="b2 ${sel.includes(id)?'on':''}" onclick="tg(${id})">${sel.includes(id)?'✓ در مقایسه':'+ مقایسه'}</button></div>
 <div class="sec ${OB[t.id]?'open':''}"><div class="sh2"><h3>درباره‌ی استاد</h3>${t.b?`<button class="more-btn" onclick="OB[${t.id}]=!OB[${t.id}];renderProfile(${t.id})">${OB[t.id]?'کمتر':'بیشتر ...'}</button>`:''}</div>${bioHtml(t)}</div>${coursesHtml(t)}
 <div class="sec"><h3>اساتید رقیب</h3><div class="sc">${sim.map(x=>`<div class="mn" onclick="location.hash='#/t/${x.id}'"><i>${av(x)}</i>${x.n}<small>${x.c?'⭐ '+fa(x.r):x.s}</small><u class="${sel.includes(x.id)?'on':''}" onclick="event.stopPropagation();tg(${x.id})">${sel.includes(x.id)?'✓':'+'}</u></div>`).join('')}</div><div class="mut">برای مقایسه روی + بزن.</div></div>
 <div class="sec"><div class="sh2"><h3>نظرات دانش‌آموزان</h3><span class="demo">نمونه‌ی آزمایشی</span></div><div class="sum"><big>${t.c?fa(t.r):'—'}</big><div><s style="color:#f0a800;text-decoration:none">${'★'.repeat(Math.round(t.r||0))}</s><div class="mut">${t.c?'بر اساس '+fa(t.c)+' نظر':'هنوز نظری ثبت نشده؛ اولین نفر باش ✍️'}</div></div></div>${(RV[t.id]||[]).map(r=>`<div class="rv"><b>${r.w}</b> <s>${'★'.repeat(r.s)+'☆'.repeat(5-r.s)}</s><p>${r.t}</p></div>`).join('')}</div>`}
