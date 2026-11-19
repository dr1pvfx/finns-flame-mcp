from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from types import SimpleNamespace
from typing import Any

import pytest

from flame_mcp.ops import delivery, editorial_review
from flame_mcp.tracing import traced_call
from flame_mcp.types import ServerOpError


class RenameFixture:
    def __init__(self) -> None:
        self.name = "Original Cut"
        self.project = "Fixture"
        self.write_lock = RLock()
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def do(self, op: str, args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((op, kwargs))
        if op == "desktop.info":
            return {
                "ok": True,
                "context": {"projectName": self.project},
                "result": {
                    "type": "PySequence",
                    "name": self.name,
                    "uid": "101",
                    "wiretapId": args["target"]["id"],
                },
            }
        assert kwargs["precondition"] == {"name": self.name}
        self.name = args["name"]
        return {
            "ok": True,
            "result": {"name": self.name},
            "affected": 1,
            "journal": {"group": "fixture-group", "id": "fixture-intent"},
        }


def test_reviewed_rename_uses_readback_and_rejects_replay() -> None:
    rt = RenameFixture()
    args = {"target": {"kind": "wiretap", "id": "fixture"}, "name": "New Cut"}
    preview = editorial_review._preview(args, rt)
    assert rt.name == "Original Cut"

    approved = {**args, "fingerprint": preview.result["fingerprint"]}
    for change in ({"name": "Changed Cut"}, {"fingerprint": "a" * 64}):
        with pytest.raises(ServerOpError, match="changed"):
            editorial_review._apply({**approved, **change}, rt)
    rt.project = "Other"
    with pytest.raises(ServerOpError, match="changed"):
        editorial_review._apply(approved, rt)
    assert all(op == "desktop.info" for op, _ in rt.calls)

    rt.project = "Fixture"
    result = editorial_review._apply(approved, rt)
    assert result.journal == {"group": "fixture-group", "id": "fixture-intent"}
    assert rt.name == "New Cut"
    with pytest.raises(ServerOpError, match="already"):
        editorial_review._apply(approved, rt)
    assert sum(op == "desktop.rename" for op, _ in rt.calls) == 1


def test_anchor_uses_numbered_image_hint_and_omits_paths() -> None:
    ns: dict[str, Any] = {"_v": lambda value: value, "_try": lambda fn: fn()}
    exec(delivery._ANCHOR_SOURCE, ns)
    segment = SimpleNamespace(
        name="Plate",
        file_path="/fixture/private/shot.001001.exr",
        source_in=SimpleNamespace(frame=1001, timecode="00:00:41:17"),
        source_out=SimpleNamespace(frame=1030, timecode="00:00:42:22"),
        record_in=SimpleNamespace(frame=500, timecode="00:00:20:00"),
        start_frame=SimpleNamespace(frame=0),
    )
    row = ns["_anchor_row"](segment, 0, 0, 0)
    assert row["verdict"] == "matches"
    assert row["versionStart"] == 0
    assert row["filenameFrameHint"] == 1001
    assert "private" not in json.dumps(row)
    segment.source_in.frame = 0
    assert ns["_anchor_row"](segment, 0, 0, 0)["verdict"] == "check_zero_anchor"


def test_trace_carries_parent_and_omits_results(tmp_path: Path, monkeypatch: Any) -> None:
    path = tmp_path / "trace.jsonl"
    monkeypatch.setenv("FINNS_FLAME_MCP_TRACE", str(path))

    def nested() -> dict[str, Any]:
        return traced_call(
            "desktop.rename",
            lambda: {
                "ok": True,
                "result": {"name": "Confidential Fixture Name"},
                "journal": {"group": "group-1"},
            },
        )

    traced_call("review.rename_apply", nested)
    raw = path.read_text()
    rows = [json.loads(line) for line in raw.splitlines()]
    assert [row["event"] for row in rows] == ["start", "start", "finish", "finish"]
    assert rows[1]["parent"] == rows[0]["id"]
    assert rows[2]["journalGroup"] == "group-1"
    assert "Confidential" not in raw
    assert not path.stat().st_mode & 0o077
