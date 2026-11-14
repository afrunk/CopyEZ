// 审校脚本：生成 18 个文种的五段提示词，做交叉引用解析与逻辑检查
// 运行：node scripts/audit_gongwen_prompts.js
const fs=require('fs');
const html=fs.readFileSync(__dirname+'/../templates/gongwen/index.html','utf8');
const m=html.match(/<script>([\s\S]*)<\/script>/);
if(!m){ console.error('未找到 script'); process.exit(1); }
let code=m[1];
// 暴露内部函数供审校
code=code.replace('  fill(load()); render();',
  '  fill(load()); render();\n  global.__G={build:build,GENRES:GENRES,GENRE_INPUT:GENRE_INPUT,GENRE_BODY:GENRE_BODY,GENRE_CLEAN:GENRE_CLEAN,GENRE_TITLE:GENRE_TITLE,DEFAULTS:DEFAULTS};');
// DOM 桩
const els={};
function mkEl(){
  const el={checked:true,textContent:'',innerHTML:'',style:{},className:'',dataset:{},type:'text',
    addEventListener(){},appendChild(){},setAttribute(){},removeChild(){},click(){},select(){},
    classList:{toggle(){return false}},querySelector(){return mkEl()},closest(){return null},focus(){}};
  let val='';
  Object.defineProperty(el,'value',{get:()=>val,set:v=>{val=String(v==null?'':v);}});
  return el;
}
global.document={ getElementById(id){ if(!els[id]) els[id]=mkEl(); return els[id]; },
  createElement(){ return mkEl(); }, querySelectorAll(){ return []; }, body: mkEl(), addEventListener(){} };
global.navigator={clipboard:{writeText:async()=>true}};
global.localStorage={getItem:()=>null,setItem(){}};
global.URL={createObjectURL:()=>'blob:x'}; global.Blob=function(){};
global.window=global;
eval(code);
const G=global.__G;
let fail=0, warn=0;
function bad(msg){ fail++; console.log('  ✗ '+msg); }
function w(msg){ warn++; console.log('  ⚠ '+msg); }

// ---------- 1. 数据表完整性 ----------
console.log('== 1. 数据表完整性 ==');
const ids=G.GENRES.map(g=>g.id);
if(ids.length!==18) bad('GENRES 数量 '+ids.length+' != 18');
for(const t of ['GENRE_INPUT','GENRE_BODY','GENRE_CLEAN','GENRE_TITLE']){
  const missing=ids.filter(id=>!G[t][id]);
  if(missing.length) bad(t+' 缺少: '+missing.join(','));
}
G.GENRES.forEach(g=>{
  const gi=G.GENRE_INPUT[g.id];
  ['brief','src','task','anchor','from'].forEach(k=>{ if(!gi[k]) bad(g.name+' GENRE_INPUT 缺 '+k); });
  ['name','aud','len'].forEach(k=>{ if(!Array.isArray(gi[k])||gi[k].length!==3) bad(g.name+' GENRE_INPUT.'+k+' 不是 3 元数组'); });
  if(!Array.isArray(G.GENRE_BODY[g.id])||G.GENRE_BODY[g.id].length<4) bad(g.name+' GENRE_BODY 条数不足');
  if(!Array.isArray(G.GENRE_CLEAN[g.id])||G.GENRE_CLEAN[g.id].length<3) bad(g.name+' GENRE_CLEAN 条数不足');
  if(!Array.isArray(g.review)||!g.review.length) bad(g.name+' review 缺失');
});

