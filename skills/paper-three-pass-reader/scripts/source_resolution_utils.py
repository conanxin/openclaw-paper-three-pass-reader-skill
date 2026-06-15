"""source_resolution_utils.py

Shared helpers for consumers of the structured `source_resolution` block
that lives at the top level of every paper_reading.json draft (v0.2.7+).

Canonical structured fields (v0.2.7 round-2 design):

    steps
    hint_input
    resolver_source
    resolver_helper
    resolver_status
    resolver_match_type
    confidence
    matched_paper_id
    matched_canonical_title
    matched_arxiv_id
    matched_alias
    matched_repo
    candidates
    source_resolution_step
    degraded
    fallback_legacy

A draft that only carries the legacy `intake_quality.source_resolution`
list (v0.2.5 era) is still accepted. `legacy_source_resolution_to_structured`
upgrades it on the fly so that downstream consumers do not need a branch.

stdlib-only.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

CANONICAL_FIELDS = (
    "steps",
    "hint_input",
    "resolver_source",
    "resolver_helper",
    "resolver_status",
    "resolver_match_type",
    "confidence",
    "matched_paper_id",
    "matched_canonical_title",
    "matched_arxiv_id",
    "matched_alias",
    "matched_repo",
    "candidates",
    "source_resolution_step",
    "degraded",
    "fallback_legacy",
)

# Required minimum fields that any structured source_resolution should
# contain. If any of these are missing the draft is incomplete even if it
# is structurally "a dict".
REQUIRED_FIELDS = (
    "resolver_status",
    "resolver_match_type",
    "confidence",
    "source_resolution_step",
)

# A "matched" draft should also point at a real paper.
MATCHED_IDENTITY_FIELDS = (
    "matched_paper_id",
    "matched_canonical_title",
    "matched_arxiv_id",
)

# Numeric confidence can be a float 0.0-1.0, or one of these high-cardinality
# string labels emitted by the shared resolver.
CONFIDENCE_LABEL_TO_NUM = {
    "high": 0.9,
    "medium": 0.6,
    "low": 0.3,
    "very_low": 0.1,
}


def is_structured_source_resolution(value: Any) -> bool:
    """True if value is the top-level structured dict we expect."""
    if not isinstance(value, dict):
        return False
    # A "structured" block has at least resolver_status + one of
    # source_resolution_step / steps.
    if "resolver_status" not in value:
        return False
    if "source_resolution_step" not in value and "steps" not in value:
        return False
    return True


def _empty_structured() -> Dict[str, Any]:
    """Return a blank but well-typed structured source_resolution dict."""
    return {
        "steps": [],
        "hint_input": None,
        "resolver_source": None,
        "resolver_helper": None,
        "resolver_status": "ambiguous_clue",
        "resolver_match_type": None,
        "confidence": None,
        "matched_paper_id": None,
        "matched_canonical_title": None,
        "matched_arxiv_id": None,
        "matched_alias": None,
        "matched_repo": None,
        "candidates": [],
        "source_resolution_step": "no_resolver_run",
        "degraded": None,
        "fallback_legacy": False,
    }


def get_source_resolution(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return the structured source_resolution block, falling back to the
    legacy `intake_quality.source_resolution` list when needed.

    Never raises. Returns a fully-populated dict even for malformed input.
    """
    if not isinstance(data, dict):
        return _empty_structured()

    top = data.get("source_resolution")
    if is_structured_source_resolution(top):
        out = dict(_empty_structured())
        out.update({k: v for k, v in top.items() if k in CANONICAL_FIELDS})
        out["fallback_legacy"] = False
        return out

    # Legacy fallback path: pull from intake_quality.source_resolution list
    # and try to infer the most useful fields.
    iq = data.get("intake_quality") or {}
    legacy = iq.get("source_resolution")
    return legacy_source_resolution_to_structured(legacy)


def legacy_source_resolution_to_structured(
    legacy: Any,
) -> Dict[str, Any]:
    """Upgrade a legacy `intake_quality.source_resolution` list (or anything
    else) into a structured dict. Marks `fallback_legacy=True` so callers
    can show a "Legacy fallback" badge.
    """
    out = _empty_structured()
    out["fallback_legacy"] = True

    if isinstance(legacy, list):
        # Try to extract a confidence / status / match type from the strings.
        joined = "\n".join(str(x) for x in legacy)
        out["steps"] = [str(x) for x in legacy]
        m = re.search(r"status:\s*(\w+)", joined, re.IGNORECASE)
        if m:
            out["resolver_status"] = m.group(1).lower()
        m = re.search(r"match(?:_type)?:\s*(\w+)", joined, re.IGNORECASE)
        if m:
            out["resolver_match_type"] = m.group(1).lower()
        m = re.search(r"confidence:\s*(\w+)", joined, re.IGNORECASE)
        if m:
            out["confidence"] = m.group(1).lower()
        m = re.search(r"paper id:\s*([\w\-]+)", joined, re.IGNORECASE)
        if m:
            out["matched_paper_id"] = m.group(1)
        m = re.search(r"arXiv[:\s]+([0-9]+\.[0-9]+)", joined, re.IGNORECASE)
        if m:
            out["matched_arxiv_id"] = m.group(1)
        m = re.search(r"step:\s*(.+?)(?:\n|$)", joined, re.IGNORECASE)
        if m:
            out["source_resolution_step"] = m.group(1).strip()
    elif isinstance(legacy, dict):
        # Already a dict but not in the canonical shape — copy what we can.
        for k, v in legacy.items():
            if k in CANONICAL_FIELDS and v is not None:
                out[k] = v
    return out


