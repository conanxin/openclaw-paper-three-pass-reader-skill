#!/usr/bin/env python3
"""
p3pr.py — paper-three-pass-reader (v0.2.5-alpha, v0.2.14-alpha adds `url` subcommand)

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
    ./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html --zh --full --publish  # v0.2.14

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
import html
import html.parser
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


# --- v0.2.14-alpha: HTML fetch + stdlib-only text extraction -----------------

class _HTMLTextExtractor(html.parser.HTMLParser):
    """Minimal stdlib-only HTML → plain text extractor.

    Drops <script> and <style> content. Emits block-level separators for
    headings, paragraphs, list items, and <br>. Captures <title>.
    """

    BLOCK_TAGS = {
        "p", "div", "section", "article", "header", "footer", "main",
        "nav", "aside", "ul", "ol", "li", "table", "tr", "pre", "blockquote",
        "h1", "h2", "h3", "h4", "h5", "h6",
    }
    SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "iframe"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._buf: list[str] = []
        self._title: str = ""
        self._in_title: bool = False
        self._skip_depth: int = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
            return
        if tag in self.BLOCK_TAGS:
            self._buf.append("\n")
        if tag == "br":
            self._buf.append("\n")
        if tag == "li":
            self._buf.append("\n- ")

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag in self.SKIP_TAGS:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
            return
        if tag in self.BLOCK_TAGS:
            self._buf.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._in_title:
            self._title += data
            return
        self._buf.append(data)

    def get_text(self) -> str:
        raw = "".join(self._buf)
        # Collapse runs of blank lines.
        lines = [ln.strip() for ln in raw.split("\n")]
        out: list[str] = []
        prev_blank = False
        for ln in lines:
            if not ln:
                if not prev_blank and out:
                    out.append("")
                prev_blank = True
            else:
                out.append(ln)
                prev_blank = False
        # Drop trailing blank lines.
        while out and not out[-1]:
            out.pop()
        return "\n".join(out)

    def get_title(self) -> str:
        return re.sub(r"\s+", " ", self._title).strip()


def _extract_html_text(html_bytes: bytes) -> tuple[str, str, int]:
    """Extract plain text from raw HTML bytes. Returns (text, title, raw_byte_count).

    Falls back to a permissive UTF-8 decode; non-decodable bytes are replaced.
    """
    raw = html_bytes.decode("utf-8", errors="replace")
    parser = _HTMLTextExtractor()
    try:
        parser.feed(raw)
        parser.close()
    except Exception as e:  # noqa: BLE001
        # On any HTML parse error, still return whatever we have.
        print(f"[warn] html parser error: {e!r}; returning partial text", file=sys.stderr)
    return parser.get_text(), parser.get_title(), len(html_bytes)


def _looks_like_pdf(url: str, content_type: str, body: bytes) -> bool:
    """Heuristic: URL ends in .pdf OR Content-Type starts with application/pdf OR magic bytes."""
    if url.lower().split("?", 1)[0].endswith(".pdf"):
        return True
    if content_type and "application/pdf" in content_type.lower():
        return True
    if body and body[:5] == b"%PDF-":
        return True
    return False


def _fetch_url(url: str, dest_dir: Path) -> tuple[dict, str]:
    """Fetch a URL and save it under dest_dir. Returns (metadata_dict, error_message).

    metadata_dict keys:
      - http_status (int)
      - final_url (str)
      - content_type (str)
      - raw_path (Path) — always written when fetch succeeded
      - is_pdf (bool)
      - title (str) — best-effort HTML <title>
      - text_path (Path | None) — written for HTML when extraction succeeded
      - text_chars (int) — number of characters in extracted text
      - bytes (int) — raw byte count
      - error (str | None) — set on hard failure
    """
    headers = {
        "User-Agent": "paper-three-pass-reader-cli/0.2.14 (+https://conanxin.github.io/paper-reading-pages/)",
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
    }
    meta: dict = {
        "http_status": 0,
        "final_url": url,
        "content_type": "",
        "raw_path": None,
        "is_pdf": False,
        "title": "",
        "text_path": None,
        "text_chars": 0,
        "bytes": 0,
        "error": None,
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            meta["http_status"] = int(getattr(resp, "status", None) or resp.getcode())
            meta["final_url"] = resp.geturl() or url
            meta["content_type"] = resp.headers.get("Content-Type", "") or ""
            body = resp.read()
    except Exception as e:  # noqa: BLE001
        meta["error"] = f"fetch failed: {e!r}"
        return meta, meta["error"]

    meta["bytes"] = len(body)
    is_pdf = _looks_like_pdf(url, meta["content_type"], body)
    meta["is_pdf"] = is_pdf

    if is_pdf:
        raw_path = dest_dir / "source.pdf"
        raw_path.write_bytes(body)
        meta["raw_path"] = raw_path
        return meta, "saved as PDF"

    # HTML: save raw bytes as source.html, then extract.
    raw_path = dest_dir / "source.html"
    raw_path.write_bytes(body)
    meta["raw_path"] = raw_path

    text, title, _ = _extract_html_text(body)
    meta["title"] = title
    meta["text_chars"] = len(text)
    if text:
        # v0.2.14-alpha: extract to <run>/extracted/page.txt (per spec),
        # not into source/. source/ keeps the raw fetched bytes only.
        extracted_dir = dest_dir.parent / "extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)
        text_path = extracted_dir / "page.txt"
        text_path.write_text(text, encoding="utf-8")
        meta["text_path"] = text_path
    return meta, "ok"


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
    source_url: str = "",
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
    if source_url:
        print(f"P3PR_SOURCE_URL: {source_url}")
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
    input_file: str | None = None,
    authors: str | None = None,
    year: str | None = None,
) -> list[str]:
    argv = [
        sys.executable, str(RUNNER),
        "--input", input_text,
        "--input-kind", input_kind,
        "--slug", slug,
        "--output-root", output_root,
        "--language", language,
    ]
    if input_file:
        # v0.2.14-alpha: when the CLI has prepared an extracted body on disk
        # (e.g. via the new `url` subcommand), pass --input-file to the runner
        # so the run layout and intake trail point at the local extracted text
        # rather than re-pasting the URL string.
        argv += ["--input-file", input_file]
    if reading_mode:
        argv += ["--reading-mode", reading_mode]
    if title:
        argv += ["--title", title]
    if authors:
        argv += ["--authors", authors]
    if year:
        argv += ["--year", year]
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


# --- v0.2.14-alpha: url subcommand -------------------------------------------

def handle_url(args) -> int:
    """Fetch an HTML page (or PDF) from a URL, extract text, run the pipeline.

    Substeps:
      1. Save the URL pointer to <run_dir>/input/source_pointer.txt.
      2. Fetch the URL → <run_dir>/source/source.html (or source.pdf).
      3. Extract plain text via stdlib html.parser → <run_dir>/extracted/page.txt.
      4. Hand the extracted text to the runner via --input-file +
         --input-kind paper_url + --paper-url <url>.
    """
    url = args.arg.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        print(f"[error] url must start with http:// or https:// (got: {url!r})", file=sys.stderr)
        return 2

    # Best-effort resolver hint (URLs may match by alias / repo fragment).
    hint = _resolve_hint(url)
    resolver_status = (hint or {}).get("_resolver_status", "not_found")
    resolver_match_type = (hint or {}).get("_resolver_match_type", "none")

    if args.slug:
        slug = args.slug
    elif hint and hint.get("arxiv_id"):
        slug = _slugify(f"arxiv-{hint['arxiv_id']}", prefix="arxiv-")
    elif hint and (hint or {}).get("_resolver_paper_id"):
        slug = hint["_resolver_paper_id"]
    else:
        slug = _slugify(f"url-{url.rsplit('/', 1)[-1] or 'page'}", prefix="url-")

    root = _make_run_dir(output_root=args.output_root, slug=slug)
    # Record the URL pointer.
    (root / "input" / "source_pointer.txt").write_text(
        f"{url}\n",
        encoding="utf-8",
    )

    # Fetch + extract (skipped only in --dry-run).
    fetch_note = "skipped (--dry-run)"
    text_chars = 0
    extracted_text: str = ""
    is_pdf = False
    text_path: Path | None = None
    body_path: Path | None = None
    http_status = 0
    final_url = url
    content_type = ""
    if not args.dry_run:
        meta, status_msg = _fetch_url(url, root / "source")
        fetch_note = status_msg
        http_status = meta["http_status"]
        final_url = meta["final_url"]
        content_type = meta["content_type"]
        is_pdf = meta["is_pdf"]
        text_chars = meta["text_chars"]
        body_path = meta["raw_path"]
        text_path = meta["text_path"]
        if meta["error"]:
            print(f"[error] {meta['error']}", file=sys.stderr)
            _print_summary(
                "BLOCKED",
                input_kind="paper_url",
                reading_mode="BLOCKED_FETCH_FAILED",
                run_dir=str(root),
                json_path="",
                fill_pack="",
                local_page="",
                page_url="",
                next_action="check the URL / network / DNS, then re-run",
                resolver_status=resolver_status,
                resolver_match_type=resolver_match_type,
                canonical_title=(hint or {}).get("title") or "",
                default_slug=slug,
                source_url=url,
            )
            return 2
        if text_path and text_path.exists():
            extracted_text = text_path.read_text(encoding="utf-8", errors="replace")

    # Reading-mode decision.
    # Heuristic threshold: >= 800 chars of extracted text → full_text;
    # otherwise partial_text (still has a body but thin). --full / --partial
    # / --abstract-only / --screenshot-only explicitly override.
    threshold = 800
    if args.full:
        reading_mode = "full_text"
    elif args.partial:
        reading_mode = "partial_text"
    elif args.abstract_only:
        reading_mode = "abstract_only"
    elif args.screenshot_only:
        reading_mode = "screenshot_only"
    elif not args.dry_run and is_pdf and text_chars == 0:
        # PDF detected but no text extracted (pdftotext missing / failed).
        # Refuse to claim full_text; we explicitly do NOT pretend a PDF
        # without body is a full_text reading.
        reading_mode = "partial_text"
    elif not args.dry_run:
        reading_mode = "full_text" if text_chars >= threshold else "partial_text"
    else:
        # Dry-run: respect explicit --full / --partial if given, else default
        # to full_text (matches the spec's "expected" P3PR_READING_MODE for
        # `--zh --full`).
        reading_mode = "full_text" if args.full else "partial_text"

    # Title: prefer user --title, then HTML <title>, then hint, then URL.
    if args.title:
        title = args.title
    elif not args.dry_run and (text_path and text_path.exists()) and not is_pdf:
        # The fetch helper already wrote the page.txt; re-read title via parser
        # by re-running (cheap). To avoid re-fetching, the title was set in
        # meta — but only when we know it. We re-parse the source.html
        # if present so we have a fresh, non-cached value.
        try:
            if body_path and body_path.exists() and not is_pdf:
                with open(body_path, "rb") as f:
                    raw_bytes = f.read()
                _, html_title, _ = _extract_html_text(raw_bytes)
                title = html_title or ""
            else:
                title = ""
        except Exception:  # noqa: BLE001
            title = ""
        if not title:
            title = (hint or {}).get("title") or url
    else:
        title = (hint or {}).get("title") or url

    # Ambiguity check: HTML <title> vs user --title
    if args.title and not args.dry_run and body_path and not is_pdf:
        try:
            with open(body_path, "rb") as f:
                raw_bytes = f.read()
            _, html_title, _ = _extract_html_text(raw_bytes)
            if html_title and html_title.strip() and args.title.strip() and html_title.strip() != args.title.strip():
                # Surface the discrepancy as a non-fatal info line; do not
                # auto-replace. The draft's intake_quality.warnings will pick
                # this up via the title being recorded as the user's choice.
                print(
                    f"[info] HTML <title> ({html_title!r}) differs from "
                    f"--title ({args.title!r}); using --title as canonical",
                    file=sys.stderr,
                )
        except Exception:  # noqa: BLE001
            pass

    # Build extra_note with full fetch + extract telemetry.
    extra_note = (
        f"url={url}; http_status={http_status}; final_url={final_url}; "
        f"content_type={content_type!r}; is_pdf={is_pdf}; "
        f"text_chars={text_chars}; body_path={body_path}"
    )
    if not args.dry_run and is_pdf and text_chars == 0:
        extra_note += (
            " — PDF detected but no text extracted; recommend using `./p3pr pdf` "
            "or installing pdftotext (poppler-utils) and re-running with --full."
        )

    # Build the input_file the runner will read (extracted body) and the
    # additional --resolver-source overlay so the draft records a clean
    # source_resolution trail pointing at the user-supplied URL.
    runner_input_file: str | None = None
    if not args.dry_run and text_path and text_path.exists() and not is_pdf:
        runner_input_file = str(text_path)
    elif not args.dry_run and is_pdf and body_path and body_path.exists():
        # Point the runner at the PDF itself; the runner will record
        # input_kind=paper_url but reading_mode is partial_text so it will
        # NOT claim full_text on a PDF without body extraction.
        runner_input_file = str(body_path)

    return _finalise(
        args,
        input_text=url,
        input_kind="paper_url",
        reading_mode=reading_mode,
        slug=slug,
        run_dir=root,
        title=title,
        arxiv_id=(hint or {}).get("arxiv_id") if hint else None,
        paper_url=url,
        extra_note=extra_note,
        resolver_status=resolver_status,
        resolver_match_type=resolver_match_type,
        canonical_title=(hint or {}).get("title") or "",
        default_slug=slug,
        hint=hint,
        source_url=url,
        input_file=runner_input_file,
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
    source_url: str = "",
    input_file: str | None = None,
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
            source_url=source_url,
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
        authors=getattr(args, "authors", None),
        year=getattr(args, "year", None),
        arxiv_id=arxiv_id,
        paper_url=paper_url,
        fill_pack=args.fill_pack,
        audit=args.audit,
        quality_gate=args.quality_gate and args.language == "zh-CN",
        render=args.render,
        audit_warn_only=args.audit_warn_only,
        resolver_source=str(resolver_source_path) if resolver_source_path else None,
        input_file=input_file,
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
                local_page="",
                page_url="",
                next_action="Fill the draft (follow fill-pack), rerun `./p3pr ... --no-publish` until quality gate passes, then re-publish. Or pass --allow-draft-publish to publish the draft as-is.",
                resolver_status=resolver_status,
                resolver_match_type=resolver_match_type,
                canonical_title=canonical_title or (title or ""),
                arxiv_id=arxiv_id or "",
                default_slug=slug,
            )
            return 1
        # Bug fix v0.2.15-alpha: when the runner skipped render (audit FAILED),
        # `paper-reading-output/index.html` is missing. Publishing an empty
        # directory pushes a 404 stub to gh-pages. Refuse hard — even with
        # --allow-draft-publish, a missing index.html is a publish-shaped bug
        # the user almost certainly did not intend.
        if not page_path.exists():
            print(
                "[error] paper-reading-output/index.html is missing — render was "
                "skipped because the audit (or quality gate) FAILED. Refusing to "
                "publish an empty stub. The fill-pack documents what to fix; "
                "re-run `./p3pr ... --no-publish` after filling, then publish.",
                file=sys.stderr,
            )
            _print_summary(
                "BLOCKED",
                input_kind=input_kind,
                reading_mode=reading_mode,
                run_dir=str(run_dir),
                json_path=str(work_json),
                fill_pack=str(fill_pack),
                local_page="",
                page_url="",
                next_action="render was skipped (audit/qg FAILED); fill the draft per fill-pack and re-run, or pass --audit-warn-only to force render.",
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


# --- finalize subcommand ----------------------------------------------------

_SLUG_FALLBACK_CHARS = re.compile(r"[^a-z0-9-]+")
_SLUG_DASHES = re.compile(r"-+")


def _slugify_title(text: str, *, max_len: int = 80) -> str:
    """Best-effort ASCII slug for a paper title.

    Rules:
    - lowercase, strip
    - ASCII letters / digits kept, anything else collapsed to '-'
    - consecutive '-' merged
    - leading / trailing '-' stripped
    - truncated to max_len characters (at a word boundary when possible)
    - if the result is empty (e.g. a pure-CJK title), returns '' so the caller
      can fall back to the run-dir basename.

    Deliberately stdlib-only: no pypinyin, no unicodedata NFKD stripping of
    Han characters. CJK-only titles fall back to run-dir basename in the
    caller. This is conservative and stable.
    """
    if not text:
        return ""
    s = text.strip().lower()
    s = _SLUG_FALLBACK_CHARS.sub("-", s)
    s = _SLUG_DASHES.sub("-", s).strip("-")
    if len(s) > max_len:
        s = s[:max_len].rsplit("-", 1)[0] or s[:max_len]
    return s.strip("-")


def _get_paper_reading(work_json: Path) -> dict:
    """Read paper_reading.json defensively; return {} on any error."""
    try:
        return json.loads(work_json.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _get_paper_metadata(work_json: Path) -> dict:
    """Return the paper_metadata block of paper_reading.json, or {}."""
    return (_get_paper_reading(work_json).get("paper_metadata", {}) or {})


def _get_reading_mode(work_json: Path) -> str:
    pr = _get_paper_reading(work_json)
    if pr.get("reading_mode"):
        return pr["reading_mode"]
    pm = pr.get("paper_metadata", {}) or {}
    return pm.get("reading_mode") or ""


def _get_target_languages(work_json: Path) -> tuple[str, str]:
    pr = _get_paper_reading(work_json)
    return (
        pr.get("target_language") or "zh-CN",
        pr.get("ui_language") or "zh-CN",
    )


def infer_site_path(run_dir: Path, work_json: Path, explicit: str | None = None) -> str:
    """Pick the gh-pages site-path for this finalize run.

    Precedence:
      1. explicit (--site-path) — used as-is
      2. paper_reading.json: page_slug / slug / paper_metadata.slug /
         paper_metadata.default_slug
      3. paper_metadata.title or top-level title, slugified
      4. run-dir basename
    """
    if explicit:
        return explicit
    pr = _get_paper_reading(work_json)
    pm = pr.get("paper_metadata", {}) or {}
    for key in ("page_slug", "slug", "default_slug"):
        v = pm.get(key) or pr.get(key)
        if isinstance(v, str) and v.strip():
            return _slugify_title(v) or run_dir.name
    title = pm.get("title") or pr.get("title") or run_dir.name
    slug = _slugify_title(title)
    return slug or run_dir.name


def infer_page_title(run_dir: Path, work_json: Path, explicit: str | None = None) -> str:
    """Pick the published page title for this finalize run.

    Precedence:
      1. explicit (--page-title) — used as-is
      2. paper_reading.json: page_title / paper_metadata.page_title
      3. For zh-CN target / ui language: prefer paper_metadata.title_zh /
         paper_metadata.title (or top-level title_zh) over the English title
      4. paper_metadata.title or top-level title
      5. run-dir basename
    """
    if explicit:
        return explicit
    pr = _get_paper_reading(work_json)
    pm = pr.get("paper_metadata", {}) or {}
    for key in ("page_title",):
        v = pm.get(key) or pr.get(key)
        if isinstance(v, str) and v.strip():
            return v
    target_lang, ui_lang = _get_target_languages(work_json)
    is_zh = target_lang == "zh-CN" or ui_lang == "zh-CN"
    if is_zh:
        for key in ("title_zh", "title_zh_cn"):
            v = pm.get(key) or pr.get(key)
            if isinstance(v, str) and v.strip():
                return v
    title = pm.get("title") or pr.get("title")
    if title and title.strip():
        return title
    return run_dir.name


def _warning_to_text(w) -> str:
    """Convert a warning entry (dict or string) to a single line of text."""
    if isinstance(w, dict):
        code = w.get("code") or w.get("type") or "warning"
        msg = (
            w.get("message")
            or w.get("detail")
            or w.get("summary")
            or w.get("path")
            or ""
        )
        path = w.get("path") or w.get("location") or ""
        if path and msg:
            return f"{code}: {msg} (at {path})"
        if msg:
            return f"{code}: {msg}"
        return str(code)
    return str(w)


def _collect_warnings(audit_json_path: str, qg_json_path: str) -> tuple[int, list[str]]:
    """Return (count, [text, ...]) for warnings across audit and quality gate."""
    warnings: list[str] = []
    for path in (audit_json_path, qg_json_path):
        if not path:
            continue
        p = Path(path)
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        # Common shapes: {warnings: [...]}, {issues: [...]}, {findings: [...]}
        for key in ("warnings", "issues", "findings", "problems"):
            items = data.get(key) or []
            if isinstance(items, list):
                for w in items:
                    sev = ""
                    if isinstance(w, dict):
                        sev = (w.get("severity") or w.get("level") or "").lower()
                    if sev and sev not in {"warn", "warning"}:
                        continue
                    warnings.append(_warning_to_text(w))
    return len(warnings), warnings


def summarize_finalize_warnings(
    audit_json_path: str, qg_json_path: str, *, max_lines: int = 3
) -> tuple[int, str]:
    """Return (count, single-line summary) for the finalize summary block.

    The single-line summary is a ' | '-joined list of up to ``max_lines``
    warning messages, ending with '...' when the list is longer.
    """
    count, items = _collect_warnings(audit_json_path, qg_json_path)
    if not count:
        return 0, "no warnings"
    head = items[:max_lines]
    text = " | ".join(head)
    if count > max_lines:
        text = f"{text} ... (+{count - max_lines} more)"
    return count, text


def build_finalize_next_action(
    *,
    status: str,
    publish_requested: bool,
    published: bool,
    page_url: str,
    qg_status: str,
    audit_status: str,
    warning_count: int,
    work_json: str,
    run_dir: str,
) -> str:
    """Produce a clear, actionable next-action string for the summary.

    Distinct messages for the common states, never a single
    "warnings exist" line. The point is to tell the operator exactly
    what to do next without making them re-read the run logs.
    """
    if status == "BLOCKED":
        if audit_status == "FAIL":
            return (
                f"audit FAILED. Edit {work_json} and re-run "
                f"`./p3pr finalize {run_dir}`."
            )
        if qg_status == "FAIL":
            return (
                f"quality gate FAILED. Edit {work_json} and re-run finalize, "
                f"or pass --allow-draft-publish to publish the draft as-is."
            )
        if qg_status == "WARN" and not publish_requested:
            return (
                f"quality gate WARN. Re-run with --allow-warnings to publish, "
                f"or edit {work_json} to address the warnings."
            )
        return (
            f"finalize blocked. Inspect {run_dir}/work/ for audit / quality "
            f"gate / render logs and re-run `./p3pr finalize {run_dir}`."
        )
    if status == "WARN":
        if warning_count:
            return (
                f"Review {warning_count} warning(s) in "
                f"{run_dir}/work/quality_gate_zh_cn.json (or audit_result.json). "
                f"Re-run with --allow-warnings if acceptable."
            )
        if qg_status == "WARN" and not published:
            return (
                "Quality gate WARN. Re-run `./p3pr finalize <run-dir> --publish` "
                "to publish, or pass --allow-warnings to accept the warnings."
            )
        if qg_status == "WARN" and published:
            return (
                "Page published with quality-gate WARN. Review before sharing. "
                f"Page: {page_url}"
            )
        return "Review the warnings above and re-run finalize if needed."
    # status == PASS
    if published:
        if warning_count:
            return (
                f"Done. Page published: {page_url}. "
                f"{warning_count} non-blocking warning(s) noted."
            )
        return (
            f"Done. Page published: {page_url}. "
            f"Re-run the same command to re-publish."
        )
    return (
        "Done. Local page rendered. "
        f"Re-run `./p3pr finalize {run_dir} --publish` to publish."
    )


def _finalize_print_summary(
    *,
    status: str,
    run_dir: str,
    reading_mode: str = "",
    language: str = "zh-CN",
    work_json: str = "",
    audit_json: str = "",
    quality_gate_json: str = "",
    site_path: str = "",
    page_title: str = "",
    local_page: str = "",
    page_url: str = "",
    published_audit_json: str = "",
    audit_status: str = "unknown",
    qg_status: str = "unknown",
    warning_count: int = 0,
    warning_summary: str = "no warnings",
    next_action: str = "",
) -> None:
    """Print the fixed P3PR_FINALIZE_STATUS summary block."""
    print()
    print("=" * 60)
    print(f"P3PR_FINALIZE_STATUS: {status}")
    print(f"P3PR_RUN_DIR: {run_dir}")
    print(f"P3PR_READING_MODE: {reading_mode}")
    print(f"P3PR_LANGUAGE: {language}")
    print(f"P3PR_SITE_PATH: {site_path}")
    print(f"P3PR_PAGE_TITLE: {page_title}")
    print(f"P3PR_JSON: {work_json}")
    print(f"P3PR_AUDIT_JSON: {audit_json}")
    print(f"P3PR_AUDIT_STATUS: {audit_status}")
    print(f"P3PR_QUALITY_GATE_JSON: {quality_gate_json}")
    print(f"P3PR_QUALITY_GATE_STATUS: {qg_status}")
    print(f"P3PR_LOCAL_PAGE: {local_page}")
    print(f"P3PR_PAGE_URL: {page_url}")
    print(f"P3PR_PUBLISHED_AUDIT_JSON: {published_audit_json}")
    print(f"P3PR_WARNING_COUNT: {warning_count}")
    print(f"P3PR_WARNING_SUMMARY: {warning_summary}")
    print(f"P3PR_NEXT_ACTION: {next_action}")
    print("=" * 60)


def handle_finalize(args) -> int:
    """Finalize an already-filled P3PR run directory.

    Reads <run-dir>/work/paper_reading.json, runs audit + zh-CN quality gate +
    render, optionally publishes to gh-pages, optionally runs the published-pages
    audit. Does NOT auto-fill the draft — the operator must have already filled
    work/paper_reading.json before invoking finalize.
    """
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.is_dir():
        print(f"[error] run-dir is not a directory: {run_dir}", file=sys.stderr)
        _finalize_print_summary(
            status="BLOCKED",
            run_dir=str(run_dir),
            next_action=f"run-dir does not exist: {run_dir}",
        )
        return 1

    work_json = run_dir / "work" / "paper_reading.json"
    if not work_json.exists():
        print(
            f"[error] missing {work_json}. finalize expects a run directory "
            "with a filled work/paper_reading.json. Run `./p3pr url <url> --no-publish` "
            "or another p3pr subcommand first, fill the draft per the fill-pack, "
            "then re-invoke finalize.",
            file=sys.stderr,
        )
        _finalize_print_summary(
            status="BLOCKED",
            run_dir=str(run_dir),
            work_json=str(work_json),
            next_action=f"work/paper_reading.json missing at {work_json}; fill the draft first.",
        )
        return 1

    # Inferred values (used by both dry-run and real run; explicit flags win).
    inferred_site_path = infer_site_path(run_dir, work_json, args.site_path)
    inferred_page_title = infer_page_title(run_dir, work_json, args.page_title)
    reading_mode = _get_reading_mode(work_json) or "unknown"
    target_lang, ui_lang = _get_target_languages(work_json)
    run_qg = (not args.skip_quality_gate) and (target_lang == "zh-CN" or ui_lang == "zh-CN")

    # Dry-run: print plan, do nothing else.
    if getattr(args, "dry_run", False):
        print()
        print("=" * 60)
        print("P3PR_FINALIZE_DRY_RUN: true")
        print(f"would_read_json: {work_json}")
        print(f"would_audit: True (audit_paper_reading.py)")
        print(f"would_quality_gate: {run_qg} "
              f"(target_language={target_lang}, ui_language={ui_lang}, "
              f"skip_quality_gate={args.skip_quality_gate})")
        print(f"would_render: True (render_page.py → {run_dir / 'paper-reading-output'})")
        print(f"would_publish: {bool(args.publish)} (repo={args.repo}, branch={args.branch})")
        print(f"inferred_site_path: {inferred_site_path} "
              f"(source: {'explicit --site-path' if args.site_path else 'auto from paper_reading.json / run-dir'})")
        print(f"inferred_page_title: {inferred_page_title} "
              f"(source: {'explicit --page-title' if args.page_title else 'auto from paper_reading.json'})")
        print(f"P3PR_SITE_PATH: {inferred_site_path}")
        print(f"P3PR_PAGE_TITLE: {inferred_page_title}")
        print(f"P3PR_READING_MODE: {reading_mode}")
        print(f"P3PR_LANGUAGE: {target_lang}/{ui_lang}")
        if args.publish:
            print(f"published_audit_after_publish: {not args.skip_published_audit}")
        print("=" * 60)
        return 0

    # --- 1. Audit ---
    audit_json = run_dir / "work" / "audit_final.json"
    audit_argv = [sys.executable, str(AUDIT), "--input", str(work_json),
                  "--json-output", str(audit_json)]
    print(f"[info] running audit: {' '.join(audit_argv)}")
    audit_rc = subprocess.call(audit_argv)
    if audit_rc != 0:
        # audit_paper_reading.py exits non-zero on FAIL
        print(
            f"[error] audit FAILED (rc={audit_rc}). finalize will not render or publish. "
            "Fix work/paper_reading.json and re-run finalize.",
            file=sys.stderr,
        )
        wcount, wsummary = summarize_finalize_warnings(str(audit_json), "")
        _finalize_print_summary(
            status="BLOCKED",
            run_dir=str(run_dir),
            reading_mode=reading_mode,
            language=f"{target_lang}/{ui_lang}",
            work_json=str(work_json),
            audit_json=str(audit_json),
            audit_status="FAIL",
            site_path=inferred_site_path,
            page_title=inferred_page_title,
            warning_count=wcount,
            warning_summary=wsummary,
            next_action=build_finalize_next_action(
                status="BLOCKED",
                publish_requested=bool(args.publish),
                published=False,
                page_url="",
                qg_status="unknown",
                audit_status="FAIL",
                warning_count=wcount,
                work_json=str(work_json),
                run_dir=str(run_dir),
            ),
        )
        return 1

    # Try to read audit result for status.
    audit_status = "PASS"
    try:
        ar = json.loads(audit_json.read_text(encoding="utf-8"))
        audit_status = ar.get("status", "PASS")
    except Exception:  # noqa: BLE001
        audit_status = "PASS"
    if audit_status == "FAIL":
        print(
            "[error] audit result is FAIL. finalize will not render or publish.",
            file=sys.stderr,
        )
        wcount, wsummary = summarize_finalize_warnings(str(audit_json), "")
        _finalize_print_summary(
            status="BLOCKED",
            run_dir=str(run_dir),
            reading_mode=reading_mode,
            language=f"{target_lang}/{ui_lang}",
            work_json=str(work_json),
            audit_json=str(audit_json),
            audit_status="FAIL",
            site_path=inferred_site_path,
            page_title=inferred_page_title,
            warning_count=wcount,
            warning_summary=wsummary,
            next_action=build_finalize_next_action(
                status="BLOCKED",
                publish_requested=bool(args.publish),
                published=False,
                page_url="",
                qg_status="unknown",
                audit_status="FAIL",
                warning_count=wcount,
                work_json=str(work_json),
                run_dir=str(run_dir),
            ),
        )
        return 1

    # --- 2. Quality gate (zh-CN only) ---
    quality_gate_json = ""
    qg_status = "SKIPPED"

    if not args.skip_quality_gate and run_qg:
        quality_gate_json = str(run_dir / "work" / "quality_gate_zh_cn.json")
        qg_argv = [sys.executable, str(QUALITY_GATE), "--input", str(work_json),
                   "--json-output", str(quality_gate_json)]
        if args.allow_warnings:
            qg_argv.append("--warn-only")
        print(f"[info] running quality gate: {' '.join(qg_argv)}")
        qg_rc = subprocess.call(qg_argv)
        try:
            qd = json.loads(Path(quality_gate_json).read_text(encoding="utf-8"))
            qg_status = qd.get("status", "UNKNOWN")
        except Exception:  # noqa: BLE001
            qg_status = "UNKNOWN"
        print(f"[info] quality gate status: {qg_status} (rc={qg_rc})")
        if qg_status == "FAIL" and not args.allow_draft_publish:
            print(
                f"[error] quality gate FAIL. finalize will not render or publish. "
                f"Re-run with --allow-warnings to ignore WARN, or fix {work_json}.",
                file=sys.stderr,
            )
            wcount, wsummary = summarize_finalize_warnings(
                str(audit_json), str(quality_gate_json)
            )
            _finalize_print_summary(
                status="BLOCKED",
                run_dir=str(run_dir),
                reading_mode=reading_mode,
                language=f"{target_lang}/{ui_lang}",
                work_json=str(work_json),
                audit_json=str(audit_json),
                audit_status=audit_status,
                quality_gate_json=str(quality_gate_json),
                qg_status=qg_status,
                site_path=inferred_site_path,
                page_title=inferred_page_title,
                warning_count=wcount,
                warning_summary=wsummary,
                next_action=build_finalize_next_action(
                    status="BLOCKED",
                    publish_requested=bool(args.publish),
                    published=False,
                    page_url="",
                    qg_status=qg_status,
                    audit_status=audit_status,
                    warning_count=wcount,
                    work_json=str(work_json),
                    run_dir=str(run_dir),
                ),
            )
            return 1
    else:
        print(f"[info] quality gate skipped (skip_quality_gate={args.skip_quality_gate}, "
              f"target_language={target_lang}, ui_language={ui_lang})")

    # --- 3. Render ---
    output_dir = run_dir / "paper-reading-output"
    output_dir.mkdir(parents=True, exist_ok=True)
    render_argv = [sys.executable, str(RENDER), "--input", str(work_json),
                   "--output", str(output_dir)]
    print(f"[info] running render: {' '.join(render_argv)}")
    render_rc = subprocess.call(render_argv)
    if render_rc != 0:
        print(
            f"[error] render_page.py exited {render_rc}. finalize will not publish.",
            file=sys.stderr,
        )
        wcount, wsummary = summarize_finalize_warnings(
            str(audit_json), str(quality_gate_json)
        )
        _finalize_print_summary(
            status="BLOCKED",
            run_dir=str(run_dir),
            reading_mode=reading_mode,
            language=f"{target_lang}/{ui_lang}",
            work_json=str(work_json),
            audit_json=str(audit_json),
            audit_status=audit_status,
            quality_gate_json=quality_gate_json,
            qg_status=qg_status,
            site_path=inferred_site_path,
            page_title=inferred_page_title,
            warning_count=wcount,
            warning_summary=wsummary,
            next_action=build_finalize_next_action(
                status="BLOCKED",
                publish_requested=bool(args.publish),
                published=False,
                page_url="",
                qg_status=qg_status,
                audit_status=audit_status,
                warning_count=wcount,
                work_json=str(work_json),
                run_dir=str(run_dir),
            ),
        )
        return 1

    # v0.2.15 core guard: index.html must exist before publish.
    index_html = output_dir / "index.html"
    if not index_html.exists():
        print(
            f"[error] {index_html} missing after render. finalize refuses to publish "
            "an empty stub. (This is the v0.2.15 publish-gate.) Re-run the render step "
            "or fix work/paper_reading.json.",
            file=sys.stderr,
        )
        wcount, wsummary = summarize_finalize_warnings(
            str(audit_json), str(quality_gate_json)
        )
        _finalize_print_summary(
            status="BLOCKED",
            run_dir=str(run_dir),
            reading_mode=reading_mode,
            language=f"{target_lang}/{ui_lang}",
            work_json=str(work_json),
            audit_json=str(audit_json),
            audit_status=audit_status,
            quality_gate_json=quality_gate_json,
            qg_status=qg_status,
            site_path=inferred_site_path,
            page_title=inferred_page_title,
            warning_count=wcount,
            warning_summary=wsummary,
            next_action=(
                f"render produced no index.html at {index_html}; "
                "check renderer and re-run finalize."
            ),
        )
        return 1

    local_page = str(index_html)
    page_url = ""
    published_audit_json = ""

    # --- 4. Publish (optional) ---
    if not args.publish:
        wcount, wsummary = summarize_finalize_warnings(
            str(audit_json), str(quality_gate_json)
        )
        final_status = "WARN" if qg_status == "WARN" else "PASS"
        _finalize_print_summary(
            status=final_status,
            run_dir=str(run_dir),
            reading_mode=reading_mode,
            language=f"{target_lang}/{ui_lang}",
            work_json=str(work_json),
            audit_json=str(audit_json),
            audit_status=audit_status,
            quality_gate_json=quality_gate_json,
            qg_status=qg_status,
            site_path=inferred_site_path,
            page_title=inferred_page_title,
            local_page=local_page,
            page_url="",
            published_audit_json="",
            warning_count=wcount,
            warning_summary=wsummary,
            next_action=build_finalize_next_action(
                status=final_status,
                publish_requested=False,
                published=False,
                page_url="",
                qg_status=qg_status,
                audit_status=audit_status,
                warning_count=wcount,
                work_json=str(work_json),
                run_dir=str(run_dir),
            ),
        )
        return 0

    site_path = inferred_site_path
    page_title = inferred_page_title

    pub_argv = [
        str(PUBLISH_SH),
        "--output", str(output_dir),
        "--repo", args.repo,
        "--branch", args.branch,
        "--site-path", site_path,
        "--page-title", page_title,
        "--message", f"Finalize P3PR page: {site_path}",
    ]
    print(f"[info] running publisher: {' '.join(pub_argv)}")
    pub_rc = subprocess.call(pub_argv)
    if pub_rc != 0:
        print(
            f"[error] publisher exited {pub_rc}. The local page is at {local_page} "
            "but gh-pages push failed.",
            file=sys.stderr,
        )
        wcount, wsummary = summarize_finalize_warnings(
            str(audit_json), str(quality_gate_json)
        )
        _finalize_print_summary(
            status="BLOCKED",
            run_dir=str(run_dir),
            reading_mode=reading_mode,
            language=f"{target_lang}/{ui_lang}",
            work_json=str(work_json),
            audit_json=str(audit_json),
            audit_status=audit_status,
            quality_gate_json=quality_gate_json,
            qg_status=qg_status,
            site_path=site_path,
            page_title=page_title,
            local_page=local_page,
            page_url="",
            published_audit_json="",
            warning_count=wcount,
            warning_summary=wsummary,
            next_action=(
                f"publish FAILED (rc={pub_rc}); "
                "check gh login / branch protection / network."
            ),
        )
        return 1

    # Compute the public page URL.
    if "/" in args.repo:
        owner, repo_name = args.repo.split("/", 1)
        page_url = f"https://{owner}.github.io/{repo_name}/{site_path}/"

    # --- 5. Published-pages audit (optional) ---
    if not args.skip_published_audit:
        if args.repo != DEFAULT_REPO:
            print(
                f"[warn] published-pages audit uses default site root "
                f"(https://{DEFAULT_REPO.split('/')[0]}.github.io/{DEFAULT_REPO.split('/')[1]}/); "
                f"--repo={args.repo} is non-default. Skipping audit to avoid false negatives.",
                file=sys.stderr,
            )
        else:
            audit_dir = run_dir / "work"
            audit_dir.mkdir(parents=True, exist_ok=True)
            reports_dir = run_dir / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            published_audit_json = str(audit_dir / "published_pages_audit_after_finalize.json")
            pa_md = reports_dir / "published_pages_audit_after_finalize.md"
            site_root = f"https://{DEFAULT_REPO.split('/')[0]}.github.io/{DEFAULT_REPO.split('/')[1]}"
            pa_argv = [
                sys.executable, str(HERE / "audit_published_pages.py"),
                "--manifest-url", f"{site_root}/published_pages.json",
                "--site-root", site_root,
                "--json-output", published_audit_json,
                "--markdown-output", str(pa_md),
                "--include-root", "--warn-only",
            ]
            print(f"[info] running published-pages audit: {' '.join(pa_argv)}")
            pa_rc = subprocess.call(pa_argv)
            try:
                pd = json.loads(Path(published_audit_json).read_text(encoding="utf-8"))
                pa_overall = pd.get("overall")
                pa_fail = pd.get("pages_fail", 0)
                print(f"[info] published-pages audit overall={pa_overall} pages_fail={pa_fail} (rc={pa_rc})")
            except Exception:  # noqa: BLE001
                print(f"[warn] could not parse published-pages audit output (rc={pa_rc})")

    # --- Summary ---
    wcount, wsummary = summarize_finalize_warnings(
        str(audit_json), str(quality_gate_json)
    )
    if qg_status == "WARN" and not args.allow_warnings:
        final_status = "WARN"
    else:
        final_status = "PASS"

    _finalize_print_summary(
        status=final_status,
        run_dir=str(run_dir),
        reading_mode=reading_mode,
        language=f"{target_lang}/{ui_lang}",
        work_json=str(work_json),
        audit_json=str(audit_json),
        audit_status=audit_status,
        quality_gate_json=quality_gate_json,
        qg_status=qg_status,
        site_path=site_path,
        page_title=page_title,
        local_page=local_page,
        page_url=page_url,
        published_audit_json=published_audit_json,
        warning_count=wcount,
        warning_summary=wsummary,
        next_action=build_finalize_next_action(
            status=final_status,
            publish_requested=True,
            published=True,
            page_url=page_url,
            qg_status=qg_status,
            audit_status=audit_status,
            warning_count=wcount,
            work_json=str(work_json),
            run_dir=str(run_dir),
        ),
    )
    return 0


def build_finalize_parser() -> argparse.ArgumentParser:
    """Build the standalone argparse parser for `p3pr finalize <run-dir>`.

    Kept separate from the main `p3pr` parser so the finalize subcommand has
    its own clean flag set (no carry-over of url/arxiv flags, etc.). When
    invoked as `./p3pr finalize <run-dir>` the main parser dispatches here
    before the rest of the pipeline runs.
    """
    p = argparse.ArgumentParser(
        prog="p3pr finalize",
        description=(
            "Finalize an already-filled P3PR run directory: audit, "
            "zh-CN quality gate, render, optional publish, optional "
            "published-pages audit. Does NOT auto-fill the draft."
        ),
    )
    p.add_argument("run_dir", help="Path to a P3PR run directory "
                                    "(must contain work/paper_reading.json)")
    p.add_argument("--publish", dest="publish", action="store_true", default=False)
    p.add_argument("--no-publish", dest="publish", action="store_false")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--branch", default=DEFAULT_BRANCH)
    p.add_argument("--site-path", default=None,
                   help="Override site-path for the published page "
                        "(default: <run-dir> basename)")
    p.add_argument("--page-title", default=None)
    p.add_argument("--allow-warnings", action="store_true", default=False,
                   help="Treat quality-gate WARN as non-blocking")
    p.add_argument("--allow-draft-publish", action="store_true", default=False,
                   help="Publish even when quality gate FAILED (still BLOCKs "
                        "if audit FAILED or render produced no index.html)")
    p.add_argument("--skip-quality-gate", action="store_true", default=False)
    p.add_argument("--skip-published-audit", action="store_true", default=False)
    p.add_argument("--published-audit", dest="published_audit",
                   action="store_true", default=True,
                   help="Run published-pages audit after publish (default true)")
    p.add_argument("--no-published-audit", dest="published_audit",
                   action="store_false")
    p.add_argument("--dry-run", action="store_true", default=False)
    p.add_argument("--json-output", default=None,
                   help="Reserved for future structured summary output")
    return p


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
    p.add_argument("--authors", help="Override paper authors (comma-separated, e.g. 'Hamming, R. W., Preview, A.')")
    p.add_argument("--year", help="Override paper year (integer)")
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
        ("url", "Fetch an HTML / PDF page from a URL and run the pipeline (v0.2.14)"),
        ("finalize", "Finalize an already-filled run directory: audit + zh-CN quality gate + render + optional publish (v0.2.17)"),
    ]:
        sp = sub.add_parser(name, help=help_text)
        if name == "finalize":
            # finalize has its own dedicated parser (build_finalize_parser) with
            # a different flag set (no --language, --full, etc.). We register
            # the same flag set on this stub subparser too, so `./p3pr finalize
            # --help` produces the correct usage line. main() will re-parse argv
            # with build_finalize_parser() for full validation. Skip the parent-
            # flag loop below.
            sp.add_argument("run_dir", nargs="?", default=None,
                            help="Path to a P3PR run directory "
                                 "(must contain work/paper_reading.json)")
            sp.add_argument("--publish", dest="publish",
                            action="store_true", default=False)
            sp.add_argument("--no-publish", dest="publish",
                            action="store_false")
            sp.add_argument("--repo", default=DEFAULT_REPO)
            sp.add_argument("--branch", default=DEFAULT_BRANCH)
            sp.add_argument("--site-path", default=None,
                            help="Override site-path for the published page "
                                 "(default: <run-dir> basename)")
            sp.add_argument("--page-title", default=None)
            sp.add_argument("--allow-warnings", action="store_true",
                            default=False,
                            help="Treat quality-gate WARN as non-blocking")
            sp.add_argument("--allow-draft-publish", action="store_true",
                            default=False,
                            help="Publish even when quality gate FAILED "
                                 "(still BLOCKs if audit FAILED or render "
                                 "produced no index.html)")
            sp.add_argument("--skip-quality-gate", action="store_true",
                            default=False)
            sp.add_argument("--skip-published-audit", action="store_true",
                            default=False)
            sp.add_argument("--published-audit", dest="published_audit",
                            action="store_true", default=True,
                            help="Run published-pages audit after publish "
                                 "(default true)")
            sp.add_argument("--no-published-audit", dest="published_audit",
                            action="store_false")
            sp.add_argument("--dry-run", action="store_true", default=False)
            sp.add_argument("--json-output", default=None,
                            help="Reserved for future structured summary output")
            continue
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
        sp.add_argument("--authors", default=None)
        sp.add_argument("--year", default=None)
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
    # Use parse_known_args so that subcommand-specific flags (especially for
    # `finalize`, which has its own dedicated parser) are not rejected at the
    # top level. We re-parse argv with the finalize-specific parser in
    # main()'s dispatch below.
    args, _unknown = parser.parse_known_args(argv)

    # Promote subcommand-level flag values to the top-level namespace so the
    # handlers can use a single `args.foo` regardless of where the user put
    # the flag. If the sub-level parser did not see the flag (sub_val is None),
    # fall back to the parser-level default.
    _PROMOTE = (
        "language", "slug", "output_root", "full", "partial", "abstract_only",
        "screenshot_only", "title", "authors", "year", "fill_pack", "audit",
        "quality_gate", "render", "publish", "repo", "branch", "page_title",
        "audit_warn_only", "allow_draft_publish", "dry_run", "zh", "en",
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
        "url": handle_url,
    }
    # finalize has its own dedicated parser because its flag set is intentionally
    # different from the url/arxiv subcommands. We re-parse argv with the
    # finalize parser and dispatch to handle_finalize.
    if args.command == "finalize":
        finalize_parser = build_finalize_parser()
        # The main parser consumed `finalize` from argv; pass the remainder
        # (after `finalize`) to the finalize parser so it sees the run_dir
        # positional and finalize-specific flags.
        if argv is None:
            argv = sys.argv[1:]
        # Skip leading flags parsed by the main parser; we want everything
        # from `finalize` onward. Simpler: find `finalize` in argv and take
        # the slice after it.
        try:
            idx = argv.index("finalize")
            finalize_argv = argv[idx + 1:]
        except ValueError:
            finalize_argv = []
        finalize_args = finalize_parser.parse_args(finalize_argv)
        return handle_finalize(finalize_args)

    handler = handlers.get(args.command)
    if handler is None:
        print(f"[error] unknown subcommand: {args.command}", file=sys.stderr)
        return 2
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
