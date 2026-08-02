# Product Matrices — Turning GA Operations into Linear Systems

`Tan.GA/Matrix_MapToBladeMask.h` (umbrella), `Matrix_BladeMask.h`, and
`Matrix_Product.h` provide the tools to convert a geometric algebra product
into a matrix equation and, together with `Tan.Math/Matrix.Algo.GE.h` and
`Tan.Math/Matrix.Algo.SVD.h`, to solve it.  `GA::Inverse` (in `Tan.GA/Algo.h`)
is the high-level wrapper for the most common case; the functions here give full
access to every intermediate step.

---

## The Tensor-Product View

For any binary GA operation $A \circ B = C$ (where $\circ$ is the geometric,
inner, or outer product), the coefficients satisfy

$$c^k = \sum_{i,\,j} a^i \cdot b^j \cdot O^k_{ij}$$

where $i$, $j$, $k$ are blade-index slots and $O^k_{ij}$ is the **product tensor**
that encodes the algebra's Cayley table: it is $\pm 1$ when blade $i$ and blade $j$
multiply (under $\circ$) to blade $k$, and $0$ otherwise.

---

## Partial Contraction — The Product Matrix

Fix the coefficient vector of $A$ and contract only the $A$-indices:

$$M^k_j = \sum_i a^i \cdot O^k_{ij} \qquad (\text{left, } A \circ X)$$
$$M^k_i = \sum_j a^j \cdot O^k_{ij} \qquad (\text{right, } X \circ A)$$

The full contraction then collapses to an ordinary matrix–vector product:

$$\vec{c} = M \cdot \vec{x}$$

Solving $M \cdot \vec{x} = \vec{y}$ for $\vec{x}$ recovers the multivector $X$
such that $A \circ X = Y$ (or $X \circ A = Y$ for the right case).

The `bLeftToRight` flag selects which index of $O$ is contracted:

| `bLeftToRight` | Product evaluated | A-index contracted |
|---|---|---|
| `true` | $A \circ X$ (A on left) | $i$ |
| `false` | $X \circ A$ (A on right) | $j$ |

---

## Involution on Operands (`EInv`)

Each product-matrix function accepts optional *involution* flags
`eInvLeft` and `eInvRight` (type `GA::EInv`, default `GA::EInv::Id`)
that apply a blade-wise sign to the left and right operands **before**
contraction:

| `EInv` value | Formula | Sign for blade of grade $k$ |
|---|---|---|
| `EInv::Id` | identity | $+1$ |
| `EInv::Rev` | reverse | $(-1)^{k(k-1)/2}$ — negates grades 2, 3 mod 4 |
| `EInv::Conj` | Clifford conjugate | $(-1)^{k(k-1)/2 + r}$ — reverse sign $\times (-1)^r$ where $r$ is the count of negative-metric basis vectors in the blade |

In combination with the tensor product sign $s$ from `GPSign`/`IPSign`/`OPSign`,
the final sign at matrix position $(k,j)$ is

$$\text{sign} = s \oplus \text{rev\_sign}(E_i) \oplus \text{rev\_sign}(E_j)$$

This lets you build product matrices for equations such as
$\operatorname{rev}(A) \circ X = C$ or $A \circ \operatorname{conj}(X) = C$
without pre-computing the involuted operands.

---

## Blade Masks — Subspace Restriction

A D-dimensional algebra has $2^D$ blades.  Storing a full $2^D \times 2^D$
matrix is impractical for large algebras, but in practice $A$ and $X$ live in
small subspaces.  A `CBladeMask` is a compact ordered set of blade ids that
defines the row or column index space.

| Mask | Role in $M$ |
|---|---|
| `xMaskB` | **Columns** — the subspace in which the unknown $X$ lives |
| `xMaskC` | **Rows** — the subspace in which the result $C$ is expected |
| `xMaskA` *(optional)* | Restricts which blades of $A$ enter the contraction |

Entries whose result blade falls outside `xMaskC`, or whose input blade falls
outside `xMaskB`, are silently discarded.  This keeps the matrix small even in
high-dimensional algebras.

---

## API Overview

### Step 1 — Establish blade masks

```cpp
#include "Tan.GA/Matrix_BladeMask.h"

TMask xMaskA, xMaskX, xMaskY;

// Collect the non-zero blades of a multivector
GA::EvalBladeMask(xMaskA, wA, /*bOnlyNonZeroComps=*/true);

// Predict which blades A * X can produce, for a candidate X-mask
GA::EvalProductBladeMask_GP(xMaskY, wA, xMaskX, /*bLeftToRight=*/true,
                                                  /*bComplete=*/true);
// xMaskY is now the minimal output subspace
```

`bComplete = true` iterates `EvalProductBladeMask_GP` to a fixed point.
Each iteration expands the working set by applying A to the accumulated output
of the previous iteration, then feeds that expanded set back as the new input.
The result is the union of all blades reachable by one, two, three, … applications
of A starting from `xMaskX`:

$$S = (A \circ \text{xMaskX}) \cup (A \circ A \circ \text{xMaskX}) \cup \ldots$$

