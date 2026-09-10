# Phase 5 — CI + pre-commit

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Remove the vendored-asset drift gates and add an offline smoke job.

## Files

- Edit: `.pre-commit-config.yaml`
- Edit: `.github/workflows/ci.yml`
- Edit: `.github/workflows/cd.yml`

## Steps

- [x] **5.1 — Drop vendored drift gates**
  - Remove the `vendored-assets-drift` pre-commit hook and the
    `vendor-third-party.py --check` CI/cd steps.
- [x] **5.2 — Offline smoke job**
  - Add a CI job (Ubuntu) that installs esbuild, then runs
    `render_snapshot(..., delivery="offline")` via a small script, and
    `tools/build-viewer-js.py --check`.

## Validation

`uv run python -c "import yaml; [yaml.safe_load(open(p)) for p in ['.github/workflows/ci.yml','.github/workflows/cd.yml','.pre-commit-config.yaml']]; print('yaml ok')"`

## Notes

- The CDN-bundle drift gate (`build-viewer-js.py --check`) stays.
