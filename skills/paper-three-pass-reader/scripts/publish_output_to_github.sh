#!/usr/bin/env bash
# publish_output_to_github.sh — paper-three-pass-reader (v0.1.1-alpha)
#
# Push a paper-reading-output/ directory to the gh-pages branch of an existing
# GitHub repo. Supports two modes:
#
#   1. Legacy / single-page mode (default):
#      ./publish_output_to_github.sh \
#        --output paper-reading-output \
#        --repo OWNER/REPO [--branch gh-pages] [--message MSG]
#      Replaces the entire contents of the gh-pages branch with the output dir.
#
#   2. Multi-page mode (--site-path):
#      ./publish_output_to_github.sh \
#        --output paper-reading-output \
#        --repo OWNER/REPO [--branch gh-pages] [--message MSG] \
#        --site-path attention-is-all-you-need \
#        [--page-title "Attention Is All You Need"]
#      Copies the output dir into <site-path>/ subdirectory of gh-pages,
#      preserving other published pages. Optionally regenerates the root
#      index.html from a published_pages.json manifest.
#
# Optional:
#   --check     # only verify gh availability + auth
#
# Design rules:
# - NEVER silently create the target repo. Print the exact `gh repo create`
#   command and exit non-zero if missing.
# - NEVER print tokens or secrets.
# - NEVER force-push.
# - In multi-page mode, NEVER delete other already-published page directories.
# - Always add a .nojekyll so GitHub Pages serves assets/ verbatim.

set -euo pipefail

OUTPUT_DIR=""
TARGET_REPO=""
BRANCH="gh-pages"
MESSAGE="Publish paper reading page"
SITE_PATH=""          # if set, copy into <branch-root>/<site-path>/
PAGE_TITLE=""         # if set with --site-path, register this page in the index
CHECK_ONLY=0

usage() {
  cat <<EOF
Usage:
  $0 --output DIR --repo OWNER/REPO [--branch NAME] [--message MSG] \\
     [--site-path SLUG] [--page-title "Title"]
  $0 --check

Single-page mode (legacy):
  Replaces the gh-pages branch contents with OUTPUT_DIR.

Multi-page mode (--site-path):
  Copies OUTPUT_DIR into <branch-root>/<site-path>/ and preserves other pages.
  With --page-title, also updates the root index.html + published_pages.json
  manifest so the page appears at https://OWNER.github.io/REPO/.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)     OUTPUT_DIR="$2"; shift 2 ;;
    --repo)       TARGET_REPO="$2"; shift 2 ;;
    --branch)     BRANCH="$2"; shift 2 ;;
    --message)    MESSAGE="$2"; shift 2 ;;
    --site-path)  SITE_PATH="$2"; shift 2 ;;
    --page-title) PAGE_TITLE="$2"; shift 2 ;;
    --check)      CHECK_ONLY=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "[error] unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

# 1. Check gh CLI
if ! command -v gh >/dev/null 2>&1; then
  echo "[error] gh CLI not found on PATH. Install GitHub CLI or run on a machine that has it."
  exit 3
fi

# 2. Check gh auth (do NOT print token)
if ! gh auth status >/dev/null 2>&1; then
  echo "[error] gh is not authenticated. Run: gh auth login"
  exit 3
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  echo "[ok] gh available and authenticated"
  echo "[ok] --site-path supported: yes"
  echo "[ok] --page-title supported: yes"
  exit 0
fi

if [[ -z "$OUTPUT_DIR" || -z "$TARGET_REPO" ]]; then
  echo "[error] --output and --repo are required" >&2
  usage
  exit 2
fi

if [[ ! -d "$OUTPUT_DIR" ]]; then
  echo "[error] output dir does not exist: $OUTPUT_DIR"
  exit 4
fi

# 3. Check the target repo exists. DO NOT create silently.
if ! gh repo view "$TARGET_REPO" >/dev/null 2>&1; then
  echo "[error] target repo does not exist or is not visible to the current gh account: $TARGET_REPO"
  echo "       This script will NOT create the repo for you."
  echo "       Create it manually with:"
  echo "           gh repo create $TARGET_REPO --public --description 'Paper reading pages (paper-three-pass-reader)'"
  echo "       Then re-run this script."
  exit 5
