# Phase 3 — Algebra embedding + cone lift

## Goal

Add a general blade-relabeling primitive (`Algebra.embed` / `MV.to_algebra`) so an MV
from one algebra can be mapped into another, the canonical Q2→Q3 cone blade map,
`BasisQ3.__call__(mv)` (`BasisQ3(c)`), and `cone_from_conic(basis, vertex, conic)`.

## Files

- Edit: `py/pytanga/algebra/_algebra.py`, `py/pytanga/algebra/_mv.py`
- Edit: `py/pytanga/quadric/_basis.py`, `py/pytanga/quadric/_create.py`, `py/pytanga/quadric/__init__.py`
- New: `py/tests/algebra/test_algebra_embed.py`, `py/tests/quadric/test_cone_lift.py`

## Steps

- [x] **3.1 — `Algebra.embed(mv, blade_map) -> MV`**
  - Enumerate the source's non-zero blade ids (lazily via `BladeMask(mv).ids`), map each
    with `blade_map` (raise `ValueError` if a source id is unmapped), and build
    `self.multivector({mapped_id: mv[src_id]})`.
- [x] **3.2 — `MV.to_algebra(alg, blade_map=None) -> MV`**
  - Convenience: `alg.embed(self, blade_map)`; with `blade_map=None`, raise unless a
    canonical map is known (Q2→Q3 cone).
- [x] **3.3 — `CONE_BLADE_MAP` + `BasisQ3.__call__(mv)`**
  - In `_basis.py` add `CONE_BLADE_MAP = {1:256, 2:512, 4:64, 8:16, 16:32, 32:128}`.
  - `BasisQ3.__call__(self, mv) -> MV`: require `mv.algebra.dim == 6`, return
    `self.embed(mv, CONE_BLADE_MAP)`.
- [x] **3.4 — `cone_from_conic(basis, vertex, conic) -> MV`**
  - Normalize `conic` to a Q2 grade-1 MV (accept `Conic`, a 3×3 `np.ndarray` via
    `to_coeffs`, or a Q2 `MV`).
  - `q0_mv = basis.embed(q2_mv, CONE_BLADE_MAP)`;
    `q0 = from_coeffs(tuple(float(q0_mv[1 << i]) for i in range(10)))[:3, :3]`.
  - `q = _centered_matrix(q0, [vertex.x, vertex.y, vertex.z], 0.0)`; return
    `_matrix_to_mv(basis, q)`.
- [x] **3.5 — exports + tests**
  - Export `CONE_BLADE_MAP`, `cone_from_conic` (and re-export `embed`/`to_algebra` where appropriate).
  - `test_algebra_embed.py`: relabel round-trips; unmapped id raises.
  - `test_cone_lift.py`: a circle base + on-axis apex equals `create_cone`; a general
    ellipse base + off-axis apex gives a rank-3 `cone` with zero incidence at the apex
    and base points; round-trips through `refine_quadric` for the right-circular case.

## Validation

`uv run pytest py/tests/algebra py/tests/quadric -q`

## Notes

- The apex-at-origin relabel maps the conic's `[a13, a23, (√2/2)a33, (√2/2)a11,
  (√2/2)a22, a12]` onto the quadric's `[q13, q23, (√2/2)q33, (√2/2)q11, (√2/2)q22, q12]`,
  leaving `q14=q24=q34=q44=0` — exactly the homogeneous `z`-coordinate reinterpretation.
- A general apex is the existing `_centered_matrix` translation of that origin cone.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
