# Phase 2 — `CoordinateSystem` overlay/underlay emit

## Goal

Add `display_mode="overlay"` to `CoordinateSystem` so it emits an `axes_overlay`
(overlay) and a `grid_underlay` (underlay) object instead of world-space
`Grid`/`Axis` objects, while keeping the data group, plot content, transform, and
camera behavior unchanged.

## Files

- Edit: `py/pytanga/viz/_coordinate_system.py`
- Edit: `py/tests/viz/test_coordinate_system.py`

## Steps

- [x] **2.1 — `display_mode` parameter + validation**
  - Add `display_mode: Literal["world", "overlay"] = "world"` (import `Literal`).
  - Store it; validate the value; require `space_dim == 2` and `size is None`
    when `"overlay"` (else `ValueError`).

- [x] **2.2 — `_build_axes_overlay_spec()` / `_build_grid_underlay_spec()`**
  - `_build_axes_overlay_spec()` → `{xscale, yscale, base, value_format, labels,
    border_px, axis:{x,y}}` (from `self._xscale.is_log`/`self._yscale.is_log`,
    `self._base`, `self.value_format`, `self.labels`, `self.border_px`, and
    `self.x_style.to_dict()`/`self.y_style.to_dict()`).
  - `_build_grid_underlay_spec()` → `{xscale, yscale, base, border_px,
    grid: self.grid_style.to_dict()}`.

- [x] **2.3 — emit objects in overlay mode**
  - In `_build()`, when `display_mode == "overlay"`, skip the world `Grid`/`Axis`
    block (honoring `show_grid`/`show_axes` by omitting the corresponding object)
    and upsert the two objects via `self._handle.scene.add_object(...)` with
    stable ids (`f"{group_name}_axes_overlay"` / `f"{group_name}_grid_underlay"`)
    and `data={"spec": ...}`; on update, replace the spec and mark the node dirty.
  - Call the same upsert from `_rebuild()` / the `xlim`/`ylim` setters so
    range/style changes re-push both specs.

- [x] **2.4 — tests**
  - `display_mode="overlay"` raises for `space_dim=3` and for explicit `size`.
  - Overlay mode emits exactly one `axes_overlay` + one `grid_underlay` and no
    world `Grid`/`Axis`; `"world"` (default) still emits `Grid`/`Axis`.
  - Spec contents are correct for linear and log scales; `xlim` update re-pushes.

## Validation

`uv run pytest py/tests/viz/test_coordinate_system.py -q`

## Notes

- `display_mode` is a display concern only: the data group transform and
  `_apply_camera()` (via `fit_view2d`) stay identical to today so data placement
  and framing do not change.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
