#!/usr/bin/env bash
# publish_output_to_github.sh — paper-three-pass-reader (v0.1.0-alpha)
#
# Push a paper-reading-output/ directory to the gh-pages branch of an existing
# GitHub repo as a static site.
#
# Usage:
#   ./publish_output_to_github.sh \
#       --output paper-reading-output \
#       --repo conanxin/paper-reading-pages \
#       --branch gh-pages \
#       --message "Publish reading page"
#
# Design rules:
# - DEFAULT BRANCH: gh-pages (per skill spec).
# - Never silently create the target repo. If it does not exist, print the exact
#   `gh repo create` command and exit non-zero.
# - Never print tokens / secrets / env values.
# - No complex rollback, no retry loop. If a push fails, read the error.
# - No force pushes. No deletes.
# - Pushed contents: index.html, assets/, data/, reports/, README.md.

set -euo pipefail

OUTPUT_DIR=""
TARGET_REPO=""
BRANCH="gh-pages"
MESSAGE="Publish paper reading page"

usage() {
  cat <<EOF
Usage: $0 --output DIR --repo OWNER/REPO [--branch NAME] [--message MSG]
       $0 --check     # only check gh availability + auth
EOF
}

CHECK_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)  OUTPUT_DIR="$2"; shift 2 ;;
    --repo)    TARGET_REPO="$2"; shift 2 ;;
    --branch)  BRANCH="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    --check)   CHECK_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
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

# 4. Stage in a temp clone of the gh-pages branch.
STAGING="$(mktemp -d -t p3pr-pages-XXXXXX)"
trap 'rm -rf "$STAGING"' EXIT

echo "[info] staging in $STAGING"
git clone --depth 1 --branch "$BRANCH" "https://github.com/${TARGET_REPO}.git" "$STAGING/repo" >/dev/null 2>&1 || {
  # branch may not exist yet — clone default, then create orphan branch
  git clone --depth 1 "https://github.com/${TARGET_REPO}.git" "$STAGING/repo" >/dev/null
  (cd "$STAGING/repo" && git checkout --orphan "$BRANCH" && git rm -rf . >/dev/null 2>&1 || true)
}

# Wipe existing contents (we own this branch — it's a publish target).
# But never touch .git.
(cd "$STAGING/repo" && find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +)

# Copy contents of OUTPUT_DIR (not the dir itself).
cp -R "$OUTPUT_DIR/." "$STAGING/repo/"

# Add a .nojekyll so GitHub Pages serves the assets/ folder as static files.
touch "$STAGING/repo/.nojekyll"

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
    exit 6
  fi
)

echo "[ok] published to https://github.com/${TARGET_REPO}/tree/${BRANCH}"
echo "[ok] Pages URL (after first enablement): https://${TARGET_REPO//\//.github.io/}/  (configured per repo Settings > Pages)"
