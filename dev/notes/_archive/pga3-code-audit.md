# PGA3 Code Audit — Faithfulness to the Gunn/Dorst Model

**Date:** 31 July 2026  
**Scope:** `py/pytanga/basis/pga3.py` + `py/pytanga/geometry/` (analysis_pga3.py, create_pga3.py, analysis.py, create.py)  
**Reference documents:** `_input/Dokument_25.md` (Gunn dissertation), `_input/PGA4CS.md` (Dorst & De Keninck)

---

## 1. Embedding of the Null Vector

Both documents describe PGA as the algebra **G(3,0,1)** — a 4-dimensional Clifford algebra where the extra basis vector has signature 0 (null). TANGA cannot represent null basis vectors natively; it only supports signatures ±1. The chosen workaround uses a 5-dimensional embedding:

$$e_0 \to e_{\infty} = e_p + e_m, \qquad e_p^2 = +1,\; e_m^2 = -1$$

This is implemented in `BasisN3` (lines 36–38 of `n3.py`):

```python
self.einf = mv({_EP: 1.0, _EM: 1.0})   # ep + em
self.eo   = mv({_EP: -0.5, _EM: 0.5})  # 0.5·em - 0.5·ep
```

The 4D PGA sub-algebra lives on the subspace $\{e_1, e_2, e_3, e_{\infty}\}$. The reciprocal null vector $e_o$ is **not** used for point representation in PGA3 (it belongs to the full N3 conformal model). This is correctly noted in the `BasisPGA3` docstring.

**Verdict:** ✅ Faithful. The embedding is mathematically sound and properly isolates the 4D PGA sub-algebra.

### 1.1 Naming of the Null Basis Vector

Both Gunn and Dorst use the notation **`e₀`** for the null basis vector of PGA (Gunn §5.3, Dorst §2.1). The TANGA code names the embedded proxy `einf` (short for $e_{\infty} = e_p + e_m$), with `e0` as a convenience alias. The `einf` name is correct for the 5D embedding — it accurately reflects that this is the image of the null vector under the embedding, not the null vector itself. However, from the user's perspective, this is an internal implementation detail.

In PGA3 code, the name `einf` appears throughout:
- `BasisPGA3.point` uses `_EP` and `_EM` blade IDs directly (not even `einf`):
  ```python
  return self.multivector({1: x, 2: y, 4: z, _EP: 1.0, _EM: 1.0})
  ```
- `_pga3_dual` constructs $I_{4d}$ as `alg.e1.op(alg.e2).op(alg.e3).op(alg.einf)`
- `_point_or_direction_from_ipns` checks for `einf` presence:
  ```python
  has_einf = abs(float(dual[EP])) > 1e-15 or abs(float(dual[EM])) > 1e-15
  ```

**Recommendation:** Keep `einf` internally (it accurately describes the embedded form), but prefer `e0` in user‑facing APIs, docstrings, and documentation to match Gunn and Dorst.

---

## 2. Geometric Entities

### 2.1 Plane (Grade‑1 Vector)

**Documents:** Gunn §4.2, Dorst §3.1. A plane is a grade‑1 vector $p = \mathbf{n} - \delta e_0$ where $\mathbf{n}$ is the unit normal and $\delta$ the signed distance from the origin along $\mathbf{n}$.

**Code (`BasisPGA3.plane`):**
```python
def plane(self, nx, ny, nz, d=0.0):
    return self.multivector({1: nx, 2: ny, 4: nz, _EP: d, _EM: d})
```

This produces $n_x e_1 + n_y e_2 + n_z e_3 + d(e_p + e_m) = \mathbf{n} + d e_{\infty}$, which matches the document form. The distance sign convention ($d$ positive means the plane is at distance $d$ along the normal from the origin) matches the standard homogeneous coordinate convention (Dorst §2.1).

**Analysis (`_plane_from_vector`):** Extracts normal and offset by normalizing the Euclidean part and computing `offset = d / n_norm`. Returns a `Plane` dataclass with the correct point (closest point to origin is $-\alpha \hat{n}$). The sign is correct: $p \cdot X = \mathbf{n} \cdot \mathbf{x} - \delta = 0$.

