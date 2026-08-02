# MkDocs Documentation — Implementation Plan

Publish TanGA's existing Markdown documentation as a static site using **mkdocs
with the Material theme**, deployable to **GitHub Pages** via manual command
(no GitHub Actions workers available).

---

## Motivation

- `docs/` contains 50+ Markdown files (C++ and Python user guides) — currently
  only browsable as raw Markdown on GitHub.
- `dev/docs/` contains 13 architecture, cryptography, and workflow documents
  for developers — equally valuable but invisible to casual visitors.
- mkdocs gives us: search, navigation, dark/light theme, code highlighting
  (C++/Python), math rendering (MathJax), and a single-command deploy to
  `gh-pages`.

**Decision:** mkdocs-material was chosen over Sphinx (no RST migration
needed) and Docusaurus (no Node.js toolchain required). The project already
uses `uv`/`hatchling` — mkdocs fits naturally into the Python toolchain.

---

## Phases

| # | Phase | Detail | Done |
|---|-------|--------|------|
| 1 | Dependencies and config | Install `mkdocs-material`, create `mkdocs.yml` with full nav tree | [x] |
| 2 | Fix broken links and missing pages | Audit all internal links, create missing pages (e.g. `docs/py/env/`) | [x] |
| 3 | Developer docs integration | Pull `dev/docs/` into the mkdocs nav as a "Developer Docs" section | [x] |
| 4 | Workflow documentation | Create `dev/docs/workflows/mkdocs-publishing.md` — manual build & deploy guide | [x] |
| 5 | Local preview and validation | `mkdocs build --strict`, fix all warnings, verify output | [x] |
| 6 | Initial deployment | `mkdocs gh-deploy` to `gh-pages` branch, configure repo Pages settings | [ ] |

---

## Phase 1 — Dependencies and Config

Add `mkdocs-material` as a dev/docs dependency and create the top-level
`mkdocs.yml` configuration file.

### 1.1 Install mkdocs-material

```
uv add --dev mkdocs-material
```

This pins the dependency in `pyproject.toml` and `uv.lock`.

### 1.2 Create `mkdocs.yml`

The nav tree mirrors the existing TOC structure from `docs/index.md` and
`dev/docs/README.md`, with sections:

```
site_name: TanGA Documentation
site_url: https://dodeka12.github.io/tanga/
repo_url: https://github.com/dodeka12/tanga
theme:
  name: material
  features:
    - navigation.sections
    - navigation.expand
    - search.highlight
    - content.code.copy
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.inlinehilite
  - admonition
  - footnotes
  - toc:
      permalink: true
  - pymdownx.arithmatex:
      generic: true
extra_javascript:
  - javascripts/mathjax.js
  - https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js
plugins:
  - search
nav:
  - Home: index.md
  - C++ Documentation:
      - Overview: cpp/index.md
      - Fixed-space multivectors: cpp/multivectors-e3-p3-n3.md
      - Subspace multivectors: cpp/subspace-multivectors.md
      - Dynamic multivectors: cpp/dynamic-multivectors.md
      - Matrix mapping & equations: cpp/matrix-mapping-and-equations.md
      - Product matrices: cpp/product-matrices.md
      - Congruence maps: cpp/congruence.md
      - Duals: cpp/duals.md
  - Python Documentation:
      - Overview: py/index.md
      - Algebra: ...
      - Basis: ...
      - Blade Mask: ...
      - Matrix: ...
      - Solver: ...
      - Tensors: ...
      - Geometry: ...
      - Visualization: ...
  - Developer Documentation:
      - Overview: dev/index.md
      - Architecture: ...
      - GA Pipeline: ...
      - Cryptography: ...
      - Guides: ...
      - Workflows: ...
```

The full nav will be fleshed out with all existing sub-pages.

### 1.3 MathJax configuration

Create `docs/javascripts/mathjax.js`:

```js
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex",
  },
};
```

---

## Phase 2 — Fix Broken Links and Missing Pages

### 2.1 Audit internal links

- `docs/index.md` line 40 references `py/env/index.md` which does not exist.
  Either create the missing page or remove the row from the TOC table.
- All `docs/py/*/index.md` files use relative links like `(algebra.md)` —
  mkdocs resolves these relative to the source file, which should work as-is.
- `docs/index.md` line 50 references `../LICENSE` — mkdocs will resolve
  this from the `docs/` directory to the repo root. This needs verification
  (may need to copy LICENSE into `docs/` or use an absolute URL).

### 2.2 Create `docs/py/env/index.md` (if needed)

Minimal placeholder for the environment/setup page referenced in the main TOC.

---

## Phase 3 — Developer Docs Integration

### 3.1 Create `docs/dev/index.md`

A landing page for the developer documentation section, linking into the
`dev/docs/` material. This can be a symlink to `dev/docs/README.md` or a
thin wrapper.

### 3.2 Add `dev/docs/` to mkdocs nav

All existing dev docs pages (architecture, cryptography, GA pipeline,
guides, workflows) appear under a "Developer Documentation" top-level nav
item. Links between dev docs pages are relative and should work unchanged.

---

## Phase 4 — Workflow Documentation

Create `dev/docs/workflows/mkdocs-publishing.md` covering:

- **Prerequisites:** `uv sync` to install `mkdocs-material`
- **Local preview:** `mkdocs serve` → http://localhost:8000
- **Build and check:** `mkdocs build --strict` — generates `site/`

