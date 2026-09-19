# Phase 8 — Enforcement (pre-commit + CI) + docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make the ty + ruff ANN gates global and permanent: add them to pre-commit and
CI, confirm the whole in-scope tree is clean, and document the change.

## Files

- Edit: `pyproject.toml` — add `extend-select = ["ANN"]` + `per-file-ignores`.
- Edit: `.pre-commit-config.yaml` — add a `ty` hook.
- Edit: `.github/workflows/ci.yml` — add a `ty check` step (and `--select ANN`
  to the ruff step if not already covered).
- Edit: `docs/changelog/<branch file>` (append; per `dev/workflows/changelog.md`).

## Steps

- [x] **8.1 — Enable the ruff ANN gate in `pyproject.toml`**
  - Add to `[tool.ruff.lint]`: `extend-select = ["ANN"]` and
    `ignore = ["ANN401"]` (keep `unfixable = ["F401"]`).
  - Add `[tool.ruff.lint.per-file-ignores]` with `"py/tests/**" = ["ANN"]`
    (deferred scope).  `main.py` and `tools/` are already clean.
- [x] **8.2 — Add a `ty` pre-commit hook (gating)**
  - In `.pre-commit-config.yaml`, add a `repo: local` hook
    (`id: ty`, `name: ty check`, `entry: uv run ty check`,
    `language: system`, `pass_filenames: false`), placed after the ruff hooks.
    A non-zero exit fails the hook — every diagnostic must be fixed or
    suppressed.
- [x] **8.3 — Wire ty into CI (gating)**
  - In `.github/workflows/ci.yml`, add a `uv run ty check` step to the lint job
    (and confirm ruff already runs with `ANN` via the `pyproject.toml` change).
    The step is **gating**: a non-zero `ty check` exit fails CI.
- [x] **8.4 — Changelog** (per `dev/workflows/changelog.md`)
  - Append a `## Refactor` (or `## New Features`) bullet to the branch changelog:
    "**Type-hint coverage + ty enforcement** — `py/pytanga` and `py/examples` are
    fully type-annotated; `ty` (correctness) and ruff `ANN` (coverage) enforce it
    in pre-commit and CI (`py/tests` deferred)."
  - Title uses `uv run python tools/last-release.py`; do not hard-code a version.
- [x] **8.5 — Full regression**
  - `uv run pre-commit run --all-files`
  - `uv run ty check .` and `uv run ruff check .` → clean.
  - `uv run pytest -q`.

## Validation

`uv run pre-commit run --all-files && uv run ty check . && uv run ruff check . && uv run pytest -q`

## Notes

- `ty check .` only checks `[tool.ty.src] include` dirs (`py/pytanga` +
  `py/examples`); `ruff check .` covers everything with `ANN` relaxed on
  `py/tests/**`.
- The changelog is the **branch** file (append, don't create a new one); the
  PR-time hash rename is per `dev/workflows/pull-request.md`.
- If the work surfaced any `# ty: ignore[rule]` suppressions, list them in the
  changelog bullet or a follow-up note so they are intentional and tracked.
