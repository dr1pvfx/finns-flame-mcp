"""Source anchor diagnostics adapted from Abraham's Flame MCP."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from flame_mcp import selectors
from flame_mcp.ops._common import build_source
from flame_mcp.registry import Registry
from flame_mcp.types import OperationParam, OperationSpec

_ANCHOR_SOURCE = r"""
import re
import time

_frame_hint = re.compile(r'\.([0-9]+)\.(?:exr|dpx|cin|tif|tiff|png)$', re.I)

def _anchor_row(segment, version, track, index):
    source_in = _try(lambda: int(_v(_v(segment.source_in).frame)))
    version_start = _try(lambda: int(_v(_v(segment.start_frame).frame)))
    path = _try(lambda: _v(segment.file_path))
    match = _frame_hint.search(path) if isinstance(path, str) else None
    filename_frame = int(match.group(1)) if match else None
    expected = filename_frame if match else version_start
    if type(source_in) is not int or type(expected) is not int:
        verdict = 'unknown'
    elif source_in == expected:
        verdict = 'matches'
    elif source_in == 0:
        verdict = 'check_zero_anchor'
    else:
        verdict = 'check_trim_or_offset'
    return {
        'version': version, 'track': track, 'index': index,
        'label': _try(lambda: _v(segment.name)),
        'recordIn': _try(lambda: str(_v(_v(segment.record_in).timecode))),
        'sourceIn': source_in,
        'sourceInTimecode': _try(lambda: str(_v(_v(segment.source_in).timecode))),
        'sourceOutTimecode': _try(lambda: str(_v(_v(segment.source_out).timecode))),
        'versionStart': version_start, 'filenameFrameHint': filename_frame,
        'verdict': verdict,
    }

def _scan_anchors(sequence, offset, limit):
    rows = []
    seen = 0
    deadline = time.monotonic() + 3
    for vi, version in enumerate(list(_v(sequence.versions))):
        for ti, track in enumerate(list(_v(version.tracks))):
            for si, segment in enumerate(list(_v(track.segments))):
                if time.monotonic() >= deadline:
                    return rows, True, 'deadline'
                if str(_v(segment.type)).casefold() == 'gap':
                    continue
                if seen >= offset:
                    if len(rows) >= limit:
                        return rows, True, 'page_limit'
                    rows.append(_anchor_row(segment, vi, ti, si))
                seen += 1
    return rows, False, None
"""


def _source(args: Mapping[str, Any]) -> str:
    target = args.get("target", {"kind": "timeline"})
    offset = args.get("offset", 0)
    limit = args.get("limit", 100)
    return build_source(
        selectors.resolve_code(target, "target"),
        _ANCHOR_SOURCE,
        "if type(target).__name__ != 'PySequence':\n"
        "    raise _OpError('SELECTOR_TYPE', 'Open or select an editable sequence')\n"
        f"_rows, _truncated, _reason = _scan_anchors(target, {offset!r}, {limit!r})\n"
        "_result = {'sequence': _v(target.name), 'rows': _rows, "
        f"'offset': {offset!r}, 'truncated': _truncated, 'stopReason': _reason}}\n"
        "_affected = 0",
    )


def _inspect_source(_args: Mapping[str, Any]) -> str:
    return build_source(
        _ANCHOR_SOURCE,
        "target = _resolve_timeline()\n"
        "segment = flame.timeline.current_segment\n"
        "if type(target).__name__ != 'PySequence' or segment is None:\n"
        "    raise _OpError('SELECTOR_EMPTY', 'Open a sequence and park on a segment')\n"
        "_result = _anchor_row(segment, None, None, None)\n"
        "_result['sequence'] = _v(target.name)\n"
        "_result['recordOut'] = _try(lambda: str(_v(_v(segment.record_out).timecode)))\n"
        "_affected = 0",
    )


def register(registry: Registry) -> None:
    registry.register(
        OperationSpec(
            name="timeline.anchor_report",
            category="timeline",
            effect="read",
            description=(
                "Check video segments against source version start or a numbered-image frame hint. "
                "A trim can explain a difference. Check unusual anchors against the reference. "
                "The open sequence is the default target. Results omit file paths."
            ),
            params=(
                OperationParam(name="target", type="selector", description="Editable sequence."),
                OperationParam(
                    name="offset",
                    type="number",
                    description="First row.",
                    default=0,
                    integer=True,
                    minimum=0,
                ),
                OperationParam(
                    name="limit",
                    type="number",
                    description="Page size.",
                    default=100,
                    integer=True,
                    minimum=1,
                ),
            ),
            default_limit=100,
            max_limit=250,
            accepts=("timeline", "wiretap", "selection", "path"),
            to_python=_source,
            sample_args={},
            requires=("PySequence.versions", "PySegment.source_in", "PySegment.record_in"),
        )
    )
    registry.register(
        OperationSpec(
            name="timeline.focused_shot",
            category="timeline",
            effect="read",
            description="Read the open sequence and focused shot's record and source timecodes.",
            to_python=_inspect_source,
            sample_args={},
            requires=("PyTimeline.current_segment", "PySegment.record_in", "PySegment.source_in"),
        )
    )
