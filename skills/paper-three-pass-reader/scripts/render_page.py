#!/usr/bin/env python3
"""
render_page.py — paper-three-pass-reader (v0.2.9-alpha)

Render the interactive offline HTML reading page from a paper_reading JSON.

Usage:
    python3 render_page.py \
        --input examples/sample_paper_reading.json \
        --output paper-reading-output

Design:
- Pure stdlib (json, argparse, pathlib, shutil, html, re).
- Copies style.css + app.js verbatim into <output>/assets/.
- Generates README.md, all data/ JSONs (mirror the input), and reports/
  Markdown files (Pass 1/2/3 + final reading report).
- The output directory is self-contained: open index.html from file://.
- The template uses a small {% ... %} substitution layer — no Jinja dep.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from html import escape


HERE = Path(__file__).resolve().parent
TEMPLATE_DIR = HERE.parent / "templates"


# ---------- minimal template engine ----------------------------------------
# Supports: {{ var.path }}, {% for x in list %}...{% endfor %},
# {% if cond %}...{% endif %}, |slug filter (lowercase, alnum+underscore+hyphen),
# |length filter, |first filter. Deliberately tiny — we own the template.

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")


def _slug(v):
    s = str(v).lower()
    return _SLUG_RE.sub("-", s).strip("-") or "x"


VALID_EVIDENCE_LABELS = {
    "[Paper evidence]", "[Figure/Table evidence]", "[Author claim]",
    "[Agent inference]", "[Uncertain]", "[Needs verification]",
}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_DECISION = {"CONTINUE_FULL", "CONTINUE_PARTIAL", "STOP", "SEEK_REFERENCES_FIRST"}


def _safe_label(label):
    if label in VALID_EVIDENCE_LABELS:
        return label
    return "[Uncertain]"


def _safe_confidence(c):
    return c if c in VALID_CONFIDENCE else "low"


def _safe_decision(d):
    return d if d in VALID_DECISION else "CONTINUE_FULL"


def normalize_claim(c):
    """Defensive: accept dict or string. Return a dict with required fields."""
    if isinstance(c, dict):
        out = dict(c)
    elif isinstance(c, str):
        out = {
            "claim_id": None,
            "claim_text": c,
            "evidence_label": "[Uncertain]",
            "evidence_location": "",
            "evidence_kind": "paper_text",
            "confidence": "low",
            "notes": "(auto-promoted from string entry)",
            "needs_verification": True,
        }
    else:
        out = {
            "claim_id": None,
            "claim_text": str(c),
            "evidence_label": "[Uncertain]",
            "evidence_location": "",
            "evidence_kind": "external",
            "confidence": "low",
            "notes": "(auto-coerced from non-dict, non-string entry)",
            "needs_verification": True,
        }
    # Required keys with safe defaults.
    out.setdefault("claim_id", None)
    out["claim_id"] = out.get("claim_id") or out.get("id")
    out.setdefault("claim_text", "(missing)")
    out.setdefault("evidence_label", "[Uncertain]")
    out.setdefault("evidence_location", "")
    out.setdefault("evidence_kind", "paper_text")
    out.setdefault("confidence", "low")
    out.setdefault("notes", "")
    out.setdefault("needs_verification", True)
    out["evidence_label"] = _safe_label(out["evidence_label"])
    out["confidence"] = _safe_confidence(out["confidence"])
    return out


def normalize_figure_table(f, idx=0):
    """Defensive: accept dict or string. Return a dict with required fields."""
    if isinstance(f, dict):
        out = dict(f)
    elif isinstance(f, str):
        out = {
            "id": f"FT-{idx+1:03d}",
            "kind": "note",
            "number": "",
            "title": (f[:80] + "…") if len(f) > 80 else f,
            "explanation": f,
            "evidence_label": "[Uncertain]",
        }
    else:
        out = {
            "id": f"FT-{idx+1:03d}",
            "kind": "note",
            "number": "",
            "title": "(non-dict, non-string entry)",
            "explanation": str(f),
            "evidence_label": "[Uncertain]",
        }
    out.setdefault("id", f"FT-{idx+1:03d}")
    out.setdefault("kind", "note")
    out.setdefault("number", "")
    out.setdefault("title", "(missing title)")
    out.setdefault("explanation", "")
    if "evidence_label" in out:
        out["evidence_label"] = _safe_label(out["evidence_label"])
    else:
        out["evidence_label"] = "[Uncertain]"
    return out


def normalize_glossary(g):
    """Defensive: accept dict or string. Return a dict."""
    if isinstance(g, dict):
        out = dict(g)
    elif isinstance(g, str):
        out = {"term": g, "definition": ""}
    else:
        out = {"term": "(non-dict, non-string entry)", "definition": str(g)}
    out.setdefault("term", "(missing term)")
    out.setdefault("definition", "")
    return out


def normalize_checklist_item(c):
    """Defensive: accept dict or string. Return a dict."""
    if isinstance(c, dict):
        out = dict(c)
    elif isinstance(c, str):
        out = {"question": c, "answerable": True}
    else:
        out = {"question": str(c), "answerable": True}
    out.setdefault("question", "(missing question)")
    out.setdefault("answerable", True)
    return out


def _flatten_five_cs_item(item, default_label=""):
    """v0.2.9: a Five Cs entry may be a dict {label, value, evidence_label, note}
    OR a plain string. Normalize to a dict with all four keys so the template
    can render them individually without printing the raw dict repr."""
    if isinstance(item, dict):
        out = dict(item)
    elif isinstance(item, str):
        out = {"value": item, "label": default_label, "evidence_label": "", "note": ""}
    else:
        out = {"value": str(item), "label": default_label, "evidence_label": "", "note": ""}
    out.setdefault("label", default_label)
    out.setdefault("value", "")
    out.setdefault("evidence_label", "")
    out.setdefault("note", "")
    return out


def normalize_five_cs(five_cs):
    """v0.2.9: each Five Cs key (category, context, correctness, contributions,
    clarity) can be a dict, a list of items, or a plain string. Flatten to:
      category / context / correctness / clarity  -> single dict
      contributions                                -> list of dicts
    Also auto-derive a `label` (e.g. '类别' / '背景' / '正确性' / '贡献' / '清晰度')
    so the zh-CN UI map stays consistent."""
    if not isinstance(five_cs, dict):
        return {
            "category": _flatten_five_cs_item("", "类别"),
            "context": _flatten_five_cs_item("", "背景"),
            "correctness": _flatten_five_cs_item("", "正确性"),
            "contributions": [],
            "clarity": _flatten_five_cs_item("", "清晰度"),
        }
    out = {}
    out["category"] = _flatten_five_cs_item(five_cs.get("category", ""), "类别")
    out["context"] = _flatten_five_cs_item(five_cs.get("context", ""), "背景")
    out["correctness"] = _flatten_five_cs_item(five_cs.get("correctness", ""), "正确性")
    out["clarity"] = _flatten_five_cs_item(five_cs.get("clarity", ""), "清晰度")
    contribs = five_cs.get("contributions", []) or []
    if isinstance(contribs, str):
        contribs = [c.strip() for c in contribs.split("\n") if c.strip()] or [contribs]
    norm_contribs = []
    for i, c in enumerate(contribs, 1):
        if isinstance(c, dict):
            item = _flatten_five_cs_item(c, f"贡献 {i}")
        elif isinstance(c, str):
            item = {"value": c, "label": f"贡献 {i}", "evidence_label": "", "note": ""}
        else:
            item = {"value": str(c), "label": f"贡献 {i}", "evidence_label": "", "note": ""}
        norm_contribs.append(item)
    out["contributions"] = norm_contribs
    return out


def is_essay_talk(data):
    """v0.2.9: True if the reading is an essay / talk / methodology lecture.
    These get essay-aware UI branches (conceptual notes, 实践计划)."""
    pm = data.get("paper_metadata") or {}
    cat = (pm.get("category") or "").lower()
    cats = [str(c).lower() for c in (pm.get("categories") or [])]
    hay = {cat, *cats}
    return bool(hay & ESSAY_TALK_CATEGORIES)


def normalize_related_work(rw):
    """v0.2.9: Related Work can be a list of dicts OR a list of strings OR
    a string OR missing. Return a list of {title, authors, year, why} dicts."""
    if not rw:
        return []
    if isinstance(rw, str):
        rw = [s.strip() for s in rw.split("\n") if s.strip()]
    out = []
    for item in rw:
        if isinstance(item, dict):
            entry = {
                "title": item.get("title") or item.get("ref") or item.get("name") or "(unnamed)",
                "authors": item.get("authors") or [],
                "year": item.get("year") or "",
                "why": item.get("why") or item.get("note") or item.get("evidence_label") or "",
                "kind": item.get("kind") or "reference",
            }
        else:
            entry = {"title": str(item), "authors": [], "year": "", "why": "", "kind": "reference"}
        out.append(entry)
    return out


def normalize_reproduction_plan(rp):
    """v0.2.9: make the reproduction-plan shape consistent and essay-friendly.
    Older `actionable_steps` is auto-promoted into `steps`."""
    if not isinstance(rp, dict):
        rp = {}
    out = dict(rp)
    src_steps = out.get("steps")
    if not src_steps and out.get("actionable_steps"):
        src_steps = list(out["actionable_steps"])
    if not src_steps and isinstance(src_steps, str):
        src_steps = [s for s in src_steps.split("\n") if s.strip()]
    out["steps"] = list(src_steps) if src_steps else []
    out.setdefault("plan_7_day", [])
    out.setdefault("plan_30_day", [])
    out.setdefault("plan_90_day", [])
    out.setdefault("success_criteria", [])
    out.setdefault("risks", [])
    out.setdefault("rationale", "")
    out.setdefault("applicable", True)
    out.setdefault("kind", "experiment")
    return out


def normalize_reading(data):
    """Top-level normalization. Mutates and returns data."""
    if not isinstance(data, dict):
        return data
    data["claims_evidence_map"] = [normalize_claim(c) for c in (data.get("claims_evidence_map") or [])]
    data["figures_tables"]      = [normalize_figure_table(f, i) for i, f in enumerate(data.get("figures_tables") or [])]
    data["glossary"]            = [normalize_glossary(g) for g in (data.get("glossary") or [])]
    data["final_checklist"]     = [normalize_checklist_item(c) for c in (data.get("final_checklist") or [])]
    # v0.2.9: Five Cs flatten, Related Work, Reproduction Plan normalize.
    data["five_cs"]             = normalize_five_cs(data.get("five_cs") or {})
    data["related_work"]        = normalize_related_work(data.get("related_work") or [])
    data["reproduction_plan"]   = normalize_reproduction_plan(data.get("reproduction_plan") or {})
    # v0.2.9: essay/talk flag + generator version are exposed to the template.
    data["_is_essay_talk"]      = is_essay_talk(data)
    data["generator_version"]   = GENERATOR_VERSION
    # Defensive on pass1.decision
    if isinstance(data.get("pass1"), dict):
        data["pass1"]["decision"] = _safe_decision(data["pass1"].get("decision", "CONTINUE_FULL"))
    # Defensive on intake_quality.reading_mode (must be one of 4)
    VALID_MODES = {"full_text", "partial_text", "abstract_only", "screenshot_only"}
    for k in ("paper_metadata", "intake_quality"):
        if isinstance(data.get(k), dict):
            rm = data[k].get("reading_mode")
            if rm not in VALID_MODES:
                data[k]["reading_mode"] = "full_text"
    return data


def _get(dotted, ctx):
    """Resolve dotted path in ctx. ctx may be a dict; list items are dicts too."""
    cur = ctx
    for part in dotted.split("."):
        if isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError:
                return ""
            cur = cur[idx] if 0 <= idx < len(cur) else ""
        elif isinstance(cur, dict):
            cur = cur.get(part, "")
        else:
            return ""
        if cur is None:
            return ""
    return cur


def _apply_filters(value, filters, ctx):
    for f in filters:
        if f == "slug":
            value = _slug(value)
        elif f == "length":
            try:
                value = str(len(value) if hasattr(value, "__len__") else value)
            except Exception:
                value = "0"
        elif f == "first":
            try:
                value = value[0]
            except Exception:
                value = ""
        else:
            # unknown filter: leave value alone
            pass
    return value


_VAR_RE = re.compile(r"\{\{\s*([^\}]+?)\s*\}\}")
# v0.2.9: recognise `else` so the engine can render {% if … %}{% else %}{% endif %}
# without leaking the literal `{% else %}` into the output.
_TAG_RE = re.compile(r"\{\%\s*(for|if|else|endfor|endif|set)\b([^%]*?)\%\}", re.DOTALL)

GENERATOR_VERSION = "v0.2.9-alpha"

ESSAY_TALK_CATEGORIES = {
    "essay",
    "talk",
    "talk_essay",
    "research_advice",
    "methodology_lecture",
    "methodology",
    "scientific_career",
}


def render(template: str, ctx: dict) -> str:
    """Render a small {% ... %} / {{ ... }} template. ctx is a dict."""
    # Tokenise first. Two kinds of tokens:
    #   ('text', s) — literal text
    #   ('var', expr)  — {{ ... }} variable interpolation
    #   ('tag', kind, expr) — {% ... %} control tag (for / if / endfor / endif / set)
    pos = 0
    tokens = []
    while pos < len(template):
        # find next {% ... %} or {{ ... }}
        m_tag = _TAG_RE.search(template, pos)
        m_var = _VAR_RE.search(template, pos)
        candidates = []
        if m_tag: candidates.append(('tag', m_tag))
        if m_var: candidates.append(('var', m_var))
        if not candidates:
            tokens.append(("text", template[pos:]))
            break
        # pick the earliest
        candidates.sort(key=lambda x: x[1].start())
        kind, m = candidates[0]
        if m.start() > pos:
            tokens.append(("text", template[pos:m.start()]))
        if kind == "tag":
            tokens.append(("tag", m.group(1), m.group(2).strip()))
        else:
            tokens.append(("var", m.group(1).strip()))
        pos = m.end()

    # Parse into a tree: nodes = list of either ('text', s), ('var', expr),
    # ('if', expr, body, else_body_or_none), ('for', var, iter_expr, body).
    def parse(seq, end_kinds):
        out = []
        i = 0
        while i < len(seq):
            t = seq[i]
            if t[0] == "text":
                out.append(("text", t[1]))
                i += 1
            elif t[0] == "tag":
                kind = t[1]
                if kind in end_kinds:
                    return out, i  # stop at end
                if kind == "if":
                    expr = t[2]
                    # An if's body ends at endif OR at endfor (when the if is nested in a for),
                    # OR at the optional `else` clause.
                    body, consumed = parse(seq[i + 1:], end_kinds={"endif", "else"} | end_kinds)
                    else_body = None
                    if consumed < len(seq[i + 1:]) and seq[i + 1 + consumed][0] == "tag" and seq[i + 1 + consumed][1] == "else":
                        # Skip the `else` token, parse the else-body, expect endif.
                        eb, ec = parse(seq[i + 2 + consumed:], end_kinds={"endif"} | end_kinds)
                        else_body = eb
                        consumed = 1 + consumed + ec
                    out.append(("if", expr, body, else_body))
                    i += 1 + consumed
                elif kind == "set":
                    # {% set var = expr %}
                    parts = t[2].split("=", 1)
                    if len(parts) == 2:
                        var = parts[0].strip()
                        expr = parts[1].strip()
                        out.append(("set", var, expr))
                    i += 1
                elif kind == "for":
                    parts = t[2].split("in", 1)
                    var = parts[0].strip()
                    it = parts[1].strip()
                    # A for's body ends at endfor OR at any outer end_kinds (unused at top level).
                    body, consumed = parse(seq[i + 1:], end_kinds={"endfor"} | end_kinds)
                    out.append(("for", var, it, body))
                    i += 1 + consumed
                else:
                    i += 1
            elif t[0] == "var":
                # n is a tuple but tokens use ('var', expr) — emit keeps that shape.
                out.append(("var", t[1]))
                i += 1
            else:
                i += 1
        return out, i

    nodes, _ = parse(tokens, end_kinds=set())

    def emit(ns, scope):
        out = []
        for n in ns:
            if n[0] == "text":
                out.append(n[1])
            elif n[0] == "var":
                expr = n[1].strip()
                # split filters: name|filter|filter
                parts = [p.strip() for p in expr.split("|")]
                name = parts[0]
                filters = parts[1:]
                if name == "loop":
                    # special: {% for x in list %} exposes loop.last etc.
                    val = scope.get("__loop__", "")
                    out.append(str(_apply_filters(val, filters, scope)))
                else:
                    val = _get(name, scope)
                    val = _apply_filters(val, filters, scope)
                if isinstance(val, bool):
                    out.append("true" if val else "false")
                else:
                    out.append(str(val))
            elif n[0] == "if":
                expr = n[1].strip()
                body = n[2]
                else_body = n[3] if len(n) > 3 else None
                # Support simple 'not <path>' negation.
                negated = False
                if expr.startswith("not "):
                    negated = True
                    expr = expr[4:].strip()
                val = _get(expr, scope)
                truthy = bool(val) and val != "false"
                if negated:
                    truthy = not truthy
                if truthy:
                    out.append(emit(body, scope))
                elif else_body is not None:
                    out.append(emit(else_body, scope))
            elif n[0] == "for":
                var, it, body = n[1], n[2], n[3]
                seq = _get(it, scope)
                if not isinstance(seq, list):
                    seq = []
                for idx, item in enumerate(seq):
                    sub = dict(scope)
                    sub[var] = item
                    loop_dict = {"last": idx == len(seq) - 1, "index": idx}
                    sub["__loop__"] = loop_dict
                    sub["loop"] = loop_dict
                    out.append(emit(body, sub))
            elif n[0] == "set":
                # Local short-hand. Mutate the scope dict in place so
                # subsequent siblings in the same emit call see `var`.
                var, expr = n[1], n[2]
                scope[var] = _get(expr, scope)
        return "".join(out)

    return emit(nodes, ctx)


# ---------- main render flow -----------------------------------------------

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_assets(out: Path):
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ("style.css", "app.js"):
        src = TEMPLATE_DIR / name
        dst = assets / name
        shutil.copyfile(src, dst)


def render_index(out: Path, data: dict):
    tpl_path = TEMPLATE_DIR / "index.html"
    template = tpl_path.read_text(encoding="utf-8")
    # Inject a renderer-friendly summary of the structured
    # `source_resolution` block. We import lazily so the file is still
    # usable on bare render runs that lack the utility (e.g. historical
    # smokes). Failure to import must NEVER break rendering.
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from source_resolution_utils import summarize_source_resolution
        data = dict(data)  # do not mutate caller's dict
        data["source_resolution_summary"] = summarize_source_resolution(data)
    except Exception as _exc:  # noqa: BLE001
        data = dict(data)
        data["source_resolution_summary"] = {
            "structured": False,
            "fallback_legacy": True,
            "resolver_status": "ambiguous_clue",
            "resolver_match_type": None,
            "confidence": None,
            "confidence_numeric": None,
            "matched_paper_id": None,
            "matched_canonical_title": None,
            "matched_arxiv_id": None,
            "matched_repo": None,
            "resolver_source": None,
            "source_resolution_step": "summary_unavailable",
            "degraded": None,
            "candidate_count": 0,
            "candidates_top": [],
            "steps_count": 0,
            "hint_input": None,
        }
    html = render(template, data)
    # UI language localization (zh-CN)
    ui_lang = data.get("ui_language", "en")
    if ui_lang == "zh-CN":
        html = _localize_ui_zh_cn(html)
    write_text(out / "index.html", html)


_UI_ZH_CN_MAP = {
    "Three-Pass Reading": "三遍阅读法",
    "Paper Metadata": "论文信息",
    "Intake Status": "输入解析状态",
    "Summaries": "摘要",
    "One sentence": "一句话总结",
    "Three sentences": "三句话总结",
    "Ten sentences": "十句话总结",
    "Paper Map": "论文地图",
    "Five Cs": "Five Cs",
    "Pass 1 / 2 / 3": "第一遍 / 第二遍 / 第三遍阅读",
    "Claims → Evidence Map": "主张—证据地图",
    "Figures & Tables": "图表解读",
    "Glossary": "术语表",
    "Method Reconstruction": "方法重建",
    "Correctness & Limitations": "正确性与局限",
    "Related Work": "相关工作",
    "Practical Implications": "实践启发",
    "Reproduction Plan": "复现计划",
    "Open Questions": "开放问题",
    "Final Checklist": "最终理解检查表",
    "Contents": "目录",
    "Title": "标题",
    "Authors": "作者",
    "Year": "年份",
    "Venue": "发表 venue",
    "Source kind": "来源类型",
    "Reading mode": "阅读模式",
    "Input kind": "输入类型",
    "Confidence": "置信度",
    "Needs confirmation": "需要确认",
    "Warnings": "警告",
    "Missing fields": "缺失字段",
    "Category": "类别",
    "Context": "背景",
    "Correctness": "正确性",
    "Contributions": "贡献",
    "Clarity": "清晰度",
    "Decision": "决策",
    "Main ideas": "核心观点",
    "Method summary": "方法摘要",
    "Figure / table notes": "图表注释",
    "Key references": "关键参考文献",
    "Method reconstruction": "方法重建",
    "Critical review": "批判性审视",
    "Hidden assumptions": "隐含假设",
    "Limitations": "局限",
    "Future work": "未来工作",
    "Application notes": "应用场景",
    "Dataset": "数据集",
    "Baseline": "基线",
    "Hardware": "硬件",
    "Steps": "步骤",
    "Sanity checks": "合理性检查",
    "Success criteria": "成功标准",
    "Do I understand this paper?": "我是否理解了这篇论文？",
    "Reading mode badge": "阅读模式",
    "Evidence labels": "证据标签",
    "Progress timeline": "阅读进度",
    "Glossary chips": "术语卡片",
    "Claim filter": "主张筛选",
    "Confidence labels": "置信度标签",
    "Tabs": "标签页",
    "Accordions": "折叠面板",
    "Local-only static HTML": "纯本地静态 HTML",
    "No backend service": "不依赖后端服务",
    "Pass 1 · Bird's-eye": "第一遍 · 鸟瞰",
    "Pass 2 · Understand": "第二遍 · 理解",
    "Pass 3 · Reconstruct": "第三遍 · 重建",
    "Pass 1 — Bird's-eye view": "第一遍 — 鸟瞰视图",
    "Pass 2 — Understanding": "第二遍 — 深入理解",
    "Pass 3 — Reconstruction": "第三遍 — 重建",
    "Pass 1": "第一遍阅读",
    "Pass 2": "第二遍阅读",
    "Pass 3": "第三遍阅读",
    # v0.2.8 — structured source_resolution consumers
    "Resolver Trail": "解析路径",
    "Resolver status": "解析状态",
    "Match type": "匹配类型",
    "Matched paper": "匹配论文",
    "Matched paper id": "匹配论文 ID",
    "Matched arXiv ID": "匹配 arXiv ID",
    "Matched repo": "匹配仓库",
    "Resolver source": "解析来源",
    "Source resolution step": "解析步骤",
    "Degraded fallback": "降级回退",
    "Legacy fallback": "兼容旧格式",
    "Candidate count": "候选数量",
    "Structured trail": "结构化解析路径",
}


def _localize_ui_zh_cn(html: str) -> str:
    """Replace known English UI strings with zh-CN equivalents."""
    for en, zh in _UI_ZH_CN_MAP.items():
        html = html.replace(en, zh)
    return html


def write_data_mirrors(out: Path, data: dict):
    data_dir = out / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Whole reading as one file.
    write_text(data_dir / "paper_reading.json", json.dumps(data, indent=2, ensure_ascii=False))

    # Splits (all optional, but produce sensible defaults if missing).
    write_text(data_dir / "paper_metadata.json",
               json.dumps(data.get("paper_metadata", {}), indent=2, ensure_ascii=False))
    write_text(data_dir / "intake_quality.json",
               json.dumps(data.get("intake_quality", {}), indent=2, ensure_ascii=False))
    write_text(data_dir / "paper_outline.json",
               json.dumps(data.get("paper_outline", []), indent=2, ensure_ascii=False))
    write_text(data_dir / "claims_evidence_map.json",
               json.dumps(data.get("claims_evidence_map", []), indent=2, ensure_ascii=False))
    write_text(data_dir / "figures_tables.json",
               json.dumps(data.get("figures_tables", []), indent=2, ensure_ascii=False))
    write_text(data_dir / "glossary.json",
               json.dumps(data.get("glossary", []), indent=2, ensure_ascii=False))
    write_text(data_dir / "final_checklist.json",
               json.dumps(data.get("final_checklist", []), indent=2, ensure_ascii=False))
    write_text(data_dir / "source_resolution.json",
               json.dumps(data.get("source_resolution", {"steps": []}), indent=2, ensure_ascii=False))
    write_text(data_dir / "candidate_papers.json",
               json.dumps(data.get("candidate_papers", []), indent=2, ensure_ascii=False))


def write_reports(out: Path, data: dict):
    r = out / "reports"
    r.mkdir(parents=True, exist_ok=True)

    pm = data.get("paper_metadata", {})
    title = pm.get("title", "Untitled")
    year = pm.get("year", "")
    venue = pm.get("venue", "")
    authors = pm.get("authors", [])
    mode = pm.get("reading_mode", "full_text")

    def fmt_authors(a):
        return ", ".join(a) if isinstance(a, list) else str(a)

    # Stage 0
    write_text(r / "stage0_intake_report.md",
        f"""# Stage 0 — Intake & Resolution

