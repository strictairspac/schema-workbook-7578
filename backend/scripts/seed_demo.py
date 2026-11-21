from datetime import date
from sqlalchemy import select,func
from src.config.database import Session,Base,engine
from src.models.entities import User,Relation,Dependency,Report,RulePeriod,RuleEntry
from src.utils.security import password_hash

BASELINE=date(2026,1,1)
CORRECTION_DATE=date(2026,6,1)
# 仅用于演示：A单在 6/1 生效的更正——新增“委托号→检测项”规则，旧规则原样沿用
A_CORRECTION=[(['委托号'],['客户'],'业务确认依赖'),(['检测项'],['方法'],'业务确认依赖'),
              (['委托号','检测项'],['结果'],'业务确认依赖'),(['委托号'],['检测项'],'2026-06-01 补录更正：一份委托登记一个检测项')]

def seed():
    Base.metadata.create_all(engine)
    with Session() as db:
        for role in ('admin','operator','viewer'):
            email=role+'@nanlu.test'
            if not db.scalar(select(User).where(User.email==email)):db.add(User(email=email,password=password_hash('Demo2026!'),role=role))
        cases=[('NL-1117-A','材料检测委托单',['委托号','客户','检测项','方法','结果'],[(['委托号'],['客户']),(['检测项'],['方法']),(['委托号','检测项'],['结果'])]),('NL-1117-B','循环编号与独立属性',['A','B','C'],[(['A'],['B']),(['B'],['A'])]),('NL-1117-C','尚未确认业务依赖',['批号','容器','记录人'],[])]
        for code,title,attrs,fds in cases:
            rel=db.scalar(select(Relation).where(Relation.code==code))
            if not rel:
                rel=Relation(code=code,title=title,attributes=attrs,note='南麓材料实验室 · 09:15 委托表复核');db.add(rel);db.flush()
                for lhs,rhs in fds:db.add(Dependency(relation_id=rel.id,lhs=lhs,rhs=rhs,note='业务确认依赖'))
            # 规则生效期：基线期承接当前依赖草稿；已存在则跳过（按自然键幂等）
            if not db.scalar(select(RulePeriod).where(RulePeriod.relation_id==rel.id,RulePeriod.effective_from==BASELINE)):
                baseline=RulePeriod(relation_id=rel.id,effective_from=BASELINE,source='baseline',correction_note='基线生效期：承接关系草案确认规则')
                db.add(baseline);db.flush()
                base_deps=list(db.scalars(select(Dependency).where(Dependency.relation_id==rel.id)))
                for d in base_deps:db.add(RuleEntry(period_id=baseline.id,lhs=d.lhs,rhs=d.rhs,note=d.note or '业务确认依赖'))
        rel_a=db.scalar(select(Relation).where(Relation.code=='NL-1117-A'))
        if rel_a and not db.scalar(select(RulePeriod).where(RulePeriod.relation_id==rel_a.id,RulePeriod.effective_from==CORRECTION_DATE)):
            corrected=RulePeriod(relation_id=rel_a.id,effective_from=CORRECTION_DATE,source='correction',
                                 correction_note='补录更正：新增委托号→检测项，未改规则照旧',idempotency_key='seed-A-20260601')
            db.add(corrected);db.flush()
            for lhs,rhs,note in A_CORRECTION:db.add(RuleEntry(period_id=corrected.id,lhs=lhs,rhs=rhs,note=note))
        db.commit()
        print({cls.__tablename__:db.scalar(select(func.count()).select_from(cls)) for cls in (User,Relation,Dependency,RulePeriod,RuleEntry,Report)})
if __name__=='__main__':seed()
