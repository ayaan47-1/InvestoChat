import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

WORKSPACE = Path(__file__).parent / "workspace"
LOG_PATH = WORKSPACE / "events.log"


def log_event(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    entry = {"ts": time.time(), "event": event}
    if payload:
        entry.update(payload)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def log_interaction(channel: str, user_id: str, project_id: Optional[int], question: str, answer: str, mode: str, latency_ms: int) -> None:
    log_event(
        "interaction",
        {
            "channel": channel,
            "user": user_id,
            "project_id": project_id,
            "question": question,
            "answer": answer,
            "mode": mode,
            "latency_ms": latency_ms,
        },
    )
