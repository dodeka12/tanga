# Phase 7 — Example Scripts

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing any step in this plan.  
> In particular: the [Python Coding Style Guide](../../../docs/dev/guides/py-coding-style-guide.md).  
> Also review any relevant architecture docs, use-case examples, and best practice documentation found there.

## Goal

Write three example scripts in `py/examples/` that demonstrate `MVSolver` in
progressively more complex settings: basic inverse / solve, geometric
least-squares fitting in projective 2D, and rotor estimation via a
sandwiching constraint.

Each script is self-contained (imports only `pytanga` and `numpy`), prints
labelled output, and includes inline comments that explain the mathematical
reasoning behind each step.

---

## Steps

### 7.1 — `py/examples/solver_basics.py` ✓

Demonstrate the core `MVSolver` API in G(5,0) float64.

**Part A — Multivector inverse via `solve`.**

Construct an invertible **general** multivector `A` in G(3,0) (mixed grades,
not just grade-1).  Show two paths to its inverse and verify they agree:

```python
# Path 1: high-level one-liner — scalar 1.0 is coerced to MV automatically
X1 = slv.solve(A, 1.0)                # solve A * X = 1

# Path 2: explicit step-by-step (educational)
col_mask = BladeMask.full(alg)         # all 8 blades of G(3,0)
row_mask = slv.product_blade_mask(A, col_mask)   # complete=False (default):
                                       # one-step output mask; complete=True
                                       # would be wrong here — that computes
                                       # the closure under *repeated* A-mult
M        = slv.product_matrix(A, col_mask, row_mask)
b        = slv.to_matrix(1.0, row_mask)   # scalar 1.0 coerced to MV
x_arr    = np.linalg.solve(M.data, b.data)
X2       = slv.from_matrix(MVMatrix(x_arr, col_mask))
```

Print `A`, `X1`, `A * X1` (should be scalar 1), and confirm `X1 ≈ X2`.

**Part B — General solve `A * X = B`.**

Construct a target `B` in the same sub-algebra as `A`.  Solve with
`slv.solve(A, B)`, verify `A * X ≈ B`, and print the residual norm
`‖A*X − B‖∞` (max absolute coefficient error).

**Part C — Detecting a singular system.**

Construct a singular `A` (e.g. zero multivector or a multivector whose
sub-algebra product matrix is rank-deficient).  Show that `slv.solve` raises
`numpy.linalg.LinAlgError` and that `slv.solve_lsq` returns a least-norm
solution instead, printing the residual.

### 7.2 — `py/examples/solver_line_fitting_p2.py` ✓

Demonstrate least-squares homogeneous solve in P2 (projective plane).

**Background (inline comments in the script).**

P2 is modelled as G(3,0) with `e3` as the projective (homogeneous) dimension.

- **Point** (grade-1 vector with e3=1): `p = x·e1 + y·e2 + 1·e3`,
  blade ids `{1, 2, 4}`.
- **Line** (grade-2 blade): `L = a·e12 + b·e13 + c·e23`,
  blade ids `{3, 5, 6}`.
- **Incidence**: a point lies on a line iff `p ^ L = 0`
  (the outer product lands in the pseudoscalar `e123`, id `7`).

**Implementation steps.**

1. Construct `n` noisy sample points near a known line `L_true`.

2. Define the blade masks using `grades` for clarity:
   ```python
   col_mask = BladeMask(alg, grades=[2])   # all grade-2 blades = lines in P2
   row_mask = BladeMask(alg, grades=[3])   # grade-3 = pseudoscalar e123
   ```

3. Build the stacked outer-product matrix using `product_matrix_array`:
   ```python
   M = slv.product_matrix_array(points, col_mask, row_mask, product='op')
   # M.data has shape (n, 3); M * vec(L) ≈ 0
   ```

