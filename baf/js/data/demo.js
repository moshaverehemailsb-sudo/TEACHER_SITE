/* DEMO ONLY: placeholder ratings and photos. Delete when real data comes from the backend. */
T.forEach(t=>{t.demo=true;t.r=(42+(t.id*7)%8)/10;t.c=20+(t.id*53)%240;t.rec=72+(t.id*11)%26;if(PHOTOS[t.id])t.img=PHOTOS[t.id]});
Object.assign(g0(1),{r:4.7,c:214,rec:92});Object.assign(g0(3),{r:4.8,c:187,rec:94});
function g0(id){return T.find(t=>t.id==id)}
