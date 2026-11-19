"""Exercise real Qt dispatch with synthetic Flame objects. Run outside Autodesk Flame."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread, get_ident
from types import SimpleNamespace
from typing import Any

from PySide6.QtCore import QCoreApplication, QObject, Qt, QTimer, Signal, Slot

from flame_mcp_bridge.impl import start


class MainThreadDispatcher(QObject):
    requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.requested.connect(self.invoke, Qt.ConnectionType.QueuedConnection)

    @Slot(object)
    def invoke(self, callback: Callable[[], None]) -> None:
        callback()


class PySequence:
    name = "Synthetic Timeline"


class Segment:
    type = "Video"
    name = "Synthetic Shot"
    file_path = "/synthetic/plate.1001.exr"

    def __init__(self, main_thread: int) -> None:
        self.main_thread = main_thread
        self.record_in = SimpleNamespace(frame=90000, timecode="01:00:00:00")
        self.record_out = SimpleNamespace(frame=90024, timecode="01:00:00:24")
        self.source_out = SimpleNamespace(frame=1025, timecode="00:00:41:00")
        self.start_frame = SimpleNamespace(frame=1000, timecode="00:00:40:00")

    @property
    def source_in(self) -> Any:
        assert get_ident() == self.main_thread
        return SimpleNamespace(frame=1001, timecode="00:00:40:01")


def main() -> None:
    app = QCoreApplication([])
    sequence = PySequence()
    segment = Segment(get_ident())
    sequence.versions = [SimpleNamespace(tracks=[SimpleNamespace(segments=[segment])])]
    flame = SimpleNamespace(timeline=SimpleNamespace(clip=sequence, current_segment=segment))
    errors: list[Exception] = []
    with TemporaryDirectory(prefix="fmp-", dir="/tmp") as folder:
        root = Path(folder)
        trace = root / "trace.jsonl"
        env = {
            **os.environ,
            "FLAME_MCP_RUN_DIR": str(root / "run"),
            "FLAME_MCP_JOURNAL_DIR": str(root / "journal"),
            "FINNS_FLAME_MCP_TRACE": str(trace),
        }
        dispatcher = MainThreadDispatcher()
        bridge = start(
            dispatcher.requested.emit, flame, "2027.1", "Synthetic Fixture", str(root / "run")
        )

        def call(op: str) -> dict[str, Any]:
            result = subprocess.run(
                [sys.executable, "-m", "flame_mcp.client", "--expect-flame-pid", str(os.getpid())],
                input=json.dumps({"op": op, "args": {}}),
                env=env,
                capture_output=True,
                text=True,
                timeout=12,
                check=True,
            )
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            return data

        def check() -> None:
            try:
                shot = call("timeline.focused_shot")
                assert shot["ok"], shot
                assert shot["result"]["sourceIn"] == 1001, shot["result"]
                assert shot["result"]["verdict"] == "matches"
                anchors = call("timeline.anchor_report")
                assert anchors["ok"], anchors
                assert anchors["result"]["rows"][0]["filenameFrameHint"] == 1001
                lines = trace.read_text().splitlines()
                rows = [json.loads(line) for line in lines]
                assert len(rows) == 4 and rows[1]["ok"] is True
                assert "Synthetic Shot" not in "\n".join(lines)
            except Exception as exc:
                errors.append(exc)
            finally:
                app.quit()

        worker = Thread(target=check, daemon=True)
        schedule: Callable[[], None] = worker.start
        QTimer.singleShot(0, schedule)
        QTimer.singleShot(30_000, app.quit)
        app.exec()
        worker.join(timeout=2)
        bridge.stop()
        assert not worker.is_alive(), "Probe timed out"
        if errors:
            raise errors[0]
        print("Qt main-thread dispatch, stdio MCP, Unix socket and redacted trace passed")


if __name__ == "__main__":
    main()
