from pydantic import BaseModel,Field,field_validator
from datetime import date
class RuleLine(BaseModel):
    lhs:list[str]=Field(default_factory=list,max_length=10)
    rhs:list[str]=Field(min_length=1,max_length=10)
    note:str=Field(default='',max_length=300)
    @field_validator('lhs','rhs')
    @classmethod
    def valid_attributes(cls,v):
        if len(set(v))!=len(v) or any(not x.strip() or len(x)>40 for x in v): raise ValueError('规则属性不能为空或重复')
        return v
class CorrectionInput(BaseModel):
    relation_id:int=Field(gt=0)
    effective_from:date
    entries:list[RuleLine]=Field(min_length=1,max_length=64)
    correction_note:str=Field(default='',max_length=300)
    idempotency_key:str|None=Field(default=None,max_length=80)
class BaselineInput(BaseModel):
    relation_id:int=Field(gt=0)
    effective_from:date
    idempotency_key:str|None=Field(default=None,max_length=80)
