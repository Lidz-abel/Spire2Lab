const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const translations = {StrikeIronclad:'打击',DefendIronclad:'防御',Bash:'痛击',BurningBlood:'燃烧之血',Wound:'伤口',Dazed:'晕眩',Slimed:'黏液',StatusCard:'加入状态牌',Buff:'强化',Debuff:'减益',Defend:'防御',Unknown:'未知'};
const name = s => translations[s] || s;
let live = null, replay = null, replayFrames = [], busy = false, acceptance = null;
async function api(path, body) {
  const res = await fetch(path, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data = await res.json();
  if (!res.ok) throw Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
  return data;
}
function showError(error) { $('error').hidden = false; $('error').textContent = error.message; }
async function action(fn) {
  if (busy) return;
  busy = true; $('error').hidden = true; if (live && !replay) render(live);
  try { await fn(); $('error').hidden = true; } catch (e) { try { live=await api('/api/state'); } catch {} showError(e); }
  finally { busy = false; if (live && !replay) render(live); }
}
function powers(items) { return `<div class="powers">${items.map(p=>`<span class="power">${esc(p.type_id)} ${p.amount}</span>`).join('')}</div>`; }
function health(entity) { return `<div class="hp-line"><span>生命</span><span>${entity.hp} / ${entity.max_hp}</span></div><div class="bar"><span style="width:${Math.max(0,Math.min(100,100*entity.hp/entity.max_hp))}%"></span></div>`; }
function render(view) {
  const o=view.observation, d=view.decision;
  const selected=d?.selected_action_id, chosen=o.legal_actions.find(a=>a.action_id===selected);
  const missing=path=>(o.unavailable_fields||[]).includes(path);
  const executing=['executing','reconciling'].includes(view.status);
  const canPause=view.status==='running'||(executing&&view.resume_after_step);
  const original=view.metadata.backend==='original_game';
  $('backend-label').textContent=original?'Windows 原版游戏':'C# 原生模拟器';
  $('acceptance-status').textContent=acceptance?.verified?'限定参考集已通过':acceptance?.status==='stale_evidence'?'证据已变化 · 需重新验收':'等待本机原版校验';
  $('acceptance-status').className=acceptance?.verified?'':'pending';
  $('source-note').textContent=view.metadata.build?.evidence_kind==='synthetic_transport_fixture'?'合成接口测试数据：用于验证控制与显示，不是原版游戏证据。':original?'状态与动作结果来自原版游戏。牌面基础伤害与格挡来自固定规则表；跨后端一致性仍待校验。':'状态来自固定版本模拟器，尚未通过本机原版逐步校验。';
  if(acceptance?.verified&&view.metadata.build?.evidence_kind!=='synthetic_transport_fixture')$('source-note').textContent=original?'状态与动作来自原版；固定参考集已通过对照。牌面基础数值来自规则表。':'当前状态来自模拟器。固定参考集已通过对照；本次对局未自动计入实机证据。';
  $('new-session').disabled=busy||executing||view.status==='awaiting_confirmation';
  $('reconcile').hidden=!!replay||view.status!=='awaiting_confirmation';
  $('reconcile').disabled=busy;
  $('archive-controls').hidden=!!replay||!['awaiting_confirmation','error'].includes(view.status);
  $('archive').disabled=busy;
  if(view.status==='closed')$('source-note').textContent='本次实验已归档。显示的是最后确认的状态，可能与当前游戏不同；未决动作不会记为胜负。';
  $('mode').textContent = replay ? '轨迹回放' : '实时实验';
  $('status').textContent = replay ? '只读' : ({paused:'已暂停',running:'运行中',executing:'执行中 · 等待结算',reconciling:'正在确认结果',awaiting_confirmation:'结果待确认',finished:'已结束',error:'执行异常',closed:'已归档 · 显示最后确认状态'}[view.status]||view.status);
  $('run').textContent=canPause?'Ⅱ 暂停':executing?'本步结束后暂停':'▶ 自动运行';
  $('run').disabled=!!replay||(!canPause&&(busy||view.status!=='paused'));
  $('step').disabled=!!replay||view.status!=='paused'||busy;
  $('speed').disabled=!!replay;
  $('encounter-title').textContent=view.metadata.encounter;
  $('turn').textContent=missing('turn')?'战斗已结束':`回合 ${o.turn+1}`;
  $('player').innerHTML=`<div class="character-mark">♜</div><div class="player-name">铁甲战士</div>${health(o.player)}<div class="resources"><span>能量<b class="energy">${o.player.energy??'—'}<small> / ${o.player.max_energy??'—'}</small></b></span><span>护甲<b>${o.player.block}</b></span></div>${powers(o.player.powers)}<div class="relic">◇ ${o.relics.map(r=>esc(name(r.name))).join(' · ')}</div>`;
  $('enemies').innerHTML=o.enemies.map((e,index)=>`<article class="enemy"><div class="enemy-top"><span class="enemy-icon">${index+1}</span><span class="intent">${e.intents.map(i=>i.deals_damage?`⚔ ${i.magnitude}${i.hits>1?` (${i.hits} 次)` : ''}`:`${esc(name(i.type))}${i.magnitude!==null?' '+i.magnitude:''}`).join(' / ')}</span></div><div class="enemy-name">${esc(e.name)}</div>${health(e)}<div class="small muted" style="margin-top:12px">护甲 ${e.block}</div>${powers(e.powers)}</article>`).join('') || `<p class="empty">${missing('enemies')?'结算页面不再提供敌人状态':'敌人已全部离场'}</p>`;
  $('hand-count').textContent=missing('hand')?'当前不可读取':`${o.hand.length} 张`;
  $('piles').textContent=`抽牌 ${missing('draw_pile')?'—':o.draw_pile.length} · 弃牌 ${missing('discard_pile')?'—':o.discard_pile.length} · 消耗 ${missing('exhaust_pile')?'—':o.exhaust_pile.length}`;
  $('hand').innerHTML=o.hand.map((c,i)=>{
    const playable=o.legal_actions.some(a=>a.card_ref===c.ref);
    return `<article class="card ${c.card_type==='Skill'?'skill':''} ${chosen?.card_ref===c.ref?'suggested':''} ${!playable?'unplayable':''}"><div class="card-top"><span class="cost">${c.cost}</span><span class="card-kind">${esc(c.card_type)}</span></div><div class="card-name">${esc(name(c.name))}${c.upgraded?'+':''}</div><div class="card-stats">${c.printed_damage?`牌面伤害 ${c.printed_damage}`:''}${c.printed_block?`牌面格挡 ${c.printed_block}`:''}${c.type_id==='BASH'?'<br>施加易伤':''}</div><span class="card-index">#${i+1}</span></article>`;
  }).join('') || `<p class="empty">${missing('hand')?'结算页面不再提供手牌':'当前没有手牌'}</p>`;
  $('outcome').hidden=o.outcome==='ongoing';
  $('outcome').textContent={won:'战斗胜利 · 完整轨迹已记录',lost:'战斗失败 · 完整轨迹已记录',truncated:'达到实验步数上限 · 记录为截断'}[o.outcome]||'';
  $('observation-json').textContent=JSON.stringify(o,null,2);
  $('decision-id').textContent=`决策 ${o.decision_id}`;
  $('decision-meta').textContent=d?`${d.policy} · ${d.elapsed_ms.toFixed(2)} ms`:'当前没有待执行决策';
  const best=d?.candidates.find(c=>c.action_id===selected);
  $('proposal').innerHTML=chosen?`<div class="proposal"><span class="tag">当前选择</span><strong>${esc(chosen.label)}</strong><ul class="reasons">${best.reasons.map(r=>`<li>${esc(r)}</li>`).join('')}</ul></div>`:`<p class="empty">${view.status==='closed'?'实验已归档，不再生成动作。':'当前没有可执行的决策。'}</p>`;
  $('candidates').innerHTML=(d?.candidates||[]).map(c=>`<button class="candidate ${c.action_id===selected?'chosen':''}" data-action="${esc(c.action_id)}" ${replay||view.status!=='paused'||busy?'disabled':''}><span>${esc(o.legal_actions.find(a=>a.action_id===c.action_id)?.label)}</span><span class="candidate-score">${c.score.toFixed(2)}</span></button>`).join('');
  for(const b of $('candidates').querySelectorAll('button')) b.onclick=()=>step(b.dataset.action);
  $('history').innerHTML=[...view.history].reverse().map(h=>`<div class="history-row"><span class="number">${String(h.step).padStart(2,'0')}</span><span>${esc(h.label)}${h.manual?' · 人工干预':''}</span><span class="${h.hp_delta<0?'loss':'neutral'}">HP ${h.hp_delta>0?'+':''}${h.hp_delta}</span></div>`).join('')||'<p class="empty">执行第一步后，这里会出现实际状态变化。</p>';
  const r=view.last_result;
  $('last-result').innerHTML=r?`<strong>${esc(r.action.label)}</strong><br>生命变化 ${r.facts.player_hp_delta>0?'+':''}${r.facts.player_hp_delta}<br>执行 ${r.execution_ms.toFixed(2)} ms${r.facts.manual_intervention?'<br>本步包含人工干预':''}`:'等待第一步执行。';
  $('download').href=`/api/runs/${view.metadata.run_id}/download`;
  if(view.error)showError(Error(view.error));
}
async function refreshRuns() {
  const runs=await api('/api/runs');
  $('run-list').innerHTML=runs.map(r=>`<option value="${r.run_id}">${r.backend==='original_game'?'原版':'模拟'} · ${esc(r.encounter)} · ${r.seed??'未记录种子'} · ${r.run_id.slice(0,5)}</option>`).join('');
}
function step(actionId=null) { action(async()=>{ live=await api('/api/step',{request_id:crypto.randomUUID(),decision_id:live.observation.decision_id,action_id:actionId}); render(live); }); }
$('step').onclick=()=>step();
$('run').onclick=()=>{
  const stop=live.status==='running'||['executing','reconciling'].includes(live.status);
  const control=async()=>{live=await api('/api/control',{running:!stop,delay:Number($('speed').value)});render(live);};
  if(stop)control().catch(showError);else action(control);
};
$('reconcile').onclick=()=>action(async()=>{live=await api('/api/reconcile',{});render(live);});
$('archive').onclick=()=>action(async()=>{live=await api('/api/archive',{run_id:live.metadata.run_id});render(live);await refreshRuns();});
$('backend').onchange=()=>{
  const original=$('backend').value==='original_game';
  $('seed').disabled=original;
  $('new-session').textContent=original?'连接当前原版战斗':'新建实验';
  $('backend-hint').textContent=original?'请在原版中准备符合条件的首回合战斗。连接会核对版本与场景，不会重置游戏。':'新建固定初始条件的模拟战斗。';
};
$('scenario-form').onsubmit=e=>{e.preventDefault();action(async()=>{live=await api('/api/session',{backend:$('backend').value,encounter:$('encounter').value,seed:Number($('seed').value),policy:$('policy').value,policy_seed:Number($('policy-seed').value)});exitReplay();render(live);await refreshRuns();});};
function exitReplay(){replay=null;$('replay-controls').hidden=true;$('back-live').hidden=true;}
$('back-live').onclick=()=>{exitReplay();render(live);};
$('load-replay').onclick=()=>action(async()=>{
  if(live.status==='running')live=await api('/api/control',{running:false});
  const events=await api(`/api/runs/${$('run-list').value}`);
  replay={metadata:events[0].data.metadata};replayFrames=[];
  let observation=events[0].data.observation, decision=null, history=[], last_result=null;
  for(const event of events.slice(1)){
    if(event.kind==='decision')decision=event.data;
    if(event.kind==='action_submitted')replayFrames.push({metadata:replay.metadata,observation,decision,history:[...history],last_result,status:'paused'});
    if(event.kind==='transition'){
      const t=event.data;
      history.push({step:history.length+1,label:t.action.label,hp_delta:t.facts.player_hp_delta,manual:t.facts.manual_intervention});
      observation=t.observation;decision=null;last_result={action:t.action,facts:t.facts,execution_ms:t.execution_ms};
    }
  }
  replayFrames.push({metadata:replay.metadata,observation,decision,history,last_result,status:observation.outcome==='ongoing'?'paused':'finished'});
  $('replay-controls').hidden=false;$('back-live').hidden=false;
  $('replay-position').max=replayFrames.length-1;$('replay-position').value=0;
  renderReplay();
});
function renderReplay(){const i=Number($('replay-position').value);$('replay-label').textContent=`${i} / ${replayFrames.length-1}`;render(replayFrames[i]);}
$('replay-position').oninput=renderReplay;
const events=new EventSource('/api/events');
events.addEventListener('state',e=>{live=JSON.parse(e.data);$('connection').textContent='已连接 · 实时状态';$('connection-dot').className='connected';if(!replay)render(live);});
events.onerror=()=>{$('connection').textContent='连接中断 · 正在重连';$('connection-dot').className='';};
refreshRuns().catch(showError);
api('/api/acceptance').then(data=>{acceptance=data;if(live&&!replay)render(live);}).catch(showError);
