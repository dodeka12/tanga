# Phase 3 — Serializer + wire contract

## Goal

Wire the six new entities through the standard viewer serializer so they emit the
JSON in the README wire contract. Resolve `startDirection` / `rotation`
Python-side so the frontend always receives concrete values.

## Files

- Modify: `py/pytanga/viz/_types.py` (`SceneEntity` union)
- Modify: `py/pytanga/viz/serializer.py` (`_dispatch_entity` + `_serialize_*`)
- Modify: `py/tests/viz/test_serializer.py`

## Steps

- [x] **3.1 — `_types.py`**
  - Add `Disk`, `PartialDisk`, `Box`, `Ellipsoid`, `Ellipse`, `RegularPolygon`
    to the `SceneEntity` union (and import them).

- [x] **3.2 — `serializer.py` dispatch**
  - Import the new entities; add `isinstance` branches in `_dispatch_entity`
    (entities section) routing to the new `_serialize_*` functions.

- [x] **3.3 — `_serialize_disk`**
  - Emit `kind`, `center`, `radius`, `normal` + `_apply_defaults` with
    `{"thickness": 0.02}` (so the style resolves the slab thickness).

- [x] **3.4 — `_serialize_partial_disk`**
  - Emit `kind`, `center`, `radius`, `normal`, `angle` (radians),
    `startDirection` (normalized ⊥ normal, computed if the entity left it
    `None`) + thickness defaults.

- [x] **3.5 — `_serialize_box`**
  - Emit `kind`, `center`, `size`, `rotation` (a `Rotor` → Euler `[rx,ry,rz]`
    via `_as_euler`, else `null`) + `{}` defaults (wireframe-only style).

- [x] **3.6 — `_serialize_ellipsoid`**
  - Emit `kind`, `center`, `radii`, `rotation` (same Rotor→Euler rule) + `{}`
    defaults.

- [x] **3.7 — `_serialize_ellipse`**
  - Emit `kind`, `center`, `radiusU`, `radiusV`, `normal` + thickness defaults.

- [x] **3.8 — `_serialize_regular_polygon`**
  - Emit `kind`, `center`, `radius`, `sides`, `normal`, `angle` + thickness
    defaults.

- [ ] **3.9 — Unit tests**
  - Serialize each entity and assert the exact flat JSON shape (content fields +
    merged `style.style_type` / `thickness` where applicable).
  - `Box`/`Ellipsoid` with a `Rotor` serialize to an Euler `rotation` triple;
    without rotation `rotation` is `null`.
  - `PartialDisk` without `start_direction` serializes a normalized vector ⊥
    `normal`.

- [ ] **3.10 — Validate**
  - `uv run pytest py/tests/viz/test_serializer.py -q`.

## Validation

`uv run pytest py/tests/viz/test_serializer.py -q`

## Notes

- Follow the existing serializer conventions: `_apply_defaults(props, kind,
  builtin, styles_map=styles_map) | {...content fields...}`.
- `_as_euler` already handles Rotor → Euler and rejects displaced `GeneralRotor`;
  reuse it rather than writing new conversion code.
- Wire field names are camelCase on the wire (`startDirection`, `radiusU`,
  `radiusV`), matching `tubeRadius` / `alignCenter` in the existing contract.
