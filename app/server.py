from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI

from .pipeline import run_pipeline
from .schemas import EmailRequest, EmailResponse
from tools import chat_ingest

app = FastAPI()
MODEL_READY = True
CHAT_QUEUE_PATH = Path("data/email_queue.xlsx")


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {"status": "ok", "model_loaded": MODEL_READY}


@app.post("/reply", response_model=EmailResponse)
def reply(req: EmailRequest) -> EmailResponse:
    metadata: Dict[str, Any] = {}
    if req.expected_keys:
        metadata["expected_keys"] = req.expected_keys
    if req.customer_email:
        metadata["customer_email"] = req.customer_email
    if req.subject:
        metadata["subject"] = req.subject
    result = run_pipeline(req.email, metadata=metadata or None)
    return EmailResponse(**result)


@app.post("/chat/enqueue")
def enqueue_chat(payload: Dict[str, Any]) -> Dict[str, int]:
    message = {
        "conversation_id": payload.get("conversation_id") or "api-web",
        "text": payload.get("text") or payload.get("message") or "",
        "end_user_handle": payload.get("end_user_handle") or payload.get("user") or "api-user",
        "channel": payload.get("channel") or "web_chat",
    }
    count = chat_ingest.ingest_messages(CHAT_QUEUE_PATH, [message])
    return {"enqueued": count}
