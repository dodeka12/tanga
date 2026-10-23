# Phase 1 — Python model + serialization

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `DepthImage` uniform block and
> `_styles` default resolution) and `py/pytanga/viz/_styles/__init__.py`.  This
> phase only adds a style field + one serialized uniform to an existing payload;
> no wire-contract or architecture change.

## Goal

Add `DepthImageStyle(max_grazing_angle=…)` (degrees) and serialize it as the
`u_max_stretch` uniform, with the angle→slope conversion in one shared helper.

## Files

- Edit `py/pytanga/viz/depth_image.py`
- Edit `py/pytanga/viz/_styles/_entity_styles.py`
- Edit `py/tests/viz/test_depth_image.py`

## Steps

- [x] **1.1 — Add the angle→stretch helper**
  - In `py/pytanga/viz/depth_image.py`, add `import math`.
  - Add `def grazing_angle_to_stretch(angle_deg: float | None) -> float`:
    - `None` or `<= 0.0` → `0.0` (off);
    - `>= 90.0` → `raise ValueError("max_grazing_angle must be < 90 degrees")`;
    - else `math.tan(math.radians(angle_deg))`.
  - Do not add it to `__all__` (module-level helper, like `normalize_depth_kind`).

- [x] **1.2 — Serialize `u_max_stretch`**
  - In `DepthImage._serialize_uniforms`, add
    `"u_max_stretch": grazing_angle_to_stretch(style.get("max_grazing_angle"))`
    (use `.get`, because the canonical default omits `None` fields).

- [x] **1.3 — Add the style field**
  - In `py/pytanga/viz/_styles/_entity_styles.py::DepthImageStyle`, add field
    `max_grazing_angle: float | None = None` (documented in the docstring).
  - In `to_dict()`, emit `max_grazing_angle` when not `None`.
  - In `__post_init__`, validate early via
    `from ..depth_image import grazing_angle_to_stretch; grazing_angle_to_stretch(self.max_grazing_angle)`
    and normalize `self.max_grazing_angle = float(...)` when set.

- [x] **1.4 — Unit tests**
  - In `py/tests/viz/test_depth_image.py::TestDepthImageStyle`:
    - `DepthImageStyle(max_grazing_angle=80)` → `to_dict()["max_grazing_angle"] == 80`;
    - default style → `max_grazing_angle` absent from `to_dict()`.
  - In `TestDepthImageBuild`, add: `_build` with `max_grazing_angle=80` →
    `content["uniforms"]["u_max_stretch"] == pytest.approx(math.tan(math.radians(80)))`;
    default `_resolved()` → `content["uniforms"]["u_max_stretch"] == 0.0`.
  - Add `with pytest.raises(ValueError, match="max_grazing_angle"): DepthImageStyle(max_grazing_angle=90)`.

## Validation

```bash
uv run pytest py/tests/viz/test_depth_image.py -q
uv run ruff check py/pytanga/viz/depth_image.py py/pytanga/viz/_styles/_entity_styles.py py/tests/viz/test_depth_image.py
```

## Notes

- Keep the canonical default block in `_styles/__init__.py` unchanged — `None`
  fields are intentionally omitted there (like `image_scale`/`camera`/`codec`).
- The conversion helper is the single source of truth; serialization, style
  validation, and (later) the example slider all go through it or mirror its
  formula.
