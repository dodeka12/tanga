# Setup GitHub Actions CI/CD Pipeline

## Overview

Replace the manual/local-only workflows (post-merge hook for versioning, manual `mkdocs gh-deploy`) with automated GitHub Actions pipelines.

----

## 1. Branch Protection (Manual GitHub Settings)

Go to **https://github.com/dodeka12/tanga/settings/branches** and add a branch protection rule:

| Setting | Value |
|---|---|
| **Branch name pattern** | `main` |
| **Require a pull request before merging** | ✓ |
| **Require status checks to pass before merging** | ✓ (select `CI` after first run) |
| **Require branches to be up to date before merging** | ✓ |

---

## 2. Workflow Files to Create

| File | Purpose | Triggers |
|---|---|---|
| `.github/workflows/ci.yml` | Run pytest + C++ tests | `pull_request` → `main`, `push` → `main` |
| `.github/workflows/cd.yml` | Version bump + mkdocs deploy | `push` → `main` (auto), `workflow_dispatch` (manual, docs only) |

### `ci.yml` — Continuous Integration

- **Runner**: `ubuntu-24.04`
- **Steps**:
  1. Checkout with `fetch-depth: 0` (needed for `hatch-vcs` version detection)
  2. Install `uv` package manager
  3. `uv sync --group dev` (installs all deps including pybind11, cmake, ninja, pytest)
  4. Build the C++ extension (hatchling handles pybind11 compilation during `uv sync`)
  5. `uv run pytest` — Python test suite
  6. Build C++ test executables via CMake
  7. Run C++ tests via `ctest`

### `cd.yml` — Continuous Delivery

- **Runner**: `ubuntu-24.04`
- **Permissions**: `contents: write`
- **Jobs**:

  **Job 1: Version bump** (skip on `workflow_dispatch`)
  - Checkout with `fetch-depth: 0` and all tags
  - Configure git user (needed for tag creation)
  - Run `tools/version-tag.sh --push`
  - Creates and pushes semver tag based on Conventional Commits since last tag

  **Job 2: Docs deploy**
  - Checkout
  - `uv sync --group dev`
  - `uv run mkdocs build --strict`
  - Deploy `site/` → `gh-pages` branch using `peaceiris/actions-gh-pages@v4`

---

## 3. Pipeline Flow

```
PR opened/updated → ci.yml runs pytest + C++ tests
                        ↓ (pass)
PR merged to main ────→ ci.yml runs on main
                        ↓ (success)
                  cd.yml triggered:
                    1. version-tag.sh → creates & pushes new tag
                    2. mkdocs build --strict → deploy to gh-pages
```

Manual docs deploy: trigger `cd.yml` via "Run workflow" button (skips version bump).

---

## 4. Key Decisions

- **C++ tests included**: Build via CMake and run with `ctest` in ci.yml
- **Version bump**: Only on merge to `main`, not on `workflow_dispatch`
- **Docs deploy**: On every merge to `main` AND available manually via `workflow_dispatch`
- **Branch protection**: `main` requires PR + passing CI before merge
- **Tag pushes do not re-trigger workflows**: CI trigger restricted to branches; CD trigger also restricted to branches (tags excluded)

---

## 5. Post-Implementation

- [ ] Push workflow files to `main`
- [ ] Create a test PR to verify CI runs
- [ ] Go to branch protection settings and select the CI status check as required
- [ ] Merge test PR and verify CD: version tag created + docs deployed
- [ ] Verify GitHub Pages at https://dodeka12.github.io/tanga/
- [ ] Update `dev/docs/workflows/` documentation to reflect automated CI/CD