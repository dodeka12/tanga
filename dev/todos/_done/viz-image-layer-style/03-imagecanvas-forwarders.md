# Phase 3 — `ImageCanvas` forwarders

## Goal

Expose the style-based API on `ImageCanvas`, emit one granular `image_update`
per change, and remove the per-parameter setters.

## Files

- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/tests/viz/test_image_canvas_integration.py`

## Steps

- [x] **3.1 — Forwarders.**
  - `add_layer(image, style=DEFAULT)` (returns the index, then `_sync_image()`),
    `set_image(image, style=DEFAULT)`, `set_layer(index, image, style=DEFAULT)`,
    `set_layer_style(index, style)` (view change → `_push_uniforms` +
    `_resync_node`).

- [x] **3.2 — `_push_uniforms(patch)` + remove granular setters.**
  - Add `_push_uniforms(patch: dict[str, float | int])` sending one
    `image_update`; keep `_resync_node()`.
  - Remove `set_layer_enabled/opacity/blend/value_range/channel` and the
    single-key `_push_uniform` (or fold `_push_uniform` into `_push_uniforms`).

- [x] **3.3 — Tests.**
  - `add_layer` returns index + emits one binary frame; `set_layer_style` emits
    one `image_update` with only the changed keys and no binary bytes; full
    state reflects the style change.

## Validation

```
uv run pytest py/tests/viz/test_image_canvas_integration.py -q
uv run ruff check py/pytanga/viz/_image_view.py
uv run ty check
```
