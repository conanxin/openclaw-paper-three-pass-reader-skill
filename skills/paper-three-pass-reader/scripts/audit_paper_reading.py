#!/usr/bin/env python3
"""
audit_paper_reading.py — paper-three-pass-reader (v0.2.1-alpha)

Structural + reading-mode discipline audit for paper_reading.json.

The audit does NOT judge whether the paper_reading content is correct or
comprehensive. It checks:
  1. JSON shape / schema-required fields.
  2. reading_mode / input_kind / evidence_label enum validity.
  3. reading-mode discipline: do not claim full reading when only an
     abstract / screenshot was supplied.
  4. claims-evidence map: every claim has an evidence_label; full_text
     mode has >= 5 claims; weak modes prefer Author claim / Uncertain /
     Needs verification labels.
  5. Final checklist: at least 5 questions; full_text suggests >= 8.
  6. Optional warnings for incomplete drafts.

It returns:
  - exit code 0 on PASS, 1 on FAIL (unless --warn-only).
  - human-readable summary to stdout.
  - JSON audit result to --json-output if provided.

Usage:
    python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \\
        --input runs/fill-pack-smoke-20260615/fillpack-title-attention/work/paper_reading.json
    python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \\
        --input ... --warn-only
    python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \\
        --input ... --json-output .../audit_result.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

# v0.2.8 — consume structured source_resolution
# Use a module-level guarded import so Pyright does not flag the names
# as "possibly unbound". Names default to None and are checked at use
# time via `_SR_UTILS_AVAILABLE`.
import source_resolution_utils as _sr_utils  # type: ignore[import-not-found]
is_structured_source_resolution = _sr_utils.is_structured_source_resolution
summarize_source_resolution = _sr_utils.summarize_source_resolution
validate_source_resolution = _sr_utils.validate_source_resolution
_SR_UTILS_AVAILABLE = True
del _sr_utils

VALID_READING_MODES = {"full_text", "partial_text", "abstract_only", "screenshot_only"}
VALID_INPUT_KINDS = {
    "complete_paper", "paper_url", "paper_identifier", "paper_title",
    "paper_metadata", "paper_excerpt", "paper_image", "paper_screenshot",
    "paper_topic", "project_or_repo", "ambiguous_clue",
}
VALID_EVIDENCE_LABELS = {
    "[Paper evidence]",
    "[Figure/Table evidence]",
    "[Author claim]",
    "[Agent inference]",
    "[Uncertain]",
    "[Needs verification]",
}
WEAK_MODES = {"abstract_only", "screenshot_only"}
REQUIRED_TOP_KEYS = {
    "schema_version", "paper_metadata", "intake_quality", "summaries",
    "five_cs", "pass1", "pass2", "pass3", "claims_evidence_map",
    "figures_tables", "glossary", "limitations", "reproduction_plan",
    "open_questions", "final_checklist",
}

PLACEHOLDER_RE = re.compile(r"\[DRAFT\b", re.IGNORECASE)
MISSING_FULL_BODY_HINTS = (
    "full body", "full_body", "references", "figures", "tables",
)


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[error] could not parse JSON at {path}: {e}", file=sys.stderr)
        sys.exit(2)


def audit(doc: dict) -> dict:
    errors: list = []
    warnings: list = []
    recommendations: list = []

    # 1. Top-level required keys.
    missing_top = sorted(k for k in REQUIRED_TOP_KEYS if k not in doc)
    if missing_top:
        errors.append(f"Missing top-level keys: {missing_top}")

    if doc.get("schema_version") != "0.1.0":
        warnings.append(
            f"schema_version is {doc.get('schema_version')!r}, expected '0.1.0'. "
            "Audit was designed for v0.1.0 schema."
        )

    # 2. paper_metadata fields.
    pm = doc.get("paper_metadata") or {}
    reading_mode = pm.get("reading_mode")
    input_kind = pm.get("source_kind") or pm.get("input_kind")
    if reading_mode not in VALID_READING_MODES:
        errors.append(
            f"paper_metadata.reading_mode {reading_mode!r} not in "
            f"{sorted(VALID_READING_MODES)}"
        )
    if input_kind not in VALID_INPUT_KINDS:
        errors.append(
            f"paper_metadata.source_kind {input_kind!r} not in "
            f"{sorted(VALID_INPUT_KINDS)}"
        )
    for required in ("title", "authors", "year"):
        if required not in pm:
            warnings.append(
                f"paper_metadata.{required} is missing — page header will look empty."
            )

    # 3. Reading-mode discipline.
    pass2 = doc.get("pass2") or {}
    pass3 = doc.get("pass3") or {}
    iq = doc.get("intake_quality") or {}
    missing_parts = iq.get("missing_fields") or []

    if reading_mode in WEAK_MODES:
        # Pass 2 / Pass 3 must NOT claim full completion.
        p2_method = (pass2.get("method_summary") or "").lower()
        p3_recon = " ".join(pass3.get("method_reconstruction") or []).lower()
        if "draft" not in p2_method and "[draft" not in p2_method and len(p2_method.strip()) > 30:
            warnings.append(
                f"reading_mode = {reading_mode}; pass2.method_summary is filled in "
                "but no body was supplied. Confirm this was authored from the "
                "abstract, not invented."
            )
        if "draft" not in p3_recon and "[draft" not in p3_recon and len(p3_recon.strip()) > 30:
            warnings.append(
                f"reading_mode = {reading_mode}; pass3.method_reconstruction is "
                "filled in but no body was supplied. This is a strong signal of "
                "an over-claim."
            )

        # screenshot_only must explicitly mark body parts as missing.
        if reading_mode == "screenshot_only":
            marked = any(any(h in (m or "").lower() for h in MISSING_FULL_BODY_HINTS)
                         for m in missing_parts)
            if not marked:
                errors.append(
                    "reading_mode = screenshot_only but intake_quality.missing_fields "
                    "does not explicitly mention full body / references / figures / tables. "
                    "Add one of: 'full body', 'references', 'figures', 'tables'."
                )

    if reading_mode == "full_text":
        for stage_name, stage in (("pass1", doc.get("pass1") or {}),
                                  ("pass2", pass2),
                                  ("pass3", pass3)):
            blob = json.dumps(stage, ensure_ascii=False).lower()
            if "[draft" in blob:
                warnings.append(
                    f"reading_mode = full_text but {stage_name} still contains "
                    "[DRAFT] placeholders. The reading should be complete."
                )

    # 4. Claims-evidence map.
    cem = doc.get("claims_evidence_map") or []
    if not isinstance(cem, list):
        errors.append("claims_evidence_map is not a list.")
        cem = []
    bad_labels: list = []
    claims_with_evidence = 0
    for i, c in enumerate(cem):
        if not isinstance(c, dict):
            errors.append(f"claims_evidence_map[{i}] is not an object.")
            continue
        ev = c.get("evidence_label")
        if ev not in VALID_EVIDENCE_LABELS:
            bad_labels.append(f"#{i}: {ev!r}")
        else:
            claims_with_evidence += 1

    if bad_labels:
        errors.append(
            "claims_evidence_map contains invalid evidence_label values: "
            + "; ".join(bad_labels)
        )

    if reading_mode == "full_text" and len(cem) < 5:
        errors.append(
            f"reading_mode = full_text but claims_evidence_map has only "
            f"{len(cem)} entries. full_text mode requires at least 5 claims."
        )

    if reading_mode in WEAK_MODES and cem:
        allowed_for_weak = {"[Author claim]", "[Uncertain]", "[Needs verification]"}
        bad_in_weak = [
            i for i, c in enumerate(cem)
            if isinstance(c, dict)
            and c.get("evidence_label") not in allowed_for_weak
        ]
        if bad_in_weak:
            warnings.append(
                f"reading_mode = {reading_mode}; weak mode should prefer "
                f"{sorted(allowed_for_weak)}. "
                f"Claims with strong labels: {bad_in_weak}. "
                "Downgrade or add a Needs verification note."
            )

    # 5. Final checklist.
    fc = doc.get("final_checklist") or []
    if not isinstance(fc, list):
        errors.append("final_checklist is not a list.")
    elif len(fc) < 5:
        errors.append(
            f"final_checklist has only {len(fc)} questions; minimum is 5."
        )
    elif reading_mode == "full_text" and len(fc) < 8:
        recommendations.append(
            f"reading_mode = full_text; final_checklist has {len(fc)} questions. "
            "Suggest >= 8 for full readings."
        )

    # 6. Draft placeholders (informational).
    blob = json.dumps(doc, ensure_ascii=False)
    placeholder_hits = len(PLACEHOLDER_RE.findall(blob))
    if placeholder_hits:
        recommendations.append(
            f"Document contains {placeholder_hits} [DRAFT] placeholders. "
            "These are normal for a freshly-generated runner draft; they should "
            "be replaced before the page is treated as a real reading."
        )

    # 7. Intake quality completeness.
    if not iq:
        errors.append("intake_quality is missing.")
    else:
        for k in ("input_kind", "reading_mode", "confidence"):
            if k not in iq:
                warnings.append(f"intake_quality.{k} is missing.")

    # 8. Language check (zh-CN).
    target_lang = doc.get("target_language", "en")
    ui_lang = doc.get("ui_language", "en")
    if target_lang == "zh-CN" or ui_lang == "zh-CN":
        # Check that main interpretive fields contain Chinese characters.
        _CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
        zh_check_fields = {
            "summaries.one_sentence": (doc.get("summaries") or {}).get("one_sentence", ""),
            "pass2.main_ideas": " ".join(str(x) for x in (pass2.get("main_ideas") or [])),
            "pass3.method_reconstruction": " ".join(str(x) for x in (pass3.get("method_reconstruction") or [])),
            "pass3.critical_review": " ".join(str(x) for x in (pass3.get("critical_review") or [])),
            "glossary": " ".join(
                (g.get("definition") or "") for g in (doc.get("glossary") or [])
            ),
        }
        zh_hits = 0
        zh_total = 0
        for field_name, text in zh_check_fields.items():
            if text.strip():
                zh_total += 1
                if _CHINESE_RE.search(text):
                    zh_hits += 1
        if zh_total > 0 and zh_hits / zh_total < 0.5:
            warnings.append(
                f"target_language/ui_language = zh-CN but fewer than 50% of main "
                f"interpretive fields contain Chinese characters ({zh_hits}/{zh_total}). "
                f"Fields checked: {list(zh_check_fields.keys())}. "
                "Ensure explanatory content is in Chinese; evidence labels and "
                "paper names may remain in English."
            )

    # 12. v0.2.8 — structured source_resolution check.
    sr_block: dict = OrderedDict()
    sr_block["status"] = "skipped"
    sr_block["structured"] = False
    sr_block["legacy_fallback"] = False
    sr_block["warnings"] = []
    sr_block["errors"] = []
    sr_block["summary"] = {}
    if _SR_UTILS_AVAILABLE:
        top = doc.get("source_resolution")
        sr_block["structured"] = is_structured_source_resolution(top)
        if not sr_block["structured"]:
            iq0 = doc.get("intake_quality") or {}
            sr_block["legacy_fallback"] = bool(iq0.get("source_resolution"))
            # The presence of a legacy-only block is a WARN, not a FAIL.
            # It does NOT block by itself; the reading_mode-specific
            # logic below decides whether it becomes an error.
            if sr_block["legacy_fallback"]:
                warnings.append(
                    "legacy intake_quality.source_resolution detected; "
                    "top-level structured source_resolution recommended"
                )
            else:
                # No block at all. WARN unless reading_mode is screenshot_only
                # / abstract_only (those never have a structured block).
                if reading_mode not in WEAK_MODES:
                    warnings.append(
                        "source_resolution is missing; "
                        "top-level structured block recommended"
                    )
        else:
            sr_block["summary"] = summarize_source_resolution(doc)
            status_v = (top.get("resolver_status") or "").lower()  # type: ignore[union-attr]
            sr_block["status"] = status_v or "unknown"
            if status_v == "error":
                degraded = top.get("degraded")  # type: ignore[union-attr]
                wn = (doc.get("intake_quality") or {}).get("warnings") or []
                if not degraded and not wn:
                    errors.append(
                        "source_resolution.resolver_status=error but no "
                        "degraded / warning marker recorded"
                    )
            if status_v == "matched":
                if not any(
                    top.get(f)  # type: ignore[union-attr]
                    for f in ("matched_paper_id", "matched_canonical_title", "matched_arxiv_id")
                ):
                    warnings.append(
                        "source_resolution.resolver_status=matched but "
                        "matched_paper_id / canonical_title / arxiv_id all empty"
                    )
            conf = top.get("confidence")  # type: ignore[union-attr]
            if conf is None:
                warnings.append("source_resolution.confidence is missing")
        # Always run the utility's own validation as a sanity overlay.
        util_errs, util_warns = validate_source_resolution(doc)
        for w in util_warns:
            if w not in warnings:
                warnings.append(w)
        for e in util_errs:
            if e not in errors:
                errors.append(e)
        sr_block["warnings"] = list(util_warns)
        sr_block["errors"] = list(util_errs)

    # Decide status.
    if errors:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    return OrderedDict([
        ("status", status),
        ("reading_mode", reading_mode),
        ("input_kind", input_kind),
        ("schema_version", doc.get("schema_version")),
        ("source_resolution", sr_block),
        ("counts", OrderedDict([
            ("claims_total", len(cem)),
            ("claims_with_valid_evidence", claims_with_evidence),
            ("final_checklist_questions", len(fc) if isinstance(fc, list) else 0),
            ("draft_placeholders", placeholder_hits),
        ])),
        ("errors", errors),
        ("warnings", warnings),
        ("recommendations", recommendations),
    ])


def render_text(result: dict) -> str:
    lines = []
    lines.append(f"Audit status: {result['status']}")
    lines.append(
        f"reading_mode = {result['reading_mode']!r}, "
        f"input_kind = {result['input_kind']!r}, "
        f"schema_version = {result['schema_version']!r}"
    )
    c = result["counts"]
    lines.append(
        f"Counts: claims={c['claims_total']} "
        f"(valid evidence={c['claims_with_valid_evidence']}), "
        f"final_checklist={c['final_checklist_questions']}, "
        f"[DRAFT] placeholders={c['draft_placeholders']}"
    )
    if result["errors"]:
        lines.append("")
        lines.append(f"Errors ({len(result['errors'])}):")
        for e in result["errors"]:
            lines.append(f"  - {e}")
    if result["warnings"]:
        lines.append("")
        lines.append(f"Warnings ({len(result['warnings'])}):")
        for w in result["warnings"]:
            lines.append(f"  - {w}")
    if result["recommendations"]:
        lines.append("")
        lines.append(f"Recommendations ({len(result['recommendations'])}):")
        for r in result["recommendations"]:
            lines.append(f"  - {r}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Audit a paper_reading.json draft.")
    p.add_argument("--input", required=True, help="Path to paper_reading.json.")
    p.add_argument("--warn-only", action="store_true",
                   help="Do not exit non-zero on WARN; only exit non-zero on FAIL.")
    p.add_argument("--json-output", help="Write audit result as JSON here.")
    p.add_argument("--quality-gate", action="store_true",
                   help="Run the zh-CN quality gate after the structural audit. "
                        "Only effective when target_language/ui_language is zh-CN.")
    args = p.parse_args(argv)

    path = Path(args.input)
    if not path.exists():
        print(f"[error] --input file does not exist: {path}", file=sys.stderr)
        return 2
    doc = _load(path)
    result = audit(doc)
    sys.stdout.write(render_text(result))

    # Optional: zh-CN quality gate.
    target_lang = doc.get("target_language", "en")
    ui_lang = doc.get("ui_language", "en")
    qg_status: str = "SKIPPED"
    qg_warn = ""
    if args.quality_gate and (target_lang == "zh-CN" or ui_lang == "zh-CN"):
        try:
            from quality_gate_zh_cn import run_quality_gate, render_text as _qg_render
            qg_result = run_quality_gate(doc, _DummyArgs())
            qg_status = qg_result["status"]
            print()
            print("[quality_gate_zh_cn]")
            sys.stdout.write(_qg_render(qg_result))
            if args.json_output:
                qg_out = Path(args.json_output).with_name("quality_gate_zh_cn.json")
                qg_out.write_text(
                    json.dumps(qg_result, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
        except ImportError as e:
            qg_warn = f"quality gate module not importable: {e}"
            print(f"[warn] {qg_warn}", file=sys.stderr)
    elif not args.quality_gate and (target_lang == "zh-CN" or ui_lang == "zh-CN"):
        print()
        print(
            "[hint] target_language/ui_language = zh-CN. Re-run with --quality-gate "
            "to invoke skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py.",
        )

    if args.json_output:
        out = Path(args.json_output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[ok] wrote audit result: {out}")
    if result["status"] == "FAIL":
        return 1
    if qg_status == "FAIL":
        return 1
    if result["status"] == "WARN" and not args.warn_only:
        # WARN still returns 0 (informational); use --warn-only to silence that.
        return 0
    return 0


class _DummyArgs:
    """Stand-in for argparse Namespace so the quality gate can be invoked
    directly from audit without re-parsing argv."""
    min_cjk_ratio = 0.5
    min_claims = 8
    min_glossary = 10
    min_checklist = 8


if __name__ == "__main__":
    sys.exit(main())