until no new blades appear.  This gives the **minimal subspace closed under the
repeated action of A**, so that the product matrix built from it is square and
self-consistent.  Use `bComplete = false` (the default) when a single step
suffices and the output subspace is already known.

### Step 2 — Build the product matrix

```cpp
#include "Tan.GA/Matrix_Product.h"

CMatrix<TValue> matA;

// Left-multiplication by wA, columns = xMaskX, rows = xMaskY
GA::EvalProductMatrix_GP(matA, wA, xMaskX, xMaskY, /*bLeftToRight=*/true);

// With involution: rev(A) * X
GA::EvalProductMatrix_GP(matA, wA, xMaskX, xMaskY, true,
                         GA::EInv::Rev, GA::EInv::Id);
```

The result is a `|xMaskY| × |xMaskX|` matrix.  Functions exist for all three
products and two overload families:

| Function family | Overloads | Product |
|---|---|---|
| `EvalProductMatrix_GP` | 2-mask, 3-mask (with `xMaskA`) | Geometric * |
| `EvalProductMatrix_IP` | 2-mask, 3-mask | Inner \| |
| `EvalProductMatrix_OP` | 2-mask, 3-mask | Outer ^ |

Each overload also accepts `eInvLeft` and `eInvRight` (`EInv::Id` by default).

The **3-mask overloads** accept an additional `xMaskA` that restricts which
blades of $A$ participate.  Use this when $A$ is known to inhabit a specific
sub-algebra (e.g. the even sub-algebra for rotors in G3), ensuring the matrix
reflects that sub-algebra even for zero-valued blades.

### Step 3 — Assemble the right-hand side

```cpp
CMatrix<TValue> matY;
GA::ToMatrix(matY, wY, xMaskY);   // |xMaskY| × 1 column
```

`ToMatrix` extracts the coefficient vector of a multivector into a
single-column matrix ordered by the blade mask.  The inverse operation,
`ToMultivector`, converts a solution column back to a multivector.

### Step 4 — Solve the system

```cpp
#include "Tan.Math/Matrix.Algo.GE.h"

Tan::CCongruence_Float<double> xCong;
CMatrix<double> matAug(matA);
matAug.AppendCols(matY);

if (GaussElim(matAug, xCong))
{
    CMatrix<double> matX = matAug.GetSubMatrix(
        0, matAug.GetRowCount(), matA.GetColCount(), 1);
    TMV wX;
    GA::ToMultivector(wX, matX, xMaskX);
    wX.Prune();
}
```

For modular integer arithmetic replace `CCongruence_Float` with
`CCongruence_HMod` and pass the modulus at construction:

```cpp
Tan::CCongruence_HMod<int64_t> xCong(97);
```

---

## Reverse and Conjugate Sign Matrices

Two helper functions build **diagonal** sign matrices from a blade mask alone —
no MV contraction needed:

```cpp
GA::EvalProductMatrix_Reverse(mat, xMask);    // Rev signs on diagonal
GA::EvalProductMatrix_Conjugate(mat, xMask);  // Conj signs on diagonal
```

The result is a `|xMask| × |xMask|` diagonal matrix $D$ where
$D_{ii} = \pm 1$.  These can be used to pre- or post-multiply coefficient
vectors to apply involution operations in matrix form:
`vec(rev(A)) = D_rev · vec(A)`.

---

## Choosing xMaskX and xMaskY

The key design decision is the choice of the two masks.

**Square system (most common).** Start with `xMaskX = xMaskA` (the blades of
$A$ itself), then call `EvalProductBladeMask_GP(..., bComplete=true)` to
obtain `xMaskY`.  This gives a square matrix when $A$ closes over its own
sub-algebra — which holds for versors, rotors, and most invertible multivectors.

**Restricting the output.** Sometimes only part of the output is needed.  For
example, when solving for a rotor $R$ in G3, both $R$ and its dual $R^*$ are
algebraic solutions.  By restricting `xMaskY` to the even sub-algebra you
select only the rotor family.  Any output blade outside `xMaskY` is discarded,
effectively projecting the system onto the desired solution subspace.

**Overdetermined system.** Use the Array variants (see below) to stack
multiple equations with the same unknown $X$ and solve via SVD.

---

## The Array Variants

`EvalProductMatrixArray_GP/IP/OP` accept a `std::vector<TMultivector>` and
build a **stacked** matrix whose row blocks correspond to elements of the list:

$$\begin{bmatrix} M_0 \\ M_1 \\ \vdots \end{bmatrix} \vec{x} = \begin{bmatrix} \vec{y}_0 \\ \vec{y}_1 \\ \vdots \end{bmatrix}$$

The sparsity pattern (which blade pairs produce which output blades) is
determined by `wListA[0]`; each subsequent element provides its own set of
coefficient values for the same structural positions.  The resulting
overdetermined system is solved in the least-squares sense using
`CMatrixAlgoSVD::Inverse`.

---

## Worked Example — Solving A * X = Y in G(5,0)

