#!/usr/bin/env python3
"""
resolver_hints.py — shared resolver hints data source for paper-three-pass-reader.

This module is the single source of truth for paper / repo resolution. It loads
resolver_hints.json and exposes helpers used by p3pr CLI, run_paper_reading runner,
tests, and documentation.

Stdlib-only. No network access. No external dependencies.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Resolve the data file relative to this script so the helper works regardless of CWD.
_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_FILE = os.path.normpath(
    os.path.join(_HERE, "..", "data", "resolver_hints.json")
)


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_hints(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the resolver hints JSON. Single source of truth."""
    p = path or _DATA_FILE
    if not os.path.isfile(p):
        return {"schema_version": "missing", "papers": [], "repo_hints": []}
    try:
        data = json.loads(_read_text(p))
    except json.JSONDecodeError as e:
        return {
            "schema_version": "invalid",
            "error": f"JSON decode error: {e}",
            "papers": [],
            "repo_hints": [],
        }
    if not isinstance(data, dict):
        return {"schema_version": "invalid", "papers": [], "repo_hints": []}
    data.setdefault("papers", [])
    data.setdefault("repo_hints", [])
    return data


def normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, strip surrounding quotes / punctuation."""
    if text is None:
        return ""
    s = str(text).strip().lower()
    # Strip leading/trailing quotes and parens
    s = s.strip("'\"`()[]")
    # Collapse multiple whitespace
    s = re.sub(r"\s+", " ", s)
    return s


_ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5}(v\d+)?)", re.IGNORECASE)
_ARXIV_URL_RE = re.compile(
    r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", re.IGNORECASE
)
_GH_URL_RE = re.compile(
    r"github\.com/([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+?)(?:\.git|/.*)?$",
    re.IGNORECASE,
)
_OWNER_REPO_RE = re.compile(
    r"^([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)$"
)


def _extract_arxiv_id(text: str) -> Optional[str]:
    if not text:
        return None
    m = _ARXIV_URL_RE.search(text)
    if m:
        return m.group(1)
    m = _ARXIV_ID_RE.search(text)
    if m:
        return m.group(1)
    return None


def _extract_repo(text: str) -> Optional[str]:
    """Return normalized owner/repo or None."""
    if not text:
        return None
    s = text.strip()
    m = _GH_URL_RE.search(s)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    # bare owner/repo
    bare = re.sub(r"\.git$", "", s)
    if "/" in bare and " " not in bare and not bare.startswith("http"):
        m2 = _OWNER_REPO_RE.match(bare)
        if m2:
            return f"{m2.group(1)}/{m2.group(2)}"
    return None


def _paper_to_dict(p: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of the paper entry with only the public fields."""
    out = dict(p)
    return out


def _empty_result(reason: str) -> Dict[str, Any]:
    return {
        "status": "not_found",
        "match_type": "none",
        "confidence": "low",
        "paper": {},
        "candidates": [],
        "source_resolution_step": reason,
    }


def _make_step(stage: str, detail: str) -> str:
    return f"{stage}: {detail}"


