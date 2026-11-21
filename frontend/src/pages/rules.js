import {esc,date} from '../utils/html.js';
import {session} from '../hooks/session.js';
import {rulebookStore} from '../stores/rulebook.js';
import {PERIOD_SOURCE} from '../constants/enums.js';
const ruleText=e=>`${esc((e.lhs||[]).join(', ')||'∅')} → ${esc((e.rhs||[]).join(', '))}`;
export function rulesPage(relations){
  const disabled=session.user.role==='viewer'?'disabled':'';
  const first=relations[0];
  const latest=first?rulebookStore.latest(first.id):null;
  const initialRules=latest?latest.entries.map(e=>`${(e.lhs||[]).join(', ')} -> ${(e.rhs||[]).join(', ')}`).join('\n'):'委托号 -> 客户';
  return `<div class="split"><section><div class="section-top"><h2>规则生效期时间线</h2><span>AS-OF / IMMUTABLE PERIODS</span></div>${relations.length===0?'<div class="empty">先在「关系草案」登记委托单属性。</div>':relations.map(rel=>{
    const chain=rulebookStore.forRelation(rel.id);
    return `<div class="period-block"><div class="period-rel"><strong>${esc(rel.code)}</strong><small>${esc(rel.title)}</small></div>${chain.length?chain.map(p=>`<div class="period-card"><div class="period-head"><b>${esc(p.effective_from)}</b><span class="badge ${p.source}">${esc(PERIOD_SOURCE[p.source]||p.source)}</span><small>生效期 #${p.id} · ${p.entries.length} 条规则 · 登记于 ${date(p.created_at)}</small></div>${p.correction_note?`<p class="period-note">${esc(p.correction_note)}</p>`:''}<ul class="rule-list">${p.entries.map(e=>`<li>${ruleText(e)}</li>`).join('')}</ul></div>`).join(''):'<div class="empty">尚未建立生效期：先在右侧登记基线。</div>'}${chain.length?`<p class="help">规则覆盖自 <b>${esc(chain[0].effective_from)}</b> 起；早于该日的委托日期属于缺档，分解将被拦下并提示该缺口。</p>`:''}</div>`;
  }).join('')}<div class="protocol"><h3>版本口径</h3><ol><li>委托分解按业务发生日选取最近的已生效规则期</li><li>补录更正登记为新生效期，可回溯插入；未改规则照旧沿用</li><li>生效期一经登记不可修改，已受理报告永远沿用原规则</li><li>同关系同日期并发更正冲突（409）；带幂等键的重试不重复登记</li></ol></div></section>
  <section class="form-panel"><span class="eyebrow">BASELINE PERIOD</span><h2>建立基线生效期</h2><form id="baseline-form"><label>关系草案<select name="relation_id">${relations.map(r=>`<option value="${r.id}">${esc(r.code)} · ${esc(r.title)}</option>`).join('')}</select></label><label>生效日期<input name="effective_from" type="date" value="2026-01-01" required></label><input type="hidden" name="idempotency_key" value="base-${Date.now()}"><button class="primary" ${disabled}>冻结依赖登记簿为基线 +</button></form><p class="help">基线只能建立一次，内容承接「依赖编辑」页已确认的规则；之后的变更请用补录更正。</p>
  <hr class="form-divider"><span class="eyebrow">RETROACTIVE CORRECTION</span><h2>补录规则更正</h2><form id="correction-form"><label>关系草案<select name="relation_id" id="correction-relation">${relations.map(r=>`<option value="${r.id}">${esc(r.code)} · ${esc(r.title)}</option>`).join('')}</select></label><button type="button" class="small" id="load-rules" ${disabled}>载入该草案当前规则</button><label>生效日期<input name="effective_from" type="date" value="2026-06-01" required></label><label>更正后完整规则（每行一条，左 → 右，逗号分隔）<textarea name="entries" rows="7" required>${esc(initialRules)}</textarea></label><label>更正说明<input name="correction_note" value="补录更正：未改规则照旧，仅标注变更项"></label><input type="hidden" name="idempotency_key" value="${esc(rulebookStore.idemKey)}"><button class="primary" ${disabled}>登记新生效期 ↗</button></form><p class="help">更正可跨多个生效期：提交的是该日期起的完整规则状态，没改的规则原样抄入；同日新报告立即使用更正后规则。</p></section></div>`;
}
