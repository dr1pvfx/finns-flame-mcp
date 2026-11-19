"""Prepare and apply a single rename against the same inspected target."""

from __future__ import annotations

import hmac
from collections.abc import Mapping
from typing import Any

from flame_mcp.approval import canonical_fingerprint
from flame_mcp.errors import as_error_code
from flame_mcp.registry import Registry
from flame_mcp.runtime import ServerContext
from flame_mcp.types import Category, OperationParam, OperationSpec, ServerOpError, ServerResult

_CATEGORY = Category(
    name="review",
    description="Preview an editorial change and apply the exact reviewed manifest.",
    default_thread="server",
    default_pacing="none",
    allowed_thread=frozenset({"server"}),
    allowed_pacing=frozenset({"none"}),
)

_PARAMS = (
    OperationParam(
        name="target", type="selector", description="Stable Media Panel Wiretap ID.", required=True
    ),
    OperationParam(
        name="name",
        type="string",
        description="New clip or sequence name.",
        required=True,
        non_empty=True,
    ),
)


def _failure(response: Mapping[str, Any]) -> ServerOpError:
    return ServerOpError(
        as_error_code(response.get("errorCode")) or "FLAME_API_ERROR",
        str(response.get("error") or "Flame did not complete the operation."),
        result=response.get("result"),
        journal=response.get("journal"),
    )


def _inspect(rt: ServerContext, args: Mapping[str, Any]) -> dict[str, Any]:
    target = args["target"]
    response = rt.do("desktop.info", {"target": target})
    if not response.get("ok"):
        raise _failure(response)
    item = response.get("result")
    if (
        not isinstance(item, dict)
        or item.get("type") not in ("PyClip", "PySequence")
        or not isinstance(item.get("name"), str)
        or not item.get("uid")
        or item.get("wiretapId") != target["id"]
    ):
        raise ServerOpError("CONFLICT", "Review requires one stable clip or sequence.")
    old = item["name"]
    if old == args["name"]:
        raise ServerOpError("CONFLICT", "The clip already has the requested name.")
    if not args["name"].isprintable() or args["name"].strip() != args["name"]:
        raise ServerOpError(
            "INVALID_ARGS", "Use a printable name without leading or trailing space."
        )
    return {
        "operation": "desktop.rename",
        "target": target,
        "expectedName": old,
        "name": args["name"],
        "uid": item["uid"],
        "scope": response.get("context"),
    }


def _preview(args: Mapping[str, Any], rt: ServerContext) -> ServerResult:
    manifest = _inspect(rt, args)
    return ServerResult({"manifest": manifest, "fingerprint": canonical_fingerprint(manifest)})


def _apply(args: Mapping[str, Any], rt: ServerContext) -> ServerResult:
    with rt.write_lock:
        manifest = _inspect(rt, args)
        fingerprint = canonical_fingerprint(manifest)
        approval = args["fingerprint"]
        if len(approval) != 64 or not hmac.compare_digest(fingerprint, approval):
            raise ServerOpError(
                "CONFLICT", "The target or proposed rename changed. Build a new preview."
            )
        outcome = rt.do(
            "desktop.rename",
            {"target": args["target"], "name": args["name"]},
            precondition={"name": manifest["expectedName"]},
        )
        if not outcome.get("ok"):
            raise _failure(outcome)
        return ServerResult(
            {"rename": outcome["result"], "reviewFingerprint": fingerprint},
            affected=outcome.get("affected", 0),
            journal=outcome.get("journal"),
            undo_steps=0,
        )


def register(registry: Registry) -> None:
    registry.register_category(_CATEGORY)
    sample = {"target": {"kind": "wiretap", "id": "example"}, "name": "Cut B"}
    registry.register(
        OperationSpec(
            name="review.rename_preview",
            category="review",
            effect="read",
            params=_PARAMS,
            description="Prepare a single clip or timeline rename and return its fingerprint.",
            accepts=("wiretap",),
            server_handler=_preview,
            sample_args=sample,
        )
    )
    registry.register(
        OperationSpec(
            name="review.rename_apply",
            category="review",
            effect="reversible",
            description="Apply an artist-reviewed rename with the exact preview fingerprint.",
            params=(
                *_PARAMS,
                OperationParam(
                    name="fingerprint",
                    type="string",
                    description="The artist-approved manifest fingerprint.",
                    required=True,
                    non_empty=True,
                ),
            ),
            accepts=("wiretap",),
            server_handler=_apply,
            undo="value",
            undo_steps=lambda args, affected: 0,
            sample_args={**sample, "fingerprint": "a" * 64},
        )
    )