### GitHub Repository Setup (one-time, required before first deploy)

The `mkdocs gh-deploy` command pushes static HTML to a `gh-pages` branch,
but **GitHub must be told to serve that branch as a website**. This section
must be documented as a step-by-step guide with the GitHub UI navigation
path:

1. **Push access.** The person deploying needs write/push access to
   `dodeka12/tanga`. Verify: `git push --dry-run origin main` succeeds.

2. **Navigate to Pages settings.** On GitHub, go to the repository →
   **Settings** (top-level tab, not repo navbar) → left sidebar
   **"Pages"** (under "Code and automation").

3. **Configure source.**
   - **Source:** "Deploy from a branch" (not "GitHub Actions").
   - **Branch:** Select `gh-pages` from the dropdown. If the branch does
     not exist yet, run `mkdocs gh-deploy` once first — it creates the
     branch, then come back to this step.
   - **Folder:** `/ (root)` (the default).

4. **Save.** Click **Save**. GitHub shows a blue banner: "Your site is
   ready to be published at https://dodeka12.github.io/tanga/."

5. **Enforce HTTPS (optional but recommended).** On the same Settings →
   Pages page, check **"Enforce HTTPS"** so all traffic is redirected to
   `https://`. This may take a few minutes to take effect.

6. **Custom domain (optional).** If you ever want to use a custom domain
   (e.g. `docs.tanga.dev`), enter it in the "Custom domain" field, update
   your DNS with a `CNAME` record, and check "Enforce HTTPS." This is
   not needed for the default `*.github.io` URL.

7. **Verify the deployment.** After saving, GitHub dispatches a Pages
   build. Wait ~1–2 minutes, then visit the URL shown in the banner.
   Subsequent `mkdocs gh-deploy` pushes trigger automatic rebuilds —
   no manual intervention needed.

Screenshot references (not included in the doc but useful for the person
writing it):
- Settings → Pages is at `https://github.com/dodeka12/tanga/settings/pages`
- The branch dropdown lists all branches; `gh-pages` appears after the
  first `mkdocs gh-deploy`.

### Deployment and Maintenance

- **Manual deploy:** `mkdocs gh-deploy` — builds and force-pushes to
  `gh-pages`. Run from repo root on any machine with push access.
- **Verification:** Visit `https://dodeka12.github.io/tanga/` after deploy.
- **Updating docs:** Edit Markdown → `mkdocs serve` (preview) →
  `mkdocs gh-deploy` (publish).
- **Troubleshooting:**
  - `gh-pages` branch not appearing: check `git branch -r`
  - Pages not updating: check repo Settings → Pages for build status;
    GitHub occasionally delays rebuilds by a few minutes
  - 404 on first visit: the initial Pages build can take up to 5 minutes
  - Broken links: run `mkdocs build --strict` locally first
  - HTTPS not working: wait a few minutes after enabling "Enforce HTTPS";
    Let's Encrypt certificate provisioning can take time

---

## Phase 5 — Local Preview and Validation

1. Run `mkdocs build --strict` — fixes any warnings about missing pages,
   broken cross-references, or invalid YAML.
2. Run `mkdocs serve` and click through all nav entries.
3. Verify:
   - Search works (magnifying glass in header)
   - Code blocks have syntax highlighting
   - MathJax renders inline math
   - Dark/light mode toggle works
   - All internal links resolve
   - External links open in new tabs (add `target: _blank` if needed)
4. Add `site/` to `.gitignore`.

---

## Phase 6 — Initial Deployment

1. Run `mkdocs gh-deploy` from repo root.
2. Verify `gh-pages` branch exists on GitHub.
3. Configure repository Settings → Pages:
   - Source: Deploy from branch
   - Branch: `gh-pages`, directory: `/ (root)`
4. Wait ~1 minute, then visit `https://dodeka12.github.io/tanga/`.
5. Verify the full nav tree, search, and math rendering work in production.

---

## Files Created

| File | Purpose |
|------|---------|
| `mkdocs.yml` | mkdocs configuration with full nav and Material theme |
| `docs/javascripts/mathjax.js` | MathJax inline/display math configuration |
| `docs/dev/index.md` | Developer docs landing page (or symlink) |
| `docs/py/env/index.md` | Environment/setup page (currently missing) |
| `dev/docs/workflows/mkdocs-publishing.md` | Manual build & deploy guide for developers |
| `.gitignore` update | Add `site/` to ignore list |

## Dependencies Added

| Package | Purpose |
|---------|---------|
| `mkdocs-material` | Theme, search, code highlighting, admonitions |
| (transitive) `mkdocs` | Static site generator core |

All dependencies are dev-only, installed via `uv add --dev`.

---

## Notes

- **No CI/CD required.** The `mkdocs gh-deploy` command handles everything:
  build → commit to `gh-pages` branch → push. It's a single manual command.
- **Math rendering uses MathJax 3** via CDN. Works offline once cached by the
  browser. No server-side math rendering needed.
- **The `docs/` and `dev/docs/` directories remain the canonical source.**
  The `gh-pages` branch is a build artifact and should never be edited directly.
- **Navigation is explicit** in `mkdocs.yml`. Adding a new Markdown file
  requires updating the nav in `mkdocs.yml`. This is intentional — it prevents
  orphaned pages and gives control over ordering.
- **The `site/` directory** is git-ignored (added to `.gitignore`). It is only
  used for local preview; deployment goes directly to the `gh-pages` branch.