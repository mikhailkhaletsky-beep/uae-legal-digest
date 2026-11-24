// Paste into Claude in Chrome's javascript tool on a firm's homepage or news page.
// Usage (REPL): await scan(minMentions, startPath)
//   minMentions: 0 for regional firms; 8-10 for international firms (counts UAE/GCC words in the article;
//                site footers listing Dubai offices add noise, so keep it high)
//   startPath:   optional news-listing path, e.g. '/news-insights/insights/'
// Edit FROM/TO for the period. Returns "MM-DD | MEn | title | path" lines.
const FROM='2026-11-16', TO='2026-11-22';
async function scan(NEED_ME=0, START=null){
  const inRange=d=>d&&d>=FROM&&d<=TO;
  const ME=/\b(UAE|U\.A\.E|Dubai|Abu Dhabi|Saudi|KSA|Middle East|GCC|Qatar|Bahrain|Oman|Kuwait|Egypt|DIFC|ADGM|MENA|Emirati)\b/g;
  // 1) WordPress sites: REST API gives exact publication dates
  try{const r=await fetch(`/wp-json/wp/v2/posts?after=${FROM}T00:00:00&before=${TO}T23:59:59&per_page=50&_fields=date,link,title,content`);
    if(r.ok&&/json/.test(r.headers.get('content-type')||'')){const j=await r.json(); if(j.length){const f=j.filter(p=>((p.content?.rendered||'').match(ME)||[]).length>=NEED_ME);
      return 'WP '+j.length+'/'+f.length+'\n'+f.map(p=>p.date.slice(5,10)+' | '+p.title.rendered.replace(/<[^>]+>|&#\d+;|&\w+;/g,' ').slice(0,80)+' | '+p.link.replace(location.origin,'')).join('\n');}}}catch(e){}
  // 2) Otherwise: find listing pages, collect article links, read each article's own date
  const NEWS=/(insight|news|publication|knowledge|thought|article|update|perspective|briefing|alert|blog)/i;
  const pats=[/"datePublished"\s*:\s*"([^"]+)"/,/article:published_time"\s+content="([^"]+)"/,/content="([^"]+)"\s+property="article:published_time"/,/<time[^>]*datetime="([^"]+)"/,/"publishedDate"\s*:\s*"([^"]+)"/,/Published:?\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+20\d\d)/,/(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+20\d\d)/,/((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+20\d\d)/];
  const norm=s=>{if(!s)return null; if(/^\d{4}-/.test(s))return s.slice(0,10); const d=new Date(s.replace(/(\d)(st|nd|rd|th)/,'$1').replace(',','')+' UTC'); return isNaN(d)?null:d.toISOString().slice(0,10);};
  const anchors=(doc,base)=>[...doc.querySelectorAll('a[href]')].map(a=>{let h;try{h=new URL(a.getAttribute('href'),base).href.split(/[?#]/)[0]}catch(e){return null}return{h,t:(a.textContent||'').replace(/\s+/g,' ').trim()}}).filter(o=>o&&o.h.startsWith(location.origin));
  let pages=START?[new URL(START,location.href).href]:[location.href.split(/[?#]/)[0]];
  if(!START&&!NEWS.test(location.pathname)) pages=[...new Set(anchors(document,location.href).filter(o=>NEWS.test(o.h.replace(location.origin,''))&&o.h.replace(location.origin,'').split('/').filter(Boolean).length<=2).map(o=>o.h))].slice(0,4);
  const cand=new Map();
  for(const p of pages){let doc=document; if(p!==location.href.split(/[?#]/)[0]){try{doc=new DOMParser().parseFromString(await (await fetch(p)).text(),'text/html')}catch(e){continue}}
    for(const o of anchors(doc,p)){if(o.t.length<30||cand.has(o.h)||pages.includes(o.h))continue; if(o.h.replace(location.origin,'').split('/').filter(Boolean).length<2)continue; cand.set(o.h,o);}}
  const list=[...cand.values()].slice(0,60);
  await Promise.all(list.map(async o=>{try{const x=await (await fetch(o.h)).text(); for(const p of pats){const m=x.match(p); if(m){o.d=norm(m[1]);break;}} o.me=(x.replace(/<[^>]+>/g,' ').match(ME)||[]).length;}catch(e){}}));
  const hit=list.filter(o=>inRange(o.d)&&o.me>=NEED_ME);
  return 'pages:'+pages.map(p=>p.replace(location.origin,'')).join(',')+' cand:'+list.length+' dated:'+list.filter(o=>o.d).length+' newest:'+list.map(o=>o.d||'').sort().at(-1)+' hits:'+hit.length+'\n'
    +hit.map(o=>o.d.slice(5)+' | ME'+o.me+' | '+o.t.slice(0,70).replace(/[^\w\s,.:;'’%&()$-]/g,'')+' | '+o.h.replace(location.origin,'')).join('\n');
}
