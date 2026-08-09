# 2D Algebra & Visualization Support — Overview Plan

This plan adds support for 2D geometric algebras (E2, P2, N2, PGA2) and a 2D
visualization mode to the Tanga library. The existing 3D entity/operator
dataclasses are reused unchanged — only the `x` and `y` fields carry data
(`z` is set to zero) when working with 2D algebras.

## Phases

| Phase | Description | Dependencies |
|-------|-------------|-------------|
| [1 — Basis Classes](phase-1-basis-classes.md) | `BasisE2`, `BasisP2`, `BasisN2`, `BasisPGA2` | None |
| [2 — Create Modules](phase-2-create-modules.md) | Entity/operator → MV for each 2D algebra + helpers | Phase 1 |
| [3 — Analysis Modules](phase-3-analysis-modules.md) | MV → entity/operator for each 2D algebra | Phase 1 |
| [4 — Dispatcher Updates](phase-4-dispatcher-updates.md) | Wire new modules into `analysis.py`, `create.py`, `basis/__init__.py`, `_algebra.py` | Phases 2, 3 |
| [5 — Viz Backend](phase-5-viz-backend.md) | `space_dim` parameter, 2D camera/config defaults | Phase 4 |
| [6 — Viz Frontend](phase-6-viz-frontend.md) | Orthographic top‑down camera, 2D controls in viewer.js | Phase 5 |
| [7 — Tests](phase-7-tests.md) | Unit tests for 2D algebras + integration tests for 2D viz | Phases 4, 6 |
| [8 — Documentation](phase-8-documentation.md) | User‑facing docs for 2D algebras and 2D viewer mode | All |

## Architecture Notes

- **Entity/Operator dataclasses unchanged.** `Point(x, y, z)` works for 2D by
  setting `z=0`. The renderers already receive `[x, y, z]` arrays and will
  display correctly in orthographic top‑down view.
- **C++ codegen unchanged.** The existing `_template.cpp` + `_generator.py`
  pipeline is dimension‑agnostic. First use of a new `(dim, sig)` pair
  auto‑generates and compiles the binding.
- **Precompiled wheels include 2D bindings.** The `tools/build-precompiled.py`
  script must be updated to include E2 (dim=2), P2 (dim=3), N2/PGA2 (dim=4,
  sig=8) in the `ALGEBRAS` list so that `uv build --wheel` bundles them.
- **No renderer changes needed.** All Three.js geometry objects (`Sphere`,
  `Line`, `Plane`, etc.) render identically in orthographic mode.
- **Full 3D entities work in 2D mode.** The 2D viewer simply uses an
  orthographic top‑down camera; any 3D entity (e.g. a `Sphere` with
  non‑zero `z`, a `Plane` tilted in space) can be added and will render
  faithfully from the top‑down perspective. This works out of the box
  with no additional code — the camera change alone handles it.
- **2D viz = orthographic camera + pan/zoom controls.** The 3D rendering
  pipeline stays intact; only the camera and control scheme change based on
  a `space_dim` flag in `SceneConfig`.
- **Z‑coordinate = overlay order in 2D mode.** When `space_dim=2`, the `z`
  field of entity dataclasses determines draw order, not position in 3D space.
  Entities with larger positive `z` render on top of those with smaller `z`.
  This allows users to control layering (e.g. `Point(3, 4, 0)` on the base
  layer, `Point(3, 4, 10)` on top) without changing 2D position.
