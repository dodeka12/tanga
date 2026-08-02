# Geometry Basis Audit Template

**Purpose:** Systematic checklist for auditing any geometry basis implementation (E3, P3, N3, PGA3) against its reference model.

**Reference documents per basis:**
- **E3:** Perwass, *Geometric Algebra with Applications in Engineering*, Chapter "Euclidean Space"
- **P3:** Perwass, *Geometric Algebra with Applications in Engineering*, Chapter "Projective Space"
- **N3:** Perwass, *Geometric Algebra with Applications in Engineering*, Chapter "Conformal Space"
- **PGA3:** Gunn, *Geometric algebras for Euclidean geometry* (arXiv:1411.6502); Dorst & De Keninck, *A Guided Tour to PGA* (bivector.net/PGA4CS.html)

---

## A. Algebraic Embedding

### A.1 Signature and dimension

| Question | Example (PGA3) |
|----------|----------------|
| What is the target signature? | G(3,0,1) — 4D algebra with one null basis vector |
| How is it implemented? | 5D embedding: $e_0 \to e_p + e_m$, $e_p^2 = +1$, $e_m^2 = -1$ |
| Is the embedding isomorphic to the target algebra? | ✅ The 4D sub‑algebra $\{e_1, e_2, e_3, e_{\infty}\}$ is algebraically isomorphic to G(3,0,1) |
| Are there unused basis vectors that could leak into computations? | $e_o$ exists in BasisN3 but is not used for PGA3 point representation — correctly excluded |

### A.2 Naming conventions

| Question |
|----------|
| What notation does the primary reference use for basis vectors? |
| Does the code use the same names? |
| Are there aliases? Are they documented? |
| Would a user familiar with the literature recognize the names? |

### A.3 Dual/meet/join operations

| Question |
|----------|
| How is the pseudoscalar defined? Is it invertible? |
| If not invertible, how is dualization implemented? |
| Is the `meet` operator consistent with the reference model? |
| Is the `join` operator consistent with the reference model? |
| Do `meet` and `join` satisfy the Common Factor Axiom? |

---

## B. Geometric Entities

For each entity type supported by the basis:

### B.1 Entity grades and forms

| Question | Entity 1 | Entity 2 | ... |
|----------|----------|----------|-----|
| What grade is the entity in OPNS? | | | |
| What grade is the entity in IPNS? | | | |
| Does creation produce both forms? | | | |
| Does analysis handle both forms? | | | |

### B.2 Coordinate correspondence

For each entity, verify the mapping between MV coordinates and geometric parameters:

| Question |
|----------|
| Does creation produce the coordinate form described in the reference? |
| Does analysis recover the correct geometric parameters? |
| Are signs (orientation, distance direction) consistent with the reference convention? |
| Are there edge cases (entities at the origin, at infinity, degenerate)? |

### B.3 Round-trip fidelity

```
mv = create_entity(basis, params, opns=True)
entity = analyze_entity(mv, opns=True)
# Verify: recreated params ≈ original params
```

| Question |
|----------|
| Does create → analyze return the same geometric parameters (up to orientation sign)? |
| Does this hold for both OPNS and IPNS paths? |
| Does this hold for entities not at the origin? |

### B.4 Linear combinations

| Question |
|----------|
| Can entities be added to produce meaningful results (e.g., centroids, bisectors)? |
| Does analysis handle non‑unit‑weight elements correctly? |
| Are composite entities (sums, interpolations) analyzed correctly? |

---

## C. Operators (Versors)

### C.1 Reflection operators

For each reflection type supported by the basis:

| Question | ReflLine | ReflPlane | ReflOrigin | Inversion |
|----------|----------|-----------|------------|-----------|
| What grade is the versor? | | | | |
| Does creation produce the correct MV? | | | | |
| Does analysis recognize it? | | | | |
| Does sandwiching with the versor produce the expected geometric result? | | | | |

### C.2 Rotation operators

| Question | Rotor | GeneralRotor |
|----------|-------|--------------|
| What grades does the versor have? | | |
| Does creation produce the correct MV? | | |
| Does analysis recover the correct angle and axis? | | |
| Can it represent rotations about axes not through the origin? | | |
| Does it compose correctly (R₁·R₂ → rotor)? | | |

### C.3 Translation operators

| Question |
|----------|
| What grades does the versor have? |
| Does creation produce the correct MV? |
| Does analysis recover the correct translation vector? |
| Does sandwiching translate points by the expected amount? |

### C.4 Motor / combined operators

| Question | Motor | GeneralRotor | GeneralDilator |
|----------|-------|--------------|----------------|
| What grades does the versor have? | | | |
| Does creation produce the correct MV? | | | |
| Does analysis recover the components? | | | |
| Is the grade‑4 term correctly handled (present in Motor, absent in GeneralRotor)? | | | |

### C.5 Operator round-trip fidelity

```
mv = create_operator(basis, params)
op = analyze_operator(mv)
# Verify: recreated params ≈ original params
```

| Question |
|----------|
| Does create → analyze return the same parameters? |
| Does this hold for composite operators (T·R, R₁·R₂)? |