def summarize_source_resolution(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a renderer-friendly summary of the structured block.

    Always returns a dict with these keys, suitable for direct use in a
    Jinja-style template (and the stdlib `render()` in render_page.py):

        structured          (bool)
        fallback_legacy     (bool)
        resolver_status     (str)
        resolver_match_type (str or None)
        confidence          (str or float or None)
        confidence_numeric  (float or None)
        matched_paper_id    (str or None)
        matched_canonical_title (str or None)
        matched_arxiv_id    (str or None)
        matched_repo        (str or None)
        resolver_source     (str or None)
        source_resolution_step (str)
        degraded            (str or None)
        candidate_count     (int)
        candidates_top      (list)        # up to 3 candidate summaries
        steps_count         (int)
    """
    sr = get_source_resolution(data)
    candidates = sr.get("candidates") or []
    cand_top: List[Dict[str, Any]] = []
    for c in candidates[:3]:
        if isinstance(c, dict):
            cand_top.append({
                "id": c.get("id"),
                "title": c.get("title") or c.get("canonical_title"),
                "arxiv_id": c.get("arxiv") or c.get("arxiv_id"),
                "confidence": c.get("confidence"),
            })
        else:
            cand_top.append({"raw": str(c)})

    conf = sr.get("confidence")
    conf_num: Any = None
    if isinstance(conf, (int, float)):
        conf_num = float(conf)
    elif isinstance(conf, str):
        if conf in CONFIDENCE_LABEL_TO_NUM:
            conf_num = CONFIDENCE_LABEL_TO_NUM[conf]
        else:
            try:
                conf_num = float(conf)
            except ValueError:
                conf_num = None

    return {
        "structured": not bool(sr.get("fallback_legacy")),
        "fallback_legacy": bool(sr.get("fallback_legacy")),
        "resolver_status": sr.get("resolver_status"),
        "resolver_match_type": sr.get("resolver_match_type"),
        "confidence": conf,
        "confidence_numeric": conf_num,
        "matched_paper_id": sr.get("matched_paper_id"),
        "matched_canonical_title": sr.get("matched_canonical_title"),
        "matched_arxiv_id": sr.get("matched_arxiv_id"),
        "matched_repo": sr.get("matched_repo"),
        "resolver_source": sr.get("resolver_source"),
        "source_resolution_step": sr.get("source_resolution_step"),
        "degraded": sr.get("degraded"),
        "candidate_count": len(candidates),
        "candidates_top": cand_top,
        "steps_count": len(sr.get("steps") or []),
        "hint_input": sr.get("hint_input"),
    }


def validate_source_resolution(
    data: Dict[str, Any],
) -> Tuple[List[str], List[str]]:
    """Validate the structured source_resolution block.

    Returns (errors, warnings) lists. Both are always present.
    An empty (errors=[], warnings=[]) tuple means the block is healthy.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(data, dict):
        errors.append("data is not a dict")
        return errors, warnings

    top: Any = data.get("source_resolution")
    iq = data.get("intake_quality") or {}
    legacy = iq.get("source_resolution")

    if not is_structured_source_resolution(top):
        if legacy:
            warnings.append(
                "legacy intake_quality.source_resolution detected; "
                "top-level structured source_resolution recommended"
            )
        else:
            warnings.append(
                "source_resolution is missing; "
                "top-level structured block recommended"
            )
        # No further checks possible without a structured block.
        return errors, warnings

    # Pyright loses narrowing of `top` across the early-return; restore it.
    assert isinstance(top, dict)
    sr_block: Dict[str, Any] = top

    # We have a structured block. Check required fields.
    for f in REQUIRED_FIELDS:
        if sr_block.get(f) in (None, "", []):
            warnings.append(
                f"source_resolution.{f} is missing or empty"
            )

    status = (sr_block.get("resolver_status") or "").lower()
    if status in ("matched",):
        if not any(sr_block.get(f) for f in MATCHED_IDENTITY_FIELDS):
            warnings.append(
                "source_resolution.resolver_status=matched but none of "
                "matched_paper_id / matched_canonical_title / matched_arxiv_id "
                "are populated"
            )

    conf = sr_block.get("confidence")
    if conf is None:
        warnings.append("source_resolution.confidence is missing")
    elif isinstance(conf, (int, float)):
        if not (0.0 <= float(conf) <= 1.0):
            warnings.append(
                f"source_resolution.confidence={conf!r} is outside [0, 1]"
            )
    elif isinstance(conf, str):
        if conf not in CONFIDENCE_LABEL_TO_NUM:
            try:
                float(conf)
            except ValueError:
                warnings.append(
                    f"source_resolution.confidence={conf!r} is not a number"
                )

    if status == "error":
        if not (sr_block.get("degraded") or sr_block.get("warnings")):
            errors.append(
                "source_resolution.resolver_status=error but no "
                "degraded / warning marker recorded"
            )

    return errors, warnings


def main() -> int:
    """Tiny CLI for debugging. Reads paper_reading.json from --path
    (or stdin) and prints a JSON summary + validation result.
    """
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        help="Path to paper_reading.json. Reads from stdin if omitted.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Print only the validation result.",
    )
    args = parser.parse_args()

    if args.path:
        with open(args.path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.loads(__import__("sys").stdin.read())

    errors, warnings = validate_source_resolution(data)
    summary = summarize_source_resolution(data)

    if args.validate_only:
        out = {"errors": errors, "warnings": warnings}
    else:
        out = {"summary": summary, "errors": errors, "warnings": warnings}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
