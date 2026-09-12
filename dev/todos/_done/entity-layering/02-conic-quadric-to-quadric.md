# Phase 2 — Move Conic / Quadric3D into `pytanga.quadric`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Relocate `Conic`, `Quadric3D`, `Quadric2D`, `EConicKind`, `EQuadricKind`, and the
classification helpers from `geometry/entities/conic.py` into `pytanga.quadric`,
importing `Point`/`Direction` from the leaf `pytanga.entity` so the
`quadric ↔ geometry.entities` cycle is gone.

## Files

- New: `py/pytanga/quadric/conic.py` (moved from `geometry/entities/conic.py`)
- Edit: `py/pytanga/quadric/__init__.py` (export Conic/Quadric3D/enums)
- Edit: `py/pytanga/geometry/entities/conic.py` (→ shim)
- Edit: `py/pytanga/geometry/entities/__init__.py` (Entity Union + re-exports)
- Edit: `py/pytanga/geometry/analysis_q2.py` (import Conic from quadric)
- Edit: `py/pytanga/geometry/_pointset.py` (no change expected; verify)

## Steps

- [x] **2.1 — Move the module**
  - Copy `geometry/entities/conic.py` to `quadric/conic.py`.
  - Change `from pytanga.quadric import from_coeffs` → `from ._mapping import from_coeffs`.
  - Change `from .point import Point` / `from .direction import Direction` →
    `from pytanga.entity import Point, Direction`.

- [x] **2.2 — Export from `quadric/__init__.py`**
  - Add `from .conic import Conic, Quadric3D, Quadric2D, EConicKind, EQuadricKind`
    and extend `__all__`.

- [x] **2.3 — Shim `geometry/entities/conic.py`**
  - Replace the body with `from pytanga.quadric import Conic, Quadric3D, Quadric2D,
    EConicKind, EQuadricKind` (+ `__all__`).

- [x] **2.4 — Update `geometry/entities/__init__.py`**
  - Import `Conic`, `Quadric3D`, `EConicKind`, `EQuadricKind` from `pytanga.quadric`
    (make it direct rather than via the shim).
  - Keep the `Entity` Union and `__all__` unchanged.

- [x] **2.5 — Update `analysis_q2.py`**
  - `from .entities import Conic` → `from pytanga.quadric import Conic`.

## Validation

```
uv run pytest py/tests/quadric -q py/tests/geometry -q
uv run python -c "from pytanga.quadric import Conic, Quadric3D, from_coeffs; from pytanga.geometry import Conic as C; assert C is Conic; print('ok')"
uv run grep -rn "pytanga.geometry" py/pytanga/quadric/ || echo "no geometry imports in quadric (expected)"
```

## Notes

- After this phase the import graph is a DAG: `quadric.conic` imports only
  `numpy` + `pytanga.entity` + `._mapping`.  The final grep in `Validation`
  must report no `pytanga.geometry` imports under `pytanga/quadric/`.