- **Title:** {title}
- **Authors:** {fmt_authors(authors)}
- **Year:** {year}
- **Venue:** {venue}
- **Source kind:** {pm.get('source_kind', '')}
- **Reading mode:** {mode}

## Intake quality

- **Input kind:** {data.get('intake_quality', {}).get('input_kind', '')}
- **Confidence:** {data.get('intake_quality', {}).get('confidence', '')}
- **Needs confirmation:** {data.get('intake_quality', {}).get('needs_confirmation', False)}

## Warnings

""" + "\n".join(f"- {w}" for w in data.get('intake_quality', {}).get('warnings', []) or ["(none)"]) + "\n")

    # Pass 1
    p1 = data.get("pass1", {})
    write_text(r / "pass1_first_pass.md",
        f"""# Pass 1 — First Pass

## Bird's-eye notes

{p1.get('bird_eye_notes', '')}

## Decision

**{p1.get('decision', 'CONTINUE_FULL')}** — {p1.get('decision_rationale', '')}
""")
    five_cs = data.get("five_cs", {})
    # v0.2.9: each Five Cs entry may be a string OR a dict (post-normalize).
    def _fc_str(x, default=""):
        if isinstance(x, dict):
            return x.get("value", "") or default
        return str(x) if x is not None else default
    def _fc_list(items):
        out = []
        for x in (items or []):
            if isinstance(x, dict):
                v = x.get("value") or ""
                if v: out.append(v)
            elif x is not None:
                out.append(str(x))
        return out
    write_text(r / "pass1_five_cs.md",
        f"""# Pass 1 — Five Cs

