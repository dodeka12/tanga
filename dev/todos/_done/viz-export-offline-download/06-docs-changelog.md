# Phase 6 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the export-time offline requirement and add the changelog entry.

## Files

- Edit: `py/examples/viz/export/export_delivery.py` (+ regenerate example docs)
- Edit: `docs/dev/architecture/viz-theme-system.md` (Delivery modes)
- Edit: `NOTICE` (note offline bundles libs at export time)
- New: `docs/changelog/2026-09-07_feat-viz-export-cdn.md` (append) or a new entry
- Edit: `docs/changelog/index.md`

## Steps

- [x] **6.1 — Example**
  - Update `export_delivery.py` to note `offline` needs Node + esbuild + internet
    at export time; run `tools/generate-example-docs.py`.
- [x] **6.2 — Architecture doc**
  - Update the "Delivery modes" section: offline downloads + bundles at export
    time and raises if Node/esbuild is missing.
- [x] **6.3 — NOTICE**
  - Adjust the attribution note: three/marked/KaTeX/html2canvas are fetched at
    export time and embedded into the generated HTML.
- [x] **6.4 — Changelog**
  - Update the existing branch changelog entry (or add a follow-up) describing
    the export-time download model.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`
