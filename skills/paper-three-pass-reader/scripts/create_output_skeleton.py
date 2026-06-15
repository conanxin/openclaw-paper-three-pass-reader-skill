#!/usr/bin/env python3
"""
create_output_skeleton.py — paper-three-pass-reader (v0.1.0-alpha)

Create an empty paper-reading-output/ skeleton for a new paper.

Usage:
    python3 create_output_skeleton.py \
        --output paper-reading-output \
        --title "Attention Is All You Need"

Design:
- Pure stdlib (argparse, json, pathlib).
- Writes empty templates for every required data/ JSON.
- Writes placeholder Markdown for every required reports/ file.
- Writes a minimal index.html copy + assets/ so the page is browsable
  even before any reading pass has been done.
- Idempotent: re-running is safe; missing files are created, existing ones
  are NOT overwritten (so partial work is preserved).
"""

from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
TEMPLATE_DIR = HERE.parent / "templates"


PLACEHOLDER_PAPER_READING = {
    "schema_version": "0.1.0",
    "paper_metadata": {
        "title": None,
        "authors": [],
        "year": None,
        "venue": None,
        "identifiers": {
            "arxiv_id": None, "doi": None, "openreview_id": None, "url": None
        },
        "source_kind": None,
        "reading_mode": "full_text",
    },
    "intake_quality": {
        "input_kind": None,
        "reading_mode": None,
        "confidence": "low",
        "needs_confirmation": True,
        "missing_fields": ["title", "authors", "year"],
        "warnings": ["Skeleton only — no reading pass has been run yet."],
    },
    "summaries": {
        "one_sentence": "",
        "three_sentence": ["", "", ""],
        "ten_sentence": [""] * 10,
    },
    "five_cs": {
        "category": "", "context": "", "correctness": "",
        "contributions": [], "clarity": "",
    },
    "pass1": {
        "bird_eye_notes": "",
        "decision": "CONTINUE_FULL",
        "decision_rationale": "",
    },
    "pass2": {
        "main_ideas": [],
        "key_references": [],
    },
    "pass3": {
        "method_reconstruction": [],
        "critical_review": [],
    },
    "claims_evidence_map": [],
    "figures_tables": [],
    "glossary": [],
    "limitations": [],
    "reproduction_plan": {
        "dataset": "", "baseline": "", "hardware": "",
        "steps": [], "sanity_checks": [], "success_criteria": [],
    },
    "open_questions": [],
    "final_checklist": [
        {"question": "Can I state the paper's main contribution in one sentence?", "answerable": True},
        {"question": "Can I name the three most load-bearing claims?", "answerable": True},
        {"question": "Can I point to the figure/table that grounds each main claim?", "answerable": True},
        {"question": "Can I describe the method without referring to the paper?", "answerable": True},
        {"question": "Can I name two limitations of the paper?", "answerable": True},
        {"question": "Can I describe a reproduction plan with a sanity check?", "answerable": True},
        {"question": "Can I list three open questions this paper raises?", "answerable": True},
        {"question": "Can I explain who should read this paper and why?", "answerable": True},
        {"question": "Have I marked every interpretive statement with an evidence label?", "answerable": True},
        {"question": "Have I distinguished full-text / partial / abstract-only / screenshot-only honestly?", "answerable": True},
    ],
}


REPORT_PLACEHOLDERS = {
    "stage0_intake_report.md": "# Stage 0 — Intake & Resolution\n\n_(fill after running Stage 0)_\n",
    "pass1_first_pass.md":      "# Pass 1 — First Pass\n\n_(fill after running Pass 1)_\n",
    "pass1_five_cs.md":         "# Pass 1 — Five Cs\n\n_(fill after running Pass 1)_\n",
    "pass1_reading_decision.md":"# Pass 1 — Reading Decision\n\n_(fill after running Pass 1)_\n",
    "pass2_main_ideas.md":      "# Pass 2 — Main Ideas\n\n_(fill after running Pass 2)_\n",
    "pass2_figures_tables.md":  "# Pass 2 — Figures & Tables\n\n_(fill after running Pass 2)_\n",
    "pass2_claims_evidence_map.md": "# Pass 2 — Claims → Evidence Map\n\n_(fill after running Pass 2)_\n",
    "pass2_key_references.md":  "# Pass 2 — Key References\n\n_(fill after running Pass 2)_\n",
    "pass3_reconstruction.md":  "# Pass 3 — Method Reconstruction\n\n_(fill after running Pass 3)_\n",
    "pass3_critical_review.md": "# Pass 3 — Critical Review\n\n_(fill after running Pass 3)_\n",
    "pass3_reproduction_plan.md":"# Pass 3 — Reproduction Plan\n\n_(fill after running Pass 3)_\n",
    "final_reading_report.md":  "# Final Reading Report\n\n_(fill after all three passes)_\n",
}