**Verdict:** ✅ Faithful.

---

### 2.2 Line (Grade‑2 Bivector)

**Documents:** Dorst §2.2, §3.2. A line is a 2‑blade (simple bivector), the `meet` of two planes: $L = p_1 \wedge p_2$. In coordinates it has the directional term $\mathbf{n}_1 \wedge \mathbf{n}_2$ and the positional term $e_0 \left(\mathbf{d} \cdot (\mathbf{n}_1 \wedge \mathbf{n}_2)\right)$.

**Creation (`create_pga3.py:create_line`):** Constructs two orthogonal planes containing the line and wedges them. This is a valid construction.

**Analysis (`_line_from_bivector`):**
- Calls `blade_factorize()` on the grade‑2 part
- Interprets each factor as a plane vector via `_plane_from_vector`
- Computes direction as cross product of the two plane normals
- Finds closest point to origin via solving a 3×3 linear system

**Issues:**
1. **No blade-ness check before factorization.** The code does not verify that the bivector is simple ($B \wedge B = 0$). If the caller passes a non‑simple 2‑vector (a screw), `blade_factorize()` may fail unpredictably. The N3 model handles this by distinguishing lines (simple) from more general entities. Dorst §5.6 explicitly warns: "Non‑blade bivectors are screws." PGA3 analysis should either reject non‑simple bivectors or classify them as screws/motors.

2. **`_line_origin_from_planes` has dead code.** The first three determinant computations are immediately overwritten by a second set labeled "Correction." The corrected formulas appear correct, but the dead code is confusing.

**Verdict:** ✅ Conceptually faithful. ⚠️ Missing blade‑ness validation. ⚠️ Code quality issues.

---

### 2.3 Point (Grade‑3 Trivector in OPNS, Grade‑1 Vector in IPNS)

**Documents:** Gunn/Dorst: In the dual (plane‑based) construction, points are trivectors in OPNS (intersection of three planes) and vectors in IPNS. A finite point at $\mathbf{x}$ has the IPNS form $X = \mathbf{x} + e_{\infty}$ (or equivalently $x_1 e_1 + x_2 e_2 + x_3 e_3 + e_{\infty}$). The OPNS form is the wedge of three orthogonal planes through the point: $(e_1 - x e_{\infty}) \wedge (e_2 - y e_{\infty}) \wedge (e_3 - z e_{\infty})$.

**Creation (`create_pga3.py:create_point`):**
- **IPNS:** `{E1: x, E2: y, E3: z, EP: 1.0, EM: 1.0}` — correct.
- **OPNS:** Wedges three orthogonal planes through the point — correct.

**Analysis (`_point_from_trivector`):** Dualizes the OPNS trivector via `_pga3_dual(mv)` to get the IPNS vector, then reads coordinates directly. Correct.

**Scale handling:** The IPNS point always has $e_{\infty}$ coefficient = 1. No division by the projective coordinate is needed; the convention bakes this in. If a point were scaled (e.g., $2\mathbf{x} + 2 e_{\infty}$), the analysis code would wrongly read doubled coordinates. However, the creation code always produces unit‑weight points.

Dorst §2.8 discusses centroids as sums of weighted points, which would produce points with non‑unit weight. The analysis does not normalize — it assumes unit weight. This is a **gap** in the analysis for composite/weighted points.

**Verdict:** ✅ Faithful for unit‑weight points. ⚠️ No weight normalization in analysis.

---

### 2.4 Direction / Ideal Point

**Documents:** Dorst §2.6. A direction (vanishing point) has no $e_{\infty}$ component: $V = v_1 e_1 + v_2 e_2 + v_3 e_3$ (IPNS). Its OPNS is a trivector whose dual has zero $e_{\infty}$ component.

**Creation (`create_direction`):**
- **IPNS:** `{E1: x, E2: y, E3: z}` — correct (no einf component).

