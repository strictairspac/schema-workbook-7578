import {table} from '../components/common/table.js';
import {badge} from '../components/common/badge.js';
import {esc,date} from '../utils/html.js';
import {session} from '../hooks/session.js';
import {rulebookStore} from '../stores/rulebook.js';
import {PERIOD_SOURCE} from '../constants/enums.js';
export function reportsPage(items,relations){
  const first=relations[0];
  const latest=first?rulebookStore.latest(first.id):null;
  return `<div class="split"><section><div class="section-top"><h2>分解任务记录</h2><span>COMMISSION-DATE DRIVEN</span></div>${table(['任务 / 时间','草案 / 委托日期','生效期','状态','报告'],items.map(r=>{
    const p=r.input_snapshot?.rule_provenance||{};
    return [`<strong>${esc(r.name)}</strong><small>${date(r.created_at)}</small>`,
      `${esc(relations.find(x=>x.id===r.relation_id)?.code)}<small>委托日 ${esc(r.commission_date||'—')}</small>`,
      p.effective_from?`<b>${esc(p.effective_from)}</b><small>${esc(PERIOD_SOURCE[p.source]||p.source||'')} · ${p.rule_count??0} 条规则</small>`:'<small>—</small>',
      badge(r.status),`<a href="#evidence/${r.id}">查看 →</a>`];
  }))}<div class="protocol"><h3>按业务日期取规则的四步协议</h3><ol><li>按委托日期定位适用生效期；缺档则拦下并指出缺口区间</li><li>入队即冻结生效期编号、生效日与完整规则快照</li><li>计算属性闭包，精确枚举候选键并合成3NF关系</li><li>追赶法判定无损；报告可追溯所用生效期与每条规则</li></ol></div></section>
  <section class="form-panel"><span class="eyebrow">SYNTHESIZE BY COMMISSION DATE</span><h2>按委托日期发起分解</h2><form id="report-form"><label>任务名称<input name="name" value="shift-${new Date().toISOString().slice(0,10).replace(/-/g,'')}" required></label><label>选择业务草案<select name="relation_id" id="report-relation">${relations.map(r=>`<option value="${r.id}">${esc(r.code)} · ${esc(r.title)}</option>`).join('')}</select></label><label>委托日期（业务发生日）<input name="commission_date" id="commission-date" type="date" value="2026-03-10" required></label><button type="button" class="small" id="preview-rules" ${session.user.role==='viewer'?'disabled':''}>预览当日生效规则</button><div id="rule-preview" class="rule-preview"></div><button class="primary" ${session.user.role==='viewer'?'disabled':''}>执行3NF合成 ↗</button></form><p class="help">分解严格使用委托日期当天的规则：同一天的新报告取更正后的规则；已受理报告即使尚未计算完成，也沿用受理时冻结的原规则。</p></section></div>`;
}
