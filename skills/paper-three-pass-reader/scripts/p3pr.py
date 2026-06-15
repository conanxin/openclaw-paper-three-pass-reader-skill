#!/usr/bin/env python3
"""
p3pr.py — paper-three-pass-reader (v0.2.5-alpha)

One-line CLI wrapper for the paper-reading skill.

This script does NOT do any deep reading on its own. It orchestrates the
existing runner / fill-pack / audit / zh-CN quality gate / renderer /
publisher into a single command:

    ./p3pr arxiv 2503.08102 --zh --full --publish
    ./p3pr title "Attention Is All You Need" --zh --full --publish
    ./p3pr abstract path/to/abstract.md --zh --publish
    ./p3pr screenshot path/to/screenshot-transcript.md --zh --publish
    ./p3pr repo https://github.com/google-research/bert --zh --full --publish
    ./p3pr pdf path/to/paper.pdf --zh --full --publish

All reading-time work is delegated to:
    - run_paper_reading.py       (draft + fill-pack + audit + render)
    - audit_paper_reading.py     (structural audit, optional --quality-gate)
    - quality_gate_zh_cn.py      (zh-CN bilingual discipline)
    - render_page.py             (HTML page)
    - publish_output_to_github.sh (GitHub Pages)

The CLI is stdlib-only.

Boundaries:
    - The CLI does NOT call external LLM APIs.
    - The CLI does NOT auto-fill the draft. The fill-pack is the task
      description; the agent / human fills it.
    - The CLI WILL refuse to publish a draft that fails the quality gate
      unless --allow-draft-publish is set.
    - The CLI WILL NOT pretend an abstract-only / screenshot-only draft
      is a full_text reading.

Exit codes:
    0  -- the run was created and (if --publish) the page was published.
    1  -- a quality gate or audit FAILed and the user did not allow it.
    2  -- usage / IO error.
    3  -- publish failed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# --- Paths --------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
PROJECT_ROOT = SKILL_ROOT.parent
SKILLS_DIR = PROJECT_ROOT  # /skills/paper-three-pass-reader/ scripts live HERE

RUNNER = HERE / "run_paper_reading.py"
AUDIT = HERE / "audit_paper_reading.py"
QUALITY_GATE = HERE / "quality_gate_zh_cn.py"
RENDER = HERE / "render_page.py"
PUBLISH_SH = HERE / "publish_output_to_github.sh"

DEFAULT_REPO = "conanxin/paper-reading-pages"
DEFAULT_BRANCH = "gh-pages"

# --- Resolver hints -----------------------------------------------------------
# v0.2.6: all hint data lives in skills/paper-three-pass-reader/data/resolver_hints.json
# and is loaded through resolver_hints.py. Do NOT add a separate HINTS dict here.
sys.path.insert(0, str(HERE))
from resolver_hints import (  # noqa: E402  -- import after sys.path tweak
    load_hints as _load_hints,
    resolve_title as _resolver_resolve_title,
    resolve_arxiv as _resolver_resolve_arxiv,
    resolve_repo as _resolver_resolve_repo,
    resolve_any as _resolver_resolve_any,
    paper_to_runner_overrides as _resolver_overrides,
)


def _resolve_hint(text: str):
    """Compatibility wrapper: returns a runner-style hint dict from the shared resolver.

    Returns None when the shared resolver has no match. The shape is intentionally
    compatible with the historical p3pr HINTS dict so downstream callers do not change.
    """
    if not text:
        return None
    res = _resolver_resolve_any(text, "ambiguous_clue")
    paper = res.get("paper") or {}
    if not paper:
        return None
    # Build a runner-style hint dict
    out = {
        "title": paper.get("canonical_title"),
        "arxiv_id": paper.get("arxiv_id"),
        "url": paper.get("paper_url"),
        "default_reading_mode": "full_text" if paper.get("arxiv_id") else "abstract_only",
        "year": int(paper["year"]) if str(paper.get("year", "")).isdigit() else paper.get("year"),
        "authors": paper.get("authors") or [],
        "venue": paper.get("venue"),
        "field": paper.get("field"),
        "category": paper.get("field"),  # the historical category key aliased to field
        "source_kind_override": "project_or_repo" if "github.com" in (text or "").lower() else None,
        "_resolver_status": res.get("status"),
        "_resolver_match_type": res.get("match_type"),
        "_resolver_confidence": res.get("confidence"),
        "_resolver_paper_id": paper.get("id"),
    }
    return out


# --- Helpers ------------------------------------------------------------------

_ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5}(v\d+)?)")


def _now() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _today() -> str:
    return datetime.now().strftime("%Y%m%d")


def _slugify(s: str, prefix: str = "", max_len: int = 60) -> str:
    """Build a safe slug from arbitrary text."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if prefix and not s.startswith(prefix):
        s = f"{prefix}{s}" if s else prefix.rstrip("-")
    return s[:max_len] or "x"