// ---------- 2. 逐文种生成与检查 ----------
console.log('== 2. '+ids.length+' 个文种逐一生成 ==');
const NAME_FORBID={}; // 会议方案类词汇只允许 speech / democratic
const texts={}; // genre -> {P1:..}
for(const id of ids){
  const g=G.GENRES.find(x=>x.id===id);
  const cfg={genre:id,meeting:'测试材料名称',audience:'测试对象',subject:'测试主体',scope:'测试范围',
    length:'测试篇幅',ban:'赋能、助力',rewrite:true};
  const parts=G.build(cfg);
  if(parts.length!==5) bad(g.name+' 段数 != 5');
  const t={}; parts.forEach(p=>t[p.id]=p.text); texts[id]=t;
  console.log('-- '+g.name+' --');
  // 占位符残留
  parts.forEach(p=>{
    if(/undefined|NaN|\[object/.test(p.text)) bad(g.name+' '+p.id+' 有占位符残留');
    if(/\{x\}|\{\{/.test(p.text)) bad(g.name+' '+p.id+' 有未替换模板');
  });
  // 文体泄漏：非 speech/democratic 不得出现会议方案/粗框架/跟领导定
  if(!['speech','democratic'].includes(id)){
    ['P1','P2','P3','P5'].forEach(pid=>{
      if(/会议方案|粗框架|跟领导定/.test(t[pid])) bad(g.name+' '+pid+' 泄漏了「会议方案/粗框架/跟领导定」');
    });
  }
  // 泛化检查：除 speech 外，正文段不应把平安建设写死
  if(id!=='speech' && /平安建设/.test(t.P3.replace('测试材料名称',''))) w(g.name+' P3 出现「平安建设」（若非默认场景素材需确认）');
  // genre 名必须在 P1
  if(!t.P1.includes(g.name)) bad(g.name+' P1 未含本类名');
  // P1 必须指向第二段【标题】
  if(!t.P1.includes('第二段【标题】')) bad(g.name+' P1 缺「第二段【标题】」指引');
}

// ---------- 3. 交叉引用解析（全对话union + 白名单） ----------
console.log('== 3. 交叉引用解析 ==');
for(const id of ids){
  const g=G.GENRES.find(x=>x.id===id); const t=texts[id];
  const all=Object.keys(t).map(k=>t[k]).join('\n');
  const headings=new Set();
  all.split('\n').forEach(line=>{
    const s=line.trim(); if(s.startsWith('【')){ const tk=s.match(/^【[^】]+】/); if(tk) headings.add(tk[0]); }
  });
  const WHITELIST_PREFIX=['待补'];
  const WHITELIST=['【核对说明】'];
  // 每段单独扫 token，允许前向引用（同一对话会累积），但记录
  const paraOrder=['P1','P2','P3','P4','P5'];
  const seenHead=new Set();
  for(const pid of paraOrder){
    const txt=t[pid];
    const toks=[...txt.matchAll(/【[^】]{1,24}】/g)].map(x=>x[0]);
    for(const tk of toks){
      if(WHITELIST.includes(tk)||WHITELIST_PREFIX.some(p=>tk.slice(1).startsWith(p))) continue;
      if(seenHead.has(tk)) continue; // 本段或前段已有节名
      if(headings.has(tk)){ seenHead.add(tk); continue; } // 后段定义（前向引用）
      // 前缀匹配已定义节名（引用短名、节名带后缀的情况）
      const pref=[...headings].find(h=>h.startsWith(tk.slice(0,-1))&&h!==tk);
      if(pref){ w(g.name+' '+pid+' 引用 '+tk+' 只前缀匹配到节名 '+pref); continue; }
      bad(g.name+' '+pid+' 引用 '+tk+' 在全部五段中找不到节名');
    }
    // 收集本段节名
    txt.split('\n').forEach(line=>{ const s=line.trim(); if(s.startsWith('【')){ const tk=s.match(/^【[^】]+】/); if(tk) seenHead.add(tk[0]); } });
  }
}
console.log('  （节名总数见上；前缀告警需人工确认）');

// ---------- 4. P4 恒定 / 其余按类变化 ----------
console.log('== 4. 按类差异 ==');
for(const pid of ['P1','P2','P3','P5']){
  const set=new Set(ids.map(id=>texts[id][pid]));
  if(set.size!==18) bad(pid+' 在 18 类下只有 '+set.size+' 种（应 18 种）');
  else console.log('  '+pid+': 18 种 ✓');
}
{
  const set=new Set(ids.map(id=>texts[id].P4));
  if(set.size!==1) bad('P4 应恒定 1 种，实际 '+set.size+' 种');
  else console.log('  P4: 恒定 1 种 ✓');
}

// ---------- 5. 参数插值与禁用词 ----------
console.log('== 5. 参数插值 ==');
{
  const cfg={genre:'summary',meeting:'MM1',audience:'AA1',subject:'SS1',scope:'SC1',length:'LL1',ban:'BB1',rewrite:true};
  const parts=G.build(cfg); const all=parts.map(p=>p.text).join('\n');
  ['MM1','AA1','SS1','SC1','LL1','BB1'].forEach(k=>{ if(!all.includes(k)) bad('参数 '+k+' 未插入提示词'); });
}
console.log('== 完成：'+fail+' 处错误，'+warn+' 处告警 ==');
process.exit(fail?1:0);
