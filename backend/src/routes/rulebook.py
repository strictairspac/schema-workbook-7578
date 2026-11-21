from datetime import date as date_type
from fastapi import APIRouter,Depends,HTTPException
from src.config.database import db_session
from src.utils.security import current,writer
from src.schemas.rulebook import CorrectionInput,BaselineInput
from src.services import rulebook as service
router=APIRouter()
@router.get('/rule-periods')
def listing(relation_id:int|None=None,db=Depends(db_session),user=Depends(current)):
    return service.listing(db,relation_id)
@router.post('/rule-periods/baseline',status_code=201)
def baseline(data:BaselineInput,db=Depends(db_session),user=Depends(writer)):
    return service.register_baseline(db,data.relation_id,data.effective_from,user,data.idempotency_key)
@router.post('/rule-periods/corrections',status_code=201)
def correction(data:CorrectionInput,db=Depends(db_session),user=Depends(writer)):
    return service.register_correction(db,data,user)
@router.get('/rule-periods/effective')
def effective(relation_id:int,on_date:str,db=Depends(db_session),user=Depends(current)):
    try:on=date_type.fromisoformat(on_date)
    except ValueError:raise HTTPException(422,'日期格式应为 YYYY-MM-DD')
    return service.coverage(db,relation_id,on)