**Issue:**
- **OPNS form is incorrect.** The code creates `p1.op(p2).op(p3)` where $p_1 = e_1$, $p_2 = e_2$, $p_3 = e_3$. These are the three coordinate planes through the origin. Their wedge is $e_1 \wedge e_2 \wedge e_3 = \mathbf{I}_3$, which corresponds to the **origin point**, not a direction at infinity.

  Per the Gunn/Dorst model, a direction at infinity (OPNS) should be formed by three planes that all contain the given direction but are parallel in the finite sense — essentially, the `meet` of $e_0$ with a line in that direction. A correct construction would be: take any point $P$, translate it along the direction to create a line, then wedge with $e_0$. Alternatively, dualize the IPNS direction vector: `mv.dual()`.

**Verdict:** ❌ The OPNS form of `create_direction` is wrong. The IPNS form is correct.

---

### 2.5 Space (Pseudoscalar)

**Creation (`create_space`):** Constructs $e_1 \wedge e_2 \wedge e_3 \wedge e_{\infty}$ (grade 4) using a manual blade assignment that reconstructs the grade‑4 part from the 5D basis elements. This is somewhat fragile but functionally correct.

**Verdict:** ✅ Faithful but implementation is fragile.

---

## 3. Operators (Versors)

### 3.1 Reflection

**Documents:** Gunn §5.6.1, Dorst §6.1. A reflection in a plane $p$ is the sandwich operator $\Pi_p(X) = p X p^{-1}$ for odd‑grade $X$ (with sign). The versor is the plane vector itself.

**Code:** `create_pga3.py:create_reflection` returns a grade‑1 vector. `analyze_operator` recognizes single‑factor versors and returns a `Reflection` dataclass with the normal.

**Verdict:** ✅ Faithful.

---

### 3.2 Rotor (Rotation About an Axis Through the Origin)

**Documents:** Dorst §6.3. A rotation is the product of two plane reflections whose line of intersection $L$ is the rotation axis. In exponential form: $R = \exp(-\phi L / 2) = \cos(\phi/2) + \sin(\phi/2) L$ (where $L$ is a unit 2‑blade with $L^2 = -1$).

**Code (`create_rotor`):**
```python
def create_rotor(basis, angle, axis):
    half = angle / 2.0
    return basis.multivector({
        0: math.cos(half),
        E23: math.sin(half) * axis.x,
        E31: math.sin(half) * axis.y,
        E12: math.sin(half) * axis.z,
    })
```

This creates a rotor with a purely Euclidean bivector. This corresponds to a rotation about a line **through the origin** in the direction $\mathbf{r} = (a_x, a_y, a_z)$. The axis is $L = r_x e_{23} + r_y e_{31} + r_z e_{12}$.

**Is this sufficient for arbitrary rotations?** No. This only represents rotations about lines passing through the origin. A rotation about an arbitrary line not passing through the origin requires a **general rotor** (or equivalently, a motor constructed as $T \cdot R \cdot \tilde{T}$). The Gunn document §7.11 discusses this:

> *"A general rotor: $G = T \cdot R \cdot \tilde{T}$ … represents a rotation about an axis that does NOT pass through the origin."*

**Code analysis for `analyze_operator`:** Returns only `Reflection | Rotor | Translator | Motor`. There is **no recognition of a `GeneralRotor`** in the PGA3 analysis. The `analysis_n3.py` does recognize `GeneralRotor`, but `analysis_pga3.py` does not.

**Verdict:** ⚠️ Rotations about axes through the origin are faithfully represented. ❌ Rotations about arbitrary axes not through the origin are **not implemented** in PGA3 (no `create_general_rotor`, no analysis for it).

---

### 3.3 Translator

**Documents:** Dorst §6.3. A translation over vector $\mathbf{t}$ is the product of two reflections in parallel planes. In exponential form: $T = 1 - \frac{1}{2} e_0 \mathbf{t}$.

**Code (`create_translator`):**
```python
def create_translator(basis, dx, dy, dz):
    return basis.multivector({
        0: 1.0,
        9: -0.5*dx, 17: -0.5*dx  # e1∧ep, e1∧em
        10: -0.5*dy, 18: -0.5*dy
        12: -0.5*dz, 20: -0.5*dz
    })
```

This is $1 - \frac{1}{2}(dx \cdot e_{1\infty} + dy \cdot e_{2\infty} + dz \cdot e_{3\infty})$ which matches the document formula.

