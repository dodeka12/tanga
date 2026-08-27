# Phase 8 — Docs + changelog

## Goal

Document the new controls, icons, and tooltips, and record the change per
`dev/workflows/changelog.md`.

## Steps

- [x] **8.1 — Docs `docs/py/viz/visualizerapp/controls.md`**
  - Add `add_text_field`/`add_text_area`/`add_color_picker`/`add_checkbox`
    sections (parameter tables + handler signatures).
  - Extend `add_button` with `icon`/`icon_only`.
  - Add an "Icons" section: `family:name` grammar, `EIconMaterial`/`EIconUC`,
    bare-string→material default, online Google Fonts link caveat.
  - Add a "Tooltips" note (native `title`, all controls + group title bar).

- [x] **8.2 — Changelog `docs/changelog/2026-08-27_feat-more-controls.md`**
  - Title `# Changes since version 1.7.0` (from `tools/last-release.py`).
  - New Features bullets: four new controls; button icons + icon_only;
    per-control tooltips; group title-bar icon/tooltip.

- [x] **8.3 — Validate**
  - `uv run mkdocs build --strict` passes (no new warnings).

## Validation

`uv run mkdocs build --strict`

## Notes

- Do **not** predict a release version; the changelog is renamed to its hash
  form at PR time (`dev/workflows/pull-request.md`).
