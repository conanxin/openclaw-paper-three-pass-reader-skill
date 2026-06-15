#!/usr/bin/env python3
"""
audit_published_pages.py — published-pages regression audit for paper-three-pass-reader
(v0.2.12-alpha: page-type classification + root-index exemption)

Reads published_pages.json (live URL or local file), fetches every page, and checks
for regressions against the v0.2.9+ renderer/template expectations:

  A. HTTP / fetch                (error if non-200 or empty)
  B. Template tag leak           (error if any {% %} / {{ }} / {% else %} / {# #} leak)
  C. Old footer / old renderer   (error if v0.1.0-alpha / raw dict repr / etc.)
  D. zh-CN UI markers            (warning if a -cn / Chinese page is missing 5+ zh markers)
  E. Resolver trail              (warning if missing in v0.2.8+ page)
  F. Claims / Evidence           (warning if claims section missing or all claim IDs empty)
  G. Glossary                    (warning if section missing for non-screenshot-only)
  H. Essay / talk rendering      (warning if essay page missing 实践计划 / 结构说明 / 相关脉络)
  I. Page-type classification    (site_index / paper_page / manifest / unknown)
  J. Site-index / manifest-only  (warning if site_root has no manifest links or empty)

Page-type rules (v0.2.12-alpha):

  * site_index   — the site root itself (`<site_root>/` or `<site_root>`). The page is
                   a manifest of all published paper pages. It is NOT a paper page,
                   so paper-level checks (Resolver Trail, Claims, Glossary,
                   no_visible_claim_id, glossary_no_explicit_definition,
                   essay_page_missing_practice_plan, weak_zh_cn_ui) are skipped.
                   Severe checks (template_leak, raw_dict, old_footer) still apply.
                   Index-specific checks are added: HTTP 200, non-empty, has title,
                   has at least one published-page link, and link count roughly
                   matches the manifest.
  * paper_page   — a normal paper reading page produced by render_page.py. All
                   paper-level checks apply.
  * manifest     — the published_pages.json manifest itself (when --include-manifest
                   is set). Manifest-only checks apply: JSON valid, pages list present,
                   every entry has title+slug+path, no duplicate slugs / urls.
  * unknown      — fallback. Treated as paper_page for safety.

stdlib-only. No external deps.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html as _html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

ZH_CN_MARKERS = [
    "输入解析状态",
    "摘要",
    "论文地图",
    "主张",
    "证据",
    "最终理解检查表",
]

ESSAY_SLUG_HINTS = (
    "you-and-your-research",
    "essay",
    "talk",
    "lecture",
    "keynote",
)

ESSAY_REQUIRED_MARKERS = [
    "实践计划",   # Practical Plan
    "结构说明",   # Figures & Tables -> 结构说明 in essay mode
    "相关脉络",   # Related Work -> 相关脉络 in essay mode
]

EVIDENCE_LABELS = [
    "[Paper evidence]",
    "[Figure/Table evidence]",
    "[Author claim]",
    "[Agent inference]",
    "[Uncertain]",
    "[Needs verification]",
]

# Page types
PAGE_TYPE_SITE_INDEX = "site_index"
PAGE_TYPE_PAPER_PAGE = "paper_page"
PAGE_TYPE_MANIFEST = "manifest"
PAGE_TYPE_UNKNOWN = "unknown"
ALL_PAGE_TYPES = [PAGE_TYPE_SITE_INDEX, PAGE_TYPE_PAPER_PAGE, PAGE_TYPE_MANIFEST, PAGE_TYPE_UNKNOWN]

# Paper-level checks that site_index is exempt from (codes).
PAPER_LEVEL_CODES = {
    "missing_resolver_trail",
    "missing_claims_section",
    "missing_glossary",
    "no_visible_claim_id",
    "no_evidence_label",
    "glossary_no_explicit_definition",
    "essay_missing_markers",
    "zh_cn_markers_weak",
    "empty_claim_id",
}

# Severe checks that still apply to site_index (templates leaks / footers).
SEVERE_CODES = {"template_leak", "raw_dict", "old_footer"}

# ----------------------------------------------------------------------------
# HTTP helpers
# ----------------------------------------------------------------------------

def _http_get(url: str, timeout: float = 20.0) -> Tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "paper-three-pass-reader-audit/0.1 (+https://conanxin.github.io/paper-reading-pages/)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            raw = resp.read()
            try:
                body = raw.decode("utf-8", errors="replace")
            except Exception:
                body = raw.decode("latin-1", errors="replace")
            return int(status), body
    except urllib.error.HTTPError as e:
        try:
            raw = e.read()
            body = raw.decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return int(e.code), body
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, ""


def _extract_title(body: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


def _normalize_url_for_compare(u: str) -> str:
    """Lowercase + strip trailing slashes + drop fragment for slug-like comparison."""
    if not u:
        return ""
    parsed = urllib.parse.urlparse(u)
    path = parsed.path.rstrip("/")
    return path.lower()


# ----------------------------------------------------------------------------
# Page-type classification
# ----------------------------------------------------------------------------

def _classify_page_type(
    url: str,
    slug: str,
    title_hint: str,
    body: str,
    site_root: str,
    is_root_requested: bool = False,
) -> str:
    """Classify a page entry as site_index / paper_page / manifest / unknown.

    Site-index detection is conservative: it requires either (a) the caller
    marked this URL as the requested site root, or (b) the URL path is empty /
    "/" AND the body shows manifest-style content. Manifest detection is via
    JSON content shape (returns manifest when body is a valid published_pages.json).
    """
    parsed = urllib.parse.urlparse(url)
    site_root_norm = site_root.rstrip("/")
    path = (parsed.path or "").rstrip("/")
    body_low = body or ""

    # Manifest: JSON published_pages.json
    if body_low.lstrip().startswith("{") and '"pages"' in body_low and '"slug"' in body_low:
        try:
            obj = json.loads(body_low)
            if isinstance(obj, dict) and isinstance(obj.get("pages"), list):
                return PAGE_TYPE_MANIFEST
        except Exception:
            pass

    # Site-index: explicit root flag, or URL is the bare site_root.
    if is_root_requested:
        return PAGE_TYPE_SITE_INDEX
    if url.rstrip("/") == site_root_norm and path == "":
        return PAGE_TYPE_SITE_INDEX
    # Strong HTML evidence (for live audits that follow manifest-only).
    if path == "":
        manifest_signals = (
            "published_pages.json" in body_low
            or "Paper Reading Pages" in body_low
            or "Published pages" in body_low
        )
        links_to_slugs = bool(re.search(r'<a href="[^"]+/[^"]+/">', body_low))
        if manifest_signals or links_to_slugs:
            return PAGE_TYPE_SITE_INDEX

    return PAGE_TYPE_PAPER_PAGE


# ----------------------------------------------------------------------------
# Issue construction
# ----------------------------------------------------------------------------

def _mk_issue(severity: str, code: str, message: str, recommendation: str = "") -> Dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "recommendation": recommendation,
    }


# ----------------------------------------------------------------------------
# Check functions (paper-level)
# ----------------------------------------------------------------------------

def _check_template_leak(body: str) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    leaks = []
    for needle, label in [
        ("{% else %}", "{% else %}"),
        ("{%", "{%"),
        ("%}", "%}"),
        ("{{", "{{"),
        ("}}", "}}"),
        ("{#", "{#"),
        ("#}", "#}"),
        ("No key references recorded", "No key references recorded"),
    ]:
        if needle in body:
            leaks.append(label)
    if leaks:
        issues.append(_mk_issue(
            "error",
            "template_leak",
            "渲染页包含未闭合的 template tag 或占位符: " + ", ".join(sorted(set(leaks))),
            "重新用 v0.2.9+ 渲染器 (render_page.py) 渲染该页面,确认 mini-template 的 {% else %} 分支已处理。",
        ))
    return issues


def _check_old_footer(body: str) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    for needle in [
        "v0.1.0-alpha",
        "Generated by paper-three-pass-reader v0.1.0-alpha",
        "Generated by paper-three-reader v0.1.0-alpha",
    ]:
        if needle in body:
            issues.append(_mk_issue(
                "error",
                "old_footer",
                f"页面仍显示旧版本 footer: '{needle}'",
                "重新渲染该页面以使用 v0.2.9+ 的 generator_version footer。",
            ))
            break
    return issues


def _check_raw_dict(body: str) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    if re.search(r"\{'label'\s*:", body):
        issues.append(_mk_issue(
            "error",
            "raw_dict",
            "页面含 raw Python dict repr (例如 {'label': ...})。",
            "重新用 v0.2.9+ renderer (render_page.py) 渲染;Five Cs 现在被 normalize_five_cs 展平为 {label,value,evidence_label,note}。",
        ))
    return issues


def _check_resolver_trail(body: str, url: str) -> List[Dict[str, str]]:
    has_resolver_en = ("Resolver Trail" in body) or ("Resolver status" in body) or ("Confidence" in body and "Matched" in body)
    has_resolver_zh = ("解析状态" in body) or ("置信度" in body) or ("匹配 arXiv ID" in body) or ("匹配论文" in body)
    if not (has_resolver_en or has_resolver_zh):
        return [_mk_issue(
            "warning",
            "missing_resolver_trail",
            "页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。",
            "重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。",
        )]
    return []


def _check_claims(body: str) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    if not (("Claims" in body) or ("主张" in body) or ("Claim" in body) or ("证据" in body) or ("Evidence" in body)):
        issues.append(_mk_issue(
            "warning",
            "missing_claims_section",
            "页面缺少 Claims / Evidence 区段。",
            "确认 paper_reading.json 含 claims_evidence_map,重新渲染。",
        ))
        return issues
    # Detect empty claim IDs
    if re.search(r"<code>\s*</code>", body):
        issues.append(_mk_issue(
            "warning",
            "empty_claim_id",
            "页面包含 <code></code> 空 claim ID 单元格。",
            "重新渲染;v0.2.9+ normalize_claim 会从 id 派生 claim_id。",
        ))
    # Detect at least one claim ID
    if not re.search(r">C\d{2,}<", body):
        issues.append(_mk_issue(
            "info",
            "no_visible_claim_id",
            "页面没有可见的 claim ID (例如 C01/C02)。",
            "如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。",
        ))
    # Detect at least one evidence label
    if not any(lbl in body for lbl in EVIDENCE_LABELS):
        issues.append(_mk_issue(
            "info",
            "no_evidence_label",
            "页面未出现任何 evidence label。",
            "如果页面是弱输入,可忽略;否则为每个 claim/figure 字段加 [Paper evidence] / [Author claim] 等标签。",
        ))
    return issues


def _check_glossary(body: str) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    has_glossary = ("Glossary" in body) or ("术语" in body) or ("关键术语" in body)
    if not has_glossary:
        issues.append(_mk_issue(
            "warning",
            "missing_glossary",
            "页面缺少 Glossary / 关键术语 区段。",
            "如果页面是 screenshot_only,可忽略;否则补 paper_reading.json 的 glossary 字段并重新渲染。",
        ))
        return issues
    # v0.2.9+ exposes explicit chip-body with definition; warn if chip without def
    if re.search(r'class="chip"', body) and not re.search(r'class="chip-body"', body) and "v0.2.9" not in body:
        # weak check — old glossary chips used tooltips only
        issues.append(_mk_issue(
            "info",
            "glossary_no_explicit_definition",
            "Glossary 仍是 v0.2.8 之前的 chip 形态(无显式定义块)。",
            "v0.2.9+ 渲染器会输出 chip-body 块,重新渲染即可。",
        ))
    return issues


def _check_essay_talk(body: str, slug: str, title: str, url: str) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    s = (slug + " " + title + " " + url).lower()
    if not any(h in s for h in ESSAY_SLUG_HINTS):
        return issues
    # Essay-mode page should have 实践计划 / 结构说明 / 相关脉络
    missing = [m for m in ESSAY_REQUIRED_MARKERS if m not in body]
    if missing:
        issues.append(_mk_issue(
            "warning",
            "essay_missing_markers",
            f"essay / talk 页面缺少 essay-mode 标记: {', '.join(missing)}。可能是 v0.2.9 之前渲染的旧页面。",
            "重新用 v0.2.9+ renderer 渲染 essay 页面;Reproduction Plan 会切换为「实践计划」,Figures & Tables 会切换为「结构说明」,Related Work 会切换为「相关脉络」。",
        ))
    return issues


def _check_zh_cn_markers(body: str, slug: str, title: str) -> List[Dict[str, str]]:
    s = (slug + " " + title).lower()
    is_zh_page = (
        "-cn" in s
        or "cn-" in s
        or "human-inspired-memory-cn" in s
        or "second-me-human-inspired-memory" in s
        or re.search(r"[\u4e00-\u9fff]", title or "")
    )
    if not is_zh_page:
        return []
    present = [m for m in ZH_CN_MARKERS if m in body]
    if len(present) < 5:
        return [_mk_issue(
            "warning",
            "zh_cn_markers_weak",
            f"zh-CN 页面只检测到 {len(present)}/{len(ZH_CN_MARKERS)} 个中文 UI marker: {', '.join(present) or '(none)'}。",
            "重新用 v0.2.9+ renderer 渲染,确认 ui_language=zh-CN 且模板 zh-CN 文本未遗漏。",
        )]
    return []


# ----------------------------------------------------------------------------
# Site-index specific checks
# ----------------------------------------------------------------------------

def _check_site_index(body: str, url: str, manifest_pages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Index-specific checks (run only when page_type == site_index).

    Returns a list of issues. By convention, the site index should:
      - have a non-empty body (already checked upstream)
      - have a <title>
      - contain at least one published-page link
      - reference published_pages.json (or have a corresponding manifest loaded)
      - link count should roughly match the manifest
    """
    issues: List[Dict[str, str]] = []

    # Title
    title = _extract_title(body)
    if not title:
        issues.append(_mk_issue(
            "warning",
            "index_missing_title",
            "site_index 缺少 <title>。",
            "publish_output_to_github.sh 会写入 <title>Paper Reading Pages — index</title>;检查 publisher 模板。",
        ))

    # At least one published-page link
    page_links = re.findall(r'<a\s+href="([^"#]+)"[^>]*>([^<]*)</a>', body)
    slugs_from_links: List[str] = []
    for href, _ in page_links:
        # Only treat as a paper link if it has the path form /<slug>/...
        m = re.search(r"/([^/]+)/?$", urllib.parse.urlparse(href).path.rstrip("/"))
        if m:
            slugs_from_links.append(m.group(1))

    if not slugs_from_links:
        issues.append(_mk_issue(
            "warning",
            "index_no_page_links",
            "site_index 没有指向任何已发布页面(/<slug>/ 形式)的链接。",
            "确认 publisher 用 multi-page mode + manifest 列表正确注入。",
        ))
    else:
        # Compare to manifest
        manifest_slugs = {str(p.get("slug", "")).strip() for p in manifest_pages if p.get("slug")}
        manifest_slugs.discard("")
        if manifest_slugs:
            only_in_index = set(slugs_from_links) - manifest_slugs
            only_in_manifest = manifest_slugs - set(slugs_from_links)
            # Only emit a warning when the delta is large (>50% of manifest missing).
            missing_ratio = (len(only_in_manifest) / len(manifest_slugs)) if manifest_slugs else 0
            if missing_ratio > 0.5:
                issues.append(_mk_issue(
                    "warning",
                    "index_links_mismatch",
                    f"site_index 仅链接 {len(set(slugs_from_links))} 个 slug,manifest 有 {len(manifest_slugs)} 个;超过 50% manifest 条目在 index 缺失。",
                    "确认 publish_output_to_github.sh 的 index 重新生成逻辑使用了最新 manifest。",
                ))

    # Reference to published_pages.json (or the manifest URL)
    if "published_pages.json" not in body:
        issues.append(_mk_issue(
            "info",
            "index_no_manifest_link",
            "site_index 页面未引用 published_pages.json (audit 仍可工作,但用户可能无法直接跳转到 manifest)。",
            "publisher 可选地在 <head> 或 <footer> 加 <link rel=alternate> 到 manifest URL。",
        ))

    return issues