**Analysis (`_translator_from_versor`):** Extracts $dx = -2 \cdot mv[9]$, etc. Correct.

**Verdict:** ✅ Faithful.

---

### 3.4 Motor

**Documents:** Dorst §6.5. A motor is the general rigid body motion: product of 4 reflections, or equivalently $M = T \cdot R = \exp(-B/2)$ where $B$ is a (possibly non‑simple) bivector. It encodes a rotation and a translation.

**Code (`create_motor`):** $M = T \cdot R$ — correct.

**Analysis (`_motor_from_factors`):** Detects 4‑factor versors, separates Euclidean (rotation) and null (translation) factors. Correct.

**Verdict:** ✅ Faithful for motors.

---

### 3.5 General Rotor (Rotation About an Arbitrary Line)

**Documents:** Gunn §7.11, `create_n3.py:create_general_rotor`. A general rotor is $G = T \cdot R \cdot \tilde{T}$ — a displacement‑conjugated rotor that rotates about a line not through the origin. Its bivector components include both Euclidean and $e_0 \wedge \mathbf{v}$ terms but it has **no** grade‑4 component (distinguishing it from a motor).

**Code status:** `create_pga3.py` does **NOT** implement `create_general_rotor`. `analysis_pga3.py` does **NOT** recognize `GeneralRotor`. The N3 module implements both.

This is a significant gap because the Gunn/Dorst PGA model intrinsically supports this operation. Users who want to represent a rotation about an arbitrary axis in 3D space must fall back to constructing it manually (via conju‑gation with a translator).

**Verdict:** ❌ Missing. Rotations about arbitrary axes not through the origin cannot be created or analyzed in PGA3.

---

## 4. Scale Handling in Homogeneous Coordinates

### 4.1 The Problem

In the Gunn/Dorst PGA model, the null basis vector is $e_0$ with $e_0^2 = 0$. A point at Euclidean position $\mathbf{x}$ is represented in IPNS as:

$$X = \mathbf{x} + \alpha \cdot e_0$$

where $\alpha$ is the **homogeneous weight**. To map back to Euclidean space, we must divide by $\alpha$:

$$\mathbf{x} = \frac{x_1}{\alpha} e_1 + \frac{x_2}{\alpha} e_2 + \frac{x_3}{\alpha} e_3$$

For unit‑weight points, $\alpha = 1$ and the coordinates can be read directly.

### 4.2 The 5D Embedding Complicates Extraction

Because TANGA cannot represent a null basis vector natively, $e_0$ is embedded as:

$$e_0 \to e_{\infty} = e_p + e_m, \quad e_p^2 = +1,\; e_m^2 = -1$$

The reciprocal vector $e_o = 0.5 \cdot e_m - 0.5 \cdot e_p$ satisfies $e_{\infty} \cdot e_o = -1$. A PGA3 IPNS point is then:

$$X = x_1 e_1 + x_2 e_2 + x_3 e_3 + \alpha(e_p + e_m)$$

The critical issue is: **we cannot simply read the $e_p$ or $e_m$ blade coefficient to extract $\alpha$**. The value $\alpha$ is distributed across two blade IDs (`EP=8` and `EM=16`). What's worse, a general MV in the 5D algebra may have independent $e_p$ and $e_m$ coefficients — the subspace where they are *equal* is the PGA3 sub‑algebra, but operations within the full 5D algebra may temporarily produce MVs where they differ.

### 4.3 The Correct Algebraic Approach

The N3 conformal model demonstrates the proper technique in `analysis_n3.py`:

```python
def _get_einf(alg):
    return alg.multivector({8: 1.0, 16: 1.0})

def _get_eo(alg):
    return alg.multivector({8: -0.5, 16: 0.5})

def _einf_coeff(mv, eo):
    """e∞ coefficient of mv = -mv·eo  (since einf·eo = -1)"""
    return -float(mv.sp(eo))
```

The dot product $-X \cdot e_o$ algebraically extracts the $e_{\infty}$ coefficient **regardless of the embedding**. This works because:
- $e_i \cdot e_o = 0$ for $i \in \{1,2,3\}$ (Euclidean basis vectors are orthogonal to $e_o$)
- $e_{\infty} \cdot e_o = -1$ (by construction)
- Linear combinations are handled automatically by bilinearity