def _download(url: str, dest: Path) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "paper-three-pass-reader-cli/0.2.5"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.write_bytes(resp.read())
        return True, f"downloaded {url} ({dest.stat().st_size} bytes)"
    except Exception as e:  # noqa: BLE001
        return False, f"download failed: {e}"


def _extract_pdf(pdf_path: Path, out_txt: Path) -> tuple[bool, str]:
    """Try pdftotext -layout first. Return (success, message)."""
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        return False, "pdftotext not available on PATH"
    try:
        rc = subprocess.run(
            [pdftotext, "-layout", str(pdf_path), str(out_txt)],
            capture_output=True, text=True, timeout=120,
        )
        if rc.returncode != 0:
            return False, f"pdftotext failed: {rc.stderr}"
        if not out_txt.exists() or out_txt.stat().st_size < 200:
            return False, f"pdftotext produced too-little output ({out_txt.stat().st_size if out_txt.exists() else 0} bytes)"
        return True, f"extracted {out_txt.stat().st_size} chars via pdftotext"
    except Exception as e:  # noqa: BLE001
        return False, f"pdftotext exception: {e}"


def _extract_id(text: str) -> str | None:
    """Pull a 4-digit arXiv id out of any input string."""
    m = _ARXIV_ID_RE.search(text or "")
    return m.group(1) if m else None


def _extract_arxiv_id_from_transcript(text: str) -> str | None:
    """Heuristic: arXiv IDs look like NNNN.NNNNN. Pull the first one."""
    m = re.search(r"\b(\d{4}\.\d{4,5}(?:v\d+)?)\b", text or "")
    return m.group(1) if m else None


def _resolver_result_for_cli(
    resolver_status: str,
    resolver_match_type: str,
    canonical_title: str | None,
    arxiv_id: str | None,
    *,
    hint_dict,
    input_text: str,
    input_kind: str,
) -> dict:
    """Build the resolver_result JSON we pass to the runner via --resolver-source.

    The runner overlays this on top of its own auto-detected resolver result,
    so the draft's `source_resolution` reflects the CLI's view.
    """
    paper = {}
    matched_paper_id = None
    if hint_dict and hint_dict.get("title"):
        paper = {
            "id": hint_dict.get("_resolver_paper_id") or "(cli-overlay)",
            "canonical_title": hint_dict.get("title"),
            "arxiv_id": hint_dict.get("arxiv_id"),
            "paper_url": hint_dict.get("url"),
        }
        matched_paper_id = paper["id"]
    if resolver_status == "matched" and not paper and canonical_title:
        paper = {
            "id": "(cli-overlay)",
            "canonical_title": canonical_title,
            "arxiv_id": arxiv_id or None,
        }
        matched_paper_id = paper["id"]
    return {
        "status": resolver_status or "not_found",
        "match_type": resolver_match_type or "none",
        "confidence": "high" if resolver_status == "matched" else "low",
        "paper": paper,
        "candidates": [paper] if paper else [],
        "source_resolution_step": (
            f"cli overlay via p3pr {input_kind} subcommand; input={input_text!r}"
        ),
        "matched_paper_id": matched_paper_id,
        "matched_alias": None,
        "matched_repo": None,
        "_cli_hint_input": input_text,
        "_cli_hint_kind": input_kind,
    }


def _print_summary(
    status: str,
    *,
    input_kind: str,
    reading_mode: str,
    run_dir: str,
    json_path: str,
    fill_pack: str,
    local_page: str,
    page_url: str,
    next_action: str,
    resolver_status: str = "",
    resolver_match_type: str = "",
    canonical_title: str = "",
    arxiv_id: str = "",
    default_slug: str = "",
) -> None:
    print()
    print("=" * 60)
    print(f"P3PR_STATUS: {status}")
    print(f"P3PR_INPUT_KIND: {input_kind}")
    print(f"P3PR_READING_MODE: {reading_mode}")
    print(f"P3PR_RUN_DIR: {run_dir}")
    print(f"P3PR_JSON: {json_path}")
    print(f"P3PR_FILL_PACK: {fill_pack}")
    print(f"P3PR_LOCAL_PAGE: {local_page}")
    print(f"P3PR_PAGE_URL: {page_url}")
    if resolver_status:
        print(f"P3PR_RESOLVER_STATUS: {resolver_status}")
    if resolver_match_type:
        print(f"P3PR_RESOLVER_MATCH_TYPE: {resolver_match_type}")
    if canonical_title:
        print(f"P3PR_CANONICAL_TITLE: {canonical_title}")
    if arxiv_id:
        print(f"P3PR_ARXIV_ID: {arxiv_id}")
    if default_slug:
        print(f"P3PR_DEFAULT_SLUG: {default_slug}")
    print(f"P3PR_NEXT_ACTION: {next_action}")
    print("=" * 60)


# --- Command builders ---------------------------------------------------------

