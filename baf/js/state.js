/* Global UI state and caches. */
const OB={},PG=12;
let sel=[],subj='همه',ci=0,timer,cur=null;
let subjL='همه',s2='',openMore=false;
let TOP=['همه'],G=[];        // subject chips and filter groups (loaded from the API)
let P=[];                    // popular comparisons: [idA, idB, label]
const TM=new Map();          // teacher cache: id -> teacher object
const PD={};                 // profile cache: id -> loaded profile data
let L={items:[],total:0,page:0,loading:false,error:''};   // home list state
let listCtrl=null;