fi

# 4. Stage in a temp clone of the target branch.
STAGING="$(mktemp -d -t p3pr-pages-XXXXXX)"
trap 'rm -rf "$STAGING"' EXIT

echo "[info] staging in $STAGING"

CLONE_OK=0
if git clone --depth 1 --branch "$BRANCH" "https://github.com/${TARGET_REPO}.git" "$STAGING/repo" >/dev/null 2>&1; then
  CLONE_OK=1
else
  # Branch may not exist yet — clone default, then create orphan branch.
  git clone --depth 1 "https://github.com/${TARGET_REPO}.git" "$STAGING/repo" >/dev/null
  (cd "$STAGING/repo" && git checkout --orphan "$BRANCH" && git rm -rf . >/dev/null 2>&1 || true)
fi

# Sanity: ensure .nojekyll exists at branch root.
touch "$STAGING/repo/.nojekyll"

if [[ -z "$SITE_PATH" ]]; then
  # ----- Single-page (legacy) mode -----
  echo "[info] single-page mode: replacing gh-pages contents"
  (cd "$STAGING/repo" && find . -mindepth 1 -maxdepth 1 ! -name '.git' ! -name '.nojekyll' -exec rm -rf {} +)
  cp -R "$OUTPUT_DIR/." "$STAGING/repo/"