def _build_runner_argv(
    *,
    input_text: str,
    input_kind: str,
    slug: str,
    output_root: str,
    language: str,
    reading_mode: str | None,
    title: str | None,
    arxiv_id: str | None,
    paper_url: str | None,
    fill_pack: bool,
    audit: bool,
    quality_gate: bool,
    render: bool,
    audit_warn_only: bool,
    resolver_source: str | None = None,
) -> list[str]:
    argv = [
        sys.executable, str(RUNNER),
        "--input", input_text,
        "--input-kind", input_kind,
        "--slug", slug,
        "--output-root", output_root,
        "--language", language,
    ]
    if reading_mode:
        argv += ["--reading-mode", reading_mode]
    if title:
        argv += ["--title", title]
    if arxiv_id:
        argv += ["--arxiv-id", arxiv_id]
    if paper_url:
        argv += ["--paper-url", paper_url]
    if resolver_source:
        argv += ["--resolver-source", resolver_source]
    if fill_pack:
        argv += ["--fill-pack"]
    if audit:
        argv += ["--audit"]
    if audit_warn_only:
        argv += ["--audit-warn-only"]
    if quality_gate:
        argv += ["--quality-gate"]
    if render:
        argv += ["--render"]
    return argv


def _make_run_dir(*, output_root: str, slug: str) -> Path:
    root = Path(output_root) / slug
    for sub in ("input", "source", "extracted", "work", "paper-reading-output", "reports"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


# --- Subcommand handlers ------------------------------------------------------

def handle_arxiv(args) -> int:
    raw = args.arg
    arxiv_id = _extract_id(raw) or raw
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    # v0.2.6: also try the shared resolver for canonical title / arxiv id
    hint = _resolve_hint(raw) or _resolve_hint(arxiv_id)
    resolver_status = (hint or {}).get("_resolver_status", "not_found")
    resolver_match_type = (hint or {}).get("_resolver_match_type", "none")
    if args.slug:
        slug = args.slug
    elif hint and hint.get("arxiv_id"):
        slug = _slugify(f"arxiv-{hint['arxiv_id']}", prefix="arxiv-")
    else:
        slug = _slugify(f"arxiv-{arxiv_id}", prefix="arxiv-")
    root = _make_run_dir(output_root=args.output_root, slug=slug)
    (root / "input" / "input.md").write_text(
        f"# arXiv input\n\n- arg: `{raw}`\n- arXiv id: `{arxiv_id}`\n- abs: {abs_url}\n- pdf: {pdf_url}\n- resolver_status: `{resolver_status}`\n- resolver_match_type: `{resolver_match_type}`\n",
        encoding="utf-8",
    )

    # Download + extract if --full or default full_text (skip in --dry-run)
    reading_mode = "full_text" if args.full else "abstract_only"
    extraction_status = "skipped (--dry-run)"
    if reading_mode == "full_text" and not args.dry_run:
        pdf_path = root / "source" / "paper.pdf"
        ok, msg = _download(pdf_url, pdf_path)
        extraction_status = msg
        if ok and pdf_path.exists() and pdf_path.stat().st_size > 0:
            txt_path = root / "extracted" / "full_body.txt"
            ok2, msg2 = _extract_pdf(pdf_path, txt_path)
            extraction_status = f"{msg}; {msg2}"
            if not ok2:
                reading_mode = "partial_text"
                extraction_status += " — falling back to partial_text"

    if args.partial:
        reading_mode = "partial_text"
    elif args.abstract_only:
        reading_mode = "abstract_only"
    elif args.screenshot_only:
        reading_mode = "screenshot_only"

    return _finalise(
        args,
        input_text=f"arXiv:{arxiv_id} — {abs_url}",
        input_kind="paper_identifier",
        reading_mode=reading_mode,
        slug=slug,
        run_dir=root,
        title=args.title or (hint or {}).get("title") or arxiv_id,
        arxiv_id=(hint or {}).get("arxiv_id") or arxiv_id,
        paper_url=(hint or {}).get("url") or abs_url,
        extra_note=extraction_status,
        resolver_status=resolver_status,
        resolver_match_type=resolver_match_type,
        canonical_title=(hint or {}).get("title") or "",
        default_slug=slug,
        hint=hint,
    )


def handle_title(args) -> int:
    title = args.arg
    hint = _resolve_hint(title)
    resolver_status = (hint or {}).get("_resolver_status", "not_found")
    resolver_match_type = (hint or {}).get("_resolver_match_type", "none")
    # Prefer hint's default_slug when user did not pass --slug
    if args.slug:
        slug = args.slug
    else:
        if hint and hint.get("arxiv_id"):
            slug = _slugify(f"arxiv-{hint['arxiv_id']}", prefix="arxiv-")
        elif hint and (hint or {}).get("_resolver_paper_id"):
            slug = hint["_resolver_paper_id"]
        else:
            slug = _slugify(title, prefix="title-")
    root = _make_run_dir(output_root=args.output_root, slug=slug)
    (root / "input" / "input.md").write_text(
        f"# title input\n\n- title: `{title}`\n- hint matched: `{bool(hint)}`\n- resolver_status: `{resolver_status}`\n- resolver_match_type: `{resolver_match_type}`\n",
        encoding="utf-8",
    )

    reading_mode = (hint or {}).get("default_reading_mode", "partial_text")
    if args.full:
        reading_mode = "full_text"
    elif args.partial:
        reading_mode = "partial_text"
    elif args.abstract_only:
        reading_mode = "abstract_only"

    arxiv_id = (hint or {}).get("arxiv_id")
    paper_url = (hint or {}).get("url")
    return _finalise(
        args,
        input_text=title,
        input_kind="paper_title",
        reading_mode=reading_mode,
        slug=slug,
        run_dir=root,
        title=args.title or (hint or {}).get("title") or title,
        arxiv_id=arxiv_id,
        paper_url=paper_url,
        extra_note=(
            f"hint matched: {bool(hint)}; resolver_status={resolver_status}; "
            f"match_type={resolver_match_type}; canonical_title={(hint or {}).get('title')}"
        ),
        resolver_status=resolver_status,
        resolver_match_type=resolver_match_type,
        canonical_title=(hint or {}).get("title") or "",
        default_slug=slug,
        hint=hint,
    )


def handle_abstract(args) -> int:
    path = Path(args.arg).expanduser().resolve()
    if not path.exists():
        print(f"[error] abstract file does not exist: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="replace")
    # v0.2.6: also try the shared resolver against the abstract text
    hint = _resolve_hint(text[:400])
    resolver_status = (hint or {}).get("_resolver_status", "not_found")
    resolver_match_type = (hint or {}).get("_resolver_match_type", "none")
    if args.slug:
        slug = args.slug
    elif hint and hint.get("arxiv_id"):
        slug = _slugify(f"arxiv-{hint['arxiv_id']}", prefix="arxiv-")
    else:
        slug = _slugify(f"abstract-{path.stem}", prefix="abstract-")
    root = _make_run_dir(output_root=args.output_root, slug=slug)
    (root / "input" / "input.md").write_text(
        f"# abstract input\n\n- source: `{path}`\n- bytes: {path.stat().st_size}\n- excerpt (first 400 chars):\n\n```\n{text[:400]}\n```\n- resolver_status: `{resolver_status}`\n- resolver_match_type: `{resolver_match_type}`\n",
        encoding="utf-8",
    )

    reading_mode = "abstract_only"
    if args.full:
        reading_mode = "full_text"
    elif args.partial:
        reading_mode = "partial_text"

    arxiv_id = (hint or {}).get("arxiv_id") or _extract_arxiv_id_from_transcript(text)
    paper_url = (hint or {}).get("url") or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None)
    return _finalise(
        args,
        input_text=f"abstract excerpt of {path.name}",
        input_kind="paper_excerpt",
        reading_mode=reading_mode,
        slug=slug,
        run_dir=root,
        title=args.title or (hint or {}).get("title") or (f"arXiv:{arxiv_id}" if arxiv_id else path.stem),
        arxiv_id=arxiv_id,
        paper_url=paper_url,
        extra_note="abstract-only by default; Pass 2/3 will not be auto-filled",
        resolver_status=resolver_status,
        resolver_match_type=resolver_match_type,
        canonical_title=(hint or {}).get("title") or "",
        default_slug=slug,
        hint=hint,
    )


def handle_screenshot(args) -> int:
    path = Path(args.arg).expanduser().resolve()
    if not path.exists():
        print(f"[error] screenshot transcript does not exist: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="replace")
    # v0.2.6: also try the shared resolver against the transcript
    hint = _resolve_hint(text[:400])
    resolver_status = (hint or {}).get("_resolver_status", "not_found")
    resolver_match_type = (hint or {}).get("_resolver_match_type", "none")
    if args.slug:
        slug = args.slug
    elif hint and hint.get("arxiv_id"):
        slug = _slugify(f"arxiv-{hint['arxiv_id']}", prefix="arxiv-")
    else:
        slug = _slugify(f"screenshot-{path.stem}", prefix="screenshot-")
    root = _make_run_dir(output_root=args.output_root, slug=slug)
    (root / "input" / "input.md").write_text(
        f"# screenshot transcript input\n\n- source: `{path}`\n- bytes: {path.stat().st_size}\n- first 400 chars:\n\n```\n{text[:400]}\n```\n- resolver_status: `{resolver_status}`\n- resolver_match_type: `{resolver_match_type}`\n",
        encoding="utf-8",
    )

    reading_mode = "screenshot_only"
    if args.full:
        reading_mode = "full_text"
    elif args.partial:
        reading_mode = "partial_text"
    elif args.abstract_only:
        reading_mode = "abstract_only"

    arxiv_id = (hint or {}).get("arxiv_id") or _extract_arxiv_id_from_transcript(text)
    paper_url = (hint or {}).get("url") or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None)
    note = (
        f"transcript length: {len(text)} chars; "
        + (f"detected arXiv id: {arxiv_id}. Re-run with `./p3pr arxiv {arxiv_id} --full` to get a full reading." if arxiv_id else "no arXiv id detected in transcript")
    )
    return _finalise(
        args,
        input_text=f"screenshot transcript of {path.name}",
        input_kind="paper_screenshot",
        reading_mode=reading_mode,
        slug=slug,
        run_dir=root,
        title=args.title or (hint or {}).get("title") or (f"arXiv:{arxiv_id}" if arxiv_id else path.stem),
        arxiv_id=arxiv_id,
        paper_url=paper_url,
        extra_note=note,
        resolver_status=resolver_status,
        resolver_match_type=resolver_match_type,
        canonical_title=(hint or {}).get("title") or "",
        default_slug=slug,
        hint=hint,
    )


def handle_repo(args) -> int:
    url = args.arg
    hint = _resolve_hint(url)
    resolver_status = (hint or {}).get("_resolver_status", "not_found")
    resolver_match_type = (hint or {}).get("_resolver_match_type", "none")
    if args.slug:
        slug = args.slug
    else:
        if hint and hint.get("arxiv_id"):
            slug = _slugify(f"arxiv-{hint['arxiv_id']}", prefix="arxiv-")
        elif hint and (hint or {}).get("_resolver_paper_id"):
            slug = hint["_resolver_paper_id"]
        else:
            slug = _slugify(f"repo-{url.rsplit('/', 1)[-1]}", prefix="repo-")
    root = _make_run_dir(output_root=args.output_root, slug=slug)
    (root / "input" / "input.md").write_text(
        f"# repo input\n\n- url: `{url}`\n- hint matched: `{bool(hint)}`\n- resolver_status: `{resolver_status}`\n- resolver_match_type: `{resolver_match_type}`\n",
        encoding="utf-8",
    )

    reading_mode = (hint or {}).get("default_reading_mode", "partial_text")
    if args.full:
        reading_mode = "full_text"
    elif args.partial:
        reading_mode = "partial_text"

    arxiv_id = (hint or {}).get("arxiv_id")
    paper_url = (hint or {}).get("url")
    return _finalise(
        args,
        input_text=url,
        input_kind="project_or_repo",
        reading_mode=reading_mode,
        slug=slug,
        run_dir=root,
        title=args.title or (hint or {}).get("title") or url,
        arxiv_id=arxiv_id,
        paper_url=paper_url,
        extra_note=(
            f"hint matched: {bool(hint)}; resolver_status={resolver_status}; "
            f"match_type={resolver_match_type}; canonical_title={(hint or {}).get('title')}"
        ),
        resolver_status=resolver_status,
        resolver_match_type=resolver_match_type,
        canonical_title=(hint or {}).get("title") or "",
        default_slug=slug,
        hint=hint,
    )


def handle_pdf(args) -> int:
    path = Path(args.arg).expanduser().resolve()
    if not path.exists():
        print(f"[error] PDF does not exist: {path}", file=sys.stderr)
        return 2
    slug = args.slug or _slugify(f"pdf-{path.stem}", prefix="pdf-")
    root = _make_run_dir(output_root=args.output_root, slug=slug)
    (root / "input" / "input.md").write_text(
        f"# PDF input\n\n- path: `{path}`\n- bytes: {path.stat().st_size}\n",
        encoding="utf-8",
    )
    # Copy PDF to source/
    src_pdf = root / "source" / "paper.pdf"
    shutil.copyfile(path, src_pdf)

    reading_mode = "full_text"
    note = f"copied PDF ({path.stat().st_size} bytes) to source/"
    if args.partial:
        reading_mode = "partial_text"
    elif args.abstract_only:
        reading_mode = "abstract_only"
    elif args.screenshot_only:
        reading_mode = "screenshot_only"

    if reading_mode == "full_text" and not args.dry_run:
        txt_path = root / "extracted" / "full_body.txt"
        ok, msg = _extract_pdf(src_pdf, txt_path)
        note += f"; {msg}"
        if not ok:
            print(f"[error] {msg}", file=sys.stderr)
            _print_summary(
                "BLOCKED",
                input_kind="complete_paper",
                reading_mode="BLOCKED_EXTRACTION_UNAVAILABLE",
                run_dir=str(root),
                json_path="",
                fill_pack="",
                local_page="",
                page_url="",
                next_action="Install pdftotext (poppler-utils) or provide pre-extracted text.",
            )
            return 2

    return _finalise(
        args,
        input_text=f"local PDF: {path.name}",
        input_kind="complete_paper",
        reading_mode=reading_mode,
        slug=slug,
        run_dir=root,
        title=args.title or path.stem,
        arxiv_id=None,
        paper_url=None,
        extra_note=note,
    )


# --- Finaliser ---------------------------------------------------------------

def _finalise(
    args,
    *,
    input_text: str,
    input_kind: str,
    reading_mode: str,
    slug: str,
    run_dir: Path,
    title: str | None,
    arxiv_id: str | None,
    paper_url: str | None,
    extra_note: str,
    resolver_status: str = "",
    resolver_match_type: str = "",
    canonical_title: str = "",
    default_slug: str = "",
    hint: dict | None = None,
) -> int:
    print(f"[info] {extra_note}")
    print(f"[info] run dir: {run_dir}")
    print(f"[info] input_kind={input_kind}, reading_mode={reading_mode}, language={args.language}")

    if args.dry_run:
        _print_summary(
            "DRY_RUN",
            input_kind=input_kind,
            reading_mode=reading_mode,
            run_dir=str(run_dir),
            json_path=str(run_dir / "work" / "paper_reading.json"),
            fill_pack=str(run_dir / "fill-pack"),
            local_page=str(run_dir / "paper-reading-output" / "index.html"),
            page_url="(publish skipped in --dry-run)",
            next_action="remove --dry-run to actually run the pipeline",
            resolver_status=resolver_status,
            resolver_match_type=resolver_match_type,
            canonical_title=canonical_title or (title or ""),
            arxiv_id=arxiv_id or "",
            default_slug=default_slug or slug,
        )
        return 0

    # Build runner argv. v0.2.6: also write the resolver's full output to a
    # JSON file under run_dir/work/ and pass it via --resolver-source so the
    # runner's draft source_resolution reflects the CLI's view exactly.
    work_dir = run_dir / "work"
    resolver_source_path = work_dir / "resolver_source.json"
    try:
        work_dir.mkdir(parents=True, exist_ok=True)
        resolver_source_path.write_text(
            json.dumps(_resolver_result_for_cli(resolver_status, resolver_match_type,
                                               title, arxiv_id, hint_dict=hint,
                                               input_text=input_text, input_kind=input_kind),
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception as e:  # noqa: BLE001
        print(f"[warn] could not write resolver_source.json: {e!r}", file=sys.stderr)
        resolver_source_path = None  # type: ignore[assignment]

    runner_argv = _build_runner_argv(
        input_text=input_text,
        input_kind=input_kind,
        slug=slug,
        output_root=args.output_root,
        language=args.language,
        reading_mode=reading_mode if reading_mode != "BLOCKED_EXTRACTION_UNAVAILABLE" else None,
        title=title,
        arxiv_id=arxiv_id,
        paper_url=paper_url,
        fill_pack=args.fill_pack,
        audit=args.audit,
        quality_gate=args.quality_gate and args.language == "zh-CN",
        render=args.render,
        audit_warn_only=args.audit_warn_only,
        resolver_source=str(resolver_source_path) if resolver_source_path else None,
    )
    print(f"[info] running runner: {' '.join(runner_argv)}")
    rc = subprocess.call(runner_argv)
    if rc != 0:
        print(f"[error] runner exited {rc}", file=sys.stderr)
        _print_summary(
            "BLOCKED",
            input_kind=input_kind,
            reading_mode=reading_mode,
            run_dir=str(run_dir),
            json_path=str(run_dir / "work" / "paper_reading.json"),
            fill_pack=str(run_dir / "fill-pack"),
            local_page="",
            page_url="",
            next_action=f"runner exited {rc}; check fill-pack and re-run",
            resolver_status=resolver_status,
            resolver_match_type=resolver_match_type,
            canonical_title=canonical_title or (title or ""),
            arxiv_id=arxiv_id or "",
            default_slug=default_slug or slug,
        )
        return rc if rc in (1, 2) else 1

    work_json = run_dir / "work" / "paper_reading.json"
    page_path = run_dir / "paper-reading-output" / "index.html"
    fill_pack = run_dir / "fill-pack"

    # Run quality gate separately if requested and zh-CN (so we can decide publish gate)
    qg_status = "SKIPPED"
    if args.quality_gate and args.language == "zh-CN":
        qg_out = run_dir / "work" / "quality_gate_zh_cn.json"
        qg_argv = [sys.executable, str(QUALITY_GATE), "--input", str(work_json), "--json-output", str(qg_out)]
        print(f"[info] running quality gate: {' '.join(qg_argv)}")
        qg_rc = subprocess.call(qg_argv)
        try:
            qg_data = json.loads(qg_out.read_text(encoding="utf-8"))
            qg_status = qg_data.get("status", "UNKNOWN")
        except Exception:  # noqa: BLE001
            qg_status = "UNKNOWN"
        print(f"[info] quality gate status: {qg_status} (rc={qg_rc})")

    page_url = ""
    if args.publish:
        if qg_status == "FAIL" and not args.allow_draft_publish:
            print("[error] quality gate FAIL; refusing to publish without --allow-draft-publish.", file=sys.stderr)
            _print_summary(
                "BLOCKED",
                input_kind=input_kind,
                reading_mode=reading_mode,
                run_dir=str(run_dir),
                json_path=str(work_json),
                fill_pack=str(fill_pack),
                local_page=str(page_path),
                page_url="",
                next_action="Fill the draft (follow fill-pack), rerun `./p3pr ... --no-publish` until quality gate passes, then re-publish. Or pass --allow-draft-publish to publish the draft as-is.",
                resolver_status=resolver_status,
                resolver_match_type=resolver_match_type,
                canonical_title=canonical_title or (title or ""),
                arxiv_id=arxiv_id or "",
                default_slug=slug,
            )
            return 1
        # Build publish argv
        page_title = args.page_title or title or slug
        pub_argv = [
            str(PUBLISH_SH),
            "--output", str(run_dir / "paper-reading-output"),
            "--repo", args.repo,
            "--branch", args.branch,
            "--site-path", slug,
            "--page-title", page_title,
            "--message", f"Publish p3pr-cli run: {slug}",
        ]
        print(f"[info] running publisher: {' '.join(pub_argv)}")
        pub_rc = subprocess.call(pub_argv)
        if pub_rc != 0:
            print(f"[error] publisher exited {pub_rc}", file=sys.stderr)
            _print_summary(
                "BLOCKED",
                input_kind=input_kind,
                reading_mode=reading_mode,
                run_dir=str(run_dir),
                json_path=str(work_json),
                fill_pack=str(fill_pack),
                local_page=str(page_path),
                page_url="",
                next_action="publish failed; check gh login / network / branch protection",
                resolver_status=resolver_status,
                resolver_match_type=resolver_match_type,
                canonical_title=canonical_title or (title or ""),
                arxiv_id=arxiv_id or "",
                default_slug=slug,
            )
            return 3
        page_url = f"https://{args.repo.split('/')[0]}.github.io/{args.repo.split('/')[1]}/{slug}/"

    # Determine overall status
    if reading_mode in ("abstract_only", "screenshot_only", "partial_text") and not args.allow_draft_publish:
        status = "WARN"
    elif qg_status == "FAIL" and not args.allow_draft_publish:
        status = "BLOCKED"
    elif qg_status == "WARN":
        status = "WARN"
    else:
        status = "PASS"

    next_action = _next_action_text(
        status, reading_mode, qg_status, work_json, fill_pack, args
    )
    _print_summary(
        status,
        input_kind=input_kind,
        reading_mode=reading_mode,
        run_dir=str(run_dir),
        json_path=str(work_json),
        fill_pack=str(fill_pack),
        local_page=str(page_path) if page_path.exists() else "",
        page_url=page_url,
        next_action=next_action,
        resolver_status=resolver_status,
        resolver_match_type=resolver_match_type,
        canonical_title=canonical_title or (title or ""),
        arxiv_id=arxiv_id or "",
        default_slug=slug,
    )
    return 0 if status in ("PASS", "WARN") else 1


def _next_action_text(status, reading_mode, qg_status, work_json, fill_pack, args) -> str:
    if status == "PASS":
        return "Done. Page published (or local). To re-publish, run the same command."
    if status == "WARN":
        return (
            f"Review WARN items in {work_json.parent}/quality_gate_zh_cn.json or audit_result.json. "
            "If quality gate is WARN, the page may be published but content is shallow."
        )
    if status == "BLOCKED":
        if qg_status == "FAIL":
            return (
                f"1) edit {work_json} and fill the draft per {fill_pack}/. "
                f"2) re-run: python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py --input {work_json}. "
                f"3) re-run: ./p3pr ... --no-publish. "
                f"4) when quality gate PASS, re-run with --publish. "
                f"Or pass --allow-draft-publish to publish the draft as-is."
            )
        return (
            f"Pipeline failed. Check {work_json.parent} for audit_result.json / runner logs."
        )
    return "Unknown status."


# --- argparse ----------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="p3pr",
        description="One-line CLI wrapper for paper-three-pass-reader.",
    )
    p.add_argument("--language", choices=["zh-CN", "en"], default="zh-CN",
                   help="Output language (default zh-CN)")
    p.add_argument("--slug", help="Override slug (default: auto)")
    p.add_argument("--output-root", default=f"runs/p3pr-cli-{_today()}",
                   help="Output root directory (default runs/p3pr-cli-YYYYMMDD)")
    p.add_argument("--full", action="store_true",
                   help="Force reading_mode = full_text (only meaningful if body is available)")
    p.add_argument("--partial", action="store_true")
    p.add_argument("--abstract-only", action="store_true")
    p.add_argument("--screenshot-only", action="store_true")
    p.add_argument("--title", help="Override paper title")
    p.add_argument("--fill-pack", dest="fill_pack", action="store_true", default=True)
    p.add_argument("--no-fill-pack", dest="fill_pack", action="store_false")
    p.add_argument("--audit", dest="audit", action="store_true", default=True)
    p.add_argument("--no-audit", dest="audit", action="store_false")
    p.add_argument("--quality-gate", dest="quality_gate", action="store_true", default=True)
    p.add_argument("--no-quality-gate", dest="quality_gate", action="store_false")
    p.add_argument("--render", dest="render", action="store_true", default=True)
    p.add_argument("--no-render", dest="render", action="store_false")
    p.add_argument("--publish", dest="publish", action="store_true", default=False)
    p.add_argument("--no-publish", dest="publish", action="store_false")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--branch", default=DEFAULT_BRANCH)
    p.add_argument("--page-title", help="Override page title for the published page")
    p.add_argument("--audit-warn-only", action="store_true",
                   help="Treat audit WARN as PASS for the runner's render block")
    p.add_argument("--allow-draft-publish", action="store_true",
                   help="Allow publishing even when quality gate FAILS or reading mode is weak")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the plan without running anything")
    p.add_argument("--report-path", help="Reserved for future structured JSON output")

    # Aliases for --zh / --en
    p.add_argument("--zh", dest="zh", action="store_true",
                   help="Shortcut for --language zh-CN")
    p.add_argument("--en", dest="en", action="store_true",
                   help="Shortcut for --language en")

    sub = p.add_subparsers(dest="command", required=True, metavar="SUBCOMMAND")
    for name, help_text in [
        ("arxiv", "arXiv ID or arXiv URL (e.g. 2503.08102 or https://arxiv.org/abs/2503.08102)"),
        ("title", "Paper title (best-effort hint lookup)"),
        ("abstract", "Path to a text file containing the paper abstract"),
        ("screenshot", "Path to a text file containing a screenshot / poster / page OCR transcript"),
        ("repo", "GitHub repo URL (best-effort hint lookup)"),
        ("pdf", "Path to a local PDF file"),
    ]:
        sp = sub.add_parser(name, help=help_text)
        sp.add_argument("arg", help=help_text)
        # Forwarded from parent (so users can put flags before or after subcommand).
        sp.add_argument("--language", choices=["zh-CN", "en"], default=None)
        sp.add_argument("--slug", default=None)
        sp.add_argument("--output-root", default=None)
        sp.add_argument("--full", action="store_true", default=None)
        sp.add_argument("--partial", action="store_true", default=None)
        sp.add_argument("--abstract-only", action="store_true", default=None)
        sp.add_argument("--screenshot-only", action="store_true", default=None)
        sp.add_argument("--title", default=None)
        sp.add_argument("--fill-pack", dest="fill_pack", action="store_true", default=None)
        sp.add_argument("--no-fill-pack", dest="fill_pack", action="store_false", default=None)
        sp.add_argument("--audit", dest="audit", action="store_true", default=None)
        sp.add_argument("--no-audit", dest="audit", action="store_false", default=None)
        sp.add_argument("--quality-gate", dest="quality_gate", action="store_true", default=None)
        sp.add_argument("--no-quality-gate", dest="quality_gate", action="store_false", default=None)
        sp.add_argument("--render", dest="render", action="store_true", default=None)
        sp.add_argument("--no-render", dest="render", action="store_false", default=None)
        sp.add_argument("--publish", dest="publish", action="store_true", default=None)
        sp.add_argument("--no-publish", dest="publish", action="store_false", default=None)
        sp.add_argument("--repo", default=None)
        sp.add_argument("--branch", default=None)
        sp.add_argument("--page-title", default=None)
        sp.add_argument("--audit-warn-only", action="store_true", default=None)
        sp.add_argument("--allow-draft-publish", action="store_true", default=None)
        sp.add_argument("--dry-run", action="store_true", default=None)
        sp.add_argument("--zh", dest="zh", action="store_true", default=None)
        sp.add_argument("--en", dest="en", action="store_true", default=None)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Promote subcommand-level flag values to the top-level namespace so the
    # handlers can use a single `args.foo` regardless of where the user put
    # the flag. If the sub-level parser did not see the flag (sub_val is None),
    # fall back to the parser-level default.
    _PROMOTE = (
        "language", "slug", "output_root", "full", "partial", "abstract_only",
        "screenshot_only", "title", "fill_pack", "audit", "quality_gate",
        "render", "publish", "repo", "branch", "page_title", "audit_warn_only",
        "allow_draft_publish", "dry_run", "zh", "en",
    )
    # Defaults the user would have got at parser level.
    _DEFAULTS = {
        "language": "zh-CN",
        "output_root": f"runs/p3pr-cli-{_today()}",
        "fill_pack": True,
        "audit": True,
        "quality_gate": True,
        "render": True,
        "publish": False,
        "repo": DEFAULT_REPO,
        "branch": DEFAULT_BRANCH,
    }
    for key in _PROMOTE:
        sub_val = getattr(args, key, None)
        if sub_val is None:
            setattr(args, key, _DEFAULTS.get(key))
        else:
            setattr(args, key, sub_val)

    # Re-apply --zh / --en aliases (parent values may not have been set if user
    # used the subcommand-level alias).
    if getattr(args, "zh", None) and getattr(args, "en", None):
        print("[error] --zh and --en are mutually exclusive", file=sys.stderr)
        return 2
    if getattr(args, "zh", None):
        args.language = "zh-CN"
    if getattr(args, "en", None):
        args.language = "en"

    if not RUNNER.exists():
        print(f"[error] runner script missing: {RUNNER}", file=sys.stderr)
        return 2

    handlers = {
        "arxiv": handle_arxiv,
        "title": handle_title,
        "abstract": handle_abstract,
        "screenshot": handle_screenshot,
        "repo": handle_repo,
        "pdf": handle_pdf,
    }
    handler = handlers.get(args.command)
    if handler is None:
        print(f"[error] unknown subcommand: {args.command}", file=sys.stderr)
        return 2
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
