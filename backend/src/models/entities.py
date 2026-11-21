from sqlalchemy import Column,Integer,String,JSON,DateTime,Date,ForeignKey,Text,UniqueConstraint
from datetime import datetime,timezone
from src.config.database import Base
class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True);email=Column(String(120),unique=True,nullable=False);password=Column(String(300),nullable=False);role=Column(String(20),nullable=False)
class Relation(Base):
    __tablename__='relations'
    id=Column(Integer,primary_key=True);code=Column(String(80),unique=True,nullable=False);title=Column(String(160),nullable=False);attributes=Column(JSON,nullable=False);note=Column(String(300),default='')
class Dependency(Base):
    """规则草稿：基线生效期（baseline）的录入来源；报告不再直接读取本表。"""
    __tablename__='dependencies'
    id=Column(Integer,primary_key=True);relation_id=Column(Integer,ForeignKey('relations.id'),nullable=False);lhs=Column(JSON,nullable=False);rhs=Column(JSON,nullable=False);note=Column(String(300),default='')
class RulePeriod(Base):
    """规则生效期：同一关系同一生效日期只允许登记一次（并发更正冲突的数据库防线）。"""
    __tablename__='rule_periods'
    id=Column(Integer,primary_key=True);relation_id=Column(Integer,ForeignKey('relations.id'),nullable=False)
    effective_from=Column(Date,nullable=False);source=Column(String(20),nullable=False,default='correction')
    correction_note=Column(String(300),default='');idempotency_key=Column(String(80),nullable=True,unique=True)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    __table_args__=(UniqueConstraint('relation_id','effective_from',name='uq_rule_period_relation_date'),)
class RuleEntry(Base):
    """生效期内的完整规则状态（含原样沿用的规则），期内行不可变，保证已受理报告规则永不被改写。"""
    __tablename__='rule_entries'
    id=Column(Integer,primary_key=True);period_id=Column(Integer,ForeignKey('rule_periods.id'),nullable=False)
    lhs=Column(JSON,nullable=False);rhs=Column(JSON,nullable=False);note=Column(String(300),default='')
class Report(Base):
    __tablename__='reports'
    id=Column(Integer,primary_key=True);name=Column(String(120),nullable=False);relation_id=Column(Integer,ForeignKey('relations.id'),nullable=False)
    commission_date=Column(Date,nullable=True)
    status=Column(String(20),nullable=False,default='queued');input_snapshot=Column(JSON,nullable=False);result=Column(JSON,nullable=True);error=Column(Text,nullable=True)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Audit(Base):
    __tablename__='audit_logs'
    id=Column(Integer,primary_key=True);actor=Column(String(120),nullable=False);action=Column(String(160),nullable=False);created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