```cpp
#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/MV_Operators.h"
#include "Tan.GA/Matrix_MapToBladeMask.h"
#include "Tan.GA/String.h"
#include "Tan.Math/Matrix.h"
#include "Tan.Math/Matrix.Algo.GE.h"
#include "Tan.Math/Congruence.h"

using namespace Tan;
using TBlade = GA::CBlade<5, 0>::TBlade;
using TValue = double;
using TMV    = GA::CDynamicMultivector<TValue, TBlade>;
using TMask  = GA::CBladeMask<TBlade>;

int main()
{
    TMV wA, wY;
    wA.AddValueBlade( 1.0, 1u);   // e1
    wA.AddValueBlade(-2.0, 2u);   // e2
    wA.AddValueBlade( 3.0, 4u);   // e3

    wY.AddValueBlade(0.5, 0u);    // scalar
    wY.AddValueBlade(1.0, 3u);    // e12

    // --- Step 1: blade masks ---
    TMask xMaskX;
    GA::EvalBladeMask(xMaskX, wA, true);   // start with blades of A

    TMask xMaskY;
    GA::EvalProductBladeMask_GP(xMaskY, wA, xMaskX, true, true);
    // expand xMaskX to the closed sub-algebra
    GA::EvalProductBladeMask_GP(xMaskY, wA, xMaskX, true, true);

    // ensure wY blades are in xMaskY (add if missing)
    GA::EvalBladeMask(xMaskY, wY, true);

    // --- Step 2: product matrix ---
    CMatrix<TValue> matA;
    GA::EvalProductMatrix_GP(matA, wA, xMaskX, xMaskY);

    // --- Step 3: RHS ---
    CMatrix<TValue> matY;
    GA::ToMatrix(matY, wY, xMaskY);

    // --- Step 4: solve ---
    CCongruence_Float<TValue> xCong;
    CMatrix<TValue> matAug(matA);
    matAug.AppendCols(matY);

    if (GaussElim(matAug, xCong))
    {
        CMatrix<TValue> matX = matAug.GetSubMatrix(
            0, matAug.GetRowCount(), matA.GetColCount(), 1);

        TMV wX;
        GA::ToMultivector(wX, matX, xMaskX);
        wX.Prune();

        printf("X   = %s\n", GA::ToString(wX).c_str());

        TMV wCheck;
        GA::GP(wCheck, wA, wX);
        wCheck.Prune();
        printf("A*X = %s\n", GA::ToString(wCheck).c_str());
        printf("Y   = %s\n", GA::ToString(wY).c_str());
    }
    else
    {
        printf("System has no unique solution.\n");
    }
}
```

---

## High-Level Shortcut — `GA::Inverse`

For the common case $A \cdot X = 1$, use `GA::Inverse` from `Tan.GA/Algo.h`
directly.  It automates blade-mask computation, matrix assembly, and Gaussian
elimination:

```cpp
#include "Tan.GA/Algo.h"
#include "Tan.Math/Congruence.h"

Tan::CCongruence_Float<double> xCong;
TMV wInv;
GA::EResult eRes = GA::Inverse(wInv, wA, xCong);
// wInv satisfies  wA * wInv = scalar_1  within the sub-algebra of wA
```

For modular integer inversion pass `CCongruence_HMod<int64_t>(p)`.  This is
the mechanism used in the NTRU-style experiments in `Tan.Crypt.Test/`.

---

## Solver Selection Guide

| Situation | Solver |
|---|---|
| Square, full-rank (typical) | `GaussElim` — fastest |
| Overdetermined (`rows > cols`) | SVD pseudo-inverse — least-squares fit |
| Underdetermined (`rows < cols`) | SVD pseudo-inverse — minimum-norm solution |
| Rank-deficient (near-zero pivots) | SVD with `tPrec` threshold |
| Modular integer ring | `GaussElim` with `CCongruence_HMod` only — SVD requires exact division |

See [Matrix Mapping and Equation Solving](matrix-mapping-and-equations.md) for
the complete SVD least-squares workflow.

---

## Related Files

| File | Purpose |
|---|---|
| `Tan.GA/Matrix_MapToBladeMask.h` | Umbrella header |
| `Tan.GA/Matrix_BladeMask.h` | Blade-mask prediction functions |
| `Tan.GA/Matrix_Product.h` | Product-matrix construction (`_GP`, `_IP`, `_OP`) |
| `Tan.GA/Enum.h` | `EInv` enum (identity, reverse, conjugate) |
| `Tan.GA/BladeMask.h` | `CBladeMask` type |
| `Tan.GA/Algo.h` | `GA::Inverse` high-level wrapper |
| `Tan.Math/Matrix.h` | `CMatrix` type |
| `Tan.Math/Matrix.Algo.GE.h` | `GaussElim` |
| `Tan.Math/Matrix.Algo.SVD.h` | `CMatrixAlgoSVD` |
| `Tan.Math/Congruence.h` | `CCongruence_Float`, `CCongruence_HMod` |

---

> **Python API:** See [Equation Solving (Python)](../py/solver/index.md) for the pytanga
> bindings that expose this functionality as `BladeMask`, `MVMatrix`,
> and the solver functions.
