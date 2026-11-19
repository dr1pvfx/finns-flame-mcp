"""Manifest fingerprint from forge-bridge (GPL-3.0).

canonical_fingerprint adapted from Chris Nollert's forge_bridge/orchestration/workflow_core.py
at 96312adf9f3b10a4c82f5c5cfca221feab35f24b. See LICENSE and THIRD_PARTY_NOTICES.md.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_fingerprint(value: Any) -> str:
    """SHA-256 over deterministic JSON with sorted keys."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
