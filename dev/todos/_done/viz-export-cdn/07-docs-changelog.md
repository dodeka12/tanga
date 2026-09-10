# Phase 7 — Docs + changelog (+ NOTICE)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the delivery modes, update the export-packing architecture note, add
third-party attribution, and write the branch changelog.

## Files

- Edit: `docs/py/examples/viz/export/html_export.md`
- Edit: `docs/dev/architecture/viz-theme-system.md` (Export packing)
- Edit: `NOTICE` (MIT attribution for three/marked/katex/html2canvas)
- New: `docs/changelog/2026-09-07_feat-viz-export-cdn.md`
- Edit: `docs/changelog/index.md`

## Steps

- [x] **7.1 — Example docs**
  - Update `html_export.md` to document `delivery`/`delivery_ref`, add the
    `export_delivery.py` example (per `dev/workflows/example-docs.md`), then
    regenerate via `tools/generate-example-docs.py`.
- [x] **7.2 — Architecture doc**
  - In `viz-theme-system.md` "Export packing", describe the library/adapter
    split, the `window.__tanga` bridge, the three delivery modes, and the
    vendored offline assets.
- [x] **7.3 — NOTICE**
  - Add MIT attribution for the vendored Three.js, marked, KaTeX, and
    html2canvas, including their pinned versions.
- [x] **7.4 — Changelog**
  - Follow `dev/workflows/changelog.md`: title from `tools/last-release.py`, a
    `## New Features` bullet for CDN + offline delivery, and the index entry.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`
