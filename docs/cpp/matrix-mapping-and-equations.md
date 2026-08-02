# Matrix Mapping and Equation Solving

Tools for converting GA multivector products into matrices and solving the
resulting linear systems.  Part of the `Tan.GA` matrix pipeline; see
[Product matrices](product-matrices.md) for the conceptual overview.

---

## Involution Flags

All product-matrix functions in `Matrix_Product.h` accept optional `eInvLeft`
and `eInvRight` parameters (type `GA::EInv`, default `GA::EInv::Id`):

| Value | Effect |
|---|---|
| `GA::EInv::Id` | Identity — no sign change |
| `GA::EInv::Rev` | Reverse: `rev(blade) = (-1)^(k(k-1)/2) * blade` |
| `GA::EInv::Conj` | Clifford conjugate: `conj(blade) = rev(blade) * (-1)^r` |

The involution sign is applied per-blade:

- **`eInvLeft`** modifies the A-blade coefficient before the inner loop:
  `fValA_signed = rev_sign(blA) ? -fValA : fValA`
- **`eInvRight`** modifies the B-blade column sign inside the inner loop:
  `finalSign = productSign ⊕ rev_sign(blB)`

This enables building product matrices for equations such as
`rev(A) * X = C`, `A * rev(X) = C`, or `conj(A) * conj(X) = C`
without pre-computing the involuted operands.

---

## Reverse and Conjugate Sign Matrices

`EvalProductMatrix_Reverse` and `EvalProductMatrix_Conjugate` build diagonal
`|xMask| × |xMask|` matrices where `M[i,i] = ±1` for each blade in `xMask`.
These are involutions: `M² = I`.

```cpp
GA::EvalProductMatrix_Reverse(mat, xMask);    // Reverse sign on diagonal
GA::EvalProductMatrix_Conjugate(mat, xMask);  // Conjugate sign on diagonal
```

Use with `vec(rev(A)) = D_rev · vec(A)` when constructing systems that involve
involution operations as part of the unknown.

---

## Complete API Reference

### Blade Mask Evaluation

```cpp
// Collect blade ids from a multivector
GA::EvalBladeMask(xMask, wA, bOnlyNonZeroComps);
```

### Blade Mask Prediction

```cpp
// Predict output blade mask of A ∘ X
GA::EvalProductBladeMask_GP(xMaskC, wA, xMaskB, bLeftToRight, bComplete);
GA::EvalProductBladeMask_IP(xMaskC, wA, xMaskB, bLeftToRight, bComplete);
GA::EvalProductBladeMask_OP(xMaskC, wA, xMaskB, bLeftToRight, bComplete);

// Mask-based overloads (use xMaskA instead of wA)
GA::EvalProductBladeMask_GP(xMaskC, xMaskA, xMaskB, bLeftToRight, bComplete);
GA::EvalProductBladeMask_IP(xMaskC, xMaskA, xMaskB, bLeftToRight, bComplete);
GA::EvalProductBladeMask_OP(xMaskC, xMaskA, xMaskB, bLeftToRight, bComplete);

// Inverse prediction: given A and C, what can X be?
GA::EvalProductBladeMaskInv_GP(xMaskB, xMaskA, xMaskC, bLeftToRight);
GA::EvalProductBladeMaskInv_IP(xMaskB, xMaskA, xMaskC, bLeftToRight);
GA::EvalProductBladeMaskInv_OP(xMaskB, xMaskA, xMaskC, bLeftToRight);
```

### MV ↔ Matrix Conversion

```cpp
GA::ToMatrix(mat, wA, xMask);           // MV to column matrix
GA::ToMultivector(wA, mat, xMask);      // column matrix to MV
```

### Product Matrix Construction

```cpp
// 2-mask overloads
GA::EvalProductMatrix_GP(mat, wA, xMaskB, xMaskC, bLeftToRight,
                         eInvLeft, eInvRight);
GA::EvalProductMatrix_IP(mat, wA, xMaskB, xMaskC, bLeftToRight,
                         eInvLeft, eInvRight);
GA::EvalProductMatrix_OP(mat, wA, xMaskB, xMaskC, bLeftToRight,
                         eInvLeft, eInvRight);

// 3-mask overloads (restrict A to xMaskA)
GA::EvalProductMatrix_GP(mat, wA, xMaskA, xMaskB, xMaskC, bLeftToRight,
                         eInvLeft, eInvRight);
GA::EvalProductMatrix_IP(mat, wA, xMaskA, xMaskB, xMaskC, bLeftToRight,
                         eInvLeft, eInvRight);
GA::EvalProductMatrix_OP(mat, wA, xMaskA, xMaskB, xMaskC, bLeftToRight,
                         eInvLeft, eInvRight);

// Array overloads (stacked matrix from list of MVs)
GA::EvalProductMatrixArray_GP(mat, vecwListA, xMaskB, xMaskC, bLeftToRight,
                               eInvLeft, eInvRight);
GA::EvalProductMatrixArray_IP(mat, vecwListA, xMaskB, xMaskC, bLeftToRight,
                               eInvLeft, eInvRight);
GA::EvalProductMatrixArray_OP(mat, vecwListA, xMaskB, xMaskC, bLeftToRight,
                               eInvLeft, eInvRight);

// Reverse / Conjugate sign matrices (diagonal, from blade mask only)
GA::EvalProductMatrix_Reverse(mat, xMask);
GA::EvalProductMatrix_Conjugate(mat, xMask);
```

All `EInv` parameters default to `GA::EInv::Id` for backward compatibility.

---

## Related Files

| File | Purpose |
|---|---|
| `Tan.GA/Matrix_BladeMask.h` | Blade mask prediction |
| `Tan.GA/Matrix_Product.h` | Product matrix construction |
| `Tan.GA/Matrix_MapToBladeMask.h` | Umbrella header |
| `Tan.GA/Enum.h` | `EInv` enum |
| `Tan.Math/Matrix.Algo.GE.h` | Gaussian elimination |
| `Tan.Math/Matrix.Algo.SVD.h` | SVD solver |
| `Tan.Math/Congruence.h` | Modular congruence classes |