import logging
import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import llm, store
from .engine import ChatEngine
from .ratelimit import RateLimiter
from .retrieval import Retriever

log = logging.getLogger("chatbot")
STATIC = Path(__file__).resolve().parent.parent / "static"
SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
MAX_LEN = 500

app = FastAPI(title="CodeAlpha AI Chatbot")
origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if origins:  # same-origin by default; set ALLOWED_ORIGINS to embed the widget on other sites
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "DELETE"],
                       allow_headers=["Content-Type"])

engine = ChatEngine()
retriever = Retriever()
limiter = RateLimiter(int(os.getenv("RATE_LIMIT", "20")), float(os.getenv("RATE_WINDOW", "60")))


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'")
    return resp


class ChatIn(BaseModel):
    message: str = Field(..., max_length=MAX_LEN)
    session_id: str

    @field_validator("message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message is empty")
        return v

    @field_validator("session_id")
    @classmethod
    def valid_session(cls, v: str) -> str:
        if not SESSION_RE.match(v):
            raise ValueError("invalid session_id")
        return v


def client_ip(request: Request) -> str:
    if os.getenv("TRUST_PROXY") == "1":
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def llm_messages(session_id: str) -> list[dict]:
    """Recent history as alternating user/assistant turns, starting with a user turn."""
    out: list[dict] = []
    for m in store.history(session_id, 8):
        if out and out[-1]["role"] == m["role"]:
            out[-1]["content"] += "\n" + m["content"]
        elif out or m["role"] == "user":
            out.append({"role": m["role"], "content": m["content"]})
    return out


def rules_answer(message: str, hits) -> dict:
    """Clearly-labelled non-AI fallback: intent match, else best document passage, else 'don't know'."""
    tag, _ = engine.predict(message)
    if tag:
        return {"reply": engine.reply(message)["reply"], "mode": "rules", "sources": []}
    if hits:
        chunk = hits[0][0]
        return {"reply": chunk.text, "mode": "retrieval", "sources": [chunk.title]}
    return {"reply": engine.fallback[0], "mode": "fallback", "sources": []}


@app.post("/api/chat")
def chat(body: ChatIn, request: Request):
    if not limiter.allow(client_ip(request)):
        raise HTTPException(429, "Too many messages. Please wait a moment.", headers={"Retry-After": "60"})
    hits = retriever.search(body.message)
    try:
        store.add(body.session_id, "user", body.message)
    except Exception:
        log.exception("history store unavailable")
    result = None
    if llm.configured():
        context = "\n\n".join(f"[{c.title}] {c.text}" for c, _ in hits)
        msgs = llm_messages(body.session_id) or [{"role": "user", "content": body.message}]
        try:
            result = {"reply": llm.generate(msgs, context), "mode": "ai", "sources": [c.title for c, _ in hits]}
        except llm.LLMUnavailable as exc:
            log.warning("LLM unavailable (%s); using fallback", exc)
    if result is None:
        result = rules_answer(body.message, hits)
        result["ai_unavailable"] = llm.configured()  # key set but call failed
    try:
        store.add(body.session_id, "assistant", result["reply"], result["mode"])
    except Exception:
        log.exception("history store unavailable")
    return result


@app.get("/api/history/{session_id}")
def get_history(session_id: str):
    if not SESSION_RE.match(session_id):
        raise HTTPException(422, "invalid session_id")
    try:
        return {"messages": store.history(session_id)}
    except Exception:
        log.exception("history read failed")
        return {"messages": []}


@app.delete("/api/history/{session_id}")
def delete_history(session_id: str):
    if not SESSION_RE.match(session_id):
        raise HTTPException(422, "invalid session_id")
    return {"deleted": store.clear(session_id)}


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_configured": llm.configured(),
            "model": os.getenv("LLM_MODEL", "claude-sonnet-5-5") if llm.configured() else None,
            "intents": len(engine.intents), "document_chunks": len(retriever.chunks)}


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("unhandled error")
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
