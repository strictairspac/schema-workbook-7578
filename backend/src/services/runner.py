"""单个分解任务的执行逻辑，供 worker 循环与测试复用。"""
import os,json,hashlib,traceback
from pathlib import Path
from src.config.database import Session
from src.models.entities import Report
from src.services.normalization import analyze
ARTIFACT_DIR=os.getenv('ARTIFACT_DIR','/artifacts')
def handle_job(ident):
    try:
        with Session() as db:
            obj=db.get(Report,ident);obj.status='running';db.commit();snapshot=obj.input_snapshot
        result=analyze(snapshot['relation']['attributes'],snapshot['dependencies'])
        provenance=snapshot.get('rule_provenance')
        if provenance:
            # 报告可查所用生效期与规则；溯源并入校验和，保证输入-版本-结果一致
            result['rule_provenance']=provenance
            result['frozen_rules']=snapshot['dependencies']
            result['checksum']=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        with Session() as db:
            obj=db.get(Report,ident);obj.result=result;obj.status='completed';db.commit()
        Path(ARTIFACT_DIR).mkdir(parents=True,exist_ok=True)
        Path(f'{ARTIFACT_DIR}/report-{ident}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception as e:
        traceback.print_exc()
        with Session() as db:
            obj=db.get(Report,ident)
            if obj:obj.status='failed';obj.error=str(e);db.commit()
