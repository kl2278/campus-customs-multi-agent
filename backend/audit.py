"""Append-only audit trail: output/audit_trail.json (a JSON array)."""

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from filelock import FileLock

from backend.config import audit_path
from backend.models import AuditEntry

SECRET_KEY_PATTERN = re.compile(r"key|token|secret|password|authorization", re.IGNORECASE)
PERSONAL_KEYS = {"requester", "email", "phone"}
SUMMARY_LIMIT = 300


def _scrub(value: Any) -> Any:
    """Redact secret-looking keys and personal-data keys, recursively."""
    if isinstance(value, dict):
        return {
            k: "[redacted]" if (SECRET_KEY_PATTERN.search(k) or k in PERSONAL_KEYS) else _scrub(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value


def summarize(value: Any, limit: int = SUMMARY_LIMIT) -> str:
    """Short, redacted text for a tool result or argument blob."""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            pass
    text = value if isinstance(value, str) else json.dumps(_scrub(value), default=str)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def scrub_arguments(args: Any) -> dict[str, Any] | None:
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            return {"raw": summarize(args)}
    return _scrub(args) if isinstance(args, dict) else None


class AuditLog:
    """Appends entries to the audit file under a file lock, writing atomically."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else audit_path()
        self._lock = FileLock(str(self.path) + ".lock")

    def append(self, **fields: Any) -> AuditEntry:
        entry = AuditEntry(timestamp=datetime.now(timezone.utc).isoformat(), **fields)
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            entries = json.loads(self.path.read_text()) if self.path.exists() else []
            if not isinstance(entries, list):
                raise ValueError("audit file is not a JSON array; refusing to overwrite it")
            entries.append(entry.model_dump())
            fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".audit-", suffix=".tmp")
            try:
                with os.fdopen(fd, "w") as handle:
                    json.dump(entries, handle, indent=2)
                os.replace(tmp, self.path)
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
        return entry

    def ensure_exists(self) -> None:
        """Create the file as [] if it does not exist yet (never wipes an existing one)."""
        with self._lock:
            if not self.path.exists():
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text("[]")


def append_reset_marker(log: AuditLog | None = None) -> AuditEntry:
    """Record that the working copy was reset. The audit file itself is never wiped."""
    return (log or AuditLog()).append(
        run_id="reset", ticket_id=None, agent="system", depth=0, step=0, kind="reset",
        result_summary="Working copy restored from the original database.",
    )


def read_events(
    path: Path | None = None,
    *,
    ticket_id: int | None = None,
    run_id: str | None = None,
    since: datetime | None = None,
    limit: int = 100,
    include_before_reset: bool = False,
) -> list[dict[str, Any]]:
    """Read audit events without ever modifying the file.

    A missing or empty file gives []. By default only events after the most recent
    reset marker are returned (the marker itself is not). With `since`, the oldest
    `limit` events newer than it are returned so a poller never skips any; without
    it, the newest `limit` events are returned. Both come back oldest first.
    """
    path = Path(path) if path else audit_path()
    if not path.exists():
        return []
    text = path.read_text().strip()
    if not text:
        return []
    events = json.loads(text)  # atomic replace on write means a reader never sees a partial file
    if not isinstance(events, list):
        raise ValueError("audit file is not a JSON array")
    if not include_before_reset:
        last_reset = max((i for i, e in enumerate(events) if e.get("kind") == "reset"), default=-1)
        events = events[last_reset + 1:]
    if ticket_id is not None:
        events = [e for e in events if e.get("ticket_id") == ticket_id]
    if run_id is not None:
        events = [e for e in events if e.get("run_id") == run_id]
    if since is not None:
        events = [e for e in events if datetime.fromisoformat(e["timestamp"]) > since]
        return events[:limit]
    return events[-limit:]
