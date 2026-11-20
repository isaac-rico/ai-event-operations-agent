import json
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from eventops.web import app
from eventops.store import initialize
from eventops.tools import retrieve

CASES=json.loads(Path(__file__).with_name("cases.json").read_text())

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv("EVENTOPS_DB",str(tmp_path/"test.db"))
    monkeypatch.setenv("EVENTOPS_MODE","demo")
    with TestClient(app) as c:
        yield c

def ask(client,q,s=None):
    return client.post("/chat",json={"question":q,"session":str(s or uuid4())})

@pytest.mark.parametrize("case",CASES,ids=lambda c:c["question"])
def test_case(client,case):
    res=ask(client,case["question"])
    assert res.status_code==200
    data=res.json()
    assert (data["tool"],data["event"])==(case["tool"],case["event"])
    rows=data["evidence"]
    field=case["field"]
    if field=="length":
        assert len(rows)==case["value"]
    elif field:
        assert rows[0][field]==case["value"]
    else:
        assert rows==[]

def test_memory(client):
    s=uuid4()
    ask(client,"Show Systems Summit performance",s)
    assert ask(client,"What is its deadline?",s).json()["event"]=="summit"
    assert ask(client,"What is its deadline?").json()["tool"]=="clarify"
    ask(client,"Remember a 3-day deadline window",s)
    assert len(ask(client,"Show deadlines").json()["evidence"])==2

def test_failure(client,monkeypatch):
    def broken(*args):
        raise OSError("secret path")
    monkeypatch.setattr("eventops.agent.retrieve",broken)
    res=ask(client,"Rank risks")
    assert res.status_code==503 and "secret path" not in res.text

def test_reseed(client):
    initialize()
    assert retrieve("performance","summit",7)[0]["confirmed"]==84

def test_access(client):
    with pytest.raises(ValueError):
        retrieve("update","all",7)
    assert retrieve("performance","' OR 1=1 --",7)==[]

def test_ui_input(client):
    assert "Ask agent" in client.get("/").text
    assert ask(client,"x"*1001).status_code==422

def test_sdk_executes_tool(client):
    import asyncio
    from agents import Model, ModelResponse, Usage
    from openai.types.responses import ResponseFunctionToolCall
    from eventops.live import select

    class FixtureModel(Model):
        async def get_response(self,*args,**kwargs):
            call=ResponseFunctionToolCall(type="function_call",name="performance",
                                          call_id="fixture",arguments='{"event":"summit"}')
            return ModelResponse(output=[call],usage=Usage(),response_id="fixture")

        def stream_response(self,*args,**kwargs):
            raise NotImplementedError

    tool,event,rows=asyncio.run(select("Summit registrations?",[],7,test_model=FixtureModel()))
    assert (tool,event,rows[0]["confirmed"])==("performance","summit",84)
