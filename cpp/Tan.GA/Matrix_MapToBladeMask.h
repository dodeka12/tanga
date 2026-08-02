//////////////////////////////////////////////////////////////////////////////////
// <<licence: start>>
//
// This file is part of the TANGA library,
// a template library that implements geometric algebra.
//
// Copyright 2022 Christian Perwass
//
//    Licensed under the Apache License, Version 2.0 (the "License");
//    you may not use this file except in compliance with the License.
//    You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS,
//    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//    See the License for the specific language governing permissions and
//    limitations under the License.
//
// <<licence: end>>
//////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <map>

#include "Tan.Math/Matrix.h"

#include "Enum.h"
#include "Multivector.h"
#include "BladeMask.h"

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \file Matrix_MapToBladeMask.h
///
/// \brief Tools for converting GA multivector products into matrices and solving the resulting
///        linear systems.
///
/// \section overview Overview
///
/// A binary GA operation A ∘ B = C (where ∘ is the geometric, inner, or outer product) can be
/// written as a tensor contraction over a product tensor O:
/// \code
///   c^k  =  ∑_{i,j}  a^i · b^j · O^k_{ij}
/// \endcode
/// where i, j, k are blade-index slots in the chosen basis and O^k_{ij} encodes the Cayley table
/// of the algebra (sign ± and which blade results from blA ∘ blB).
///
/// \subsection partial_contraction Partial Contraction — Product Matrices
///
/// Fixing the coefficient vector of A and contracting only the A-index yields the \em product matrix:
/// \code
///   M^k_j  =  ∑_i a^i · O^k_{ij}       (bLeftToRight = true,  A on the left)
///   M^k_i  =  ∑_j b^j · O^k_{ij}       (bLeftToRight = false, A on the right)
/// \endcode
/// so that the full contraction becomes a matrix–vector product:
/// \code
///   vec(C)  =  M · vec(X)               (X is the unknown operand)
/// \endcode
/// Solving this system for vec(X) — e.g. via Gaussian elimination — recovers the multivector X
/// such that A ∘ X = C (or X ∘ A = C for the right-multiply case).
///
/// \subsection blade_masks Blade Masks and Subspace Restriction
///
/// For a D-dimensional vector space, the algebra has 2^D blades.  Storing a full 2^D × 2^D matrix
/// is impractical for large algebras.  The \c CBladeMask type selects a compact ordered subset of
/// blade ids that defines the row and column index spaces:
///
///   - \c xMaskB  — columns of M; the subspace in which the unknown X lives.
///   - \c xMaskC  — rows of M; the subspace in which we expect the result C.
///
/// Restricting to the relevant sub-algebra keeps the matrix small.  The \c EvalProductBladeMask_*
/// family of functions predicts xMaskC from a known A and a candidate xMaskB before the matrix is
/// built.  An optional \c xMaskA parameter (3-mask overloads) further restricts which blades of A
/// participate in the contraction — useful when A is known to lie in a particular sub-algebra
/// (e.g. the even sub-algebra of rotors in G3).
///
/// \subsection solving Solving the System
///
/// Once M and vec(C) are assembled:
///   - Square, full-rank systems: use \c GaussElim from \c Tan.Math/Matrix.Algo.GE.h.
///   - Rank-deficient or least-squares: use \c CMatrixAlgoSVD::Inverse from \c Tan.Math/Matrix.Algo.SVD.h.
///   - Modular integer arithmetic: use \c GaussElim with \c CCongruence_HMod.
///
/// \c GA::Inverse (declared in \c Tan.GA/Algo.h) is the high-level wrapper that automates the
/// blade-mask computation, matrix assembly, and Gaussian elimination for the common case A * X = 1.
///
/// \subsection array_variant The Array Variant
///
/// The \c EvalProductMatrixArray_* family accepts a \c std::vector<TMultivector> and builds a
/// stacked matrix whose row blocks correspond to each element of the list.  This is used when A
/// itself has unknown coefficients and is expressed as a linear combination of basis multivectors —
/// producing an overdetermined system suitable for a least-squares solve.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


#pragma once

#include "Matrix_BladeMask.h"
#include "Matrix_Product.h"

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \file Matrix_MapToBladeMask.h
///
/// \brief Umbrella header for the blade-mask-to-matrix pipeline.
///
/// Includes \c Matrix_BladeMask.h (blade-mask prediction) and
/// \c Matrix_Product.h (product-matrix construction).  All existing code that
/// includes \c Matrix_MapToBladeMask.h continues to work unchanged.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
