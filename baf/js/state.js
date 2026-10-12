/* Global UI state. */
const OB={},PG=12,nz=x=>x.replace(/ي/g,'ی').replace(/ك/g,'ک').replace(/[\s\u200c]/g,'').toLowerCase();let shown=PG,dt;function flt(){clearTimeout(dt);dt=setTimeout(()=>{shown=PG;renderCards()},150)}
let sel=[],subj='همه',ci=0,timer,cur=null;
let subjL='همه',s2='',openMore=false;