---

## D. Scale Handling (Homogeneous Coordinates)

This is the most common source of subtle bugs in geometric algebra implementations.

### D.1 The fundamental question

In any homogeneous model, an element $X$ and $\lambda X$ (for $\lambda > 0$) represent the same geometric object. The homogeneous coordinate is *weighted*. To extract Euclidean parameters, the weight must be cancelled — typically by dividing by a specific component (the "homogeneous part").

### D.2 Common normalization patterns

| Entity type | Homogeneous part | Normalization formula |
|-------------|-----------------|-----------------------|
| P3 point | $e_4$ component | $(x, y, z) = (c_1, c_2, c_3) / c_4$ |
| N3 point | $e_o$ coefficient (via $-\text{mv} \cdot e_{\infty}$) | $(x, y, z) = (c_1, c_2, c_3) / \alpha$ |
| PGA3 point | $e_{\infty}$ coefficient (via $-\text{mv} \cdot e_o$) | $(x, y, z) = (c_1, c_2, c_3) / \alpha$ |
| Plane | Normal magnitude | Normalized by $||\mathbf{n}||$ |
| Line (bivector) | Factorized plane normals | Direction/position from normalized planes |
| Rotor | Scalar part (for angle) | Angle from $\text{acos}(s)$, axis normalized |
| Translator | Scalar part (for displacement) | $dx = -2 \cdot \text{mv}[e_i \wedge e_0] / \text{mv}[0]$ |

### D.3 Audit checklist for scale

| Question | Status |
|----------|--------|
| How is the homogeneous weight extracted? (Algebraic dot product vs. raw coefficient read) | |
| Does the extraction work correctly in the presence of the embedding (if any)? | |
| Is the weight used to normalize the Euclidean coordinates? | |
| What happens for unit‑weight elements (the common case)? | |
| What happens for non‑unit‑weight elements (sums, interpolations)? | |
| Does the N3/PGA3 translator divide by the scalar part? | |
| Are there edge cases where the weight is zero (ideal elements)? Are they handled correctly? | |

---

## E. Code Quality

### E.1 Defensive checks

| Question |
|----------|
| Are zero MVs rejected early with a clear error? |
| Are scalar MVs rejected (they don't represent geometric entities)? |
| Are mixed‑grade MVs diagnosed or handled? |
| Are non‑blade bivectors checked before factorization (where applicable)? |

### E.2 Dead code / correctness

| Question |
|----------|
| Are there overwritten/commented‑out computations? |
| Are there comments indicating unresolved bugs (e.g., "No — need dual")? |
| Are manual blade ID assignments robust against blade ID scheme changes? |

### E.3 Completeness

| Question |
|----------|
| Does the creation module implement all entity types that the reference model supports? |
| Does the analysis module recognize all operator types that can arise? |
| Are there stub‑only creation functions that raise `ValueError` for supported entities? |

---

## F. Cross‑Module Consistency

### F.1 Entities ↔ Operators

| Question |
|----------|
| Are entity and operator dataclasses used consistently across creation, analysis, serialization, and visualization? |
| Do the dataclasses declared in `entities.py` and `operators.py` cover all types used by the viz module? |

### F.2 Analysis ↔ Creation

| Question |
|----------|
| Does the analysis dispatcher (`analyze()`) correctly route to the basis‑specific module? |
| Does the creation dispatcher (`create()`) correctly route to the basis‑specific module? |
| Is the basis detection (`_detect()`) reliable (e.g., subclass checks in correct order)? |

### F.3 Visualization pipeline

| Question |
|----------|
| Does `serializer.py` handle all entity/operator types that analysis can produce? |
| Does the frontend (JavaScript renderers) have a renderer for every kind string emitted by the serializer? |
| Does `_styles.py` have style classes for all kinds? |
| Does `_style_dict.py` have default styles for all kinds? |

---

## G. Edge Cases and Stress Tests

### G.1 Origin and infinity

| Test | Expected behavior |
|------|------------------|
| Point at origin | Should be representable and analyzable |
| Point at large coordinates | Should not suffer from numerical issues |
| Entity through the origin (plane, line) | Positional term should vanish; analysis should not divide by zero |
| Ideal/direction entity | Should have zero homogeneous component; analysis should distinguish from finite entity |

### G.2 Degenerate configurations

| Test | Expected behavior |
|------|------------------|
| Two identical planes wedged → zero bivector | Should produce zero, not crash |
| Parallel planes wedged → ideal line | Should produce valid ideal line |
| Three coplanar points joined | Should produce degenerate plane (zero or near‑zero) |
| Non‑simple bivector analyzed as line | Should raise error or classify as screw/motor |

### G.3 Composition

| Test | Expected behavior |
|------|------------------|
| Point + Point → weighted sum | Analysis should handle non‑unit weight |
| R₁ · R₂ → composite rotor | Analysis should recognize as Rotor |
| T · R → motor | Analysis should recognize as Motor |
| T · R · T̃ → general rotor | Analysis should recognize as GeneralRotor |
