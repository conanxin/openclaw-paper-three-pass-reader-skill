#!/usr/bin/env python3
"""
quality_gate_zh_cn.py — paper-three-pass-reader (v0.2.4-alpha)

Chinese (zh-CN) quality gate for paper_reading.json.

This is a **structural + bilingual-discipline** check. It does NOT judge whether
the paper's content is correct or whether the Chinese explanation is "good" in a
subjective sense. It catches these specific failure modes:

  1. Language field is missing or wrong.
  2. Most interpretive fields are still in English (UI chrome in Chinese, body
     in English — a common translation-slip failure).
  3. A single field contains a long English paragraph (e.g. the operator copy-
     pasted a paragraph from the English draft without translating it).
  4. Glossary has too few terms (< min-glossary).
  5. Claims-Evidence map has too few claims (< min-claims).
  6. Final checklist has too few questions (< min-checklist).
  7. full_text mode has no [Paper evidence] / [Figure/Table evidence] claims
     (i.e. the operator marked everything as [Author claim] / [Uncertain],
     which is suspicious for a real reading).
  8. Pass 2 / Pass 3 missing in full_text mode.

Usage:
    python3 quality_gate_zh_cn.py --input <paper_reading.json>
    python3 quality_gate_zh_cn.py --input <paper_reading.json> --json-output <out.json>
    python3 quality_gate_zh_cn.py --input <paper_reading.json> --warn-only

Exit codes:
    0  PASS
    1  FAIL  (or WARN unless --warn-only)
    2  usage / I/O error

This script is stdlib only and is safe to call from the runner / audit / CI.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

# v0.2.8 — pull structured source_resolution from the shared utility
sys.path.insert(0, str(Path(__file__).parent))
from source_resolution_utils import (  # type: ignore[import-not-found]
    is_structured_source_resolution as _is_structured_sr,
    summarize_source_resolution as _summarize_sr,
)

VALID_EVIDENCE_LABELS = {
    "[Paper evidence]",
    "[Figure/Table evidence]",
    "[Author claim]",
    "[Agent inference]",
    "[Uncertain]",
    "[Needs verification]",
}

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
# "Long English paragraph" heuristic: 30+ consecutive ASCII word characters.
_LONG_EN_RE = re.compile(r"[A-Za-z][A-Za-z\s,.;:'\"()\-]{30,}")


def _has_cjk(s: str) -> bool:
    return bool(_CJK_RE.search(s or ""))


def _has_long_english(s: str) -> bool:
    """Detect a suspicious long English blob in a Chinese-claimed field."""
    if not s:
        return False
    for m in _LONG_EN_RE.finditer(s):
        # Must not be embedded in a longer CJK run. Quick check: the matched
        # span contains at least 30 ASCII word chars without a CJK character
        # inside.
        span = m.group(0)
        if not _CJK_RE.search(span) and len(span.replace(" ", "")) >= 30:
            return True
    return False


def _gather_text_values(doc: dict) -> list[tuple[str, str]]:
    """Return (field_name, text) for every interpretive text field we check."""
    out: list[tuple[str, str]] = []

    s = doc.get("summaries") or {}
    if s.get("one_sentence"):
        out.append(("summaries.one_sentence", s["one_sentence"]))
    three = s.get("three_sentence")
    if isinstance(three, list):
        out.append(("summaries.three_sentence", " ".join(str(x) for x in three)))
    ten = s.get("ten_sentence")
    if isinstance(ten, list):
        out.append(("summaries.ten_sentence", " ".join(str(x) for x in ten)))

    p1 = doc.get("pass1") or {}
    if p1.get("findings"):
        out.append(("pass1.findings", p1["findings"]))
    if p1.get("five_cs_result"):
        out.append(("pass1.five_cs_result", p1["five_cs_result"]))

    p2 = doc.get("pass2") or {}
    mi = p2.get("main_ideas")
    if isinstance(mi, list):
        out.append(("pass2.main_ideas", " ".join(str(x) for x in mi)))
    if p2.get("method_summary"):
        out.append(("pass2.method_summary", p2["method_summary"]))

    p3 = doc.get("pass3") or {}
    mr = p3.get("method_reconstruction")
    if isinstance(mr, list):
        out.append(("pass3.method_reconstruction", " ".join(str(x) for x in mr)))
    cr = p3.get("critical_review")
    if isinstance(cr, list):
        out.append(("pass3.critical_review", " ".join(str(x) for x in cr)))
    if p3.get("hidden_assumptions"):
        out.append(("pass3.hidden_assumptions", " ".join(str(x) for x in p3["hidden_assumptions"])))
    if p3.get("limitations"):
        out.append(("pass3.limitations", " ".join(str(x) for x in p3["limitations"])))
    fw = p3.get("future_work")
    if isinstance(fw, list):
        out.append(("pass3.future_work", " ".join(str(x) for x in fw)))
    an = p3.get("application_notes")
    if isinstance(an, list):
        out.append(("pass3.application_notes", " ".join(str(x) for x in an)))

    cem = doc.get("claims_evidence_map") or []
    for i, c in enumerate(cem):
        if not isinstance(c, dict):
            continue
        claim = c.get("claim_text") or c.get("claim") or ""
        comment = c.get("comment") or c.get("notes") or ""
        if claim:
            out.append((f"claims_evidence_map[{i}].claim_text", str(claim)))
        if comment:
            out.append((f"claims_evidence_map[{i}].comment", str(comment)))

    g = doc.get("glossary") or []
    for i, item in enumerate(g):
        if isinstance(item, dict):
            d = item.get("definition") or ""
            if d:
                out.append((f"glossary[{i}].definition", str(d)))
        elif isinstance(item, str):
            if item:
                out.append((f"glossary[{i}]", item))

    fc = doc.get("final_checklist") or []
    for i, item in enumerate(fc):
        if isinstance(item, dict):
            q = item.get("question") or ""
            a = item.get("answer") or ""
            if q:
                out.append((f"final_checklist[{i}].question", str(q)))
            if a:
                out.append((f"final_checklist[{i}].answer", str(a)))
        elif isinstance(item, str):
            if item:
                out.append((f"final_checklist[{i}]", item))

    return out


def run_quality_gate(doc: dict, args) -> dict:
    """Compute the quality-gate result for a paper_reading.json document."""
    errors: list = []
    warnings: list = []
    recommendations: list = []

    # 1. Language field
    target_lang = doc.get("target_language", "en")
    ui_lang = doc.get("ui_language", "en")
    if target_lang != "zh-CN":
        errors.append(
            f"target_language is {target_lang!r}, expected 'zh-CN'."
        )
    if ui_lang != "zh-CN":
        warnings.append(
            f"ui_language is {ui_lang!r}, expected 'zh-CN'."
        )

    # 2. CJK coverage
    fields = _gather_text_values(doc)
    checked = len(fields)
    cjk_hits = sum(1 for _, t in fields if _has_cjk(t))
    ratio = (cjk_hits / checked) if checked else 0.0

    if ratio < args.min_cjk_ratio:
        errors.append(
            f"CJK coverage on interpretive fields is {ratio:.2f} "
            f"({cjk_hits}/{checked}); minimum is {args.min_cjk_ratio:.2f}. "
            "Most explanatory content is still in English."
        )

    # 3. Long English paragraphs (carryover risk)
    long_en_hits = [name for name, t in fields if _has_long_english(t)]
    if long_en_hits:
        warnings.append(
            f"Found {len(long_en_hits)} interpretive field(s) with a "
            f"long English blob (>=30 ASCII chars without CJK). "
            f"Examples: {long_en_hits[:3]}. These may be carryover from "
            "the English draft that should be translated."
        )

    # 4. Glossary count + CJK in definitions
    g = doc.get("glossary") or []
    g_count = len(g) if isinstance(g, list) else 0
    if g_count < args.min_glossary:
        errors.append(
            f"glossary has {g_count} entries; minimum is {args.min_glossary}."
        )
    if g_count > 0:
        defs_with_cjk = sum(
            1 for item in g
            if isinstance(item, dict) and _has_cjk(item.get("definition") or "")
        )
        if defs_with_cjk < g_count:
            warnings.append(
                f"glossary: {g_count - defs_with_cjk}/{g_count} definitions "
                "do not contain Chinese characters."
            )

    # 5. Claims-Evidence count + evidence labels
    cem = doc.get("claims_evidence_map") or []
    cem_count = len(cem) if isinstance(cem, list) else 0
    if cem_count < args.min_claims:
        errors.append(
            f"claims_evidence_map has {cem_count} entries; "
            f"minimum is {args.min_claims}."
        )

    label_counts: dict = {}
    bad_labels: list = []
    for c in cem:
        if not isinstance(c, dict):
            continue
        ev = c.get("evidence_label")
        if ev not in VALID_EVIDENCE_LABELS:
            bad_labels.append(str(ev))
        else:
            label_counts[ev] = label_counts.get(ev, 0) + 1
    if bad_labels:
        errors.append(
            f"claims_evidence_map contains invalid evidence_label values: {bad_labels[:5]}"
        )

    paper_ev = label_counts.get("[Paper evidence]", 0)
    figure_ev = label_counts.get("[Figure/Table evidence]", 0)
    author_ev = label_counts.get("[Author claim]", 0)

    reading_mode = (doc.get("paper_metadata") or {}).get("reading_mode", "")
    if reading_mode == "full_text" and cem_count > 0:
        if paper_ev == 0 and figure_ev == 0:
            warnings.append(
                f"reading_mode = full_text but no claim uses "
                f"[Paper evidence] or [Figure/Table evidence] "
                f"({author_ev} claims are [Author claim]). "
                "This is suspicious — a real full_text reading should "
                "ground at least some claims in the paper's own text/figures."
            )
        if cem_count > 0 and author_ev == cem_count:
            warnings.append(
                f"All {cem_count} claims use [Author claim]. "
                "In full_text mode, this usually means the operator did "
                "not actually ground claims in the paper body."
            )

    # Claims CJK: at least one of (claim_text, comment) should have CJK.
    if cem_count > 0:
        claims_with_cjk = 0
        for c in cem:
            if not isinstance(c, dict):
                continue
            if _has_cjk(c.get("claim_text") or "") or _has_cjk(c.get("comment") or c.get("notes") or ""):
                claims_with_cjk += 1
        if claims_with_cjk < cem_count * 0.5:
            warnings.append(
                f"Only {claims_with_cjk}/{cem_count} claims have Chinese in "
                "claim_text or comment."
            )

    # 6. Final checklist
    fc = doc.get("final_checklist") or []
    fc_count = len(fc) if isinstance(fc, list) else 0
    if fc_count < args.min_checklist:
        errors.append(
            f"final_checklist has {fc_count} items; minimum is {args.min_checklist}."
        )
    if fc_count > 0:
        q_with_cjk = 0
        for item in fc:
            q = ""
            if isinstance(item, dict):
                q = item.get("question") or ""
            elif isinstance(item, str):
                q = item
            if _has_cjk(q):
                q_with_cjk += 1
        if q_with_cjk < fc_count * 0.5:
            warnings.append(
                f"Only {q_with_cjk}/{fc_count} final_checklist questions "
                "are in Chinese."
            )

    # 7. Pass depth for full_text
    if reading_mode == "full_text":
        p2 = doc.get("pass2") or {}
        p3 = doc.get("pass3") or {}
        p2_mi = p2.get("main_ideas") or []
        p3_mr = p3.get("method_reconstruction") or []
        if not p2_mi or all(not (m or "").strip() for m in p2_mi):
            errors.append(
                "reading_mode = full_text but pass2.main_ideas is empty. "
                "Pass 2 is required for full_text."
            )
        if not p3_mr or all(not (m or "").strip() for m in p3_mr):
            errors.append(
                "reading_mode = full_text but pass3.method_reconstruction is "
                "empty. Pass 3 is required for full_text."
            )

    # 8. Summaries shape
    s = doc.get("summaries") or {}
    if not (s.get("one_sentence") or "").strip():
        errors.append("summaries.one_sentence is empty.")
    three = s.get("three_sentence")
    if not (isinstance(three, list) and any((x or "").strip() for x in three)):
        errors.append("summaries.three_sentence is empty.")
    ten = s.get("ten_sentence")
    if not (isinstance(ten, list) and len([x for x in ten if (x or "").strip()]) >= 5):
        recommendations.append(
            "summaries.ten_sentence has fewer than 5 non-empty items."
        )

    # 9. Status
    if errors:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    # 10. v0.2.8 — source_resolution check (zh-CN target).
    #    Sits at WARN level and never overwrites content quality
    #    errors; the gate status is set by section 9 above, this block
    #    only appends source_resolution_check to the result and a
    #    recommendation if the user should re-confirm the paper.
    sr_check: "OrderedDict[str, object]" = OrderedDict()
    sr_check["structured"] = False
    sr_check["legacy_fallback"] = False
    sr_check["resolver_status"] = None
    sr_check["warnings"] = []
    sr_check["errors"] = []
    top = doc.get("source_resolution")
    sr_check["structured"] = bool(_is_structured_sr(top))
    if not sr_check["structured"]:
        iq0 = doc.get("intake_quality") or {}
        sr_check["legacy_fallback"] = bool(iq0.get("source_resolution"))
        if sr_check["legacy_fallback"]:
            sr_check["warnings"].append(
                "legacy intake_quality.source_resolution detected; "
                "top-level structured source_resolution recommended"
            )
        else:
            sr_check["warnings"].append(
                "source_resolution is missing; top-level structured block recommended"
            )
    else:
        s = _summarize_sr(doc)
        sr_check["resolver_status"] = s.get("resolver_status")
        if s.get("resolver_status") in ("error", "ambiguous_clue"):
            sr_check["warnings"].append(
                f"source_resolution.resolver_status={s.get('resolver_status')}; "
                "ask the user to confirm the paper identity before publishing"
            )
        if s.get("resolver_status") == "error" and s.get("degraded"):
            sr_check["warnings"].append(
                f"source_resolution.degraded={s.get('degraded')}; "
                "the run finished but the paper identity is not confirmed"
            )
        if not (s.get("matched_canonical_title") or s.get("matched_arxiv_id")):
            sr_check["warnings"].append(
                "source_resolution.matched_canonical_title and "
                "matched_arxiv_id are both empty; please verify the paper"
            )
    # Source-resolution warnings must NOT fail the gate. They surface as
    # recommendations, which do not affect status.
    for w in sr_check["warnings"]:
        recommendations.append(f"source_resolution_check: {w}")

    return OrderedDict([
        ("status", status),
        ("target_language", target_lang),
        ("ui_language", ui_lang),
        ("reading_mode", reading_mode),
        ("cjk_coverage", OrderedDict([
            ("checked_fields", checked),
            ("fields_with_cjk", cjk_hits),
            ("ratio", round(ratio, 3)),
            ("long_english_paragraphs", len(long_en_hits)),
        ])),
        ("counts", OrderedDict([
            ("claims", cem_count),
            ("glossary_terms", g_count),
            ("checklist_items", fc_count),
        ])),
        ("evidence_label_distribution", label_counts),
        ("source_resolution_check", sr_check),
        ("errors", errors),
        ("warnings", warnings),
        ("recommendations", recommendations),
    ])


def render_text(result: dict) -> str:
    lines: list = []
    lines.append(f"Quality gate status: {result['status']}")
    lines.append(
        f"target_language = {result['target_language']!r}, "
        f"ui_language = {result['ui_language']!r}, "
        f"reading_mode = {result['reading_mode']!r}"
    )
    cjk = result["cjk_coverage"]
    lines.append(
        f"CJK coverage: {cjk['fields_with_cjk']}/{cjk['checked_fields']} "
        f"({cjk['ratio']:.2f}); long_en_blobs = {cjk['long_english_paragraphs']}"
    )
    counts = result["counts"]
    lines.append(
        f"Counts: claims={counts['claims']}, "
        f"glossary_terms={counts['glossary_terms']}, "
        f"checklist_items={counts['checklist_items']}"
    )
    if result["evidence_label_distribution"]:
        dist = ", ".join(
            f"{k}={v}" for k, v in result["evidence_label_distribution"].items()
        )
        lines.append(f"Evidence labels: {dist}")
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
    p = argparse.ArgumentParser(
        description="zh-CN quality gate for paper_reading.json",
    )
    p.add_argument("--input", required=True, help="Path to paper_reading.json")
    p.add_argument("--json-output", help="Write JSON report to this path")
    p.add_argument("--warn-only", action="store_true",
                   help="Do not exit non-zero on WARN")
    p.add_argument("--min-cjk-ratio", type=float, default=0.5,
                   help="Minimum CJK coverage ratio on interpretive fields (default 0.5)")
    p.add_argument("--min-claims", type=int, default=8,
                   help="Minimum claims_evidence_map entries (default 8)")
    p.add_argument("--min-glossary", type=int, default=10,
                   help="Minimum glossary entries (default 10)")
    p.add_argument("--min-checklist", type=int, default=8,
                   help="Minimum final_checklist items (default 8)")
    args = p.parse_args(argv)

    path = Path(args.input)
    if not path.exists():
        print(f"[error] --input file does not exist: {path}", file=sys.stderr)
        return 2
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[error] invalid JSON in {path}: {e}", file=sys.stderr)
        return 2

    result = run_quality_gate(doc, args)
    sys.stdout.write(render_text(result))
    if args.json_output:
        out = Path(args.json_output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[ok] wrote quality gate report: {out}")
    if result["status"] == "FAIL":
        return 1
    if result["status"] == "WARN" and not args.warn_only:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