def _check_manifest_pages(manifest_pages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Manifest-specific checks. Run once per audit (top-level) and recorded as
    a synthetic page entry."""
    issues: List[Dict[str, str]] = []
    if not isinstance(manifest_pages, list):
        return [_mk_issue(
            "error",
            "manifest_pages_not_list",
            "published_pages.json.pages 不是 list。",
            "确认 publisher 用 schema_version 0.1 写入 manifest。",
        )]
    if not manifest_pages:
        issues.append(_mk_issue(
            "warning",
            "manifest_empty",
            "published_pages.json.pages 为空 — 没有任何已发布页面。",
            "publish_output_to_github.sh --site-path 会向 manifest 添加条目;确认至少有一页发布。",
        ))
        return issues

    # Each entry must have slug + title + path
    missing_fields = []
    slugs_seen: Dict[str, int] = {}
    paths_seen: Dict[str, int] = {}
    for i, p in enumerate(manifest_pages):
        if not isinstance(p, dict):
            missing_fields.append(f"#{i}: not a dict")
            continue
        for k in ("slug", "title", "path"):
            if not p.get(k):
                missing_fields.append(f"#{i}: missing {k}")
        s = (p.get("slug") or "").strip()
        path = (p.get("path") or "").strip()
        if s:
            slugs_seen[s] = slugs_seen.get(s, 0) + 1
        if path:
            paths_seen[_normalize_url_for_compare(path)] = paths_seen.get(_normalize_url_for_compare(path), 0) + 1
    if missing_fields:
        issues.append(_mk_issue(
            "warning",
            "manifest_incomplete_entries",
            f"manifest 存在不完整条目: {', '.join(missing_fields[:5])}{' ...' if len(missing_fields) > 5 else ''}。",
            "publish_output_to_github.sh 写入每个 entry 时必须含 slug + title + path。",
        ))

    dup_slugs = [s for s, n in slugs_seen.items() if n > 1]
    if dup_slugs:
        issues.append(_mk_issue(
            "warning",
            "manifest_duplicate_slugs",
            f"manifest 含重复 slug: {', '.join(sorted(dup_slugs))}。",
            "publisher 不应写入重复 slug;检查 site-path 冲突。",
        ))
    dup_paths = [p for p, n in paths_seen.items() if n > 1]
    if dup_paths:
        issues.append(_mk_issue(
            "warning",
            "manifest_duplicate_paths",
            f"manifest 含重复 path: {', '.join(sorted(dup_paths))}。",
            "publisher 不应写入重复 path;检查 site-path 冲突。",
        ))
    return issues


# ----------------------------------------------------------------------------
# Manifest handling
# ----------------------------------------------------------------------------

def _load_manifest(args) -> Tuple[str, List[Dict[str, Any]]]:
    if args.manifest_url:
        status, body = _http_get(args.manifest_url, timeout=args.timeout)
        if status != 200 or not body:
            raise SystemExit(f"FAIL: cannot fetch manifest at {args.manifest_url} (HTTP {status})")
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            raise SystemExit(f"FAIL: manifest JSON parse error: {e}")
        return args.manifest_url, data.get("pages", [])
    if args.manifest_file:
        with open(args.manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return f"file://{os.path.abspath(args.manifest_file)}", data.get("pages", [])
    raise SystemExit("FAIL: must supply --manifest-url or --manifest-file")


# ----------------------------------------------------------------------------
# Page audit
# ----------------------------------------------------------------------------

def _audit_page(
    url: str,
    title_hint: str,
    slug: str,
    args,
    site_root: str,
    manifest_pages: List[Dict[str, Any]],
    page_type_override: Optional[str] = None,
) -> Dict[str, Any]:
    page: Dict[str, Any] = {
        "url": url,
        "slug": slug,
        "title": title_hint,
        "http_status": 0,
        "fetched_bytes": 0,
        "issues": [],
        "page_type": PAGE_TYPE_UNKNOWN,
    }
    status, body = _http_get(url, timeout=args.timeout)
    page["http_status"] = status
    page["fetched_bytes"] = len(body)
    if status != 200:
        page["issues"].append(_mk_issue(
            "error", "http_error",
            f"HTTP 状态非 200 (got {status})。",
            "检查 GitHub Pages 部署状态,确认页面在 gh-pages 分支存在。",
        ))
        page["status"] = "FAIL"
        return page
    if not body or len(body) < 200:
        page["issues"].append(_mk_issue(
            "error", "empty_body",
            f"页面内容为空或过短 ({len(body)} bytes)。",
            "检查生成器输出与发布流程。",
        ))
        page["status"] = "FAIL"
        return page

    actual_title = _extract_title(body)
    if actual_title:
        page["title"] = actual_title

    # Classify the page first
    is_root = bool(getattr(args, "_root_url", None) and url == args._root_url)
    if page_type_override:
        page["page_type"] = page_type_override
    else:
        page["page_type"] = _classify_page_type(
            url=url,
            slug=slug,
            title_hint=page["title"],
            body=body,
            site_root=site_root,
            is_root_requested=is_root,
        )

    # Severe checks apply to all page types
    issues: List[Dict[str, str]] = []
    issues.extend(_check_template_leak(body))
    issues.extend(_check_old_footer(body))
    issues.extend(_check_raw_dict(body))

    if page["page_type"] == PAGE_TYPE_SITE_INDEX:
        # Index-specific checks
        issues.extend(_check_site_index(body, url, manifest_pages))
        # Note: paper-level checks are skipped by design for site_index.
    elif page["page_type"] == PAGE_TYPE_MANIFEST:
        # Manifest: only structural validity is reported (already validated upstream);
        # add a synthetic info entry confirming manifest shape.
        try:
            obj = json.loads(body)
            if isinstance(obj, dict) and isinstance(obj.get("pages"), list):
                issues.append(_mk_issue(
                    "info",
                    "manifest_ok",
                    f"published_pages.json 合法,含 {len(obj.get('pages', []))} 条 entry。",
                ))
        except Exception:
            issues.append(_mk_issue(
                "error", "manifest_invalid_json",
                "manifest 抓取后 JSON parse 失败。",
                "确认 published_pages.json 写入时无 BOM / trailing whitespace。",
            ))
    else:
        # paper_page / unknown → run full paper-level checks
        issues.extend(_check_resolver_trail(body, url))
        issues.extend(_check_claims(body))
        issues.extend(_check_glossary(body))
        issues.extend(_check_essay_talk(body, slug, page["title"], url))
        issues.extend(_check_zh_cn_markers(body, slug, page["title"]))

    page["issues"] = issues

    if any(i["severity"] == "error" for i in issues):
        page["status"] = "FAIL"
    elif any(i["severity"] == "warning" for i in issues):
        page["status"] = "WARN"
    else:
        page["status"] = "PASS"
    return page


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

def _overall_status(pages: List[Dict[str, Any]], manifest_ok: bool) -> str:
    if not manifest_ok:
        return "FAIL"
    if any(p.get("status") == "FAIL" for p in pages):
        return "FAIL"
    if any(p.get("status") == "WARN" for p in pages):
        return "WARN"
    return "PASS"


def _issue_counts(pages: List[Dict[str, Any]]) -> Dict[str, int]:
    out = {"error": 0, "warning": 0, "info": 0}
    for p in pages:
        for i in p.get("issues", []):
            sev = i.get("severity", "info")
            out[sev] = out.get(sev, 0) + 1
    return out


def _page_type_counts(pages: List[Dict[str, Any]]) -> Dict[str, int]:
    out = {t: 0 for t in ALL_PAGE_TYPES}
    for p in pages:
        t = p.get("page_type", PAGE_TYPE_UNKNOWN)
        out[t] = out.get(t, 0) + 1
    return out


def _build_recommendations(
    pages: List[Dict[str, Any]],
    page_type_counts: Dict[str, int],
) -> List[str]:
    recs: List[str] = []
    codes_seen: Dict[str, int] = {}
    for p in pages:
        # Only count issues from paper_page / manifest for paper-level codes;
        # site_index issues use index-level codes and should not pollute the
        # paper-level recommendation list.
        if p.get("page_type") == PAGE_TYPE_SITE_INDEX:
            continue
        for i in p.get("issues", []):
            codes_seen[i["code"]] = codes_seen.get(i["code"], 0) + 1
    if codes_seen.get("template_leak"):
        recs.append(f"{codes_seen['template_leak']} 页面仍泄漏 template tag — 优先 batch re-render + republish。")
    if codes_seen.get("raw_dict"):
        recs.append(f"{codes_seen['raw_dict']} 页面仍输出 raw Python dict — 重新渲染使 normalize_five_cs 生效。")
    if codes_seen.get("old_footer"):
        recs.append(f"{codes_seen['old_footer']} 页面 footer 仍写 v0.1.0-alpha — 重新渲染以使用 generator_version。")
    if codes_seen.get("http_error"):
        recs.append(f"{codes_seen['http_error']} 页面 HTTP 非 200 — 检查 gh-pages 部署状态。")
    if codes_seen.get("missing_resolver_trail"):
        recs.append(f"{codes_seen['missing_resolver_trail']} 论文页缺 Resolver Trail — v0.2.8 之前渲染,建议在 v0.2.11+ 分批重渲染。")
    if codes_seen.get("zh_cn_markers_weak"):
        recs.append(f"{codes_seen['zh_cn_markers_weak']} zh-CN 论文页中文 marker 不足 — 重新渲染并确认 ui_language=zh-CN。")
    if codes_seen.get("essay_missing_markers"):
        recs.append(f"{codes_seen['essay_missing_markers']} essay 论文页缺 essay-mode 标记 — 重新渲染以使用 is_essay_talk 切换。")
    if codes_seen.get("missing_glossary"):
        recs.append(f"{codes_seen['missing_glossary']} 论文页缺 Glossary — 检查 paper_reading.json 的 glossary 字段。")

    # site_index-specific
    site_index_pages = [p for p in pages if p.get("page_type") == PAGE_TYPE_SITE_INDEX]
    if site_index_pages:
        site_errors = [i for p in site_index_pages for i in p.get("issues", []) if i["severity"] == "error"]
        site_warnings = [i for p in site_index_pages for i in p.get("issues", []) if i["severity"] == "warning"]
        if not site_errors and not site_warnings:
            recs.append("Root index is treated as site_index and exempted from paper-page checks (missing_resolver_trail / missing_claims_section / missing_glossary skipped by design).")
        else:
            for p in site_index_pages:
                for i in p.get("issues", []):
                    if i["severity"] in ("error", "warning"):
                        recs.append(f"site_index 触发严重/警告: {i['code']} — {i['message']}")
    if page_type_counts.get(PAGE_TYPE_UNKNOWN, 0) > 0:
        recs.append(f"{page_type_counts[PAGE_TYPE_UNKNOWN]} 页面 page_type=unknown — 检查 _classify_page_type 规则是否覆盖。")
    if not recs:
        recs.append("所有页面通过审计;无需立即行动。")
    return recs


def _build_json_report(
    args,
    manifest_url: str,
    pages: List[Dict[str, Any]],
    manifest_ok: bool,
    page_type_counts: Dict[str, int],
) -> Dict[str, Any]:
    counts = _issue_counts(pages)
    pass_n = sum(1 for p in pages if p.get("status") == "PASS")
    warn_n = sum(1 for p in pages if p.get("status") == "WARN")
    fail_n = sum(1 for p in pages if p.get("status") == "FAIL")
    return {
        "schema_version": "0.2.0",
        "generated_at": _dt.datetime.utcnow().isoformat() + "Z",
        "status": _overall_status(pages, manifest_ok),
        "site_root": args.site_root,
        "manifest_url": manifest_url,
        "manifest_ok": manifest_ok,
        "pages_total": len(pages),
        "pages_checked": len(pages),
        "pages_pass": pass_n,
        "pages_warn": warn_n,
        "pages_fail": fail_n,
        "issues_by_severity": counts,
        "page_type_counts": page_type_counts,
        "pages": pages,
        "recommendations": _build_recommendations(pages, page_type_counts),
    }


def _build_markdown_report(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Published Pages Regression Audit — {report['generated_at']}")
    lines.append("")
    lines.append(f"- **Status**: {report['status']}")
    lines.append(f"- **Site root**: {report['site_root']}")
    lines.append(f"- **Manifest URL**: {report['manifest_url']}")
    lines.append(f"- **Pages total / checked**: {report['pages_total']} / {report['pages_checked']}")
    lines.append(f"- **Pages PASS / WARN / FAIL**: {report['pages_pass']} / {report['pages_warn']} / {report['pages_fail']}")
    lines.append(f"- **Issues**: error={report['issues_by_severity']['error']} warning={report['issues_by_severity']['warning']} info={report['issues_by_severity']['info']}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(
        "PASS: all pages HTTP 200 and no error-level issues. "
        "WARN: all pages accessible but legacy-render warnings present. "
        "FAIL: at least one page has template leak / raw dict / old footer / HTTP non-200."
    )
    lines.append("")

    # Page Type Summary (v0.2.12-alpha)
    ptc = report.get("page_type_counts", {})
    lines.append("## Page Type Summary")
    lines.append("")
    lines.append("| Page type | Count |")
    lines.append("|---|---|")
    for t in ALL_PAGE_TYPES:
        lines.append(f"| {t} | {ptc.get(t, 0)} |")
    lines.append("")

    lines.append("## Pages")
    lines.append("")
    lines.append("| # | URL | Status | HTTP | Page type | Title | Issues |")
    lines.append("|---|---|---|---|---|---|---|")
    for i, p in enumerate(report["pages"], 1):
        title = (p.get("title") or "")[:80].replace("|", "\\|")
        url = p.get("url", "")
        issues_short = ", ".join(sorted({i2["code"] for i2 in p.get("issues", [])})) or "—"
        lines.append(f"| {i} | {url} | {p.get('status', '?')} | {p.get('http_status', '?')} | {p.get('page_type', '?')} | {title} | {issues_short} |")
    lines.append("")

    lines.append("## Detailed issues")
    lines.append("")
    any_issue = False
    for p in report["pages"]:
        if not p.get("issues"):
            continue
        any_issue = True
        lines.append(f"### {p.get('url', '?')}")
        lines.append("")
        lines.append(f"- **Page type**: {p.get('page_type', '?')}")
        if p.get("page_type") == PAGE_TYPE_SITE_INDEX:
            lines.append("- **Paper-level checks**: skipped by design")
            lines.append("- **Index checks**: ran")
        for i in p["issues"]:
            lines.append(f"- **[{i['severity']}]** `{i['code']}` — {i['message']}")
            if i.get("recommendation"):
                lines.append(f"  - 修复建议: {i['recommendation']}")
        lines.append("")
    if not any_issue:
        lines.append("_(no per-page issues)_")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    for r in report.get("recommendations", []):
        lines.append(f"- {r}")
    lines.append("")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Self-test (used by validate.sh)
# ----------------------------------------------------------------------------

def _selftest(args) -> Dict[str, Any]:
    """Run synthetic pages through the same checks. Returns a report dict.

    Includes a fake site_index fixture so the page-type classifier can be
    validated without network access.
    """
    fake_manifest_pages = [
        {
            "slug": "fake-essay",
            "title": "Fake Essay — Self Test",
            "path": "/fake-essay/",
            "_url": "file://" + os.path.join(args.selftest_dir, "fake-essay.html"),
            "_expect": ["essay_missing_markers"],
        },
        {
            "slug": "fake-zhcn",
            "title": "Fake 中文",
            "path": "/fake-zhcn/",
            "_url": "file://" + os.path.join(args.selftest_dir, "fake-zhcn.html"),
            "_expect": ["zh_cn_markers_weak"],
        },
        {
            "slug": "fake-pass",
            "title": "Fake Pass",
            "path": "/fake-pass/",
            "_url": "file://" + os.path.join(args.selftest_dir, "fake-pass.html"),
            "_expect": [],
        },
        {
            "slug": "fake-template-leak",
            "title": "Fake Template Leak",
            "path": "/fake-template-leak/",
            "_url": "file://" + os.path.join(args.selftest_dir, "fake-template-leak.html"),
            "_expect": ["template_leak"],
        },
        {
            "slug": "fake-raw-dict",
            "title": "Fake Raw Dict",
            "path": "/fake-raw-dict/",
            "_url": "file://" + os.path.join(args.selftest_dir, "fake-raw-dict.html"),
            "_expect": ["raw_dict"],
        },
        {
            "slug": "fake-old-footer",
            "title": "Fake Old Footer",
            "path": "/fake-old-footer/",
            "_url": "file://" + os.path.join(args.selftest_dir, "fake-old-footer.html"),
            "_expect": ["old_footer"],
        },
        {
            "slug": "fake-site-index",
            "title": "Fake Site Index",
            "path": "/fake-site-index/",
            "_url": "file://" + os.path.join(args.selftest_dir, "fake-site-index.html"),
            "_expect": [],
        },
        {
            "slug": "fake-site-index-leak",
            "title": "Fake Site Index With Leak",
            "path": "/fake-site-index-leak/",
            "_url": "file://" + os.path.join(args.selftest_dir, "fake-site-index-leak.html"),
            "_expect": ["template_leak"],
        },
    ]
    # monkey-patch _http_get for file:// urls
    import urllib.parse as _up

    def _file_get(url, timeout=20.0):
        parsed = _up.urlparse(url)
        path = _up.unquote(parsed.path)
        if not os.path.isfile(path):
            return 404, ""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return 200, f.read()

    orig = globals()["_http_get"]
    globals()["_http_get"] = _file_get
    try:
        site_root = "file://" + args.selftest_dir
        # The fake site-index fixtures need to be classified as site_index
        # regardless of the URL we point _http_get at (file:// fixture path);
        # we use page_type_override so the classifier rule and the
        # page_type field both stay consistent with the spec.
        site_index_slugs = {"fake-site-index", "fake-site-index-leak"}
        pages: List[Dict[str, Any]] = []
        for entry in fake_manifest_pages:
            url = entry["_url"]
            override = PAGE_TYPE_SITE_INDEX if entry["slug"] in site_index_slugs else None
            page = _audit_page(
                url, entry["title"], entry["slug"], args,
                site_root=site_root,
                manifest_pages=fake_manifest_pages,
                page_type_override=override,
            )
            pages.append(page)
    finally:
        globals()["_http_get"] = orig
    # Annotate pages with _expect + hit/miss for the validation script
    for entry, page in zip(fake_manifest_pages, pages):
        page["_expect"] = entry["_expect"]
        codes = {i["code"] for i in page.get("issues", [])}
        page["_expect_hit"] = sorted(c for c in entry["_expect"] if c in codes)
        page["_expect_miss"] = sorted(c for c in entry["_expect"] if c not in codes)
    return _build_json_report(
        args, "selftest://manifest", pages,
        manifest_ok=True,
        page_type_counts=_page_type_counts(pages),
    )


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit every page in a published_pages.json manifest against v0.2.9+ renderer expectations (v0.2.12-alpha adds page-type classification + root-index exemption).",
    )
    parser.add_argument("--manifest-url", help="Live manifest URL (e.g. https://conanxin.github.io/paper-reading-pages/published_pages.json)")
    parser.add_argument("--manifest-file", help="Local manifest JSON path (alternative to --manifest-url)")
    parser.add_argument("--site-root", default="https://conanxin.github.io/paper-reading-pages", help="Site root used to build page URLs")
    parser.add_argument("--json-output", help="Write JSON report to this path")
    parser.add_argument("--markdown-output", help="Write Markdown report to this path")
    parser.add_argument("--warn-only", action="store_true", help="Always exit 0 unless something is structurally broken")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout per page (default 20s)")
    parser.add_argument("--max-pages", type=int, default=0, help="Cap pages to check (0 = no cap)")
    parser.add_argument("--include-root", action="store_true", help="Also audit the site root index.html (treated as site_index)")
    parser.add_argument("--include-manifest", action="store_true", help="Also audit the manifest JSON itself (treated as manifest)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures for the overall status")
    parser.add_argument("--selftest-dir", help="(selftest) directory containing fake-*.html fixtures")
    args = parser.parse_args(argv)

    if args.selftest_dir:
        report = _selftest(args)
        if args.json_output:
            with open(args.json_output, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        if args.markdown_output:
            with open(args.markdown_output, "w", encoding="utf-8") as f:
                f.write(_build_markdown_report(report))
        print(f"[selftest] overall={report['status']} pass={report['pages_pass']} warn={report['pages_warn']} fail={report['pages_fail']}")
        if args.strict and report["status"] != "PASS":
            return 2
        return 0

    # Normal run
    if not args.manifest_url and not args.manifest_file:
        parser.error("must supply --manifest-url or --manifest-file (or --selftest-dir for the smoke test)")

    try:
        manifest_url, manifest_pages = _load_manifest(args)
        manifest_ok = True
    except SystemExit as e:
        # Re-raise after writing partial report
        print(str(e), file=sys.stderr)
        if args.json_output:
            os.makedirs(os.path.dirname(os.path.abspath(args.json_output)) or ".", exist_ok=True)
            with open(args.json_output, "w", encoding="utf-8") as f:
                json.dump({
                    "schema_version": "0.2.0",
                    "status": "FAIL",
                    "site_root": args.site_root,
                    "manifest_url": args.manifest_url or "",
                    "manifest_ok": False,
                    "pages_total": 0,
                    "pages_checked": 0,
                    "pages_pass": 0,
                    "pages_warn": 0,
                    "pages_fail": 0,
                    "issues_by_severity": {"error": 1, "warning": 0, "info": 0},
                    "page_type_counts": {t: 0 for t in ALL_PAGE_TYPES},
                    "pages": [],
                    "recommendations": ["无法读取 manifest — 检查 --manifest-url 是否可访问。"],
                }, f, ensure_ascii=False, indent=2)
        return 1

    pages_to_check: List[Dict[str, Any]] = []

    # Optional: include manifest JSON itself as a manifest page entry.
    if args.include_manifest:
        pages_to_check.append({
            "url": manifest_url,
            "title": "published_pages.json (manifest)",
            "slug": "published_pages_json",
        })

    for entry in manifest_pages:
        path = entry.get("path", "")
        url = urllib.parse.urljoin(args.site_root.rstrip("/") + "/", path.lstrip("/"))
        slug = entry.get("slug", path.strip("/").rstrip("/") or "index")
        title = entry.get("title", "")
        pages_to_check.append({"url": url, "title": title, "slug": slug})

    root_url: Optional[str] = None
    if args.include_root:
        root_url = args.site_root.rstrip("/") + "/"
        # Insert root at position 0 so it appears first in the report.
        pages_to_check.insert(0, {"url": root_url, "title": "(site root)", "slug": "index"})
        args._root_url = root_url

    if args.max_pages and args.max_pages > 0:
        pages_to_check = pages_to_check[: args.max_pages]

    audited: List[Dict[str, Any]] = []
    for entry in pages_to_check:
        try:
            page_type_override = PAGE_TYPE_MANIFEST if entry["slug"] == "published_pages_json" else None
            p = _audit_page(
                entry["url"], entry["title"], entry["slug"], args,
                site_root=args.site_root,
                manifest_pages=manifest_pages,
                page_type_override=page_type_override,
            )
        except Exception as e:
            p = {
                "url": entry["url"],
                "slug": entry["slug"],
                "title": entry["title"],
                "http_status": 0,
                "fetched_bytes": 0,
                "issues": [_mk_issue("error", "audit_crashed", f"审计脚本异常: {e}", "查看 audit_published_pages.py 错误日志。")],
                "status": "FAIL",
                "page_type": PAGE_TYPE_UNKNOWN,
            }
        audited.append(p)

    # Top-level manifest-shape validation (always)
    manifest_shape_issues = _check_manifest_pages(manifest_pages)
    if manifest_shape_issues:
        # Emit as an info-level synthetic page so it appears in the report
        audited.insert(0 if not args.include_root else 1, {
            "url": manifest_url,
            "slug": "_manifest_shape",
            "title": "published_pages.json shape",
            "http_status": 200,
            "fetched_bytes": 0,
            "issues": manifest_shape_issues,
            "status": "FAIL" if any(i["severity"] == "error" for i in manifest_shape_issues) else "WARN",
            "page_type": PAGE_TYPE_MANIFEST,
        })

    page_type_counts = _page_type_counts(audited)
    report = _build_json_report(args, manifest_url, audited, manifest_ok, page_type_counts)
    if args.strict and any(i["severity"] == "warning" for p in audited for i in p.get("issues", [])):
        report["status"] = "FAIL"

    if args.json_output:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_output)) or ".", exist_ok=True)
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    if args.markdown_output:
        os.makedirs(os.path.dirname(os.path.abspath(args.markdown_output)) or ".", exist_ok=True)
        with open(args.markdown_output, "w", encoding="utf-8") as f:
            f.write(_build_markdown_report(report))

    print(f"[audit] overall={report['status']} pages={report['pages_total']} pass={report['pages_pass']} warn={report['pages_warn']} fail={report['pages_fail']}")

    if args.warn_only:
        return 0
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
