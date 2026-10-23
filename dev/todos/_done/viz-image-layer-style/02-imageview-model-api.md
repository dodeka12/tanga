# Phase 2 — `ImageView` model API

## Goal

Add the style-based layer API on the low-level `ImageView`: `add_layer` (returns
the new index), `set_image(style)`, `set_layer`, `set_layer_style`, backed by
full-apply and partial-merge helpers.

## Files

- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/tests/viz/test_image_view.py`

## Steps

- [x] **2.1 — Rename `add_image` → `add_layer`, return the new index.**
  - `add_layer(self, image, style=DEFAULT_IMAGE_LAYER_STYLE) -> int` appends,
    applies the style, and returns `len(self._images) - 1`.
  - Keep the `MAX_IMAGE_LAYERS` cap + ValueError.

- [x] **2.2 — `set_image(image, style=DEFAULT)` full-applies layer 0.**
  - Replace layer 0, set the frame, then `_apply_layer_style(0, image, style)`.

- [x] **2.3 — `set_layer(index, image, style=DEFAULT)`.**
  - Validate `index` via `_check_layer_index`; replace `_images[index]`; if
    `index == 0` update the frame; `_apply_layer_style(index, image, style)`.

- [x] **2.4 — `set_layer_style(index, style)` partial merge.**
  - Validate index; `_merge_layer_style(index, style)` — only non-`None` fields
    write their uniforms, others keep current values.

- [x] **2.5 — Helpers.**
  - `_apply_layer_style(index, image, style)` — full: `channel` `None` →
    `default_mode(channels)`, `value_min/max` `None` → `default_value_range(dtype)`,
    `enabled`/`opacity`/`blend` from the style (blend via `.code`).
  - `_merge_layer_style(index, style)` — partial: skip `None` fields.
  - `_blend_code(blend)` / channel coercion helper (shared by both).

- [x] **2.6 — Tests.**
  - `add_layer` returns the index; `set_image`/`add_layer` full apply with a
    partial style; `set_layer` overwrites; `set_layer_style` merges (only the
    given field changes, others unchanged); dtype/channel auto-derivation.

## Validation

```
uv run pytest py/tests/viz/test_image_view.py -q
uv run ruff check py/pytanga/viz/_image_view.py
uv run ty check
```
