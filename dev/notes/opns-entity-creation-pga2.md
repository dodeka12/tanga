# PGA2 — OPNS Entity Creation

Algebra `BasisPGA2`, Gunn/Dorst plane-based PGA for 2D geometry, modelled via
the **4D null-vector embedding** `e0 = ep + em` (`ep² = +1`, `em² = −1`,
`e0² = 0`). The geometric subspace `{e1, e2, e0}` is isomorphic to G(2,0,1).
The complement dual (J-map/Hodge star, `mv.dual()` via `BasisPGA2.dual`) maps
grade `k` → grade `3−k` in the PGA subspace; it is a **complement** map
(`e_A ∧ J(e_A) = +I₃`), not the metric dual.

In 2D PGA the codimension-1 hyperplane is a **line**; a "point" is the
intersection of two lines.

Source of truth: `py/pytanga/geometry/create_pga2.py` and
`docs/py/basis/pga_null_embedding.md`.
(Recorded at commit `eade1fe`; the `opns` keyword is still an explicit parameter,
`opns=True` selects the OPNS output, `opns=False` the IPNS/dual.)

## Entities

### Point

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `x·e1 + y·e2 + e0` (written `−x·e1 − y·e2 − e0`) | 1 |
| OPNS | `p_ipns.dual()` → grade-2 bivector (intersection of two lines) | 2 |

Built **via IPNS then J-dualized** for the OPNS output. The IPNS row shows the
sign convention used in the code (`{E1: -x, E2: -y, EP: -1, EM: -1}`).

### Direction (ideal point)

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `x·e1 + y·e2` (no `e0`) | 1 |
| OPNS | `d_ipns.dual()` → grade-2 bivector (ideal point) | 2 |

Built **via IPNS then J-dualized** for the OPNS output.

### Line

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `nx·e1 + ny·e2 + d·e0` (normal `n = (−dy, dx)` from direction, `d = −n·origin`) | 1 |
| IPNS | `(OPNS).dual()` | 3 |

OPNS built **directly** as a grade-1 vector. IPNS = `dual()`.

### Space

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `scale · e1 ∧ e2 ∧ e0` | 3 |
| IPNS | `(OPNS).dual()` → scalar | 0 |

Built **directly** as the grade-3 PGA pseudoscalar, then dualized for IPNS.

### Plane / Sphere / Circle / PointPair / HPoint / HDirection

- **Not representable** in PGA2. `create_plane` is absent; `create_sphere`,
  `create_circle`, `create_point_pair`, `create_homogeneous_point` raise
  `ValueError` (conformal/N2-only).

## Operators (no OPNS/IPNS distinction)

| Operator | Construction | Grade |
|----------|--------------|-------|
| Rotor | `cos(θ/2) − sin(θ/2)·e12` | 0 + 2 |
| Translator | `1 + 0.5·(dx·e1∧e0 + dy·e2∧e0)` | 0 + 2 |
| Motor | `T·R` | 0 + 2 + 3 |
| GeneralRotor | `T·R·T̃` | 0 + 2 |
| ReflectionLine | grade-1 line blade (same as OPNS line) | 1 |
| ReflectionPoint | grade-2 point bivector (same as OPNS point) | 2 |

`Dilator`, `Inversion` raise `ValueError` (conformal/N2-only).