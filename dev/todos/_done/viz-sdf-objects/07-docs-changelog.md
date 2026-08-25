# Phase 7 — Docs + changelog

## Goal

Document the SDF-object opt-in (API, style class, limitations) and record the
change in the changelog, following the repo conventions.

## Files

- Modify: `docs/py/viz/` — new/updated page for `SdfStyle` + mixing SDF and
  mesh objects (API signature, example, limitations).
- Modify: `docs/changelog/` — new branch changelog (see
  `dev/workflows/changelog.md`) and, at PR time, `docs/changelog/index.md`.
- Modify: `mkdocs.yml` — nav entry for the new docs page.

## Steps

- [x] **7.1 — Docs page**
  - `SdfStyle(color, opacity, soft_shadows, max_steps, bound_padding)` and the
    `Visualizer.add(..., style=SdfStyle(...))` usage.
  - State clearly: per-object CSG only (cross-object CSG unsupported), WebGL2
    required for SDF objects (mesh fallback on WebGL1), mutual shadows deferred.

- [x] **7.2 — Changelog**
  - Appended to the existing branch changelog `docs/changelog/2026-08-22_feat-sdf-viewer.md`
    (per `dev/workflows/changelog.md`: one changelog per branch); title updated to
    `# Changes since version 1.1.0` from `tools/last-release.py`.
  - Create `docs/changelog/YYYY-MM-DD_feat-sdf-objects.md` per
    `dev/workflows/changelog.md` (title `# Changes since version <last-stable-release>`,
    sections `New Features`, `Breaking Changes`, `Refactor` as applicable).
  - Do **not** hand-pick a version; use `uv run python tools/last-release.py`.

- [x] **7.3 — Nav**
  - Add the new page to `mkdocs.yml` and rebuild the site (`uv run mkdocs build`)
    to confirm no broken links.

- [x] **7.4 — Validate**
  - `uv run mkdocs build --strict` (if configured) or `uv run mkdocs build`.
  - Mark the overview README `Status: Done` and move the folder under
    `dev/todos/_done/` after implementation.

## Validation

`uv run mkdocs build` (site builds, no broken internal links) + changelog lint
against `dev/workflows/changelog.md`.

## Notes

- Changelog index entry (`docs/changelog/index.md`) is finalized at PR time
  (hash-renamed file), per `dev/workflows/pull-request.md`.