|| C | Answer |
||---|---|
|| **Category** | {_fc_str(five_cs.get('category'))} |
|| **Context** | {_fc_str(five_cs.get('context'))} |
|| **Correctness** | {_fc_str(five_cs.get('correctness'))} |
|| **Contributions** | {chr(10).join('- ' + c for c in _fc_list(five_cs.get('contributions')))} |
|| **Clarity** | {_fc_str(five_cs.get('clarity'))} |
""")
    write_text(r / "pass1_reading_decision.md",
        f"""# Pass 1 — Reading Decision

**Decision:** {p1.get('decision', 'CONTINUE_FULL')}

**Rationale:** {p1.get('decision_rationale', '')}
""")

    # Pass 2
    p2 = data.get("pass2", {})
    write_text(r / "pass2_main_ideas.md",
        "# Pass 2 — Main Ideas\n\n" +
        "\n".join(f"{i+1}. {m}" for i, m in enumerate(p2.get('main_ideas', []) or [])) + "\n")
    write_text(r / "pass2_figures_tables.md",
        "# Pass 2 — Figures & Tables\n\n" +
        "\n".join(
            (lambda f: f"### {f.get('kind','figure').title()} {f.get('number','')} — {f.get('title','')}\n\n{f.get('explanation','')}\n")(f if isinstance(f, dict) else {"kind":"note","number":"","title":(str(f)[:80] if f else ''),"explanation":str(f)})
            for f in (data.get('figures_tables') or [])) + "\n")
    write_text(r / "pass2_claims_evidence_map.md",
        "# Pass 2 — Claims → Evidence Map\n\n" +
        "\n".join(
            (lambda c: f"- **{c.get('claim_id','')}** — {c.get('claim_text','')}  \n  Evidence: {c.get('evidence_label','[Uncertain]')} ({c.get('evidence_location','')})  \n  Confidence: {c.get('confidence','low')}")(c if isinstance(c, dict) else {"claim_id":None,"claim_text":str(c),"evidence_label":"[Uncertain]","evidence_location":"","confidence":"low"})
            for c in (data.get('claims_evidence_map') or [])) + "\n")
    refs = p2.get('key_references', []) or []
    write_text(r / "pass2_key_references.md",
        "# Pass 2 — Key References\n\n" +
        "\n".join(
            (lambda d: f"- **{d.get('title','')}** — {', '.join(d.get('authors', []) or [])} ({d.get('year','')}). _{d.get('why','')}_")
            (r if isinstance(r, dict) else {"title": str(r), "authors": [], "year": "", "why": ""})
            for r in refs
        ) + "\n")

    # Pass 3
    p3 = data.get("pass3", {})
    write_text(r / "pass3_reconstruction.md",
        "# Pass 3 — Method Reconstruction\n\n" +
        "\n".join(f"{i+1}. {s}" for i, s in enumerate(p3.get('method_reconstruction', []) or [])) + "\n")
    write_text(r / "pass3_critical_review.md",
        "# Pass 3 — Critical Review\n\n" +
        "\n".join(f"- {c}" for c in p3.get('critical_review', []) or []) + "\n")
    rp = data.get("reproduction_plan", {})
    write_text(r / "pass3_reproduction_plan.md",
        "# Pass 3 — Reproduction Plan\n\n"
        + (f"- **Dataset:** {rp.get('dataset','')}\n" if rp.get('dataset') else "")
        + (f"- **Baseline:** {rp.get('baseline','')}\n" if rp.get('baseline') else "")
        + (f"- **Hardware:** {rp.get('hardware','')}\n" if rp.get('hardware') else "")
        + "\n## Steps\n\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(rp.get('steps', []) or [])) + "\n"
        + ("\n## Sanity checks\n\n" + "\n".join(f"- {s}" for s in rp.get('sanity_checks', []) or []) + "\n" if rp.get('sanity_checks') else "")
        + ("\n## Success criteria\n\n" + "\n".join(f"- {s}" for s in rp.get('success_criteria', []) or []) + "\n" if rp.get('success_criteria') else "")
    )

    # Final reading report
    sums = data.get("summaries", {})
    one = sums.get("one_sentence", "")
    three = sums.get("three_sentence", [])
    contribs = five_cs.get("contributions", []) or []
    contrib_strs = [
        c.get("value") if isinstance(c, dict) else str(c)
        for c in contribs
        if (c.get("value") if isinstance(c, dict) else c) is not None
    ]
    limitations = data.get("limitations", []) or []
    open_q = data.get("open_questions", []) or []
    write_text(r / "final_reading_report.md",
        f"""# Final Reading Report — {title}

