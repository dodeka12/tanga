# Viz `getattr`/`hasattr` follow-ups (TODO)

**Created:** 2026-10-06 | **Status:** Planned | **Branch:** `fix/viz-control-refactor`

Loose-ends from the `getattr`/`hasattr` survey.  These are lower-priority than
the `viz-structural-protocols` plan (which covers the view/control tree).  Each
item is a self-contained structural-typing refactor; promote any of them to a
full plan folder when picked up.

- [ ] **Geometry vector/rotation coercion — `py/pytanga/geometry/transform.py`**
  - `_is_vector_like` / `_as_vec3` (`hasattr(value, "x") and hasattr(value, "y")
    and hasattr(value, "z")`) → a `Vec3Like` `@runtime_checkable` `Protocol`.
  - `_as_euler` / `_as_quaternion` (`getattr(value, "angle"/"axis"/"origin",
    None)`) → an `AxisAngleLike` `Protocol`.

- [ ] **Camera-config duck-typing — `py/pytanga/viz/export/_gltf.py` +
  `py/pytanga/geometry/entities/frustum.py`**
  - `getattr(cam_config, "type"/"xmin"/"fov"/"up", …)` and
    `getattr(camera, "near"/"far"/"type"/"fov", …)` → a `TypedDict` or
    `Protocol` for the camera config (see `viz/camera.py` `CameraConfig` family).

- [ ] **Style/entity duck-typing — `py/pytanga/viz/serializer.py`,
  `py/pytanga/viz/_nodes.py`, `py/pytanga/viz/sdf/serializer.py`**
  - `hasattr(styles_map, "get")` → `isinstance(styles_map, Mapping)` (it is a
    `StylesMap`).
  - `hasattr(style, "to_dict")` / `getattr(style, "__dict__", {})` → a
    `ToDict`/`StyleLike` `Protocol`.
  - Scattered `getattr(style, "length"/"extent"/"smoothness"/"color", None)` →
    direct attribute reads once the style type is narrowed.

## Intentionally not tracked (leave as-is)

- `py/pytanga/matrix/_dispatch.py` + `blade_mask/_dispatch.py` — name-based C++
  binding dispatch (documented `# ty: ignore` false positive).
- `py/pytanga/viz/_controls.py::Control.register_handlers` — `getattr(self,
  f.name)` over `dataclasses.fields` (deliberate `on_*` convention).
- `py/pytanga/viz/visualizer.py` — `getattr(self, "_initialized"/"_shutdown_requested", …)`
  lazy-init (typing Rule 5 territory, not duck-typing).
