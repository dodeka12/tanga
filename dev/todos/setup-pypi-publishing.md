# Setup PyPI Publishing Pipeline

## Overview

Automated wheel building and publishing to PyPI and Test PyPI, triggered by git tags.
Uses **OIDC Trusted Publishing** (no long-lived API tokens).

---

## 1. Pipeline Flow

```
Merge PR to main
     │
     ▼
 cd.yml  ─────► version-tag.sh --rc  →  creates v1.2.3-rc1
                     │                         │
                     ▼                         ▼
               mkdocs deploy           tag push event
                                             │
                                             ▼
                                       publish.yml
                                     ┌─ -rc detected ──► builds wheels ──► Test PyPI
                                     │
                                     │  (User tests the RC on Test PyPI:
                                     │    pip install -i https://test.pypi.org/simple/ tanga-py)
                                     │
                                     │  (User manually triggers promote workflow)
                                     │
                                     ▼
                                  promote.yml (workflow_dispatch)
                               reads latest v*-rc* tag
                               strips -rcN suffix
                               creates & pushes v1.2.3
                                             │
                                             ▼
                                       publish.yml
     (clean tag detected) ─► builds pure + manylinux + macos wheels ─► Real PyPI
```

---

## 2. Git Tag Convention

| Tag Pattern | Meaning | PyPI Target |
|---|---|---|
| `v1.2.3-rc1` | Release candidate 1 for v1.2.3 | Test PyPI |
| `v1.2.3-rc2` | Release candidate 2 for v1.2.3 | Test PyPI |
| `v1.2.3` | Stable release (promoted from RC) | Real PyPI |

`version-tag.sh --rc` auto-increments the RC number. If `v1.2.3-rc1` exists,
the next merge creates `v1.2.3-rc2`. When no RC exists for the current base version,
it creates `vX.Y.Z-rc1`.

---

## 3. Wheel Build Matrix

| Job | Runner | Output Tag |
|-----|--------|------------|
| `build-pure` | `ubuntu-24.04` | `py3-none-any` |
| `build-platform` | `quay.io/pypa/manylinux_2_28_x86_64` (container) | `cp312-cp312-manylinux_2_28_x86_64` |
| `build-platform` | `windows-latest` | `cp312-cp312-win_amd64` |
| `build-platform` | `macos-13` (Intel) | `cp312-cp312-macosx_13_0_x86_64` |
| `build-platform` | `macos-14` (Apple Silicon) | `cp312-cp312-macosx_14_0_arm64` |

**Windows** — supported via `windows-latest` runner.  The JIT compilation
pipeline uses MSVC (`cl.exe`) on Windows.  Precompiled `.pyd` files are
bundled into `win_amd64` wheels.

The Linux build runs inside the `manylinux_2_28` Docker container to ensure the wheel
is installable on any Linux with glibc ≥ 2.28 (Ubuntu 20.04+, RHEL 8+, etc.).

---

## 4. Files Changed / Created

| File | Action | Purpose |
|------|--------|---------|
| `tools/version-tag.sh` | Modify | Add `--rc` flag for release candidate tags |
| `.github/workflows/cd.yml` | Modify | Pass `--rc` to version-tag.sh |
| `.github/workflows/publish.yml` | Create | Multi-platform wheel build + PyPI publish (OIDC) |
| `.github/workflows/promote.yml` | Create | `workflow_dispatch`: promote RC → stable release |

---

## 5. Workflow Details

### 5.1 `cd.yml` (modified)

**Change:** `./tools/version-tag.sh --push` → `./tools/version-tag.sh --rc --push`

This means every merge to `main` now creates a **release candidate** tag
instead of a stable release tag. Stable releases are promoted manually via
the `promote.yml` workflow.

### 5.2 `publish.yml` (new)

**Trigger:** `push: tags: ['v*']`

**Jobs:**

#### `build-pure`
- **Runner:** `ubuntu-24.04`
- **Steps:**
  1. Checkout (`fetch-depth: 0` for hatch-vcs)
  2. Install uv (`astral-sh/setup-uv@v5`)
  3. `uv sync --group dev`
  4. `uv run python tools/clean-precompiled.py`
  5. `uv build --wheel`
  6. Upload wheel artifact (`actions/upload-artifact@v4`)

#### `build-platform`
- **Strategy matrix:**
  | Runner | Container | Tag suffix |
  |--------|-----------|-------------|
  | `ubuntu-24.04` | `quay.io/pypa/manylinux_2_28_x86_64` | `manylinux_2_28_x86_64` |
  | `macos-13` | none | `macosx_x86_64` |
  | `macos-14` | none | `macosx_arm64` |

