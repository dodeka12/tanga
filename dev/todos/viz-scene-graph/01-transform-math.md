# Phase 1 — Transform math (`_transforms.py`)

**Status:** Planned

## Goal

Add a standalone module for converting geometry entities and operator
dataclasses into 4×4 matrices and TRS (translation / rotation / scale) tuples.
Pure math on the dataclass fields — no algebra analysis, no scene dependency.
Usable by the scene graph and by standalone user code.

## File

- New: `py/pytanga/viz/_transforms.py`

## Conventions

- Matrix: `numpy.ndarray`, shape `(4, 4)`, `dtype=float64`.
- Column-vector convention `v' = M @ v`; composition is `M1 @ M2` applies `M2`
  first.
- Rotation serialization uses 3×3 rotation → Euler (order `"XYZ"`, three.js
  default).
- TRS is canonical; matrix is derived from TRS and used for composition /
  decomposition only.

## Steps

- [ ] Create `py/pytanga/viz/_transforms.py`.
- [ ] Implement matrix primitives:
  - [ ] `translation_matrix(tx, ty, tz) -> M4`
  - [ ] `rotation_matrix(axis, angle) -> M4` (axis-angle → 3×3 → M4)
  - [ ] `scale_matrix(sx, sy, sz) -> M4` (accept uniform scalar too)
  - [ ] `to_trs(M) -> (position, euler, scale)` decomposition
- [ ] Implement operator → matrix converters:
  - [ ] `translator_to_matrix(Translator)`
  - [ ] `rotor_to_matrix(Rotor)`
  - [ ] `general_rotor_to_matrix(GeneralRotor)` = `T(origin) @ R @ T(-origin)`
  - [ ] `motor_to_matrix(Motor)` = `T(t) @ R`
  - [ ] `dilator_to_matrix(Dilator)` = `T(origin) @ S(f) @ T(-origin)`
- [ ] Implement operator → TRS converters:
  - [ ] `operator_to_trs(op) -> (position, euler, scale)` for
    `Rotor` / `GeneralRotor` / `Motor` / `Translator` / `Dilator`
  - [ ] Document the `GeneralRotor` position `(I - R) @ origin` and the
    `Dilator` position `(1 - f) * origin` decompositions.
- [ ] Implement `operator_to_matrix(op)` dispatch (the operators above).
- [ ] Implement `to_matrix(obj)` convenience dispatch:
  - [ ] `Point(x,y,z)` → translation matrix
  - [ ] `Direction(x,y,z)` → translation matrix (treated as a move vector)
  - [ ] operator types → `operator_to_matrix`
- [ ] Add `to_trs_tuple(obj)` convenience for entities/operators where
      meaningful.
- [ ] Validate with a small local smoke test (round-trip `to_trs` on a known
      rotation + translation matrix).

## Unit tests

File: `py/tests/viz/test_transforms.py`

- [ ] `test_translation_matrix` — translation components land in column 3.
- [ ] `test_rotation_matrix_z` — `Rotor(pi/2, Direction(0,0,1))` maps `(1,0,0)`
      to `(0,1,0)` within tolerance.
- [ ] `test_scale_matrix` — supports scalar uniform and component-wise input.
- [ ] `test_translator_to_matrix` — equals the matching translation matrix.
- [ ] `test_general_rotor_to_matrix` — `T(origin) @ R @ T(-origin)` against a
      hand-computed example.
- [ ] `test_motor_to_matrix` — `T(t) @ R` against a hand-computed example.
- [ ] `test_dilator_to_matrix` — `T(origin) @ S(f) @ T(-origin)`.
- [ ] `test_operator_to_trs` — decomposes `Rotor` / `Translator` / `Motor` /
      `GeneralRotor` / `Dilator` back into expected TRS.
- [ ] `test_to_trs_roundtrip` — compose + decompose returns the input within
      tolerance.
- [ ] `test_to_matrix_point_direction` — `Point` / `Direction` map to
      translation matrices.

## Verification

- [ ] `uv run pytest py/tests/viz/test_transforms.py` passes.
- [ ] `uv run python -c "import pytanga.viz._transforms"` imports cleanly.
