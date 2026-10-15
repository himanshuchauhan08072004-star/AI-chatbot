from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .engine import ChatEngine

STATIC = Path(__file__).resolve().parent.parent / "static"
app = FastAPI(title="CodeAlpha AI Chatbot")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
engine = ChatEngine()


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


@app.post("/api/chat")
def chat(body: ChatIn):
    return engine.reply(body.message)


@app.get("/api/health")
def health():
    return {"status": "ok", "intents": len(engine.intents)}


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
