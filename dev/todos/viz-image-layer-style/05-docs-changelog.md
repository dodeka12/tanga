# Phase 5 — Docs + changelog

## Goal

Document the new layer API and record the breaking changes in the branch
changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/10/16_feat-multi-layer-image-view.md` (append to the
  existing branch changelog)
- Edit: `docs/changelog/index.md`

## Steps

- [x] **5.1 — Developer docs.**
  - Update the "Image canvas (extension recipe)" paragraph: replace the
    `set_layer_*` list with the `ImageLayerStyle` contract, `add_layer`
    (returns index), `set_image`/`set_layer`/`set_layer_style`, and the
    `StrEnum` `LayerBlendMode`.

- [x] **5.2 — Branch changelog.**
  - Append New Features / Breaking Changes bullets (style API, `add_image` →
    `add_layer`, granular setters removed, `LayerBlendMode` now `StrEnum`).
  - Title stays `# Changes since version 2.19.1` (re-run `tools/last-release.py`).

- [x] **5.3 — Index.**
  - Update the `docs/changelog/index.md` entry bullets for this branch.

## Validation

```
uv run mkdocs build --strict
uv run pytest py/tests/viz -q
uv run ruff check . && uv run ty check
```