So for an IPNS point $X = \mathbf{x} + \alpha e_{\infty}$:
$$\alpha = -X \cdot e_o$$

And the Euclidean coordinates are:
$$\mathbf{x} = \frac{X \cdot e_1}{\alpha} e_1 + \frac{X \cdot e_2}{\alpha} e_2 + \frac{X \cdot e_3}{\alpha} e_3$$

### 4.4 Current Code Is Deficient

The current PGA3 analysis does **not** use this algebraic method. Instead, it reads blade coefficients directly:

**`_point_or_direction_from_ipns` (line 164–178):**
```python
g1 = mv.grade(1)
x = float(g1[E1])
y = float(g1[E2])
z = float(g1[E3])
has_einf = abs(float(g1[EP])) > 1e-15 or abs(float(g1[EM])) > 1e-15
if not has_einf:
    return Direction(x=x, y=y, z=z)
return Point(x=x, y=y, z=z)
```

This code:
1. **Does not extract $\alpha$** — it only checks whether *any* $e_p$ or $e_m$ is present
2. **Does not divide by $\alpha$** — coordinates are returned at face value
3. **Fragile check** — relies on `g1[EP] == g1[EM]` implicitly, but does not verify this (a MV outside the PGA3 sub‑algebra could have `g1[EP] != g1[EM]`)

**`_point_from_trivector` (line 275–290):**
```python
dual = -_pga3_dual(mv)
x = float(dual[E1])
y = float(dual[E2])
z = float(dual[E3])
has_einf = abs(float(dual[EP])) > 1e-15 or abs(float(dual[EM])) > 1e-15
if not has_einf:
    return Direction(x=x, y=y, z=z)
return Point(x=x, y=y, z=z)
```

Same problems after dualization.

### 4.5 Concrete Example of Failure

Centroids (Dorst §2.8) are sums of weighted points:

```python
P = basis.point(1, 0, 0)  # IPNS: 1·e1 + 1·einf → x=1, α=1
Q = basis.point(3, 0, 0)  # IPNS: 3·e1 + 1·einf → x=3, α=1
C = P + Q                 # IPNS: 4·e1 + 2·einf → x=4, α=2
# Current analysis: reads x=4, returns Point(4, 0, 0)  ← WRONG
# Correct: divides by α: x=4/2=2, returns Point(2, 0, 0) ← Centroid
```

Scaled points from versor applications (where the versor is not unit‑normalized) would similarly break.

### 4.6 Impact on the Visualization

Point positions from composite/weighted MVs will render at wrong positions. Even though unit‑weight points (the common case) work correctly, any operation that changes the weight — centroids, linear interpolation, scaled versor applications — produces visually incorrect results.

**Verdict:** ❌ Critical. The homogeneous scale $\alpha$ is not extracted algebraically for points. Coordinates are not divided by $\alpha$, so any non‑unit‑weight point is mapped to the wrong Euclidean position. The correct method ($\alpha = -X \cdot e_o$) is available from the N3 module but not used in PGA3.

### 4.7 Other Entities and Operators — Scale Handling Audit

**Plane (`_plane_from_vector`):** ✅ Correct. The plane is $p = \alpha(\mathbf{n} + d \cdot e_{\infty})$. Both the normal components and the $e_{\infty}$ component scale by the same $\alpha$. The code normalizes by $||\mathbf{n}||$ and computes `offset = d / n_norm`, which is invariant under uniform scaling.

**Line (`_line_from_bivector`):** ✅ Correct. Factorized via `blade_factorize()`, then each plane factor is analyzed by `_plane_from_vector` which handles scale. The direction and origin are derived from normalized plane parameters and are scale‑invariant.

**Direction:** ✅ Correct. A direction has $\alpha = 0$ (no $e_{\infty}$ component), so there is nothing to divide by. The code correctly identifies this case and reads coordinates directly.

**Reflection (`_reflection_from_factor`):** ✅ Correct. A reflection versor is a plane vector; its normal direction is read directly. Since scale does not change the geometric meaning of the reflection axis, normalization is unnecessary.

