#!/usr/bin/env python3
"""
run_paper_reading.py — paper-three-pass-reader (v0.2.1-alpha)

One-command runner that turns a weak or complete paper-shaped input into a
standard run directory + draft `paper_reading.json` + (optional) agent fill
pack + (optional) audit + (optional) rendered HTML page + (optional)
published GitHub Page.

Usage (minimal):
    python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
        --input "Attention Is All You Need" \
        --input-kind paper_title \
        --slug runner-title-attention \
        --output-root runs/runner-smoke-20260615 \
        --render

Usage (with publish):
    python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
        --input "Attention Is All You Need" \
        --input-kind paper_title \
        --slug runner-title-attention \
        --output-root runs/runner-smoke-20260615 \
        --render --publish \
        --repo conanxin/paper-reading-pages \
        --branch gh-pages \
        --page-title "Runner Smoke: Attention Is All You Need"

Design rules:
- Stdlib only (argparse, json, subprocess, pathlib, sys).
- Creates a standard run directory layout under <output-root>/<slug>/:
    input/          (the original input, captured for the audit trail)
    source/         (downloaded PDFs — not auto-downloaded by this runner)
    extracted/      (extracted text — not auto-extracted by this runner)
    work/           (the draft paper_reading.json — the main artifact)
    paper-reading-output/  (rendered page, only if --render)
- The runner does NOT attempt to deep-read the paper. It produces a DRAFT
  paper_reading.json that the operator (human or agent) fills in.
- Reading modes are strictly enforced:
    - abstract_only / screenshot_only → Pass 2 / Pass 3 marked unavailable
    - full_text allowed ONLY when the operator has manually provided the body
      in <slug>/extracted/ AND has explicitly set --reading-mode full_text.
- A small built-in resolver hints table maps well-known inputs to canonical
  arXiv IDs / DOIs / repo URLs. Anything not in the table becomes an
  ambiguous_clue with reading_mode = partial_text by default.

This is the v0.2 first step. It is a workflow scaffold, not a paper reader.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

# v0.2.6: shared resolver hints live in resolver_hints.py + data/resolver_hints.json.
# Keep RESOLVER_HINTS as a backwards-compatible alias built from the shared data so
# downstream code that imports it (including historical tests) still works.
import os as _os
import re as _re  # noqa: F401  -- keep for legacy callers
_HERE_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _HERE_DIR not in sys.path:
    sys.path.insert(0, _HERE_DIR)
from resolver_hints import load_hints as _rh_load_hints  # noqa: E402

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
RENDER_SCRIPT = HERE / "render_page.py"
PUBLISH_SCRIPT = HERE / "publish_output_to_github.sh"

VALID_INPUT_KINDS = {
    "complete_paper", "paper_url", "paper_identifier", "paper_title",
    "paper_metadata", "paper_excerpt", "paper_image", "paper_screenshot",
    "paper_topic", "project_or_repo", "ambiguous_clue",
}
VALID_READING_MODES = {"full_text", "partial_text", "abstract_only", "screenshot_only"}
VALID_DECISIONS = {"CONTINUE_FULL", "CONTINUE_PARTIAL", "STOP", "SEEK_REFERENCES_FIRST"}

# Built-in resolver hints — v0.2.6 unified into data/resolver_hints.json.
# Backwards-compatible: we now build the historical RESOLVER_HINTS dict from the
# shared JSON, so existing code paths keep working but the source of truth is the
# shared file. New code should use resolver_hints.resolve_any() directly.
def _build_legacy_resolver_hints() -> "dict":
    h = _rh_load_hints()
    out: "dict" = {}
    for p in h.get("papers", []):
        if not isinstance(p, dict):
            continue
        canonical = p.get("canonical_title")
        if not canonical:
            continue
        hint = {
            "title": canonical,
            "authors": p.get("authors") or [],
            "year": int(p["year"]) if str(p.get("year", "")).isdigit() else p.get("year"),
            "venue": p.get("venue"),
            "arxiv_id": p.get("arxiv_id"),
            "url": p.get("paper_url"),
            "field": p.get("field"),
            "category": p.get("field"),  # historical alias
            "default_reading_mode": "full_text" if p.get("arxiv_id") else "abstract_only",
        }
        # Index by canonical title (lowercased)
        out[canonical.lower()] = hint
        # Index by alias (lowercased) so historical keys keep matching
        for alias in p.get("aliases") or []:
            if alias and alias.lower() not in out:
                out[alias.lower()] = dict(hint)
    # Add repo hints: key is the GitHub URL itself
    for rh in h.get("repo_hints", []):
        url = rh.get("repo_url")
        pid = rh.get("paper_id")
        if not url or not pid:
            continue
        # Find the paper for this repo
        paper = next(
            (p for p in h.get("papers", []) if isinstance(p, dict) and p.get("id") == pid),
            None,
        )
        if not paper:
            continue
        out[url] = {
            "title": paper.get("canonical_title"),
            "authors": paper.get("authors") or [],
            "year": int(paper["year"]) if str(paper.get("year", "")).isdigit() else paper.get("year"),
            "venue": paper.get("venue"),
            "arxiv_id": paper.get("arxiv_id"),
            "url": paper.get("paper_url"),
            "field": paper.get("field"),
            "category": paper.get("field"),
            "default_reading_mode": "full_text" if paper.get("arxiv_id") else "abstract_only",
            "source_kind_override": "project_or_repo",
        }
    return out


RESOLVER_HINTS = _build_legacy_resolver_hints()


def _resolve_hint(text: str, requested_kind: str):
    """Look up canonical hints. Returns (hint_dict or None, normalized_key).

    v0.2.6: prefer the shared resolver (which supports title aliases, arXiv
    extraction, and repo URL fragment matching); fall back to the legacy
    substring matcher for backwards compatibility.
    """
    if not text:
        return None, ""
    norm = text.strip().lower()

    # Prefer shared resolver (handles aliases, arXiv, repo fragments)
    try:
        from resolver_hints import resolve_any as _rh_resolve_any  # noqa: WPS433
        r = _rh_resolve_any(text, requested_kind or "ambiguous_clue")
        paper = r.get("paper") or {}
        if paper and r.get("status") in ("matched",):
            return {
                "title": paper.get("canonical_title"),
                "authors": paper.get("authors") or [],
                "year": int(paper["year"]) if str(paper.get("year", "")).isdigit() else paper.get("year"),
                "venue": paper.get("venue"),
                "arxiv_id": paper.get("arxiv_id"),
                "url": paper.get("paper_url"),
                "field": paper.get("field"),
                "category": paper.get("field"),
                "default_reading_mode": "full_text" if paper.get("arxiv_id") else "abstract_only",
                "source_kind_override": "project_or_repo" if "github.com" in (text or "").lower() else None,
            }, norm
    except Exception:  # noqa: BLE001
        pass

    # Fallback: legacy substring matcher over RESOLVER_HINTS
    if norm in RESOLVER_HINTS:
        return RESOLVER_HINTS[norm], norm
    if text.startswith("http://") or text.startswith("https://"):
        if text in RESOLVER_HINTS:
            return RESOLVER_HINTS[text], norm
        if text.rstrip("/") in RESOLVER_HINTS:
            return RESOLVER_HINTS[text.rstrip("/")], norm
    for key, hint in RESOLVER_HINTS.items():
        if key.startswith("http"):
            continue
        if len(key) >= 5 and key in norm:
            return hint, key
    return None, norm


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug_safe(s: str) -> str:
    out = []
    for ch in s:
        if ch.isalnum() or ch in "._-":
            out.append(ch)
        elif ch in " \t":
            out.append("-")
    s2 = "".join(out).strip("-")
    return s2 or "x"


def make_draft(args, hint) -> dict:
    """Build a draft paper_reading.json from runner args + (optional) hint."""
    # Paper metadata
    if hint:
        title = args.title or hint.get("title") or args.input
        authors = args.authors or hint.get("authors") or []
        year = args.year or hint.get("year")
        venue = hint.get("venue")
        arxiv_id = args.arxiv_id or hint.get("arxiv_id")
        url = args.paper_url or hint.get("url")
        field = hint.get("field")
        category = hint.get("category")
        source_kind = args.input_kind
        if hint.get("source_kind_override"):
            source_kind = hint["source_kind_override"]
    else:
        title = args.title or args.input
        authors = args.authors or []
        year = args.year
        venue = None
        arxiv_id = args.arxiv_id
        url = args.paper_url
        field = None
        category = None
        source_kind = args.input_kind

    if not isinstance(authors, list):
        authors = [authors] if authors else []
    if isinstance(year, str):
        try:
            year = int(year)
        except Exception:
            year = None

    # Reading mode discipline.
    # Priority: user override > input-kind-forced mode > hint default.
    if args.input_kind == "paper_excerpt":
        kind_forced_mode = "abstract_only"
    elif args.input_kind == "paper_screenshot":
        kind_forced_mode = "screenshot_only"
    else:
        kind_forced_mode = None

    if args.reading_mode:
        reading_mode = args.reading_mode
    elif kind_forced_mode:
        reading_mode = kind_forced_mode
    elif hint and hint.get("default_reading_mode"):
        reading_mode = hint["default_reading_mode"]
    else:
        reading_mode = "partial_text"

    needs_confirmation = hint is None  # hint not found → ask the user

    # Confidence heuristic
    if hint is not None:
        confidence = "high"
    elif reading_mode in ("abstract_only", "screenshot_only"):
        confidence = "medium"
    else:
        confidence = "low"

    # Build metadata
    paper_metadata = OrderedDict([
        ("title", title),
        ("authors", authors),
        ("year", year),
        ("venue", venue),
        ("identifiers", OrderedDict([
            ("arxiv_id", arxiv_id),
            ("doi", None),
            ("openreview_id", None),
            ("url", url),
        ])),
        ("source_kind", source_kind),
        ("reading_mode", reading_mode),
        ("field", field),
        ("category", category),
    ])

    # Intake quality
    missing_fields = []
    if not arxiv_id:
        missing_fields.append("arxiv_id")
    if not year:
        missing_fields.append("year")
    if not authors:
        missing_fields.append("authors")
    if reading_mode != "full_text":
        missing_fields.extend(["full_body_text", "full_references", "full_figures", "full_tables"])
    if reading_mode == "abstract_only":
        missing_fields.append("abstract_only_no_body")

    warnings = [
        "Draft generated by run_paper_reading.py v0.2.0-alpha.",
        "This is a DRAFT paper_reading.json. The operator (human or agent) must "
        "fill in the interpretive content before treating the page as a real reading.",
        "Pass 1 / Pass 2 / Pass 3 notes below are SKELETON placeholders, not actual readings.",
    ]
    if hint is None:
        warnings.append(
            "Input did not match any built-in resolver hint. "
            "Canonical identification is NOT confirmed; needs human confirmation."
        )
    if reading_mode in ("abstract_only", "screenshot_only"):
        warnings.append(
            f"reading_mode = {reading_mode}. Pass 2 / Pass 3 must remain "
            "marked unavailable unless the body is later supplied and reading_mode "
            "is upgraded to full_text."
        )

    intake_quality = OrderedDict([
        ("input_kind", source_kind),
        ("reading_mode", reading_mode),
        ("confidence", confidence),
        ("needs_confirmation", needs_confirmation),
        ("missing_fields", missing_fields),
        ("warnings", warnings),
        ("ambiguities", [] if hint else [f"No resolver hint matched for: {args.input!r}"]),
        ("source_used", (
            f"runner hint: {hint['title']}" if hint
            else f"runner: no hint matched for input {args.input!r}"
        )),
        ("extraction_quality", "n/a — runner did not fetch the body"),
        ("source_resolution", [
            f"Input kind = {source_kind}.",
            f"Input string: {args.input!r}.",
            (f"Matched resolver hint: {args.input!r} → {hint['title']} (arXiv {hint.get('arxiv_id')})"
             if hint else
             f"No resolver hint matched for {args.input!r}. needs_confirmation = true."),
            "Runner did NOT fetch the paper body. Operator must supply the body "
            "(PDF → extracted text) or upgrade reading_mode manually.",
        ]),
    ])

    # Summaries (DRAFT placeholders)
    summaries = OrderedDict([
        ("one_sentence", "[DRAFT — fill after reading]"),
        ("three_sentence", ["[DRAFT]", "[DRAFT]", "[DRAFT]"]),
        ("ten_sentence", ["[DRAFT]"] * 10),
    ])

    # Five Cs (DRAFT placeholders)
    five_cs = OrderedDict([
        ("category", "[DRAFT — fill after reading]"),
        ("context", "[DRAFT — fill after reading]"),
        ("correctness", "[DRAFT — fill after reading]"),
        ("contributions", ["[DRAFT — fill after reading]"]),
        ("clarity", "[DRAFT — fill after reading]"),
    ])

    # Pass 1 / 2 / 3 (DRAFT placeholders)
    pass1 = OrderedDict([
        ("bird_eye_notes", "[DRAFT — fill after Pass 1]"),
        ("decision", "SEEK_REFERENCES_FIRST" if needs_confirmation else "CONTINUE_FULL"),
        ("decision_rationale",
         "[DRAFT — fill after Pass 1]"
         + (" — input not in resolver hints; seek references before continuing"
            if needs_confirmation else "")),
    ])
    pass2 = OrderedDict([
        ("main_ideas", ["[DRAFT — unavailable until body is available]"
                        if reading_mode in ("abstract_only", "screenshot_only") else
                        "[DRAFT — fill after Pass 2]"]),
        ("method_summary", "[DRAFT — fill after Pass 2]"
                           if reading_mode != "abstract_only"
                           else "[DRAFT — unavailable until body is available]"),
        ("figure_table_notes", "[DRAFT — fill after Pass 2]"
                               if reading_mode != "abstract_only"
                               else "[DRAFT — unavailable until body is available]"),
        ("key_references", []),
        ("claims_evidence_map", [
            OrderedDict([
                ("claim_id", "C-DRAFT-001"),
                ("claim_text", "[DRAFT — fill after Pass 2]"),
                ("evidence_label",
                 "[Needs verification]" if reading_mode in ("abstract_only", "screenshot_only") else
                 "[Paper evidence]"),
                ("evidence_location", "[DRAFT — fill after Pass 2]"),
                ("evidence_kind", "paper_text"),
                ("confidence", "low"),
                ("notes", "Skeleton claim generated by runner. Replace with a real claim after reading."),
                ("needs_verification", True),
            ])
        ]),
    ])
    pass3 = OrderedDict([
        ("method_reconstruction", [
            "[DRAFT — unavailable until body is available]"
            if reading_mode in ("abstract_only", "screenshot_only") else
            "[DRAFT — fill after Pass 3]"
        ]),
        ("critical_review", ["[DRAFT — fill after Pass 3]"]),
        ("hidden_assumptions", ["[DRAFT — fill after Pass 3]"]),
        ("limitations", ["[DRAFT — fill after Pass 3]"]),
        ("reproduction_plan", OrderedDict([
            ("dataset", ""), ("baseline", ""), ("hardware", ""),
            ("steps", ["[DRAFT — fill after Pass 3]"]),
            ("sanity_checks", []), ("success_criteria", []),
        ])),
        ("future_work", ["[DRAFT — fill after Pass 3]"]),
        ("application_notes", ["[DRAFT — fill after Pass 3]"]),
    ])

    glossary = []
    limitations = [
        f"This is a DRAFT generated by run_paper_reading.py. Reading mode = {reading_mode}.",
        "Replace all [DRAFT] placeholders before treating the page as a real reading.",
    ]
    if reading_mode in ("abstract_only", "screenshot_only"):
        limitations.append(
            "Pass 2 / Pass 3 are explicitly NOT performed because the body is not available."
        )
    open_questions = ["[DRAFT — fill after Pass 3]"]
    final_checklist = [
        {"question": "Did I read the full paper (or only the input kind I was given)?", "answerable": True},
        {"question": "Am I clear about the reading mode in the hero badge?", "answerable": True},
        {"question": "Have I marked every interpretive claim with an evidence label?", "answerable": True},
        {"question": "Did I avoid pretending that I read Pass 2 / Pass 3 content I did not actually read?",
         "answerable": True},
        {"question": "Have I replaced every [DRAFT] placeholder in this paper_reading.json?",
         "answerable": True},
        {"question": "Do I know what I would need to do to upgrade reading_mode to full_text?",
         "answerable": True},
        {"question": "Have I documented the resolution trail (input → canonical paper → body) in intake_quality?",
         "answerable": True},
        {"question": "Did I check that claims only use [Author claim] / [Uncertain] / [Needs verification] "
                     "when the body is not available?", "answerable": True},
    ]

    paper_outline = []
    source_resolution = intake_quality["source_resolution"]
    candidate_papers = [] if hint else [{"input": args.input, "rank": 1, "rationale": "no hint matched"}]

    figures_tables = []

    draft = OrderedDict([
        ("schema_version", "0.1.0"),
        ("target_language", args.language),
        ("ui_language", args.language),
        ("paper_metadata", paper_metadata),
        ("intake_quality", intake_quality),
        ("summaries", summaries),
        ("five_cs", five_cs),
        ("pass1", pass1),
        ("pass2", pass2),
        ("pass3", pass3),
        ("claims_evidence_map", pass2["claims_evidence_map"]),
        ("figures_tables", figures_tables),
        ("glossary", glossary),
        ("limitations", limitations),
        ("reproduction_plan", pass3["reproduction_plan"]),
        ("open_questions", open_questions),
        ("final_checklist", final_checklist),
        ("paper_outline", paper_outline),
        ("source_resolution", OrderedDict([("steps", source_resolution)])),
        ("candidate_papers", candidate_papers),
    ])
    return draft


def write_run_layout(out_root: Path, slug: str, args) -> tuple[Path, Path, Path, Path, Path, Path]:
    """Create the standard run directory layout. Returns paths."""
    run_dir = out_root / slug
    input_dir = run_dir / "input"
    source_dir = run_dir / "source"
    extracted_dir = run_dir / "extracted"
    work_dir = run_dir / "work"
    output_dir = run_dir / "paper-reading-output"

    for d in (input_dir, source_dir, extracted_dir, work_dir, output_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Capture the input to input/input.md (audit trail).
    input_md = input_dir / "input.md"
    if args.input_file:
        try:
            content = Path(args.input_file).read_text(encoding="utf-8")
        except Exception as e:
            print(f"[warn] could not read input file: {e}", file=sys.stderr)
            content = f"(could not read input file: {args.input_file})\n"
    else:
        content = args.input or ""
    header = (
        f"# Captured input for run {slug}\n\n"
        f"- input_kind: `{args.input_kind}`\n"
        f"- runner: paper-three-pass-reader v0.2.0-alpha\n"
        f"- captured_at: {_now_iso()}\n\n"
        f"## Raw input\n\n```\n{content}\n```\n"
    )
    input_md.write_text(header, encoding="utf-8")

    return run_dir, input_dir, source_dir, extracted_dir, work_dir, output_dir


def main(argv=None):
    p = argparse.ArgumentParser(description="One-command paper reading runner (v0.2.1-alpha).")
    p.add_argument("--input", help="Raw input string (e.g. title, URL, repo URL).")
    p.add_argument("--input-file", help="Path to a file containing the raw input.")
    p.add_argument("--input-kind", required=True,
                   choices=sorted(VALID_INPUT_KINDS),
                   help="What kind of input this is.")
    p.add_argument("--slug", required=True,
                   help="Slug for the run directory (must match [A-Za-z0-9._-]+).")
    p.add_argument("--output-root", required=True,
                   help="Root directory under which <slug>/ will be created.")
    p.add_argument("--title", help="Override paper title.")
    p.add_argument("--authors", help="Override paper authors (comma-separated).")
    p.add_argument("--year", help="Override paper year.")
    p.add_argument("--arxiv-id", help="Override arXiv ID.")
    p.add_argument("--paper-url", help="Override paper URL.")
    p.add_argument("--reading-mode", choices=sorted(VALID_READING_MODES),
                   help="Override reading mode (default: derived from input kind / hint).")
    p.add_argument("--render", action="store_true",
                   help="Render the page after writing the draft JSON.")
    p.add_argument("--publish", action="store_true",
                   help="Publish the rendered page to GitHub Pages (requires --render).")
    p.add_argument("--repo", help="Target repo for --publish (e.g. conanxin/paper-reading-pages).")
    p.add_argument("--branch", default="gh-pages", help="Branch for --publish (default gh-pages).")
    p.add_argument("--site-path", help="Site path for --publish (defaults to --slug).")
    p.add_argument("--page-title", help="Page title for --publish.")
    p.add_argument("--fill-pack", action="store_true",
                   help="Write an Agent Fill Pack into <run_dir>/fill-pack/ "
                        "with per-stage instructions and field checklist.")
    p.add_argument("--audit", action="store_true",
                   help="Run audit_paper_reading.py after writing the draft. "
                        "Blocks --render on FAIL unless --audit-warn-only.")
    p.add_argument("--audit-warn-only", action="store_true",
                   help="Treat audit WARN as PASS for the purpose of "
                        "deciding whether to render / publish.")
    p.add_argument("--quality-gate", action="store_true",
                   help="Run the zh-CN quality gate after the audit (no-op "
                        "for non-zh-CN runs). Blocks --render on FAIL unless "
                        "--audit-warn-only is also set.")
    p.add_argument("--agent-profile", default="default",
                   choices=["default", "strict", "beginner", "researcher", "engineer"],
                   help="Tone of the fill-pack instructions. Default 'default'.")
    p.add_argument("--language", default="zh-CN",
                   choices=["zh-CN", "en"],
                   help="Language of fill-pack instructions. Default 'zh-CN'.")
    p.add_argument("--max-claims", type=int, default=8,
                   help="Suggested maximum number of claims for the fill pack.")
    p.add_argument("--max-figures", type=int, default=6,
                   help="Suggested maximum number of figure/table slots.")
    args = p.parse_args(argv)

    # Validate inputs.
    if not args.input and not args.input_file:
        print("[error] either --input or --input-file is required", file=sys.stderr)
        return 2
    if args.input and args.input_file:
        print("[error] pass only one of --input or --input-file", file=sys.stderr)
        return 2
    if not _SLUG_SAFE_RE.match(args.slug):
        print("[error] --slug must match [A-Za-z0-9._-]+", file=sys.stderr)
        return 2
    if args.publish and not args.render:
        print("[error] --publish requires --render", file=sys.stderr)
        return 2
    if args.publish and not args.repo:
        print("[error] --publish requires --repo", file=sys.stderr)
        return 2
    if args.publish and not args.site_path:
        args.site_path = args.slug
    if args.publish and not args.page_title:
        # Default page title = slug.
        args.page_title = args.slug

    if args.authors and "," in args.authors:
        args.authors = [a.strip() for a in args.authors.split(",") if a.strip()]

    # Resolve input string.
    input_text = args.input
    if args.input_file:
        try:
            input_text = Path(args.input_file).read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"[error] could not read --input-file: {e}", file=sys.stderr)
            return 2

    # Look up hint.
    hint, _ = _resolve_hint(input_text, args.input_kind)
    if hint:
        print(f"[info] resolved hint for: {input_text!r} → {hint['title']}")

    # Create run layout.
    out_root = Path(args.output_root).resolve()
    run_dir, input_dir, source_dir, extracted_dir, work_dir, output_dir = write_run_layout(
        out_root, args.slug, args)

    # Write draft JSON.
    draft = make_draft(args, hint)
    work_json = work_dir / "paper_reading.json"
    work_json.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    print(f"[ok] wrote draft: {work_json}")
    print(f"[ok] run layout:  {run_dir}")
    print(f"[ok] reading_mode = {draft['paper_metadata']['reading_mode']}, "
          f"confidence = {draft['intake_quality']['confidence']}, "
          f"needs_confirmation = {draft['intake_quality']['needs_confirmation']}")

    # Audit?
    audit_status = None
    audit_result_path = None
    if args.audit:
        AUDIT_SCRIPT = HERE / "audit_paper_reading.py"
        audit_result_path = work_dir / "audit_result.json"
        audit_cmd = [
            sys.executable, str(AUDIT_SCRIPT),
            "--input", str(work_json),
        ]
        if args.audit_warn_only:
            audit_cmd.append("--warn-only")
        audit_cmd.extend(["--json-output", str(audit_result_path)])
        print(f"[info] running audit: {' '.join(audit_cmd)}")
        rc = subprocess.call(audit_cmd)
        # Note: audit_paper_reading.py returns 1 on FAIL and 0 on PASS/WARN.
        # We do NOT exit on rc != 0 — the fill-pack (if requested) is exactly
        # the task list to fix the audit findings, so it should still be written.
        # Render/publish is gated below by audit_status.
        if rc != 0:
            print(f"[warn] audit_paper_reading.py exited {rc} (audit FAIL). "
                  "Continuing to write fill-pack; render/publish will be blocked.",
                  file=sys.stderr)
        try:
            audit_doc = json.loads(audit_result_path.read_text(encoding="utf-8"))
            audit_status = audit_doc.get("status")
        except Exception:
            audit_doc = None
            audit_status = None
        print(f"[ok] audit status: {audit_status}  ({audit_result_path})")

        # Write a short markdown summary next to the JSON.
        reports_dir = run_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        try:
            audit_md = reports_dir / "audit_summary.md"
            lines = [
                f"# Audit summary for {args.slug}",
                "",
                f"- status: **{audit_status}**",
                f"- reading_mode: `{draft['paper_metadata']['reading_mode']}`",
                f"- input_kind: `{draft['intake_quality']['input_kind']}`",
                f"- audit_json: `work/audit_result.json`",
                "",
            ]
            if audit_doc:
                cnt = audit_doc.get("counts") or {}
                lines.append("## Counts")
                lines.append("")
                lines.append(f"- claims_total: {cnt.get('claims_total')}")
                lines.append(f"- claims_with_valid_evidence: {cnt.get('claims_with_valid_evidence')}")
                lines.append(f"- final_checklist_questions: {cnt.get('final_checklist_questions')}")
                lines.append(f"- draft_placeholders: {cnt.get('draft_placeholders')}")
                lines.append("")
                if audit_doc.get("errors"):
                    lines.append("## Errors")
                    lines.append("")
                    for e in audit_doc["errors"]:
                        lines.append(f"- {e}")
                    lines.append("")
                if audit_doc.get("warnings"):
                    lines.append("## Warnings")
                    lines.append("")
                    for w in audit_doc["warnings"]:
                        lines.append(f"- {w}")
                    lines.append("")
                if audit_doc.get("recommendations"):
                    lines.append("## Recommendations")
                    lines.append("")
                    for r in audit_doc["recommendations"]:
                        lines.append(f"- {r}")
                    lines.append("")
            audit_md.write_text("\n".join(lines), encoding="utf-8")
            print(f"[ok] wrote audit summary: {audit_md}")
        except Exception as e:
            print(f"[warn] could not write audit_summary.md: {e}", file=sys.stderr)

    # Fill pack?
    if args.fill_pack:
        from importlib import util as _importlib_util
        _fp_writer_path = HERE / "fill_pack_writer.py"
        _spec = _importlib_util.spec_from_file_location("fill_pack_writer", str(_fp_writer_path))
        if _spec is None or _spec.loader is None:
            print(f"[error] could not load fill_pack_writer from {_fp_writer_path}",
                  file=sys.stderr)
            return 2
        _fp_mod = _importlib_util.module_from_spec(_spec)
        _spec.loader.exec_module(_fp_mod)
        fp_dir = run_dir / "fill-pack"
        _fp_mod.write_fill_pack(
            run_dir=run_dir,
            work_json=work_json,
            draft=draft,
            out_dir=fp_dir,
            agent_profile=args.agent_profile,
            language=args.language,
            max_claims=args.max_claims,
            max_figures=args.max_figures,
        )
        print(f"[ok] wrote fill pack: {fp_dir}")

    # Decide whether to render / publish when audit is on.
    block_render = False
    if args.audit and audit_status == "FAIL":
        if not args.audit_warn_only:
            block_render = True
            print("[error] audit status FAIL; refusing to render. "
                  "Fix the JSON or pass --audit-warn-only.", file=sys.stderr)

    # Optional: zh-CN quality gate (v0.2.4+).
    if args.quality_gate and args.language == "zh-CN":
        qg_script = HERE / "quality_gate_zh_cn.py"
        if not qg_script.exists():
            print(f"[warn] quality gate script missing: {qg_script}", file=sys.stderr)
        else:
            qg_out_json = work_dir / "quality_gate_zh_cn.json"
            qg_cmd = [
                sys.executable, str(qg_script),
                "--input", str(work_json),
                "--json-output", str(qg_out_json),
            ]
            print(f"[info] running quality gate: {' '.join(qg_cmd)}")
            qg_rc = subprocess.call(qg_cmd)
            if qg_rc == 0:
                qg_status = "PASS_OR_WARN"
            else:
                qg_status = "FAIL"
            if qg_status == "FAIL" and not args.audit_warn_only:
                block_render = True
                print("[error] quality gate status FAIL; refusing to render. "
                      "Fix the JSON or pass --audit-warn-only.", file=sys.stderr)
            # Also write a markdown summary alongside audit_summary.md.
            try:
                import json as _json
                qg_data = _json.loads(qg_out_json.read_text(encoding="utf-8"))
                qg_reports_dir = run_dir / "reports"
                qg_reports_dir.mkdir(parents=True, exist_ok=True)
                qg_md = qg_reports_dir / "quality_gate_zh_cn.md"
                lines = [
                    "# Quality Gate (zh-CN) — paper-three-pass-reader",
                    "",
                    f"- Status: **{qg_data.get('status')}**",
                    f"- target_language = {qg_data.get('target_language')!r}",
                    f"- ui_language = {qg_data.get('ui_language')!r}",
                    f"- reading_mode = {qg_data.get('reading_mode')!r}",
                ]
                cjk = qg_data.get("cjk_coverage", {})
                lines.append(
                    f"- CJK coverage: {cjk.get('fields_with_cjk', 0)}/"
                    f"{cjk.get('checked_fields', 0)} = {cjk.get('ratio', 0):.2f}"
                )
                counts = qg_data.get("counts", {})
                lines.append(
                    f"- counts: claims={counts.get('claims')}, "
                    f"glossary_terms={counts.get('glossary_terms')}, "
                    f"checklist_items={counts.get('checklist_items')}"
                )
                if qg_data.get("errors"):
                    lines.append("")
                    lines.append("## Errors")
                    for e in qg_data["errors"]:
                        lines.append(f"- {e}")
                if qg_data.get("warnings"):
                    lines.append("")
                    lines.append("## Warnings")
                    for w in qg_data["warnings"]:
                        lines.append(f"- {w}")
                qg_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
                print(f"[ok] wrote quality gate summary: {qg_md}")
            except Exception as e:  # noqa: BLE001
                print(f"[warn] could not write quality gate markdown: {e}", file=sys.stderr)

    # Render?
    if args.render and not block_render:
        rc = subprocess.call([
            sys.executable, str(RENDER_SCRIPT),
            "--input", str(work_json),
            "--output", str(output_dir),
        ])
        if rc != 0:
            print(f"[error] render_page.py exited {rc}", file=sys.stderr)
            return rc
        print(f"[ok] rendered: {output_dir / 'index.html'}")
    elif args.render and block_render:
        print("[skip] render skipped because audit FAILED.")

    # Publish?
    if args.publish and not block_render:
        cmd = [
            str(PUBLISH_SCRIPT),
            "--output", str(output_dir),
            "--repo", args.repo,
            "--branch", args.branch,
            "--site-path", args.site_path,
            "--page-title", args.page_title,
            "--message", f"Publish runner draft: {args.slug}",
        ]
        rc = subprocess.call(cmd)
        if rc != 0:
            print(f"[error] publish_output_to_github.sh exited {rc}", file=sys.stderr)
            return rc
        print(f"[ok] published: https://github.com/{args.repo}/tree/{args.branch}")
    elif args.publish and block_render:
        print("[skip] publish skipped because audit FAILED.")

    return 0


import re as _re
_SLUG_SAFE_RE = _re.compile(r"^[A-Za-z0-9._-]+$")


if __name__ == "__main__":
    sys.exit(main())
