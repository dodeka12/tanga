# Phase 1 — Python `SdfStyle` + serializer routing (`kind:"sdf"`)

## Goal

Add a per-entity **`SdfStyle`** style class and route SDF-styled entities
through the SDF serializer so the **standard viewer** emits `kind:"sdf"` scene
objects instead of the normal mesh `kind`. This phase fixes the wire contract
(README) and makes the opt-in reachable from `Visualizer.add(..., style=...)`.

## Files

- New: `py/pytanga/viz/_styles/_sdf_style.py` — `SdfStyle` dataclass.
- Modify: `py/pytanga/viz/_styles/__init__.py` — export `SdfStyle`.
- Modify: `py/pytanga/viz/serializer.py` — detect `SdfStyle` in
  `serialize_entity` / `_dispatch_entity` and delegate to the SDF path.
- Modify: `py/pytanga/viz/sdf/serializer.py` — expose a small reusable entry
  for the standard serializer (do **not** change `SdfVisualizer`).
- Modify: `py/pytanga/viz/_scene.py` / `visualizer.py` — ensure a user
  `style=SdfStyle(...)` is passed through into `properties["style"]`.

## Steps

- [x] **1.1 — `SdfStyle` dataclass** (`_styles/_sdf_style.py`)
  - Extends `VizStyle` (from `_styles/_base.py`), `to_dict()` sets
    `"style_type": "SdfStyle"`.
  - Fields (all `None` = default): `color`, `opacity`, `soft_shadows: bool`
    (default `True`), `max_steps: int` (default `256`),
    `bound_padding: float` (default `0.05`).
  - Export from `_styles/__init__.py` and `py/pytanga/viz/__init__.py`.

- [x] **1.2 — Detection in `serializer.py`**
  - In `serialize_entity` / `_dispatch_entity`, before the per-kind leaf
    dispatch, check whether the resolved style is `SdfStyle`
    (`props.get("style")` is an `SdfStyle` instance, or the resolved
    `styles_map[kind]` entry is).
  - When detected, call the new SDF entry (1.3) and return its dict as the
    object body (still wrapped in the standard `{"id", "layer": "scene"}`
    envelope by `serialize_entity`).

- [x] **1.3 — SDF entry point** (`sdf/serializer.py`)
  - Add `serialize_entity_local(entity, entity_id, properties, *, styles_map)`
    returning the `kind:"sdf"` object shape from the README wire contract.
  - For this phase, delegate to the existing `_dispatch_object` to build the
    **world-space** tree and resolve `color`/`opacity`; `bound` and local-space
    placement are added in Phase 2 (emit a temporary identity `bound` and
    identity `transform` here so the shape is stable).

- [x] **1.4 — Wire-contract smoke tests** (`py/tests/viz/sdf/test_standard_serializer_sdf.py`)
  - `serialize_entity(Sphere(...), style=SdfStyle(...))` → `kind == "sdf"`,
    `sdfKind == "Sphere"`, `tree` present, `color`/`opacity` resolved.
  - A non-SDF entity serializes unchanged (regression).
  - `SdfVisualizer` output is byte-for-byte unchanged (regression).

- [x] **1.5 — Validate**
  - `uv run pytest py/tests/viz/sdf/ -q` plus the existing `py/tests/viz/ -q`.

## Validation

`uv run pytest py/tests/viz/ -q` (existing suite still green) +
`uv run pytest py/tests/viz/sdf/ -q` (new routing tests green).

## Notes

- `SdfStyle` is a *marker* style: the color/opacity resolution still reuses the
  normal priority chain; the class only adds SDF-specific knobs.
- Keep the `SdfVisualizer` path byte-for-byte stable: this phase must not alter
  the existing fullscreen SDF viewer.