else
  # ----- Multi-page mode -----
  # Validate SITE_PATH: only safe characters.
  if [[ ! "$SITE_PATH" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "[error] --site-path must match [A-Za-z0-9._-]+ (got: $SITE_PATH)"
    exit 6
  fi
  echo "[info] multi-page mode: copying into <branch>/$SITE_PATH/"
  mkdir -p "$STAGING/repo/$SITE_PATH"
  # Remove only this subdirectory's previous contents (preserve siblings).
  (cd "$STAGING/repo/$SITE_PATH" && find . -mindepth 1 -maxdepth 1 ! -name '.nojekyll' -exec rm -rf {} +)
  cp -R "$OUTPUT_DIR/." "$STAGING/repo/$SITE_PATH/"
  # Each page directory also gets its own .nojekyll (defensive).
  touch "$STAGING/repo/$SITE_PATH/.nojekyll"

  # If --page-title is given, regenerate the root index.html from published_pages.json.
  if [[ -n "$PAGE_TITLE" ]]; then
    echo "[info] updating root index.html + published_pages.json for: $PAGE_TITLE"
    # In multi-page index mode the branch root holds ONLY: .nojekyll, assets/, index.html, published_pages.json, and per-page subdirectories.
    # Wipe any stray non-infrastructure files at the root that pre-date this index mode.
    (cd "$STAGING/repo" && find . -mindepth 1 -maxdepth 1 \
        ! -name '.git' \
        ! -name '.nojekyll' \
        ! -name 'assets' \
        ! -name 'index.html' \
        ! -name 'published_pages.json' \
        -exec rm -rf {} +)
    # Also remove any top-level files that were previously placed by single-page mode (README.md, data/, reports/ etc.)
    (cd "$STAGING/repo" && find . -mindepth 1 -maxdepth 1 \
        -name 'README.md' -o -name 'data' -o -name 'reports' -o -name 'index.html.bak' \
        -exec rm -rf {} + 2>/dev/null || true)
    MANIFEST="$STAGING/repo/published_pages.json"
    if [[ -f "$MANIFEST" ]]; then
      # Read existing manifest, upsert this entry.
      python3 - "$MANIFEST" "$SITE_PATH" "$PAGE_TITLE" <<'PYEOF'
import json, sys, datetime
path, slug, title = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    if not isinstance(d, dict) or "pages" not in d or not isinstance(d["pages"], list):
        d = {"schema_version": "0.1", "pages": []}
except Exception:
    d = {"schema_version": "0.1", "pages": []}
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
# Upsert by slug.
d["pages"] = [p for p in d["pages"] if p.get("slug") != slug]
d["pages"].append({
    "slug": slug,
    "title": title,
    "path": "/" + slug + "/",
    "published_at": now,
})
d["pages"].sort(key=lambda p: p.get("published_at", ""))
with open(path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF
    else
      python3 - "$MANIFEST" "$SITE_PATH" "$PAGE_TITLE" <<'PYEOF'
import json, sys, datetime
path, slug, title = sys.argv[1], sys.argv[2], sys.argv[3]
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
d = {
    "schema_version": "0.1",
    "pages": [
        {"slug": slug, "title": title, "path": "/" + slug + "/", "published_at": now}
    ],
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF
    fi
    # Render the root index.html from the manifest.
    python3 - "$MANIFEST" "$STAGING/repo/index.html" "$TARGET_REPO" <<'PYEOF'
import json, sys, html
manifest_path, out_path, repo = sys.argv[1], sys.argv[2], sys.argv[3]
with open(manifest_path, encoding='utf-8') as f:
    d = json.load(f)
pages = d.get("pages", [])
rows = "\n".join(
    f'      <li><a href="{html.escape(p["path"])}">{html.escape(p["title"])}</a>'
    f' <span class="slug">[{html.escape(p["slug"])}]</span>'
    f' <span class="time">{html.escape(p.get("published_at",""))}</span></li>'
    for p in pages
)
body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Paper Reading Pages — index</title>
  <link rel="stylesheet" href="assets/index.css" />
</head>
<body>
  <header>
    <h1>Paper Reading Pages</h1>
    <p class="kicker">Published paper reading pages (paper-three-pass-reader)</p>
  </header>
  <main>
    <section>
      <h2>Published pages ({len(pages)})</h2>
      <ul class="pages">
{rows}
      </ul>
    </section>
    <section>
      <h2>About</h2>
      <p>Each entry above is a self-contained three-pass reading page for one paper.</p>
      <p>Repository: <a href="https://github.com/{html.escape(repo)}">{html.escape(repo)}</a></p>
      <p>Generated by <code>paper-three-pass-reader v0.1.1-alpha</code>.</p>
    </section>
  </main>
</body>
</html>
"""
with open(out_path, "w", encoding="utf-8") as f:
    f.write(body)

# Write a tiny static stylesheet so the index looks reasonable.
css_path = out_path.rsplit("/", 1)[0] + "/assets/index.css"
import os
os.makedirs(os.path.dirname(css_path), exist_ok=True)
with open(css_path, "w", encoding="utf-8") as f:
    f.write("""body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; color: #222; }
h1 { margin-bottom: 4px; }
.kicker { color: #888; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; }
.pages { list-style: none; padding: 0; }
.pages li { padding: 8px 0; border-bottom: 1px solid #eee; }
.pages a { font-weight: 600; text-decoration: none; color: #1864ab; }
.pages a:hover { text-decoration: underline; }
.slug { color: #888; font-size: 12px; margin-left: 6px; }
.time { color: #888; font-size: 12px; margin-left: 6px; }
section { margin-top: 24px; }
""")
PYEOF
  fi
fi

# Commit + push.
(cd "$STAGING/repo"
  git config user.email  "paper-three-pass-reader@local"
  git config user.name   "paper-three-pass-reader"
  git add -A
  if git diff --cached --quiet; then
    echo "[info] no changes to publish"
    exit 0
  fi
  git commit -m "$MESSAGE" >/dev/null
  # Push to the branch without forcing.
  if ! git push origin "$BRANCH" 2>&1; then
    echo "[error] push failed; branch left unchanged on remote"
    exit 7
  fi
)

echo "[ok] published to https://github.com/${TARGET_REPO}/tree/${BRANCH}"
# Compute Pages URL: https://<owner>.github.io/<repo>/
PAGES_OWNER="${TARGET_REPO%%/*}"
PAGES_REPO="${TARGET_REPO##*/}"
PAGES_BASE="https://${PAGES_OWNER}.github.io/${PAGES_REPO}/"
if [[ -n "$SITE_PATH" ]]; then
  echo "[ok] page URL: ${PAGES_BASE}${SITE_PATH}/"
  echo "[ok] root index: ${PAGES_BASE}"
else
  echo "[ok] Pages URL (after first enablement): ${PAGES_BASE}"
fi