4. Solve the homogeneous system `M · vec(L) = 0` via SVD.  The least-squares
   solution to a **homogeneous** system is the right singular vector
   corresponding to the **smallest** singular value — not `lstsq(b=0)`, which
   would give the trivial zero solution:
   ```python
   _, _, Vt = np.linalg.svd(M.data, full_matrices=True)
   L_vec = Vt[-1]                          # last row of Vt
   L = slv.from_matrix(MVMatrix(L_vec.reshape(-1, 1), col_mask))
   ```

5. Normalize `L` so that its largest coefficient is 1 (projective equivalence).

6. Print `L_true`, the estimated `L`, and the mean `|p_i ^ L|` (residual
   incidence error for each point).

### 7.3 — `py/examples/solver_rotor_estimation.py` ✓

Demonstrate estimation of a best-fit rotor R in G(3,0) from point
correspondences, using a sandwiching constraint reformulated as a linear
system.

**Background (inline comments in the script).**

A rotor `R` in G(3,0) lives in the **even sub-algebra**:
`R = r₀ + r₁₂·e12 + r₁₃·e13 + r₂₃·e23`,
blade ids `{0, 3, 5, 6}`.

The action of `R` on a vector `X` is the sandwich product `R * X * ~R`.

Given `n` point pairs `(X_i, Y_i)` related by the same unknown rotor, the
sandwich equation `R * X_i * ~R = Y_i` can be linearised.  Multiplying both
sides on the right by `R`:
```
R * X_i = Y_i * R
```
Rearranging: `R * X_i − Y_i * R = 0`, which is **linear in the coefficients
of R**.

Note in the script that this equation has exactly the same form regardless of
the grade of the matched objects.  The only things that change are:

- The blade mask of the matched objects (e.g. `grades=[1]` for vectors,
  `grades=[2]` for lines/bivectors, `grades=[0,2]` for rotors themselves,
  `grades=[1,3]` for odd-grade multivectors).
- The output blade mask — whatever grades the sandwich product of `R` with that
  object type can produce.

So the identical pipeline applies when matching lines to lines, planes to
planes, rotors to rotors, or any other multivector type — only the two masks
change.  Include a brief comment block in the script that lists a few
alternative mask pairs as a reference.

**Expressing as a product-matrix equation.**

For each pair `(X_i, Y_i)`, build two matrices using the even sub-algebra mask
for `R`:

```python
rotor_mask  = BladeMask(alg, grades=[0, 2])   # even sub-algebra (scalar + bivectors)
vector_mask = BladeMask(alg, grades=[1])       # grade-1 vectors
```

- `M_R_i = slv.product_matrix(X_i, rotor_mask, vector_mask, left=False)`
  → M such that `M_R_i · vec(R) = vec(R * X_i)`.
- `M_L_i = slv.product_matrix(Y_i, rotor_mask, vector_mask, left=True)`
  → M such that `M_L_i · vec(R) = vec(Y_i * R)`.
- The constraint matrix for pair `i` is `C_i = M_R_i − M_L_i`,
  so `C_i · vec(R) = 0`.

Stack all `C_i` vertically into a single matrix `C` of shape `(3n, 4)`.

**Solving the homogeneous system.**

Use SVD: `_, _, Vt = np.linalg.svd(C)`.  The last row of `Vt` is the
least-squares solution `vec(R)` (smallest singular value).

**Normalizing to a proper rotor.**

A proper rotor satisfies `R * ~R = 1`.  After extracting `R` from the SVD,
normalize: `R = R / sqrt(scalar_part(R * ~R))`.

**Implementation steps.**

1. Choose a known test rotor (e.g. 30° rotation in the e1∧e2 plane).
2. Apply it to `n` vectors to produce pairs `(X_i, Y_i)`, optionally adding
   Gaussian noise to test robustness.
3. Build `C_i` for each pair as above and stack into `C`.
4. Solve via SVD; extract and normalize `R`.
5. Print `R_true`, `R_estimated`, and the mean rotation error
   `‖R_true * X_i * ~R_true − R_est * X_i * ~R_est‖` per point.
6. Note: restricting the column mask to the even sub-algebra (`rotor_mask`)
   is what prevents spurious odd-grade solutions — this is the `a_mask`
   mechanism in `product_matrix`.
