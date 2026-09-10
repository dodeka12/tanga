# Phase 6 — CI drift checks + release integration

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make CI fail when any committed artifact (CDN bundle, offline bundle, vendored
third-party assets) drifts from its source, and ensure the publish/CD workflow
verifies everything before a tag is cut so jsDelivr always serves a matching
bundle.

## Files

- Edit: `.github/workflows/ci.yml`
- Edit: `.github/workflows/cd.yml` (or `publish.yml`)
- Edit: `.pre-commit-config.yaml`

## Steps

- [x] **6.1 — Drift gates in CI + pre-commit**
  - Add a `.pre-commit-config.yaml` hook running
    `uv run python tools/build-viewer-js.py --check` and
    `uv run python tools/vendor-third-party.py --check`, so a stale bundle or
    vendored asset fails the commit as soon as a dependent file changes.
  - Add the same two `--check` steps to `.github/workflows/ci.yml` (the
    fingerprint-based gate is the source of truth).
- [x] **6.2 — Verify before tag in `cd.yml`**
  - In the version-bump/push-tag flow, run both `--check` commands so the tagged
    commit always contains matching CDN + offline bundles and vendored assets.
  - Do not commit generated output in CI; require the committed files to be
    current.

## Validation

Review the workflow YAML (e.g. `uv run python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('.github/workflows/ci.yml').read_text())"`) and, if possible, trigger `ci.yml` on the branch.

## Notes

- Keeps a single source of truth (committed artifacts) and avoids a
  generate-and-commit step racing the tag.