def write_if_missing(path: Path, content: str):
    """Write content only if the file does not already exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def copy_assets_if_missing(out: Path):
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ("style.css", "app.js"):
        src = TEMPLATE_DIR / name
        dst = assets / name
        if not dst.exists() and src.is_file():
            shutil.copyfile(src, dst)


def main(argv=None):
    p = argparse.ArgumentParser(description="Create an empty paper-reading-output/ skeleton.")
    p.add_argument("--output", required=True, help="Output directory.")
    p.add_argument("--title", default=None, help="Optional initial paper title (stored as null if absent).")
    args = p.parse_args(argv)

    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)

    # data/
    data_dir = out / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    pr = json.loads(json.dumps(PLACEHOLDER_PAPER_READING))  # deep copy
    if args.title:
        pr["paper_metadata"]["title"] = args.title
    write_if_missing(data_dir / "paper_reading.json", json.dumps(pr, indent=2, ensure_ascii=False))
    write_if_missing(data_dir / "paper_metadata.json", json.dumps(pr["paper_metadata"], indent=2, ensure_ascii=False))
    write_if_missing(data_dir / "intake_quality.json", json.dumps(pr["intake_quality"], indent=2, ensure_ascii=False))
    write_if_missing(data_dir / "paper_outline.json", "[]\n")
    write_if_missing(data_dir / "source_resolution.json", json.dumps({"steps": []}, indent=2))
    write_if_missing(data_dir / "candidate_papers.json", "[]\n")
    write_if_missing(data_dir / "claims_evidence_map.json", "[]\n")
    write_if_missing(data_dir / "figures_tables.json", "[]\n")

    # reports/
    rdir = out / "reports"
    rdir.mkdir(parents=True, exist_ok=True)
    for name, content in REPORT_PLACEHOLDERS.items():
        write_if_missing(rdir / name, content)

    # assets + index.html (page is browsable but obviously empty).
    copy_assets_if_missing(out)
    if not (out / "index.html").exists():
        tpl = (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")
        # Render with the placeholder data so the page is at least structurally valid.
        # We don't need a full render engine here — just inject a clearly empty data context.
        # Easiest: call render_page.py by writing the placeholder JSON next to it... but
        # we want this script to also work without render_page.py's dependencies being on path.
        # Instead, write a notice page that still loads the assets.
        notice = (
            '<!doctype html><html><head><meta charset="utf-8"/>'
            '<title>Paper Reading — Skeleton</title>'
            '<link rel="stylesheet" href="assets/style.css"/></head>'
            '<body><main><div class="card">'
            '<h2>Empty skeleton</h2>'
            '<p>This is an empty paper-reading-output skeleton. '
            'No reading pass has been run yet. '
            'Fill <code>data/paper_reading.json</code>, then re-run:</p>'
            '<pre>python3 skills/paper-three-pass-reader/scripts/render_page.py '
            '--input paper-reading-output/data/paper_reading.json '
            '--output paper-reading-output</pre></div></main></body></html>'
        )
        write_if_missing(out / "index.html", notice)

    # README.md
    write_if_missing(out / "README.md",
        "# Paper Reading — Skeleton\n\n"
        "This directory is an empty skeleton produced by `create_output_skeleton.py`. "
        "Fill the JSON in `data/`, the Markdown in `reports/`, then re-render `index.html` "
        "with `render_page.py`.\n\n"
        f"- **Title (placeholder):** {args.title or '(unset)'}\n"
        "- **Reading mode:** full_text (default)\n"
    )

    print(f"[ok] skeleton created at {out}")
    print(f"[ok] data files in {data_dir}")
    print(f"[ok] reports placeholders in {out / 'reports'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
