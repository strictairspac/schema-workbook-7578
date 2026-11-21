from sqlalchemy import select
from redis import Redis
from fastapi import HTTPException
from src.models.entities import Relation,Report
from src.config.settings import REDIS_URL
from src.constants.enums import RUN_STATES
from src.utils.serialization import record
from .common import save
from . import rulebook
queue=Redis.from_url(REDIS_URL,decode_responses=True)
def listing(db):return [record(x) for x in db.scalars(select(Report).order_by(Report.id.desc()))]
def detail(db,ident):
    obj=db.get(Report,ident)
    if not obj:raise HTTPException(404,'报告不存在')
    return record(obj)
def create(db,data,user):
    relation=db.get(Relation,data.relation_id)
    if not relation:raise HTTPException(404,'关系不存在')
    # 委托分解按业务发生那天（委托日期）的规则；缺档在此拦下并指出缺口
    coverage=rulebook.coverage(db,relation.id,data.commission_date)
    deps=[{'lhs':x['lhs'],'rhs':x['rhs']} for x in coverage['entries']]
    snapshot={'relation':record(relation),'dependencies':deps,
              'rule_provenance':{'commission_date':coverage['on_date'],
                                 'period_id':coverage['period_id'],
                                 'effective_from':coverage['effective_from'],
                                 'source':coverage['source'],
                                 'correction_note':coverage['correction_note'],
                                 'rule_count':len(deps)}}
    payload=data.model_dump()
    obj=Report(**payload,input_snapshot=snapshot,status=RUN_STATES[0])
    result=save(db,obj,user,f"范式分解入队 {data.name}（委托日 {data.commission_date}，生效期 {coverage['effective_from']}）")
    try:queue.rpush('schemaworkbook:queue',str(obj.id))
    except Exception:
        obj.status='failed';obj.error='队列暂时不可用，请重新创建';db.commit();raise HTTPException(503,obj.error)
    return result
