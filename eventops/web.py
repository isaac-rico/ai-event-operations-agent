import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .agent import respond
from .store import initialize, AS_OF

@asynccontextmanager
async def lifespan(app):
    initialize()
    yield

app = FastAPI(title="Event Operations Agent",lifespan=lifespan)

class Question(BaseModel):
    session: UUID
    question: str = Field(min_length=1,max_length=1000)

@app.get("/")
def index():
    return FileResponse(Path(__file__).with_name("index.html"))

@app.post("/chat")
async def chat(body: Question):
    try:
        return {"as_of":AS_OF.isoformat(), **await respond(body.question,str(body.session))}
    except Exception as exc:
        logging.getLogger(__name__).error("Agent request failed (%s)",type(exc).__name__)
        raise HTTPException(503,"The request could not complete. Check the local database and model configuration.") from None