**Rotor (`_rotor_from_factors`):** ✅ Correct. Both factor planes come from `blade_factorize_versor()` with consistent scaling. The angle is computed via $\text{acos}(n_1 \cdot n_2)$ on normalized vectors, and the axis bivector is normalized — both scale‑invariant.

**Translator (`_translator_from_versor`):** ⚠️ Convention‑dependent. The creator always produces `mv[0] = 1.0`, so reading blade coefficients directly works. However, the code **does not** divide by the scalar part `mv[0]`, unlike the N3 version which properly computes `dx = -2.0 * mv[9] / mv[0]`. A scaled translator MV (e.g., $\lambda(1 - \frac{1}{2} \mathbf{t} \cdot e_{\infty})$ with $\lambda \neq 1$) would produce $\lambda \cdot \mathbf{t}$ instead of $\mathbf{t}$. This is safe for API‑created translators but fragile for general MVs.

**Motor (`_motor_from_factors`):** ✅ Correct. Combines rotor and translator extraction, both of which are individually scale‑invariant.

**Summary:** The homogeneous scaling bug is **specific to Point analysis**. All other entity and operator types handle uniform scaling correctly through normalization or ratio computation. The Point case is uniquely vulnerable because its Euclidean coordinates and homogeneous weight appear as separate coefficients that must be divided, and the code currently omits this division.

---

## 5. The 4D Dual Operation

The Gunn/Dorst model uses a 4‑dimensional pseudo‑scalar $I_{4d} = e_1 \wedge e_2 \wedge e_3 \wedge e_{\infty}$ for dualization within the PGA sub‑algebra. Since $I_{4d}^2 = 0$ (it contains the null vector $e_{\infty}$), it has no proper inverse.

**Code (`_pga3_dual`):** Uses the pseudo‑inverse via `blade_pseudo_inverse()`. This is documented in `docs/py/basis/pga_null_embedding.md` and is a mathematically sound way to handle the non‑invertible pseudoscalar. It's equivalent to treating PGA as a sub‑algebra of the full 5D N3 algebra and restricting to the 4D subspace.

**Verdict:** ✅ Faithful to the theoretical model.

---

## 6. Summary of Issues

### 🔴 Critical Issues

| # | Issue | Location | Severity |
|---|-------|----------|----------|
| 1 | `create_direction` OPNS form is wrong (produces origin, not direction) | `create_pga3.py:create_direction` | Functionally broken |
| 2 | `_analyze_entity_ipns` grade‑3 routes to `_plane_from_vector` instead of dualizing | `analysis_pga3.py:_analyze_entity_ipns` | Functionally broken |

### 🟡 Gaps (Missing Functionality)

| # | Gap | Details |
|---|-----|---------|
| 3 | No `GeneralRotor` support | Cannot create or analyze rotations about axes not through origin. N3 has `create_general_rotor`; PGA3 should too. |
| 4 | Missing creation functions | `create_pga3.py` lacks `create_reflection_line`, `create_reflection_origin`, `create_general_rotor` |
| 5 | Missing operator analysis | `analyze_operator` in PGA3 doesn't recognize `GeneralRotor`, `ReflectionLine`, `ReflectionOrigin` |
| 6 | No normalization of point weight in analysis | IPNS point analysis reads coordinates without dividing by $e_{\infty}$ coefficient; composite points will be misinterpreted |

### 🟢 Minor Issues

| # | Issue | Details |
|---|-------|---------|
| 7 | No blade‑ness check before `blade_factorize()` | A non‑simple 2‑vector passed to `_line_from_bivector` will fail unpredictably |
| 8 | Dead code in `_line_origin_from_planes` | First determinant calculation is overwritten; confusing |
| 9 | `create_space` is fragile | Uses manual blade ID assignment; could break if blade ID scheme changes |
| 10 | No `Space` analysis for grade 5 in IPNS | `_analyze_entity_ipns` handles grade 5 but the IPNS route at the start might fail on mixed grades |

---

## 7. Answers to Specific Questions

### Q1: How is the scale in homogeneous coordinates accounted for?

