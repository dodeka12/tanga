# Phase 1 — Python default opacities → 1.0

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the "Styles" and "Surface material"
> sections) and `py/pytanga/viz/_styles/__init__.py::_DEFAULT_STYLE_FOR_KIND`.
> This phase only changes canonical default values; it does not change the wire
> contract (the `style` dict already flows to the frontend).

## Goal

Change the canonical default opacity to `1.0` for all eight solid-surface kinds
and lock it with a test.

## Files

- Edit `py/pytanga/viz/_styles/__init__.py`
- Edit `py/tests/viz/test_serializer.py`

## Steps

- [x] **1.1 — Update `_DEFAULT_STYLE_FOR_KIND`**
  - `Plane` `0.3` → `1.0`; `Cylinder`/`Disk`/`PartialDisk`/`Box`/`Ellipsoid`/`Cone`
    `0.9` → `1.0`.  `Sphere` is already `1.0` — leave it.
  - Do not change colors, wireframe flags, or any non-opacity field.

- [x] **1.2 — Update the Plane regression test**
  - In `py/tests/viz/test_serializer.py::TestSerializeEntities::test_plane`,
    change `assert d["opacity"] == 0.3` → `assert d["opacity"] == 1.0`.

- [x] **1.3 — Add a contract test**
  - In `py/tests/viz/test_serializer.py`, add
    `test_surface_solid_default_opacity_is_one` asserting
    `_DEFAULT_STYLE_FOR_KIND[kind].opacity == 1.0` for
    `{"Plane","Sphere","Ellipsoid","Disk","PartialDisk","Box","Cylinder","Cone"}`.
    (Mirror the existing `test_sphere_style_opacity` style.)

## Validation

```bash
uv run pytest py/tests/viz/test_serializer.py -q
uv run ruff check py/pytanga/viz/_styles/__init__.py py/tests/viz/test_serializer.py
uv run ty check
```

## Notes

- `PlanePair`/`ParallelPlanePair` keep `0.3` — they are not solid-surface
  entities and are out of scope.
- `PartialDisk` is included here even though it has no `surface` material field
  (confirmed with the user).
