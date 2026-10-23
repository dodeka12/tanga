# Phase 6 — Docs + changelog

## Goal

Document the layer contract and update the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` (if needed)
- New: `docs/changelog/2026/10/16_feat-multi-layer-image-view.md`
- Edit: `docs/changelog/index.md`

## Steps

- [x] **6.1 — Developer docs.**  Update "Image canvas (extension recipe)" and
  "Image background" with the per-layer uniform contract, the canonical
  `images[]` shape, and the `version`/`tile_version` split.

- [x] **6.2 — Branch changelog.**  Create
  `docs/changelog/2026/10/16_feat-multi-layer-image-view.md` with title
  `# Changes since version 2.19.1` (from `tools/last-release.py`) and
  New Features / Breaking Changes bullets (tiled `version` → `tile_version`).

- [x] **6.3 — Index.**  Add the since-relative entry + details link.

## Validation

```
uv run mkdocs build --strict
uv run pytest py/tests/viz -q
uv run ruff check . && uv run ty check
```