## 1. What is this paper about?

{one}

## 2. Is it worth reading deeper?

**{p1.get('decision', 'CONTINUE_FULL')}** — {p1.get('decision_rationale', '')}

## 3. Main contributions

""" + "\n".join(f"- {c}" for c in contrib_strs) + f"""

## 4. Where is the evidence strongest / weakest?

See `pass2_claims_evidence_map.md`. Filter by confidence in the HTML page.

## 5. What would I change if I were the author?

""" + "\n".join(f"- {c}" for c in (p3.get('critical_review', []) or [])) + f"""

## 6. Can I reproduce it?

See `pass3_reproduction_plan.md`.

## 7. What remains open?

""" + "\n".join(f"- {q}" for q in open_q) + "\n")


def write_readme(out: Path, data: dict):
    pm = data.get("paper_metadata", {})
    title = pm.get("title", "Untitled")
    authors = pm.get("authors", [])
    year = pm.get("year", "")
    mode = pm.get("reading_mode", "full_text")

    write_text(out / "README.md",
        f"""# {title} — Three-Pass Reading

- **Authors:** {', '.join(authors) if isinstance(authors, list) else authors}
- **Year:** {year}
- **Reading mode:** {mode}

## What's here

- `index.html` — interactive reading page (open in any browser).
- `assets/` — `style.css` and `app.js` (offline, no CDN).
- `data/` — all the JSON behind the page.
- `reports/` — Markdown reports per stage.

Generated by **paper-three-pass-reader {GENERATOR_VERSION}** · MIT.
""")


# ---------- entry ----------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description="Render an offline three-pass reading page from JSON.")
    p.add_argument("--input", required=True, help="Path to paper_reading JSON.")
    p.add_argument("--output", required=True, help="Output directory (will be created if missing).")
    args = p.parse_args(argv)

    inp = Path(args.input).resolve()
    out = Path(args.output).resolve()

    if not inp.is_file():
        print(f"[error] input not found: {inp}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    try:
        data = load_json(inp)
    except json.JSONDecodeError as e:
        print(f"[error] input is not valid JSON: {e}", file=sys.stderr)
        return 2

    # Defensive normalization — must happen BEFORE any template/render step.
    normalize_reading(data)

    copy_assets(out)
    write_data_mirrors(out, data)
    write_reports(out, data)
    render_index(out, data)
    write_readme(out, data)

    print(f"[ok] rendered -> {out / 'index.html'}")
    print(f"[ok] data     -> {out / 'data'}")
    print(f"[ok] reports  -> {out / 'reports'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
