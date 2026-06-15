# Publishing to GitHub Pages

This document explains how to publish a generated `paper-reading-output/` directory to GitHub Pages using the bundled script.

---

## What the script does

`skills/paper-three-pass-reader/scripts/publish_output_to_github.sh` pushes the contents of `paper-reading-output/` to the **gh-pages** branch of a GitHub repo. GitHub Pages then serves it as a static site.

It supports **two modes**:

1. **Single-page mode** (legacy / default): the entire `gh-pages` branch contents are replaced with the output dir.
2. **Multi-page mode** (with `--site-path` + optional `--page-title`): the output dir is copied into a subdirectory and other pages are preserved; the branch root becomes a small index page listing every published paper.

What it does **not** do:

- It does **not** silently create the target repo. If `conanxin/paper-reading-pages` does not exist, the script prints the exact `gh repo create` command and exits.
- It does **not** enable Pages on the repo. You do that once in the repo's **Settings → Pages** panel.
- It does **not** print tokens or secrets.
- It does **not** do retries, rollbacks, or force pushes.

---

## Multi-page mode (v0.1.1+)

When you have several papers to publish into one repo, use `--site-path` to put each paper into its own subdirectory:

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output runs/attention-is-all-you-need-20260615/paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --site-path attention-is-all-you-need \
  --page-title "Attention Is All You Need" \
  --message "Publish Attention Is All You Need reading page under slug"
```

What happens:

1. The output dir is copied to `gh-pages/attention-is-all-you-need/` (overwriting that subdirectory's previous contents only — other page subdirs are preserved).
2. Each page subdir gets its own `.nojekyll`.
3. With `--page-title`, the script also regenerates the branch root's `index.html` and `published_pages.json`, upserting the entry for `attention-is-all-you-need`.
4. In index mode, the branch root is normalised to hold only `.nojekyll`, `assets/`, `index.html`, `published_pages.json`, and the per-page subdirs. Any stray top-level `data/`, `reports/`, `README.md` etc. (left over from a previous single-page deploy) are removed.

`--site-path` must match `[A-Za-z0-9._-]+`. Anything else (including path separators) is rejected with exit code 6.

### Resulting layout

```
gh-pages/
├── .nojekyll
├── assets/
│   └── index.css         (only used by the root index)
├── index.html            (lists every published page)
├── published_pages.json  (machine-readable manifest)
├── attention-is-all-you-need/
│   ├── .nojekyll
│   ├── index.html        (the actual reading page)
│   ├── assets/
│   ├── data/
│   └── reports/
└── <next-slug>/…
```

### URLs

- Root index: `https://<owner>.github.io/<repo>/`
- Each paper: `https://<owner>.github.io/<repo>/<site-path>/`

For the Attention run:

- `https://conanxin.github.io/paper-reading-pages/`
- `https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/`

### Manifest

`published_pages.json` is a JSON file with one `pages` array, each entry shaped like:

```json
{
  "slug": "attention-is-all-you-need",
  "title": "Attention Is All You Need",
  "path": "/attention-is-all-you-need/",
  "published_at": "2026-06-15T02:39:03Z"
}
```

The script upserts by `slug` (so re-publishing the same paper updates `title` and `published_at`, doesn't duplicate). The array is sorted by `published_at`. The root `index.html` is regenerated from this manifest each time.

---

## Single-page mode (legacy)

---

## One-time setup

### 1. Authenticate the GitHub CLI

```bash
gh auth login
gh auth status
```

### 2. Create the publishing repo (once)

The script refuses to create it for you, so do it yourself:

```bash
gh repo create conanxin/paper-reading-pages \
    --public \
    --description "Paper reading pages (paper-three-pass-reader)"
```

### 3. Enable GitHub Pages on the repo

Open `https://github.com/conanxin/paper-reading-pages/settings/pages`:

- **Source:** Deploy from a branch
- **Branch:** `gh-pages` / `(root)`
- Click **Save**

The first deploy takes 30–60 seconds. After that, the site is live at `https://conanxin.github.io/paper-reading-pages/`.

---

## Publishing a page

### Basic usage

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
    --output paper-reading-output \
    --repo conanxin/paper-reading-pages \
    --branch gh-pages \
    --message "Publish reading page: How to Read a Paper"
```

### What gets pushed

- `index.html`
- `assets/style.css`
- `assets/app.js`
- `data/*.json`
- `reports/*.md`
- `README.md`
- A `.nojekyll` file (so Pages serves the `assets/` folder verbatim, no Jekyll rewrite).

The script does **not** delete files on the remote that are no longer in the local output dir. If you want a clean slate, push an empty commit first and then re-run.

### Branch name

Default is `gh-pages`. Pass `--branch main` if you prefer to serve from `main` (you'll need to set Pages to serve from `main` in the repo settings).

---

## Troubleshooting

### "target repo does not exist"

```
[error] target repo does not exist or is not visible to the current gh account: conanxin/paper-reading-pages
       This script will NOT create the repo for you.
       Create it manually with:
           gh repo create conanxin/paper-reading-pages --public --description 'Paper reading pages (paper-three-pass-reader)'
       Then re-run this script.
```

Run the suggested `gh repo create` command, then re-run.

### "gh is not authenticated"

```
[error] gh is not authenticated. Run: gh auth login
```

Run `gh auth login`, then re-run.

### "push failed; branch left unchanged on remote"

```
[error] push failed; branch left unchanged on remote
```

Read the `git push` output. Common causes:

- Branch protection on `gh-pages` (unlikely for personal repos).
- Network blip — re-run.
- Repo permissions: your `gh` user must have write access.

### Site shows 404

- Did you enable Pages in Settings? It does not auto-enable.
- Did you wait 30–60 seconds after the first push?
- Is the branch name correct? Default is `gh-pages`.

---

## Manual alternative

If you'd rather not use the script, here's the manual flow:

```bash
# 1. Stage locally
mkdir -p /tmp/publish-staging
cp -R paper-reading-output/. /tmp/publish-staging/
touch /tmp/publish-staging/.nojekyll

# 2. Push to gh-pages
cd /tmp/publish-staging
git init
git checkout -b gh-pages
git add -A
git commit -m "Publish reading page"
git remote add origin https://github.com/conanxin/paper-reading-pages.git
git push -u origin gh-pages
```

The script does exactly this, but it refuses to silently create the repo and refuses to print tokens.

---

## Custom domains

If you own a custom domain, set it in **Settings → Pages → Custom domain**. The skill does not automate this — it's a one-time click in the GitHub UI.

---

## Notes on safety

- The script uses `https://` for the remote URL, which works with the token in `~/.config/gh/hosts.yml`. SSH remotes also work if `~/.gitconfig` has the right key.
- The script runs `git rm -rf .` inside the staging clone when it cannot clone the target branch directly. That `rm` is scoped to the staging clone (a tempdir). It never touches your working directory.
- The script writes a `user.email` and `user.name` into the staging clone's `.git/config`. These are paper-three-pass-reader-specific and do not affect your global git config.
