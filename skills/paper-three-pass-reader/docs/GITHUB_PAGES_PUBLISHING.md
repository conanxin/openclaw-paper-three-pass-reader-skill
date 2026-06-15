# Publishing to GitHub Pages

This document explains how to publish a generated `paper-reading-output/` directory to GitHub Pages using the bundled script.

---

## What the script does

`skills/paper-three-pass-reader/scripts/publish_output_to_github.sh` pushes the contents of `paper-reading-output/` to the **gh-pages** branch of a GitHub repo. GitHub Pages then serves it as a static site.

What it does **not** do:

- It does **not** silently create the target repo. If `conanxin/paper-reading-pages` does not exist, the script prints the exact `gh repo create` command and exits.
- It does **not** enable Pages on the repo. You do that once in the repo's **Settings → Pages** panel.
- It does **not** print tokens or secrets.
- It does **not** do retries, rollbacks, or force pushes.

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
