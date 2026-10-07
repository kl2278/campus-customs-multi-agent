"""Append-only audit trail: output/audit_trail.json (a JSON array)."""

import json
import os
import re
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from filelock import FileLock

from backend.config import audit_path
from backend.models import AuditEntry
from mcp_server.db import connect_ro

SECRET_KEY_PATTERN = re.compile(r"key|token|secret|password|authorization", re.IGNORECASE)
PERSONAL_KEYS = {"requester", "email", "phone"}
SUMMARY_LIMIT = 300


CUSTOMER_LABEL = "[customer]"
PERSON_WORD = re.compile(r"^[A-Z][a-z'\u2019-]+$")
GREETING = re.compile(r"(?im)^([ \t]*(?:hi|hello|hey|dear)[ \t]+)[^,\n!:]{1,60}(?=[,!:])")


def known_names() -> list[str]:
    """Customer names to redact, read from the tickets table (requester) right now.

    The full requester text is always included. For person-like names (two or three
    capitalised words) each word is included too, so a first name alone is caught.
    Requesters that are the lease's landlord or a vendor are businesses, not personal
    data, and are left alone. Nothing is hard-coded: if the table can't be read, no
    names are known and only the greeting-line rule applies.
    """
    try:
        with closing(connect_ro()) as conn:
            requesters = [r[0] for r in conn.execute("SELECT DISTINCT requester FROM tickets")]
            businesses = {r[0] for r in conn.execute("SELECT landlord FROM leases")}
            businesses |= {r[0] for r in conn.execute("SELECT name FROM vendors")}
    except Exception:
        return []
    names: set[str] = set()
    for full in requesters:
        full = (full or "").strip()
        if not full or full in businesses:
            continue
        names.add(full)
        words = full.split()
        if 2 <= len(words) <= 3 and all(PERSON_WORD.match(w) for w in words):
            names.update(w for w in words if len(w) >= 3)
    return sorted(names, key=len, reverse=True)


def redact_text(text: str, names: list[str] | None = None) -> str:
    """Replace customer names and the greeting line of a message with a neutral label."""
    for name in known_names() if names is None else names:
        text = re.sub(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", CUSTOMER_LABEL, text, flags=re.IGNORECASE)
    return GREETING.sub(lambda m: m.group(1) + CUSTOMER_LABEL, text)


def _scrub(value: Any, names: list[str] | None = None) -> Any:
    """Redact secret-looking keys, personal-data keys and customer names in text, recursively."""
    names = known_names() if names is None else names
    if isinstance(value, dict):
        return {
            k: "[redacted]" if (SECRET_KEY_PATTERN.search(k) or k in PERSONAL_KEYS) else _scrub(v, names)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub(v, names) for v in value]
    if isinstance(value, str):
        return redact_text(value, names)
    return value


def redact_event(event: dict[str, Any], names: list[str] | None = None) -> dict[str, Any]:
    """A copy of an audit event with customer names removed from every text field."""
    names = known_names() if names is None else names
    return {k: (_scrub(v, names) if isinstance(v, (dict, list, str)) and k not in ("timestamp", "run_id", "agent", "kind", "tool_name") else v)
            for k, v in event.items()}


SECRET_ENV_NAMES = ("PORTKEY_API_KEY", "PORTKEY_PROVIDER", "PORTKEY_VIRTUAL_KEY", "PORTKEY_CONFIG")


def scrub_secrets(text: str) -> str:
    """Remove the values of the Portkey env vars from free text (errors, logs)."""
    for name in SECRET_ENV_NAMES:
        value = os.environ.get(name)
        if value and len(value) >= 4:
            text = text.replace(value, "[removed]")
    return text


def summarize(value: Any, limit: int = SUMMARY_LIMIT) -> str:
    """Short, redacted text for a tool result or argument blob."""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            pass
    # Redact BEFORE shortening, so a name cut in half by the limit can't slip through.
    text = redact_text(value) if isinstance(value, str) else json.dumps(_scrub(value), default=str)
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
        names = known_names()  # read from the tickets table at write time
        for key in ("arguments", "result_summary", "message"):
            if fields.get(key) is not None:
                fields[key] = _scrub(fields[key], names)
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
        chosen = events[:limit]
    else:
        chosen = events[-limit:]
    names = known_names()  # also redact at read time, so older entries are never served with names
    return [redact_event(e, names) for e in chosen]
