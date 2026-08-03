# Mike Docs Versioning — Implementation Plan

**Goal:** Replace the current flat `gh-pages` docs deployment with versioned deployments using [`mike`](https://github.com/jimporter/mike), providing clean version numbers in URLs and branch-based preview deploys.

**Status:** Not started

---

## Overview

| Current | Target |
|---|---|
| Docs deployed to `gh-pages` root via `peaceiris/actions-gh-pages` | Docs deployed via `mike` into versioned subdirectories (`v0.2.3-rc1/`, `v0.2.3/`) |
| Version resolved via `importlib.metadata` (dirty hatch-vcs dev string) | Version passed explicitly from `version-bump` job output (clean tag) |
| `docs-deploy` runs in parallel with version bump | `docs-deploy` runs after `push-tag` (`needs: push-tag`) |
| No branch-based preview | `workflow_dispatch` to deploy docs from any branch under `dev-<branch>/` alias |
| Promote only publishes PyPI | Promote also deploys stable docs with `latest` alias |

**Final URL structure:**

| Version | URL |
|---|---|
| Latest stable (redirect) | `https://dodeka12.github.io/tanga/` → `/latest/` |
| RC versions | `https://dodeka12.github.io/tanga/v0.2.3-rc1/` |
| Stable releases | `https://dodeka12.github.io/tanga/v0.2.3/` |
| Branch previews | `https://dodeka12.github.io/tanga/dev-my-feature/` |

---

## Step 1: Add `mike` to dev dependencies

**File:** `pyproject.toml`

Add `"mike>=2.0"` to `[dependency-groups].dev`:

```diff
 dev = [
     "mkdocs-material>=9.7.7",
+    "mike>=2.0",
     "pre-commit>=4.3",
```

**Why `>=2.0`:** Mike 2.x is the current stable major version with full support for MkDocs Material and the version selector dropdown.

---

## Step 2: Refactor `cd.yml` — `docs-deploy` job

**File:** `.github/workflows/cd.yml`

Replace the current `docs-deploy` job entirely. Changes:

### 2a. Make `docs-deploy` depend on `push-tag`

`docs-deploy` currently runs independently (no `needs`). It must run **after** the tag is pushed so mike can resolve the version properly.

```yaml
docs-deploy:
    name: Build & deploy versioned docs
    needs: push-tag
    if: needs.push-tag.result == 'success'
```

### 2b. Fetch tags and configure git

Mike needs access to git history and the ability to push to `gh-pages`:

```yaml
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          fetch-tags: true

      - name: Configure git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
```

### 2c. Keep the uv/install steps

```yaml
      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install Python toolchain
        run: uv sync --group dev
```

### 2d. Fetch the just-pushed tag

The tag may not be in the initial checkout (it was pushed by the `push-tag` job). Fetch it explicitly:

```yaml
      - name: Fetch pushed tag
        run: git fetch origin tag ${{ needs.version-bump.outputs.tag }}
```

### 2e. Deploy with mike

Replace the `Build MkDocs` + `Deploy to GitHub Pages` steps with:

```yaml
      - name: Deploy docs with mike
        env:
          TAG: ${{ needs.version-bump.outputs.tag }}
        run: |
          export TANGA_VERSION="$TAG"
          mike deploy --push "$TAG"

      - name: Set latest as default alias
        run: |
          mike set-default --push latest
```

**Explanation:**
- `TANGA_VERSION="$TAG"` — read by `docs/_hooks/inject_version.py` to set the banner version (e.g., "TanGA Documentation v0.2.3-rc1")
- `mike deploy --push "$TAG"` — builds docs with `mkdocs build` and pushes to `gh-pages` under `v0.2.3-rc1/`
- `mike set-default --push latest` — ensures `/tanga/` redirects to the `latest` alias. If `latest` already exists, this is a no-op (safe to run every deploy).

### 2f. Complete replacement job

The full `docs-deploy` job should be:

```yaml
  docs-deploy:
    name: Build & deploy versioned docs
    needs: push-tag
    if: needs.push-tag.result == 'success'
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          fetch-tags: true

      - name: Configure git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install Python toolchain
        run: uv sync --group dev

      - name: Fetch pushed tag
        run: git fetch origin tag ${{ needs.version-bump.outputs.tag }}

      - name: Deploy docs with mike
        env:
          TAG: ${{ needs.version-bump.outputs.tag }}
        run: |
          export TANGA_VERSION="$TAG"
          mike deploy --push "$TAG"

      - name: Set latest as default alias
        run: |
          mike set-default --push latest
```

**Removed:** `peaceiris/actions-gh-pages@v4` step — mike manages `gh-pages` natively.

---

## Step 3: Create `docs-preview.yml` — branch-based preview

**File:** `.github/workflows/docs-preview.yml` (NEW)

This enables deploying docs from any branch for pre-merge testing.

```yaml
name: Docs Preview

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy-preview:
    name: Deploy branch docs preview
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Configure git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install Python toolchain
        run: uv sync --group dev

      - name: Deploy preview docs
        env:
          SAFE_ALIAS: dev-${{ github.ref_name }}
        run: |
          # Sanitize branch name: replace / with - for safe URL paths
          ALIAS=$(echo "$SAFE_ALIAS" | tr '/' '-')
          export TANGA_VERSION="$ALIAS"
          mike deploy --push --alias "$ALIAS" "$ALIAS"

      - name: Print preview URL
        run: |
          ALIAS=$(echo "dev-${{ github.ref_name }}" | tr '/' '-')
          echo ""
          echo "📄 Docs preview deployed!"
          echo "   https://dodeka12.github.io/tanga/$ALIAS/"
          echo ""
```

**Usage:** Go to GitHub → Actions → "Docs Preview" → "Run workflow" → select branch → Run.

**Note:** Preview versions accumulate on `gh-pages`. Periodically clean old previews with:
```bash
mike delete dev-old-branch
```

---

## Step 4: Add `docs-stable` job to `promote.yml`

**File:** `.github/workflows/promote.yml`

Add a new job after `publish-stable` to deploy the stable version docs with the `latest` alias.

```yaml
  docs-stable:
    name: Deploy stable docs
    needs: [promote, publish-stable]
    if: success()
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          fetch-tags: true

      - name: Configure git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install Python toolchain
        run: uv sync --group dev

      - name: Deploy stable docs
        env:
          VERSION: ${{ needs.promote.outputs.version }}
        run: |
          export TANGA_VERSION="$VERSION"
          mike deploy --push --update-aliases "$VERSION" latest

      - name: Print stable docs URL
        run: |
          echo ""
          echo "📄 Stable docs deployed!"
          echo "   https://dodeka12.github.io/tanga/${{ needs.promote.outputs.version }}/"
          echo ""
```

**Explanation:**
- `--update-aliases latest` — moves the `latest` alias from the previous version to this new stable version
- The RC version remains available at its original URL (e.g., `v0.2.3-rc1/`)

---

## Step 5: Update `mkdocs-publishing.md` — mike quick reference

**File:** `docs/dev/workflows/mkdocs-publishing.md`

Rewrite to serve as a concise mike quick reference covering:
1. What mike is and how versioned docs work
2. Local preview with `mkdocs serve` (unchanged)
3. Local deploy with `mike deploy` (replaces `mkdocs gh-deploy`)
4. Managing versions locally (`mike list`, `mike delete`, `mike set-default`)
5. Troubleshooting mike-specific issues

## Step 6: Create `docs-publishing-workflows.md` — CI/CD docs workflow guide

**File:** `docs/dev/workflows/docs-publishing-workflows.md` (NEW)

Create a new developer documentation page explaining:

### 6a. GitHub workflow automation (how CI publishes docs)

Describe each workflow's role in the docs pipeline:

| Workflow | Trigger | What it does |
|---|---|---|
| `cd.yml` → `docs-deploy` | Push to `main` | Determines the RC tag (from `version-bump`), builds docs with `mike deploy`, and pushes to `gh-pages` under `vX.Y.Z-rcN/`. Sets `latest` alias on first deploy. |
| `promote.yml` → `docs-stable` | Manual (`workflow_dispatch`) | Creates a stable version from the latest RC, deploys with `mike deploy --update-aliases latest`, moving the `latest` alias to the stable version. |
| `docs-preview.yml` | Manual (`workflow_dispatch`) | Builds docs from any selected branch and deploys under a `dev-<branch>/` alias for pre-merge testing. |

Include a diagram or ASCII flow showing:
```
push to main → version-bump (dry-run) → publish-wheels → push-tag → docs-deploy (mike)
                                                                        └── mike deploy vX.Y.Z-rcN
                                                        promote.yml (manual)
                                                                        └── mike deploy vX.Y.Z latest
                                                        docs-preview.yml (manual)
                                                                        └── mike deploy dev-<branch>
```

Also describe:
- The `TANGA_VERSION` env var and how `docs/_hooks/inject_version.py` uses it
- How `gh-pages` branch is structured by mike (versions.json, subdirectories per version, aliases)
- How the version selector dropdown works (injected by mike/Material theme)

### 6b. Manual docs publishing from any branch

Step-by-step guide for publishing docs manually from a local branch for testing:

```bash
# 1. Ensure dev dependencies are installed
uv sync --group dev

# 2. Set a version/alias for the branch (sanitize branch name)
#    Replace / with - for safe URL paths
export TANGA_VERSION="dev-$(git branch --show-current | tr '/' '-')"

# 3. Deploy with mike (builds + pushes to gh-pages)
mike deploy --push --alias "$TANGA_VERSION" "$TANGA_VERSION"

# 4. Preview URL
echo "https://dodeka12.github.io/tanga/$TANGA_VERSION/"

# 5. After testing, clean up (optional)
mike delete "$TANGA_VERSION" --push
```

Also document how to:
- View all deployed versions: `mike list`
- Set a different default: `mike set-default --push <version>`
- Delete an old preview: `mike delete dev-old-feature --push`
- Rebuild an existing version locally for testing:
  ```bash
  mike deploy --update-aliases v0.2.3-rc1  # rebuild existing, keep its aliases
  ```

### 6c. Add page to `mkdocs.yml` nav

Add the new page to the Workflows section under Developer Documentation:

```yaml
nav:
  - Developer Documentation:
    - Overview: dev/index.md
    ...
    - Workflows:
      - Build, test & navigation: dev/workflows/build-test-and-navigation.md
      ...
      - MkDocs publishing: dev/workflows/mkdocs-publishing.md
      - Docs publishing workflows: dev/workflows/docs-publishing-workflows.md   # NEW
```

---

## Step 7: One-time manual setup (after merge)

After merging these changes, run once manually (or on first `cd.yml` trigger):

```bash
# Set the default version alias (if not already set by CI)
mike set-default --push latest
```

Verify:
1. Visit `https://dodeka12.github.io/tanga/` — should redirect to `latest/`
2. Version selector dropdown appears in the header
3. RC tags deploy correctly: `https://dodeka12.github.io/tanga/v0.2.3-rc1/`
4. Branch previews work: manually trigger "Docs Preview" workflow

---

## Files Changed Summary

| File | Change Type | Description |
|---|---|---|
| `pyproject.toml` | Edit | Add `mike>=2.0` to dev dependencies |
| `.github/workflows/cd.yml` | Edit | Refactor `docs-deploy` job to use mike, add `needs: push-tag` |
| `.github/workflows/promote.yml` | Edit | Add `docs-stable` job for stable version docs |
| `.github/workflows/docs-preview.yml` | **New** | `workflow_dispatch` for branch-based docs preview |
| `docs/dev/workflows/mkdocs-publishing.md` | Edit | Rewrite to serve as mike quick reference |
| `docs/dev/workflows/docs-publishing-workflows.md` | **New** | CI/CD workflow automation guide + manual branch publishing |
| `mkdocs.yml` | Edit | Add `docs-publishing-workflows.md` to nav under Developer Docs → Workflows |
| `docs/_hooks/inject_version.py` | No change | Already reads `TANGA_VERSION` env var |
| `tools/version-tag.sh` | No change | Tag naming unchanged, mike consumes the same tags |

---

## Acceptance Criteria

- [ ] `mike` listed in `pyproject.toml` dev dependencies
- [ ] On push to `main`, `docs-deploy` runs **after** `push-tag` and deploys versioned docs (e.g., `v0.2.3-rc1/`)
- [ ] Docs banner shows clean version (e.g., "TanGA Documentation v0.2.3-rc1") not a hatch-vcs dev string
- [ ] `promote.yml` deploys stable docs with `latest` alias pointing to the stable version
- [ ] "Docs Preview" workflow can be triggered manually from any branch
- [ ] `https://dodeka12.github.io/tanga/` shows the version selector dropdown