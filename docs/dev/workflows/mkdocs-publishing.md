# MkDocs Publishing — Manual Build & Deploy Guide

This guide covers how to build the TanGA documentation site locally and how
to publish it to GitHub Pages.  **No GitHub Actions or CI/CD is required** —
everything is done with a single `mkdocs gh-deploy` command from your local
machine.

## Prerequisites

- Python environment with `mkdocs-material` installed:
  ```bash
  uv sync
  ```
- Push (write) access to `dodeka12/tanga` on GitHub.
  Verify with:
  ```bash
  git push --dry-run origin main
  ```

## One-Time GitHub Setup

Before the first deployment, GitHub must be configured to serve the
`gh-pages` branch as a website. This is a **one-time** operation.

### Step 1: Verify Push Access

```bash
git push --dry-run origin main
```

If this fails, you do not have write access to the repository. Ask the
repository owner to add you as a collaborator.

### Step 2: Navigate to Pages Settings

1. Go to the repository on GitHub: https://github.com/dodeka12/tanga
2. Click the **Settings** tab (top-level tab in the repository header,
   not the navbar inside the repo view).
3. In the left sidebar, under "Code and automation", click **Pages**.

Shortcut URL:
```
https://github.com/dodeka12/tanga/settings/pages
```

### Step 3: Configure the Source

| Setting | Value |
|---------|-------|
| **Source** | Deploy from a branch |
| **Branch** | `gh-pages` |
| **Folder** | `/ (root)` |

If `gh-pages` does not appear in the branch dropdown yet, run the first
deployment (`mkdocs gh-deploy`, see below) — it creates the branch. Then
return to this page and select it.

### Step 4: Save and Verify

Click **Save**. GitHub displays a blue banner:

> ✅ Your site is ready to be published at https://dodeka12.github.io/tanga/.

### Step 5: Enforce HTTPS (Recommended)

On the same Settings → Pages page, check **Enforce HTTPS**. This redirects
all HTTP traffic to `https://`. Certificate provisioning (Let's Encrypt)
may take a few minutes.

### Step 6: Custom Domain (Optional)

If you want to use a custom domain (e.g. `docs.tanga.dev`):

1. Enter the domain in the "Custom domain" field.
2. Click **Save**. GitHub creates a `CNAME` file in the `gh-pages` branch.
3. At your DNS provider, add a `CNAME` record pointing to
   `dodeka12.github.io`.
4. Wait for DNS propagation (can take up to 24 hours, usually minutes).
5. Check **Enforce HTTPS** once the domain is verified.

This step is **not required** for the default `*.github.io` URL.

## Local Preview

Start a live-reload development server:

```bash
mkdocs serve
```

Open http://localhost:8000 in your browser. Changes to Markdown files are
reflected instantly. Press `Ctrl+C` to stop.

## Build (Dry Run)

Build the static site into the `site/` directory without deploying:

```bash
mkdocs build --strict
```

The `--strict` flag treats warnings as errors — use it to catch broken
links, missing pages, and invalid configuration. The `site/` directory is
git-ignored and should never be committed.

## Deploy to GitHub Pages

Run from the repository root:

```bash
mkdocs gh-deploy
```

This command:

1. Builds the site (`mkdocs build`)
2. Force-pushes the contents of `site/` to the `gh-pages` branch
3. Prints the URL: `https://dodeka12.github.io/tanga/`

No other steps are needed. GitHub automatically rebuilds the Pages site
when the `gh-pages` branch is updated (this usually takes 1–2 minutes).

## Updating the Documentation

The typical workflow for updating docs:

```bash
# 1. Edit Markdown files in docs/ or dev/docs/
vim docs/py/algebra/index.md

# 2. Preview changes
mkdocs serve

# 3. Commit your changes to the main branch
git add docs/
git commit -m "Update algebra docs"
git push origin main

# 4. Deploy to GitHub Pages
mkdocs gh-deploy
```

## Adding New Pages

1. Create the new Markdown file under `docs/` or `dev/docs/`.
2. Add the page to the `nav` section in `mkdocs.yml`.
3. Run `mkdocs serve` to verify the navigation and links.
4. Commit both the new file and the updated `mkdocs.yml`.
5. Run `mkdocs gh-deploy`.

The nav is **explicit** — pages do not appear automatically. This prevents
orphaned documents and gives full control over ordering.

## Troubleshooting

### `gh-pages` branch does not appear

```bash
git branch -r | grep gh-pages
```

If the branch does not exist, run `mkdocs gh-deploy` — it creates the branch
on the first deployment.

### 404 on `https://dodeka12.github.io/tanga/`

- The initial Pages build can take up to 5 minutes.
- Check Settings → Pages for the build status indicator.
- Ensure the source is set to "Deploy from a branch" with `gh-pages` / root.

### Pages not updating after `mkdocs gh-deploy`

- Wait 1–2 minutes for GitHub's Pages rebuild to complete.
- Hard-refresh the browser (`Ctrl+Shift+R`).
- Check Settings → Pages for build errors.

### HTTPS not working

- After enabling "Enforce HTTPS", Let's Encrypt certificate provisioning
  can take several minutes.
- If it fails, try disabling and re-enabling "Enforce HTTPS".
- For custom domains, ensure the DNS `CNAME` record is correctly set.

### Broken links in the built site

Run `mkdocs build --strict` locally before deploying. This catches:

- Missing pages referenced in `mkdocs.yml`
- Dead internal links (`[link](nonexistent.md)`)
- Invalid YAML syntax in `mkdocs.yml`

### `mkdocs: command not found`

```bash
uv sync    # installs mkdocs-material (which depends on mkdocs)
```

Or activate the virtual environment manually:

```bash
source .venv/bin/activate
```

## Files Involved

| File | Role |
|------|------|
| `mkdocs.yml` | Site configuration, theme, navigation, extensions |
| `docs/` | User-facing documentation (C++ and Python) |
| `dev/docs/` | Developer documentation (architecture, workflows, guides) |
| `docs/javascripts/mathjax.js` | MathJax 3 configuration for LaTeX rendering |
| `site/` | Build output directory (git-ignored, temporary) |
| `gh-pages` branch | Deployment target (created by `mkdocs gh-deploy`) |

## Reference

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [GitHub Pages Docs](https://docs.github.com/en/pages)