def resolve_title(title: str, hints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Resolve a paper title or alias to a canonical paper entry.

    Matching is case-insensitive and tolerant to whitespace / quote stripping.
    """
    h = hints if hints is not None else load_hints()
    if not title:
        return _empty_result("empty input")

    norm_input = normalize_text(title)

    # 1. Exact canonical title match
    candidates: List[Dict[str, Any]] = []
    for p in h.get("papers", []):
        if not isinstance(p, dict):
            continue
        ct = normalize_text(p.get("canonical_title", ""))
        if not ct:
            continue
        aliases = [normalize_text(a) for a in (p.get("aliases") or [])]
        if norm_input == ct or norm_input in aliases:
            return {
                "status": "matched",
                "match_type": "title" if norm_input == ct else "alias",
                "confidence": "high",
                "paper": _paper_to_dict(p),
                "candidates": [_paper_to_dict(p)],
                "source_resolution_step": _make_step(
                    "title_resolver",
                    f"matched canonical/alias of {p.get('id', '?')}",
                ),
            }
        # collect fuzzy candidates (substring) for ambiguous
        if norm_input and (norm_input in ct or any(norm_input in a for a in aliases)):
            candidates.append(_paper_to_dict(p))

    if candidates:
        if len(candidates) == 1:
            p = candidates[0]
            return {
                "status": "matched",
                "match_type": "title",
                "confidence": "medium",
                "paper": p,
                "candidates": candidates,
                "source_resolution_step": _make_step(
                    "title_resolver",
                    f"fuzzy match {p.get('id', '?')}",
                ),
            }
        return {
            "status": "ambiguous",
            "match_type": "title",
            "confidence": "low",
            "paper": {},
            "candidates": candidates,
            "source_resolution_step": _make_step(
                "title_resolver",
                f"{len(candidates)} fuzzy candidates; needs_confirmation",
            ),
        }

    return _empty_result("no title/alias match")


def resolve_arxiv(
    arxiv_id_or_url: str, hints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Resolve an arXiv id (e.g. 2503.08102) or URL to a canonical paper entry."""
    h = hints if hints is not None else load_hints()
    aid = _extract_arxiv_id(arxiv_id_or_url or "")
    if not aid:
        return _empty_result("no arxiv id in input")

    for p in h.get("papers", []):
        if not isinstance(p, dict):
            continue
        if p.get("arxiv_id") and normalize_text(p.get("arxiv_id")) == normalize_text(aid):
            return {
                "status": "matched",
                "match_type": "arxiv",
                "confidence": "high",
                "paper": _paper_to_dict(p),
                "candidates": [_paper_to_dict(p)],
                "source_resolution_step": _make_step(
                    "arxiv_resolver",
                    f"matched {p.get('id', '?')} via arxiv {aid}",
                ),
            }

    # arXiv id parsed but no canonical paper registered
    return {
        "status": "not_found",
        "match_type": "arxiv",
        "confidence": "medium",
        "paper": {
            "arxiv_id": aid,
            "paper_url": f"https://arxiv.org/abs/{aid}",
            "pdf_url": f"https://arxiv.org/pdf/{aid}",
        },
        "candidates": [],
        "source_resolution_step": _make_step(
            "arxiv_resolver",
            f"arxiv id {aid} parsed but no canonical paper registered; needs download",
        ),
    }


def resolve_repo(
    repo_url_or_hint: str, hints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Resolve a GitHub repo URL or owner/repo fragment to a canonical paper entry."""
    h = hints if hints is not None else load_hints()
    if not repo_url_or_hint:
        return _empty_result("empty input")

    # First try explicit repo_hints table
    norm = normalize_text(repo_url_or_hint)
    repo_pair = _extract_repo(repo_url_or_hint) or norm

    for rh in h.get("repo_hints", []):
        if not isinstance(rh, dict):
            continue
        patterns = [normalize_text(p) for p in (rh.get("match_patterns") or [])]
        if any(
            pat and (pat in norm or pat == repo_pair.lower())
            for pat in patterns
        ):
            pid = rh.get("paper_id")
            paper = next(
                (
                    _paper_to_dict(p)
                    for p in h.get("papers", [])
                    if isinstance(p, dict) and p.get("id") == pid
                ),
                {},
            )
            return {
                "status": "matched",
                "match_type": "repo",
                "confidence": "high",
                "paper": paper,
                "candidates": [paper] if paper else [],
                "source_resolution_step": _make_step(
                    "repo_resolver",
                    f"matched repo hint -> paper {pid}",
                ),
            }

    # Fall back: any paper whose repo_urls contains this repo
    candidates = []
    for p in h.get("papers", []):
        if not isinstance(p, dict):
            continue
        for r in (p.get("repo_urls") or []):
            if normalize_text(r) in norm or (
                repo_pair and repo_pair.lower() in normalize_text(r)
            ):
                candidates.append(_paper_to_dict(p))
                break

    if candidates:
        if len(candidates) == 1:
            p = candidates[0]
            return {
                "status": "matched",
                "match_type": "repo",
                "confidence": "medium",
                "paper": p,
                "candidates": candidates,
                "source_resolution_step": _make_step(
                    "repo_resolver",
                    f"matched {p.get('id', '?')} via repo_urls",
                ),
            }
        return {
            "status": "ambiguous",
            "match_type": "repo",
            "confidence": "low",
            "paper": {},
            "candidates": candidates,
            "source_resolution_step": _make_step(
                "repo_resolver",
                f"{len(candidates)} candidates; needs_confirmation",
            ),
        }

    return _empty_result("no repo hint match")


def resolve_any(
    input_text: str, input_kind: str, hints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Resolve any input by trying the appropriate resolver first.

    input_kind: paper_title, paper_identifier, project_or_repo, ambiguous_clue
    """
    h = hints if hints is not None else load_hints()
    if not input_text:
        return _empty_result("empty input")

    kind = (input_kind or "ambiguous_clue").lower()

    # Try arXiv first for identifiers
    if kind in ("paper_identifier", "ambiguous_clue"):
        aid = _extract_arxiv_id(input_text)
        if aid:
            r = resolve_arxiv(aid, h)
            if r.get("status") == "matched":
                return r
            # fall through

    # Try repo
    if kind in ("project_or_repo", "ambiguous_clue"):
        if "github.com" in input_text or "/" in input_text:
            r = resolve_repo(input_text, h)
            if r.get("status") in ("matched", "ambiguous"):
                return r

    # Try title
    if kind in ("paper_title", "ambiguous_clue"):
        r = resolve_title(input_text, h)
        if r.get("status") in ("matched", "ambiguous"):
            return r

    # If identifier, also try arxiv once more
    if kind == "paper_identifier":
        r = resolve_arxiv(input_text, h)
        return r

    return _empty_result("no resolver matched")


def paper_to_runner_overrides(paper: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a canonical paper dict into runner override fields."""
    if not paper:
        return {}
    overrides: Dict[str, Any] = {}
    if paper.get("canonical_title"):
        overrides["title"] = paper["canonical_title"]
    if paper.get("arxiv_id"):
        overrides["arxiv_id"] = paper["arxiv_id"]
    if paper.get("paper_url"):
        overrides["paper_url"] = paper["paper_url"]
    if paper.get("default_slug"):
        overrides["default_slug"] = paper["default_slug"]
    return overrides


# ---------------------------------------------------------------------------
# Minimal CLI
# ---------------------------------------------------------------------------

def _cli(argv: List[str]) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="resolve_paper_hint",
        description="Resolve a paper / repo / arXiv hint to a canonical paper entry.",
    )
    ap.add_argument(
        "kind",
        choices=["title", "arxiv", "repo", "any"],
        help="resolver kind to run",
    )
    ap.add_argument("value", help="input text (title, arxiv id/url, repo url)")
    ap.add_argument(
        "--hints",
        default=None,
        help="path to resolver_hints.json (default: bundled)",
    )
    ap.add_argument(
        "--input-kind",
        default="ambiguous_clue",
        help="input_kind for 'any' resolver (paper_title, paper_identifier, project_or_repo, ambiguous_clue)",
    )
    ns = ap.parse_args(argv)

    hints = load_hints(ns.hints) if ns.hints else load_hints()

    if ns.kind == "title":
        out = resolve_title(ns.value, hints)
    elif ns.kind == "arxiv":
        out = resolve_arxiv(ns.value, hints)
    elif ns.kind == "repo":
        out = resolve_repo(ns.value, hints)
    else:
        out = resolve_any(ns.value, ns.input_kind, hints)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
