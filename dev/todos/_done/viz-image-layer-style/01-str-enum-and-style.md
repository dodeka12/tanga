# Phase 1 — `StrEnum` blend mode + `ImageLayerStyle`

## Goal

Turn `LayerBlendMode` into a `StrEnum` (with an int `.code` for the wire) and
add the `ImageLayerStyle` value object plus a default instance.  No behavior
change to `ImageView`/`ImageCanvas` yet.

## Files

- Edit: `py/pytanga/viz/image.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/tests/viz/test_image_view.py` (or new `test_image_layer_style.py`)

## Steps

- [x] **1.1 — `LayerBlendMode` → `StrEnum`.**
  - Values `NORMAL="normal"`, `ADD="add"`, `MULTIPLY="multiply"`,
    `SCREEN="screen"`; add `code` property (`0/1/2/3`) and
    `from_code(code)` classmethod.

- [x] **1.2 — `ImageLayerStyle` + `DEFAULT_IMAGE_LAYER_STYLE`.**
  - Add the frozen-of-fields dataclass (enabled/opacity/blend/channel/value_min/
    value_max) with `__post_init__` coercing `blend`/`channel` strings to enums
    and validating opacity + value-range ordering.
  - Add module constant `DEFAULT_IMAGE_LAYER_STYLE = ImageLayerStyle()`.

- [x] **1.3 — Export from `pytanga.viz`.**
  - Import `ImageLayerStyle` + `DEFAULT_IMAGE_LAYER_STYLE` in `__init__.py` and
    add to `__all__`.

- [x] **1.4 — Tests.**
  - StrEnum values + `code` + `from_code`.
  - Style defaults, partial init (`ImageLayerStyle(opacity=0.5)`),
    string coercion (`blend="add"`, `channel="gray"`), and validation errors.

## Validation

```
uv run pytest py/tests/viz/test_image_view.py -q
uv run ruff check py/pytanga/viz/image.py py/pytanga/viz/__init__.py
uv run ty check
```
