from pathlib import Path
from src.services.reports import queue
from src.services.runner import handle_job
while True:
    Path('/tmp/worker-heartbeat').touch()
    item=queue.blpop('schemaworkbook:queue',timeout=2)
    if not item:continue
    handle_job(int(item[1]))
