"""规则生效期服务：按业务日期解析规则版本；更正以完整规则状态登记新生效期，历史期不可变。"""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from src.models.entities import Relation,Dependency,RulePeriod,RuleEntry,Audit
from src.utils.serialization import record

def _periods(db,relation_id):
    return list(db.scalars(select(RulePeriod).where(RulePeriod.relation_id==relation_id).order_by(RulePeriod.effective_from)))

def _entries(db,period_id):
    return [{'lhs':x.lhs,'rhs':x.rhs,'note':x.note} for x in db.scalars(select(RuleEntry).where(RuleEntry.period_id==period_id).order_by(RuleEntry.id))]

def _period_dict(db,p):
    return {**record(p),'entries':_entries(db,p.id)}

def _require_relation(db,relation_id):
    relation=db.get(Relation,relation_id)
    if not relation:raise HTTPException(404,'关系不存在')
    return relation

def _validate_entries(relation,entries):
    attrs=set(relation.attributes)
    seen=set()
    for line in entries:
        if not set(line.get('lhs',[])+line.get('rhs',[]))<=attrs:
            raise HTTPException(422,'规则引用了关系外属性，请对照属性集合修改')
        key=(tuple(line['lhs']),tuple(line['rhs']))
        if key in seen:raise HTTPException(422,'同一规则在生效期内重复登记，请合并后重试')
        seen.add(key)
    if len(entries)>64:raise HTTPException(422,'最多64条函数依赖，请先合并重复规则')

def coverage(db,relation_id,on_date):
    """返回关系在 on_date（业务发生日）适用的生效期与完整规则；缺档则拦下并指出缺口。"""
    _require_relation(db,relation_id)
    periods=_periods(db,relation_id)
    if not periods:
        raise HTTPException(422,f'该关系尚未建立任何规则生效期，{on_date} 无规则可用；请先补录生效期')
    chosen=None
    for p in periods:
        if p.effective_from<=on_date:chosen=p
        else:break
    if chosen is None:
        first=periods[0]
        raise HTTPException(422,f'规则日期缺档：委托日期 {on_date} 早于最早生效期 {first.effective_from}，'
                                f'缺口区间 {on_date} 至 {first.effective_from}（不含），请补录覆盖该日期的生效期')
    return {'relation_id':relation_id,'on_date':on_date.isoformat(),'period_id':chosen.id,
            'effective_from':chosen.effective_from.isoformat(),'source':chosen.source,
            'correction_note':chosen.correction_note,'entries':_entries(db,chosen.id)}

def register_baseline(db,relation_id,effective_from,user,idempotency_key=None):
    """基线生效期：把依赖登记簿中已确认的规则冻结为首个不可变生效期。"""
    relation=_require_relation(db,relation_id)
    if idempotency_key:
        existing=db.scalar(select(RulePeriod).where(RulePeriod.idempotency_key==idempotency_key))
        if existing:
            if existing.relation_id!=relation.id or existing.effective_from!=effective_from:
                raise HTTPException(409,'幂等键已用于其他关系或生效日期的登记，请更换键值')
            return {**_period_dict(db,existing),'idempotent_replay':True}
    if _periods(db,relation.id):
        raise HTTPException(409,f'关系 {relation.code} 已存在生效期，基线只能建立一次；后续变更请使用补录更正')
    drafts=list(db.scalars(select(Dependency).where(Dependency.relation_id==relation.id)))
    entries=[{'lhs':d.lhs,'rhs':d.rhs,'note':d.note or ''} for d in drafts]
    _validate_entries(relation,entries)
    period=RulePeriod(relation_id=relation.id,effective_from=effective_from,source='baseline',
                      correction_note='基线生效期：承接依赖登记簿已确认规则',idempotency_key=idempotency_key)
    try:
        db.add(period);db.flush()
        for line in entries:
            db.add(RuleEntry(period_id=period.id,lhs=line['lhs'],rhs=line['rhs'],note=line['note']))
        db.add(Audit(actor=user.email,action=f'建立基线生效期 {relation.code} 生效日 {effective_from}（规则 {len(entries)} 条）'))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'并发登记撞在同一关系与日期上，本次未生效；请刷新后重试')
    return {**_period_dict(db,period),'idempotent_replay':False}

def register_correction(db,data,user):
    """登记更正：拆出生效期，未改规则原样沿用；同日并发更正冲突，幂等键保证重试不重复登记。"""
    relation=_require_relation(db,data.relation_id)
    entries=[e.model_dump() for e in data.entries]
    _validate_entries(relation,entries)
    effective_from=data.effective_from
    # 幂等：同一更正请求重试，直接返回已登记生效期，不重复登记
    if data.idempotency_key:
        existing=db.scalar(select(RulePeriod).where(RulePeriod.idempotency_key==data.idempotency_key))
        if existing:
            if existing.relation_id!=relation.id or existing.effective_from!=effective_from:
                raise HTTPException(409,'幂等键已用于其他关系或生效日期的更正，请更换键值')
            return {**_period_dict(db,existing),'idempotent_replay':True}
    periods=_periods(db,relation.id)
    if any(p.effective_from==effective_from for p in periods):
        raise HTTPException(409,f'规则 {relation.code} 在 {effective_from} 已存在生效期，'
                                f'同一生效日期的并发更正冲突；请刷新确认后改用其他日期，或在该日期之后补录')
    if not periods:
        raise HTTPException(422,'该关系尚无基线生效期，无法更正；请先由关系草案建立基线规则')
    if effective_from<periods[0].effective_from:
        raise HTTPException(422,f'更正日期 {effective_from} 早于最早生效期（基线）{periods[0].effective_from}，'
                                f'不能在基线之前补录；如需更早的规则覆盖，请重建基线生效期')
    next_period=next((p for p in periods if p.effective_from>effective_from),None)
    base_period=next_period or periods[-1]
    period=RulePeriod(relation_id=relation.id,effective_from=effective_from,source='correction',
                      correction_note=data.correction_note,idempotency_key=data.idempotency_key)
    try:
        db.add(period);db.flush()
        for line in entries:
            db.add(RuleEntry(period_id=period.id,lhs=line['lhs'],rhs=line['rhs'],note=line.get('note','')))
        db.add(Audit(actor=user.email,action=(f'登记规则更正 {relation.code} 生效日 {effective_from}'
                                              f'（承接生效期 #{base_period.id}，规则 {len(entries)} 条）')))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'并发更正撞在同一规则与日期上，本次登记未生效；请刷新生效期时间线后重试')
    return {**_period_dict(db,period),'idempotent_replay':False}

def listing(db,relation_id=None):
    q=select(RulePeriod).order_by(RulePeriod.relation_id,RulePeriod.effective_from)
    if relation_id is not None:q=q.where(RulePeriod.relation_id==relation_id)
    periods=[_period_dict(db,p) for p in db.scalars(q)]
    gaps=[]
    relation_ids=sorted({p['relation_id'] for p in periods})
    for rid in relation_ids:
        chain=[p for p in periods if p['relation_id']==rid]
        relation=db.get(Relation,rid)
        gaps.append({'relation_id':rid,'relation_code':relation.code if relation else None,
                     'earliest_effective_from':chain[0]['effective_from'],
                     'uncovered_before':chain[0]['effective_from'],
                     'period_count':len(chain)})
    return {'periods':periods,'coverage':gaps}