The scale is managed by **creation convention**: all entity creation functions produce unit‑weight elements (plane normal has unit length, point has $e_{\infty} = 1$). The analysis functions **do not** normalize — they assume unit‑weight input. This works correctly for elements created by TANGA's own construction functions but will fail for linear combinations (e.g., centroids from point addition). The N3 conformal model handles normalization explicitly; PGA3 should do the same.

### Q2: Can we represent rotations about any axis in space, also those not passing through the origin?

**In theory, yes.** The Gunn/Dorst model supports this via:
- General rotors: $G = T \cdot R \cdot \tilde{T}$
- Motors with a screw axis

**In code, no.** The PGA3 module does **not** implement `create_general_rotor`. The only rotor creation creates Euclidean bivectors representing axes through the origin. The analysis also doesn't recognize general rotors. A user must manually construct $T \cdot R \cdot \tilde{T}$ without helper functions or recognition.

The N3 module does implement `create_general_rotor` and `analyze_operator` recognizes it, showing that the infrastructure exists and needs to be ported to the PGA3 layer.

---

## 8. Recommendations

1. **Fix `create_direction` OPNS form.** Use the signed dual (`mv.dual()`) of the IPNS direction vector, or construct proper planes containing the direction.

2. **Fix `_analyze_entity_ipns` grade 3 path.** Dualize the IPNS trivector before routing to `_plane_from_vector`.

3. **Add `create_general_rotor` to `create_pga3.py`.** Implement as $T \cdot R \cdot \tilde{T}$ using existing translator and rotor creators.

4. **Add `GeneralRotor` recognition to `analysis_pga3.py`.** Follow the pattern in `analysis_n3.py` where 2‑factor versors with mixed null/Euclidean components are classified as `GeneralRotor`.

5. **Add weight normalization to point analysis.** In `_point_from_trivector` and `_point_or_direction_from_ipns`, divide coordinates by the $e_{\infty}$ coefficient when it is non‑zero.

6. **Add blade‑ness validation to `_line_from_bivector`.** Check $B \wedge B = 0$ before calling `blade_factorize()`, raising an appropriate error for non‑simple bivectors.

7. **Clean up dead code in `_line_origin_from_planes`.**

8. **Add missing creation functions:** `create_reflection_line`, `create_reflection_origin`.

9. **Standardize naming of the null vector.** Use `e0` in user‑facing code (APIs, docstrings, documentation) to match Gunn and Dorst. Keep `einf` for internal use where it correctly describes the 5D embedding.

---

## 9. Impact on the Visualization Module

### 9.1 Pipeline

The visualization module (`py/pytanga/viz`) operates on **Entity/Operator dataclasses**, not on MVs directly. The pipeline is:

```
MV  →  geometry.analyze()  →  Entity/Operator dataclass  →  serializer.py  →  JSON  →  Three.js
```

Key observations:
- `Visualizer._resolve()` (line 393 of `visualizer.py`) calls `geometry.analyze(obj, opns=opns)` to convert MVs into dataclasses.
- `serializer.py` already handles **all** entity and operator types, including `GeneralRotor`, `ReflectionLine`, and `ReflectionOrigin`.
- The frontend has JavaScript renderers for every type under `templates/renderers/operators/`, including `general_rotor.js`, `reflection_line.js`, and `reflection_origin.js`.
- The style infrastructure (`_styles.py`, `_style_dict.py`) also covers all operator and entity types.

### 9.2 Conclusion

The visualization is **fully prepared** for all entities and operators that the Gunn/Dorst model describes. The bottleneck is exclusively in the **analysis layer** (`analysis_pga3.py`):

| What's missing in analysis | Viz impact |
|---|---|
| `GeneralRotor` not recognized | User can construct a GeneralRotor MV (via N3 or manual) but `viz.add()` will fail to resolve it |
| `ReflectionLine`/`ReflectionOrigin` not recognized | Same — MV not resolvable to dataclass |
| `Direction` OPNS broken | OPNS directions won't render (IPNS works) |
| No weight normalization | Weighted/composite points will render at wrong position |

**Once the analysis functions are fixed** (items 1–6 in Recommendations), the visualization will work automatically for all entity and operator types without any changes to the viz module.