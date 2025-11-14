import os
import json
import time
import logging
from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from main import retrieve, answer_from_retrieval
from guards import guard_question, api_rate_limiter, whatsapp_rate_limiter
from telemetry import log_interaction

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
LOG = logging.getLogger("investochat.service")

DEFAULT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
WORKSPACE = Path(__file__).parent / "workspace"
ROUTES_PATH = WORKSPACE / "whatsapp_routes.json"
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
DEFAULT_PROJECT_ID = os.getenv("DEFAULT_PROJECT_ID")

app = FastAPI(title="InvestoChat Retrieval API", version="0.1.0")

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve floor plan images and brochure pages
app.mount("/images", StaticFiles(directory="outputs"), name="images")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2)
    project_id: Optional[int] = Field(None, description="Restrict search to this project id")
    k: int = Field(3, ge=1, le=10)
    overfetch: int = Field(24, ge=3, le=50)
    model: Optional[str] = Field(None, description="Override chat completion model")


class AskResponse(BaseModel):
    answer: str
    mode: str
    sources: list
    latency_ms: int


class RetrieveRequest(BaseModel):
    question: str
    project_id: Optional[int] = None
    k: int = 3
    overfetch: int = 24


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/retrieve")
def api_retrieve(payload: RetrieveRequest):
    allowed, reason = guard_question(payload.question)
    if not allowed:
        raise HTTPException(400, reason)
    start = time.perf_counter()
    result = retrieve(
        payload.question,
        k=payload.k,
        overfetch=payload.overfetch,
        project_id=payload.project_id,
    )
    latency = int((time.perf_counter() - start) * 1000)
    LOG.info("retrieve project=%s mode=%s latency_ms=%s", payload.project_id, result["mode"], latency)
    log_interaction(
        channel="api-retrieve",
        user_id=f"api:{payload.project_id or 'global'}",
        project_id=payload.project_id,
        question=payload.question,
        answer="[context-only]",
        mode=result["mode"],
        latency_ms=latency,
    )
    return {"latency_ms": latency, **result}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    allowed, reason = guard_question(payload.question)
    if not allowed:
        raise HTTPException(400, reason)
    limit_key = f"api:{payload.project_id or 'global'}"
    retry_after = api_rate_limiter.check(limit_key)
    if retry_after:
        raise HTTPException(429, f"Rate limit exceeded. Retry after {retry_after}s")
    start = time.perf_counter()
    retrieval = retrieve(
        payload.question,
        k=payload.k,
        overfetch=payload.overfetch,
        project_id=payload.project_id,
    )
    answer = answer_from_retrieval(
        payload.question,
        retrieval,
        model=payload.model or DEFAULT_MODEL,
    )
    latency = int((time.perf_counter() - start) * 1000)
    LOG.info(
        "ask project=%s mode=%s latency_ms=%s",
        payload.project_id,
        answer["mode"],
        latency,
    )
    log_interaction(
        channel="api",
        user_id=limit_key,
        project_id=payload.project_id,
        question=payload.question,
        answer=answer["answer"],
        mode=answer["mode"],
        latency_ms=latency,
    )
    return {
        "answer": answer["answer"],
        "mode": answer["mode"],
        "sources": answer["sources"],
        "latency_ms": latency,
    }


def _load_routes() -> dict:
    if not ROUTES_PATH.exists():
        return {}
    try:
        return json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        LOG.error("failed to read %s: %s", ROUTES_PATH, exc)
        return {}


def _default_project() -> Optional[int]:
    if not DEFAULT_PROJECT_ID:
        return None
    try:
        return int(DEFAULT_PROJECT_ID)
    except ValueError:
        LOG.error("DEFAULT_PROJECT_ID must be an integer, got %s", DEFAULT_PROJECT_ID)
        return None


def resolve_project(phone: Optional[str]) -> Optional[int]:
    if not phone:
        return _default_project()
    routes = _load_routes()
    if phone in routes:
        return int(routes[phone])
    return _default_project()


def extract_whatsapp_payload(payload: dict) -> Optional[dict]:
    entries = payload.get("entry") or []
    for entry in entries:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            messages = value.get("messages") or []
            contacts = value.get("contacts") or []
            if not messages:
                continue
            msg = messages[0]
            if msg.get("type") != "text":
                continue
            text = msg.get("text", {}).get("body", "")
            if not text:
                continue
            sender = msg.get("from")
            profile = contacts[0].get("profile", {}).get("name") if contacts else None
            return {"from": sender, "text": text.strip(), "name": profile}
    return None


def format_sources(sources: list) -> Optional[str]:
    if not sources:
        return None
    src = sources[0]
    page = src.get("page")
    label = src.get("source") or src.get("source_path")
    if page and label:
        return f"{label} (p.{page})"
    if label:
        return str(label)
    if page:
        return f"Brochure p.{page}"
    return None


def format_whatsapp_reply(answer: dict) -> str:
    lines = [answer["answer"]]
    source_text = format_sources(answer.get("sources") or [])
    if source_text and answer["answer"].strip().lower() != "not in the documents.":
        lines.append(f"Source: {source_text}")
    if answer["answer"].strip().lower() == "not in the documents.":
        lines.append("I'll connect you with an advisor for more details.")
    return "\n\n".join(lines)


def send_whatsapp_message(to: str, text: str) -> dict:
    if not (WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID):
        LOG.warning("missing WhatsApp creds; simulated reply to %s: %s", to, text)
        return {"status": "simulated"}
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if not resp.ok:
        LOG.error("WhatsApp send failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(resp.status_code, "WhatsApp send failed")
    return resp.json()


@app.get("/whatsapp/webhook")
def whatsapp_verify(
    hub_mode: Optional[str] = None,
    hub_challenge: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
):
    if hub_mode == "subscribe" and hub_challenge:
        if WHATSAPP_VERIFY_TOKEN and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
            return Response(content=hub_challenge, media_type="text/plain")
        raise HTTPException(403, "Invalid verify token")
    return {"status": "ok"}


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    message = extract_whatsapp_payload(payload)
    if not message:
        LOG.info("webhook received non-text payload")
        return {"status": "ignored"}
    allowed, reason = guard_question(message["text"])
    if not allowed:
        LOG.warning("guard blocked message from %s: %s", message.get("from"), reason)
        if message.get("from"):
            send_whatsapp_message(message["from"], reason)
        return {"status": "blocked"}
    retry_after = whatsapp_rate_limiter.check(message.get("from") or "anon")
    if retry_after:
        if message.get("from"):
            send_whatsapp_message(message["from"], f"Too many questions at once. Try again in {retry_after} seconds.")
        return {"status": "rate-limited"}
    project_id = resolve_project(message.get("from"))
    if not project_id:
        LOG.warning("no project mapping for %s", message.get("from"))
        if message.get("from"):
            send_whatsapp_message(message["from"], "Thanks for reaching out. An advisor will contact you shortly.")
        return {"status": "routed-to-human"}
    LOG.info("WhatsApp inbound from %s project=%s", message["from"], project_id)
    retrieval = retrieve(message["text"], project_id=project_id)
    answer = answer_from_retrieval(message["text"], retrieval, model=DEFAULT_MODEL)
    reply = format_whatsapp_reply(answer)
    send_whatsapp_message(message["from"], reply)
    log_interaction(
        channel="whatsapp",
        user_id=message["from"],
        project_id=project_id,
        question=message["text"],
        answer=answer["answer"],
        mode=answer["mode"],
        latency_ms=0,
    )
    return {"status": "sent", "mode": answer["mode"]}


# Convenience entry point for `uvicorn service:app --reload`
def get_app():
    return app
