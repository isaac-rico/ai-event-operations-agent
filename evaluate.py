"""Evaluate through the normal HTTP handler. Live mode makes paid requests."""
import json
import math
import os
import statistics
import tempfile
import time
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
from eventops.web import app

def evaluate():
    cases=json.loads((Path(__file__).parent/"tests/cases.json").read_text())
    timings=[]
    passed=routes=errors=0
    failures=[]
    with tempfile.TemporaryDirectory() as folder:
        os.environ["EVENTOPS_DB"]=str(Path(folder)/"eval.db")
        with TestClient(app) as client:
            for case in cases:
                start=time.perf_counter()
                response=client.post("/chat",json={"question":case["question"],"session":str(uuid4())})
                timings.append(1000*(time.perf_counter()-start))
                data=response.json()
                rows=data.get("evidence",[])
                routed=(data.get("tool"),data.get("event"))==(case["tool"],case["event"])
                routes+=routed
                errors+=response.status_code!=200
                field=case["field"]
                correct=(len(rows)==case["value"] if field=="length" else
                         bool(rows) and rows[0].get(field)==case["value"] if field else not rows)
                if routed and correct:
                    passed+=1
                else:
                    failures.append(case["question"])
    return dict(mode=os.getenv("EVENTOPS_MODE","demo"),cases=len(cases),passed=passed,
                route_accuracy=routes/len(cases),case_accuracy=passed/len(cases),
                http_error_rate=errors/len(cases),median_ms=round(statistics.median(timings),2),
                p95_ms=round(sorted(timings)[math.ceil(.95*len(cases))-1],2),failures=failures)

if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
