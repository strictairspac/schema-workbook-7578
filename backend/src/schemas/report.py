from pydantic import BaseModel,Field
from datetime import date
class ReportInput(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    relation_id:int=Field(gt=0)
    commission_date:date
