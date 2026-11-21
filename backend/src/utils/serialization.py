from datetime import datetime,date,timezone
def record(obj):
    result={}
    for col in obj.__table__.columns:
        value=getattr(obj,col.name)
        if isinstance(value,datetime):
            if value.tzinfo is None:value=value.replace(tzinfo=timezone.utc)
            value=value.isoformat()
        elif isinstance(value,date):
            value=value.isoformat()
        result[col.name]=value
    return result
