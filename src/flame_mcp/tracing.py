"""Opt-in local timing and outcome trace. It records no Flame names, paths or arguments."""

from __future__ import annotations

import json
import logging
import os
import re
import stat
import time
from contextvars import ContextVar
from typing import Any
from uuid import uuid4

_TRACE = ContextVar[str | None]("finns_flame_trace", default=None)
_LOG = logging.getLogger(__name__)
_OPERATION = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)?")


def _write(path: str, fields: dict[str, Any]) -> None:
    try:
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
        fd = os.open(path, flags, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise OSError("Trace file is not private.")
            payload = json.dumps(fields, separators=(",", ":")).encode("ascii") + b"\n"
            os.write(fd, payload)
        finally:
            os.close(fd)
    except OSError:
        _LOG.warning("The configured local Flame MCP trace could not be written.")


def traced_call(operation: str, call: Any) -> dict[str, Any]:
    path = os.environ.get("FINNS_FLAME_MCP_TRACE")
    if not path:
        return call()
    fields = {
        "pid": os.getpid(),
        "id": uuid4().hex,
        "parent": _TRACE.get(),
        "op": operation if _OPERATION.fullmatch(operation) else "invalid",
    }
    token = _TRACE.set(fields["id"])
    start = time.monotonic_ns()
    _write(path, {**fields, "event": "start", "timeNs": time.time_ns()})
    outcome: dict[str, Any] = {"ok": False, "errorCode": "UNHANDLED"}
    try:
        outcome = call()
        return outcome
    finally:
        journal = outcome.get("journal")
        _write(
            path,
            {
                **fields,
                "event": "finish",
                "timeNs": time.time_ns(),
                "elapsedMs": round((time.monotonic_ns() - start) / 1_000_000, 3),
                "ok": outcome.get("ok"),
                "errorCode": outcome.get("errorCode"),
                "timeoutPhase": outcome.get("timeoutPhase"),
                "journalGroup": journal.get("group") if isinstance(journal, dict) else None,
            },
        )
        _TRACE.reset(token)