- **Steps (Linux — inside manylinux container):**
  1. Checkout
  2. Install uv inside container
  3. `uv sync --group dev`
  4. `uv run python tools/build-precompiled.py`
  5. `uv build --wheel`
  6. `uv run python tools/fix-wheel-tag.py`
  7. `auditwheel repair` (ensures manylinux compliance)
  8. Upload wheel artifact

- **Steps (macOS):**
  1. Checkout (`fetch-depth: 0`)
  2. Install uv
  3. `uv sync --group dev`
  4. `uv run python tools/build-precompiled.py`
  5. `uv run bash tools/build-precompiled-wheel.sh` (build + fix tag)
  6. Upload wheel artifact

#### `publish`
- **Needs:** `build-pure`, `build-platform`
- **Permissions:** `id-token: write`, `contents: read`
- **Steps:**
  1. Download all artifacts (`actions/download-artifact@v4`)
  2. Determine target:
     ```
     if tag contains "-rc" → test.pypi.org
     else                → pypi.org
     ```
  3. Publish via `pypa/gh-action-pypi-publish@v1.xx`
     - **No `password` or `token` input** — OIDC handles authentication
     - Set `repository-url` based on target

### 5.3 `promote.yml` (new)

**Trigger:** `workflow_dispatch` (manual "Run workflow" button in GitHub Actions tab)

**Permissions:** `contents: write`

**Steps:**
1. Checkout (`fetch-depth: 0`, `fetch-tags: true`)
2. Find latest RC tag:
   ```bash
   RC_TAG=$(git tag -l 'v*-rc*' --sort=-v:refname | head -1)
   ```
3. Strip `-rc*` suffix:
   ```bash
   CLEAN_TAG=$(echo "$RC_TAG" | sed 's/-rc.*//')
   ```
4. Configure git user
5. Create and push clean tag:
   ```bash
   git tag -a "$CLEAN_TAG" -m "Release $CLEAN_TAG"
   git push origin "$CLEAN_TAG"
   ```

The push of the clean tag triggers `publish.yml`, which detects it's not an RC
and publishes to real PyPI.

---

## 6. PyPI Setup (One-Time Manual Steps)

### 6.1 Create Accounts

- [pypi.org](https://pypi.org) — real package index
- [test.pypi.org](https://test.pypi.org) — test/ staging index

Use the same username on both for consistency.

### 6.2 Configure OIDC Trusted Publishing

This is the modern, token-free method. Instead of generating a long-lived
API token and storing it as a GitHub secret, you tell PyPI to trust GitHub
Actions workflows from your repository.

#### On pypi.org:

1. Go to **https://pypi.org/manage/project/tanga-py/settings/publishing/**
   (If the project doesn't exist yet, create it first via **Publish a package**.)
2. Under **Trusted Publisher Management**, click **Add a new trusted publisher**
3. Fill in:
   | Field | Value |
   |-------|-------|
   | Owner | `dodeka12` |
   | Repository name | `tanga` |
   | Workflow name | `publish.yml` |
   | Environment name | (leave empty) |
4. Click **Add**

#### On test.pypi.org:

1. Go to **https://test.pypi.org/manage/project/tanga-py/settings/publishing/**
2. Click **Add a new trusted publisher**
3. Fill in the same values:
   | Field | Value |
   |-------|-------|
   | Owner | `dodeka12` |
   | Repository name | `tanga` |
   | Workflow name | `publish.yml` |
   | Environment name | `testpypi` |
4. Click **Add**

### 6.3 Why OIDC Instead of API Tokens?

| Aspect | API Token | OIDC Trusted Publishing |
|--------|-----------|------------------------|
| Setup | Generate token, store as GitHub secret | One-time config on PyPI |
| Lifetime | Long-lived (must rotate manually) | Short-lived (per-run, minutes) |
| Security | Token leak = anyone can publish | Impossible to leak — tied to repo identity |
| Rotation | Manual | Automatic |

---

## 7. Post-Implementation Checklist

- [ ] Modify `tools/version-tag.sh` — add `--rc` flag
- [ ] Modify `.github/workflows/cd.yml` — pass `--rc` to version-tag.sh
- [ ] Create `.github/workflows/publish.yml`
- [ ] Create `.github/workflows/promote.yml`
- [ ] Create PyPI account on pypi.org
- [ ] Create PyPI account on test.pypi.org
- [ ] Configure OIDC Trusted Publisher on pypi.org
- [ ] Configure OIDC Trusted Publisher on test.pypi.org
- [ ] Merge a test PR to `main` → verify RC tag creation + Test PyPI publish
- [ ] Install from Test PyPI to verify: `pip install -i https://test.pypi.org/simple/ tanga-py`
- [ ] Manually trigger `promote.yml` → verify stable tag creation + real PyPI publish
- [ ] Install from real PyPI to verify: `pip install tanga-py`