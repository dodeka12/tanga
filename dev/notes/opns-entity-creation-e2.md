# E2 — OPNS Entity Creation

Algebra `BasisE2`, Clifford algebra **Cl(2,0)**: basis `e1, e2`, pseudoscalar
`I = e12`. No homogeneous or conformal embedding, so only entities *through the
origin* are representable.

Source of truth: `py/pytanga/geometry/create_e2.py`.
(Recorded at commit `eade1fe`; the `opns` keyword is still an explicit parameter
here, `opns=True` selects the OPNS output.)

## Entities

### Point

A point cannot be represented as a null space in E2 (that requires P2 or N2),
but its Euclidean coordinates always map to the **e1, e2 components**,
independent of OPNS/IPNS:

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2` | 1 |
| IPNS | `x·e1 + y·e2` (same — OPNS/IPNS independent) | 1 |

### Direction

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2` | 1 |
| IPNS | `(x·e1 + y·e2).dual()` | 1 |

OPNS built **directly** as a grade-1 vector; IPNS is its `dual()`.

### Line

- Through origin only. Built as the **same grade-1 vector** as `Direction`
  (`x·e1 + y·e2`, via `create_direction`), so it also dualizes for IPNS.
- Not through the origin → `ValueError` ("only lines through the origin").
- Note: analyzing the resulting grade-1 vector with `opns=True` yields a
  `Direction`, not a `Line` (E2 cannot recover an explicit line entity).

### Space

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `scale · e12` | 2 |
| IPNS | the scalar `scale` (dual of the pseudoscalar) | 0 |

Built **directly** as the pseudoscalar; IPNS = `dual()` (a scalar).

### Plane / Sphere / Circle / PointPair / HPoint / HDirection

- **Not representable** in E2. `create_plane` is absent (dispatch raises
  `AttributeError`); `create_sphere`, `create_circle`, `create_point_pair`,
  `create_homogeneous_point` all raise `ValueError` (conformal/N2-only).

## Operators (no OPNS/IPNS distinction)

| Operator | Construction | Grade |
|----------|--------------|-------|
| Rotor | `cos(θ/2) − sin(θ/2)·e12` | 0 + 2 |
| ReflectionLine | grade-1 vector `d.x·e1 + d.y·e2` | 1 |

`Translator`, `Dilator`, `Inversion`, `Motor`, `GeneralRotor`,
`ReflectionOrigin` all raise `ValueError` (conformal/projective-only).