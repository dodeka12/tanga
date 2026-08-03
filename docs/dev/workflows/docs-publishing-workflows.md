# Docs Publishing Workflows

This page describes the GitHub Actions workflows that automate TanGA
documentation publishing, and how to manually publish docs from any branch
for testing.

## CI/CD Pipeline Overview

```
push to main → version-bump (dry-run) → publish-wheels → push-tag → docs-deploy (mike)
                                                                        └── mike deploy vX.Y.Z-rcN
                                                        promote.yml (manual)
                                                                        └── mike deploy vX.Y.Z latest
                                                        docs-preview.yml (manual)
                                                                        └── mike deploy dev-<branch>
```

---

## Workflow: `cd.yml` → `docs-deploy`

**Trigger:** Push to `main`

This job runs as part of the continuous delivery pipeline. It only executes
after the `push-tag` job successfully creates and pushes an RC tag.

**Steps:**

1. **Checkout** — full git history with all tags (`fetch-depth: 0`, `fetch-tags: true`)
2. **Configure git** — sets bot identity for `gh-pages` pushes
3. **Install toolchain** — `uv sync --group dev` (includes mike)
4. **Fetch pushed tag** — `git fetch origin tag <tag>` because the tag was
   pushed by a previous job, not present in the initial checkout
5. **Deploy with mike** — sets `TANGA_VERSION=<tag>` and runs
   `mike deploy --push "$TAG"`. This builds the site with MkDocs and pushes
   the output to `gh-pages` under `vX.Y.Z-rcN/`.
   The `TANGA_VERSION` env var is read by `docs/_hooks/inject_version.py` to
   display the clean version in the site banner (e.g.
   "TanGA Documentation v0.2.3-rc1")
6. **Set default alias** — `mike set-default --push latest` ensures the root
   URL redirects to the `latest` alias

---

## Workflow: `promote.yml` → `docs-stable`

**Trigger:** Manual (`workflow_dispatch`)

When a release candidate is promoted to a stable release, this job deploys
the stable version of the docs and moves the `latest` alias.

**Steps:**

1. **Checkout** — full history with tags
2. **Configure git** — bot identity
3. **Install toolchain** — `uv sync --group dev`
4. **Deploy stable docs** — `mike deploy --push --update-aliases "$VERSION" latest`
   where `$VERSION` is the clean tag from the `promote` job (e.g. `v0.2.3`).
   The `--update-aliases` flag moves the `latest` alias from the previous
   version to this new stable version. The RC version remains available at
   its original URL.

**Note:** This job depends on both `promote` (tag creation) and
`publish-stable` (PyPI publish) completing successfully.

---

## Workflow: `docs-preview.yml`

**Trigger:** Manual (`workflow_dispatch`)

Deploys docs from any branch for pre-merge testing. The branch name is
sanitised (`/` replaced with `-`) and used as a `dev-<branch>` alias.

**Steps:**

1. **Checkout** — full history of the selected branch
2. **Configure git** — bot identity
3. **Install toolchain** — `uv sync --group dev`
4. **Deploy preview** — `mike deploy --push --alias "dev-<branch>" "dev-<branch>"`
5. **Print URL** — outputs the preview URL for easy access

**Usage:** Go to GitHub → Actions → "Docs Preview" → "Run workflow" →
select branch → Run.

**Cleanup:** Preview versions accumulate on `gh-pages`. Delete old ones with:
```bash
mike delete dev-old-feature --push
```

---

## Manual Docs Publishing from Any Branch

You can publish docs from your local machine to `gh-pages` without waiting
for CI. This is useful for testing documentation changes before merging.

### Prerequisites

- Dev dependencies installed: `uv sync --group dev`
- Push access to `dodeka12/tanga` on GitHub

### Publish a branch preview

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

### Publish a tagged version

```bash
# Deploy a specific version tag
mike deploy --push v0.2.3-rc1

# Deploy and make it the default
mike deploy --push --update-aliases v0.2.3 latest
mike set-default --push latest
```

### Managing published versions

```bash
# View all deployed versions and their aliases
mike list

# Set a different default version
mike set-default --push v0.2.2

# Delete a version
mike delete dev-old-feature --push

# Rebuild an existing version locally (for testing without pushing)
mike deploy --update-aliases v0.2.3-rc1   # --push omitted = local only
mike serve -a                              # serve all versions locally
```

---

## How Version Resolution Works

### The `TANGA_VERSION` env var

`docs/_hooks/inject_version.py` is an MkDocs hook that runs at build time:

```python
def on_config(config):
    version = os.environ.get("TANGA_VERSION") or _resolve_version()
    config.extra["version"] = version
    config.site_name = f"{config.site_name} v{version}"
```

Priority:
1. `TANGA_VERSION` env var (set by CI or manually)
2. `importlib.metadata.version("tanga-py")` (fallback for local dev)
3. `"dev"` (last resort)

In CI, the version comes from the `version-bump` job output, which runs
`tools/version-tag.sh --rc --dry-run` to determine the next RC tag name
(e.g. `v0.2.3-rc1`). This produces a clean semantic version — no git-hash
suffixes.

### The version selector dropdown

Mike works with the Material for MkDocs theme to inject a version selector
in the page header. It reads `versions.json` from the `gh-pages` branch,
which mike maintains automatically. Users can switch between any published
version directly from the dropdown.

### gh-pages branch structure

```
gh-pages/
├── versions.json          # {"v0.2.3-rc1": {"aliases": ["rc"]}, "v0.2.3": {"aliases": ["latest"]}}
├── v0.2.2/
├── v0.2.3-rc1/
├── v0.2.3/
├── dev-my-feature/
└── index.html             # Redirect to the default version (latest)
```

---

## Files Involved

| File | Role |
|---|---|
| `.github/workflows/cd.yml` | RC docs deploy on push to main |
| `.github/workflows/promote.yml` | Stable docs deploy on manual promotion |
| `.github/workflows/docs-preview.yml` | Branch preview deploy on manual trigger |
| `docs/dev/workflows/mkdocs-publishing.md` | Mike quick reference and local usage |
| `docs/_hooks/inject_version.py` | Reads `TANGA_VERSION` to set banner version |
| `mkdocs.yml` | MkDocs configuration (unchanged, mike works transparently) |
| `tools/version-tag.sh` | Determines next RC/stable tag name |
| `pyproject.toml` | Dev dependency group includes `mike>=2.0` |