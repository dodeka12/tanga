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

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \file Matrix_Product.h
///
/// \brief Product-matrix construction — convert GA products into linear systems.
///
/// Functions to extract multivector coefficients into column matrices (\c ToMatrix),
/// convert solution vectors back (\c ToMultivector), and build product matrices
/// for the geometric, inner, and outer products (\c EvalProductMatrix_GP,
/// \c _IP, \c _OP) with optional blade-mask restriction and involution
/// (reverse/conjugate) flags on operands.
///
/// Also includes \c EvalProductMatrix_Reverse and \c EvalProductMatrix_Conjugate
/// for constructing diagonal sign matrices from pure blade masks.
///
/// \sa Matrix_BladeMask.h, Matrix_MapToBladeMask.h
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

namespace Tan
{
	namespace GA
	{
		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Extract the coefficient vector of a multivector into a single-column matrix,
		/// 	ordered by the blade mask.
		///
		/// 	The blade mask defines the row ordering: the coefficient of xMask[i] is written
		/// 	into row i of the output matrix.  Blades present in xMask but absent from wA
		/// 	contribute a zero row.  The output is always |xMask| × 1.
		///
		/// 	Typical uses:
		/// 	- Build the RHS column vec(Y) for the linear system M · vec(X) = vec(Y).
		/// 	- Prepare the coefficient vector of a known multivector before calling
		/// 	  <c>GaussElim</c> or <c>CMatrixAlgoSVD::Inverse</c>.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type.  Must expose <c>TValue</c>, <c>TBlade</c>,
		/// 	and <c>GetValueBlade</c>. </typeparam>
		/// <param name="matA">	[out] Output matrix of size |xMask| × 1. </param>
		/// <param name="wA">		Source multivector whose coefficients are extracted. </param>
		/// <param name="xMask">	Ordered blade mask that defines the row index space. </param>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template <typename TMultivector>
		void ToMatrix(CMatrix<typename TMultivector::TValue> &matA, const TMultivector &wA, const GA::CBladeMask<typename TMultivector::TBlade> &xMask)
		{
			try
			{
				typedef typename TMultivector::TValue TValue;
				typedef typename TMultivector::TBlade TBlade;

				TValue fValA;
				unsigned uDim = xMask.Count();
				matA.SetSize(uDim, 1);
				matA.Zero();

				xMask.ForEachBlade([&](unsigned uIndex, const TBlade &blA)
								   {
							if (wA.GetValueBlade(fValA, blA))
							{
								matA(uIndex, 0) = fValA;
							} });
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error converting multivector to matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Distribute a single-column matrix back into a multivector using the blade mask.
		///
		/// 	This is the inverse of <c>ToMatrix</c>.  Row i of <c>matA</c> is written into
		/// 	the blade <c>xMask[i]</c> of <c>wA</c>.  The matrix must have exactly |xMask|
		/// 	rows; a mismatch throws.
		///
		/// 	Typical use: after solving M · vec(X) = vec(Y) via Gaussian elimination or SVD,
		/// 	call this to convert the solution column into a multivector.
		/// </summary>
		///
		/// <exception cref="std::runtime_error">	Thrown when matA has the wrong number of rows,
		/// 	or when a blade id in xMask cannot be stored in wA. </exception>
		///
		/// <typeparam name="TMultivector">	Multivector type.  Must expose <c>TValue</c>, <c>TBlade</c>,
		/// 	and <c>SetValueBlade</c>. </typeparam>
		/// <param name="wA">		[out] Multivector to populate. </param>
		/// <param name="matA">	Source matrix of size |xMask| × 1. </param>
		/// <param name="xMask">	Ordered blade mask that defines the row-to-blade mapping. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void ToMultivector(TMultivector &wA, const CMatrix<typename TMultivector::TValue> &matA, const GA::CBladeMask<typename TMultivector::TBlade> &xMask)
		{
			try
			{
				typedef typename TMultivector::TValue TValue;
				typedef typename TMultivector::TBlade TBlade;

				const unsigned uMatRowCnt = (unsigned)matA.GetRowCount();

				if (uMatRowCnt != xMask.Count())
				{
					TAN_THROW_RT("Incompatible blade mask");
				}

				xMask.ForEachBlade([&](unsigned uIndex, const TBlade &blA)
								   {
							if (uIndex >= uMatRowCnt)
							{
								TAN_THROW_RT("Invalid blade mask");
							}

							if (!wA.SetValueBlade(matA(uIndex, 0), blA))
							{
								TAN_THROW_RT("Invalid blade mask");
							} });
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error converting multivector to matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the product matrix M for the action of left- or right-multiplying by A.
		///
		/// 	For a GA product ∘, the operation A ∘ X = C is a tensor contraction:
		/// 	  c^k = ∑_{i,j} a^i · x^j · O^k_{ij}
		/// 	Fixing A and contracting the A-index yields the product matrix M:
		/// 	  M^k_j = ∑_i a^i · O^k_{ij}   (bLeftToRight = true,  A on left)
		/// 	  M^k_i = ∑_j a^j · O^k_{ij}   (bLeftToRight = false, A on right)
		/// 	so that C = M · vec(X).  Solving this system recovers X given A and C.
		///
		/// 	Rows of M are indexed by xMaskC (output blade subspace).
		/// 	Columns of M are indexed by xMaskB (input blade subspace of the unknown X).
		/// 	The matrix is |xMaskC| × |xMaskB|.  Entries whose result blade falls outside
		/// 	xMaskC, or whose input blade falls outside xMaskB, are silently discarded —
		/// 	this subspace restriction keeps large-algebra matrices tractable.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type.  Must expose <c>TBlade</c>,
		/// 	<c>TValue</c>, and <c>ForEachBlade</c>. </typeparam>
		/// <typeparam name="FuncOp">		Product sign/blade callable with signature
		/// 	<c>bool(unsigned&amp;, TBlade&amp;, const TBlade&amp;, const TBlade&amp;)</c>. </typeparam>
		/// <param name="matA">			[out] Product matrix of size |xMaskC| × |xMaskB|. </param>
		/// <param name="wA">				The fixed-coefficient multivector A. </param>
		/// <param name="xMaskB">			Blade mask defining the column index space (unknown subspace of X). </param>
		/// <param name="xMaskC">			Blade mask defining the row index space (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: A ∘ X (A on left).  <c>false</c>: X ∘ A (A on right). </param>
		/// <param name="xFuncOp">			Product-specific sign/blade function. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector, typename FuncOp>
		void _EvalProductMatrix(CMatrix<typename TMultivector::TValue> &matA,
								const TMultivector &wA,
								const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								bool bLeftToRight,
								FuncOp xFuncOp,
								GA::EInv eInvLeft = GA::EInv::Id,
								GA::EInv eInvRight = GA::EInv::Id)
		{
			try
			{
				typedef typename TMultivector::TValue TValue;
				typedef typename TMultivector::TBlade TBlade;

				unsigned uDimB = xMaskB.Count();
				unsigned uDimC = xMaskC.Count();

				matA.Resize(uDimC, uDimB);
				matA.Zero();

				wA.ForEachBlade([&](const TValue &fValA, const TBlade &blA)
								{ _EvalProductMatrix_InnerLoop(matA, fValA, blA, xMaskB, xMaskC, bLeftToRight, xFuncOp, eInvLeft, eInvRight); });
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build a stacked product matrix from a list of multivectors.
		///
		/// 	This variant is used when A itself has unknown coefficients and is expressed as
		/// 	a linear combination of basis multivectors — one element per entry of wListA.
		/// 	The sparsity and product structure (which blade pairs interact) are determined by
		/// 	<c>wListA[0]</c>; the actual coefficient values come from each list element.
		///
		/// 	The output matrix has size (|wListA| × |xMaskC|) × |xMaskB|.  Each consecutive
		/// 	block of |xMaskC| rows corresponds to one element of wListA, giving an
		/// 	overdetermined system of the form:
		/// 	  M_0 · vec(X) = vec(C_0)
		/// 	  M_1 · vec(X) = vec(C_1)
		/// 	          ...
		/// 	stacked into a single matrix equation, suitable for a least-squares solve via SVD.
		/// </summary>
		///
		/// <exception cref="std::runtime_error">	Thrown when wListA is empty. </exception>
		///
		/// <typeparam name="TMultivector">	Multivector type.  Must expose <c>TBlade</c>, <c>TValue</c>,
		/// 	<c>ForEachBladeIndex</c>, and <c>GetValue</c>. </typeparam>
		/// <typeparam name="FuncOp">		Product sign/blade callable. </typeparam>
		/// <param name="matA">			[out] Stacked matrix of size (|wListA|·|xMaskC|) × |xMaskB|. </param>
		/// <param name="wListA">			List of multivectors.  Must be non-empty.
		/// 	<c>wListA[0]</c> defines the sparsity pattern; all elements provide coefficients. </param>
		/// <param name="xMaskB">			Column index space (subspace of the common unknown X). </param>
		/// <param name="xMaskC">			Row index space per element (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: each element ∘ X.  <c>false</c>: X ∘ each element. </param>
		/// <param name="xFuncOp">			Product-specific sign/blade function. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector, typename FuncOp>
		void _EvalProductMatrix(CMatrix<typename TMultivector::TValue> &matA,
								const std::vector<TMultivector> &wListA,
								const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								bool bLeftToRight,
								FuncOp xFuncOp,
								GA::EInv eInvLeft = GA::EInv::Id,
								GA::EInv eInvRight = GA::EInv::Id)
		{
			try
			{
				typedef typename TMultivector::TValue TValue;
				typedef typename TMultivector::TBlade TBlade;

				const unsigned uMvCnt = (unsigned)wListA.size();
				const unsigned uDimB = xMaskB.Count();
				const unsigned uDimC = xMaskC.Count();

				if (uMvCnt == 0)
				{
					TAN_THROW_RT("List of multivectors is empty");
				}

				matA.SetSize(uMvCnt * uDimC, uDimB);
				matA.Zero();

				xMaskB.ForEachBlade([&](unsigned uIndexB, const TBlade &blB)
									{ _EvalProductMatrix_InnerLoop(matA, wListA, uIndexB, blB, xMaskC, bLeftToRight, xFuncOp, eInvLeft, eInvRight); });
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the product matrix M for A, restricting which blades of A participate.
		///
		/// 	Same as the 4-parameter <c>_EvalProductMatrix</c> but iterates over xMaskA
		/// 	instead of all non-zero blades of wA.  Blades of A inside xMaskA that are absent
		/// 	from the stored multivector are treated as zero (they still iterate but contribute
		/// 	nothing to M).  Blades of A outside xMaskA are completely ignored.
		///
		/// 	Use this overload when A is known to inhabit a specific sub-algebra and you want
		/// 	the matrix to be defined over that sub-algebra even for currently zero-valued
		/// 	blades.  Example: a rotor in G3 restricted to the even sub-algebra, where some
		/// 	coefficients are zero but must still hold their row/column position in M.
		/// </summary>
		///
		/// <exception cref="std::runtime_error">	Thrown on internal matrix errors. </exception>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <typeparam name="FuncOp">		Product sign/blade callable. </typeparam>
		/// <param name="matA">			[out] Product matrix of size |xMaskC| × |xMaskB|. </param>
		/// <param name="wA">				The fixed-coefficient multivector A. </param>
		/// <param name="xMaskA">			Blade mask restricting which blades of A enter the contraction. </param>
		/// <param name="xMaskB">			Column index space (unknown subspace of X). </param>
		/// <param name="xMaskC">			Row index space (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: A ∘ X.  <c>false</c>: X ∘ A. </param>
		/// <param name="xFuncOp">			Product-specific sign/blade function. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector, typename FuncOp>
		void _EvalProductMatrix(CMatrix<typename TMultivector::TValue> &matA,
								const TMultivector &wA,
								const GA::CBladeMask<typename TMultivector::TBlade> &xMaskA,
								const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								bool bLeftToRight,
								FuncOp xFuncOp,
								GA::EInv eInvLeft = GA::EInv::Id,
								GA::EInv eInvRight = GA::EInv::Id)
		{
			try
			{
				typedef typename TMultivector::TValue TValue;
				typedef typename TMultivector::TBlade TBlade;

				unsigned uDimB = xMaskB.Count();
				unsigned uDimC = xMaskC.Count();

				matA.SetSize(uDimC, uDimB);
				matA.Zero();

				xMaskA.ForEachBlade([&](unsigned uIndexA, const TBlade &blA)
									{
							TValue fValA;

							if (!wA.GetValueBlade(fValA, blA))
							{
								fValA = TValue(0);
							}

							_EvalProductMatrix_InnerLoop(matA, fValA, blA, xMaskB, xMaskC, bLeftToRight, xFuncOp, eInvLeft, eInvRight); });
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Inner-loop helper for <c>_EvalProductMatrix</c> (single multivector overload).
		///
		/// 	For a fixed blade blA with coefficient fValA, iterates over every blade in xMaskB.
		/// 	For each valid product blA ∘ blB = blC with blC in xMaskC, accumulates the signed
		/// 	coefficient contribution into the matrix:
		/// 	  matA(indexC, indexB) += fValA * sign(blA, blB)
		///
		/// 	Called once per non-zero blade of A by the outer loop in the single-MV overload
		/// 	of <c>_EvalProductMatrix</c>.  Not intended for direct use.
		/// </summary>
		///
		/// <typeparam name="TValue">	Coefficient value type. </typeparam>
		/// <typeparam name="TBlade">	Blade type. </typeparam>
		/// <typeparam name="FuncOp">	Product sign/blade callable. </typeparam>
		/// <param name="matA">			[in,out] Product matrix being accumulated into. </param>
		/// <param name="fValA">			Coefficient of the A-blade being processed. </param>
		/// <param name="blA">				The A-blade being processed in this iteration. </param>
		/// <param name="xMaskB">			Column index space (unknown subspace). </param>
		/// <param name="xMaskC">			Row index space (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: evaluate blA ∘ blB.  <c>false</c>: evaluate blB ∘ blA. </param>
		/// <param name="xFuncOp">			Product-specific sign/blade function. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TValue, typename TBlade, typename FuncOp>
		void _EvalProductMatrix_InnerLoop(CMatrix<TValue> &matA,
										  const TValue &fValA,
										  const TBlade &blA,
										  const GA::CBladeMask<TBlade> &xMaskB,
										  const GA::CBladeMask<TBlade> &xMaskC,
										  bool bLeftToRight,
										  FuncOp xFuncOp,
										  GA::EInv eInvLeft = GA::EInv::Id,
										  GA::EInv eInvRight = GA::EInv::Id)
		{
			// Apply involution sign to A-blade coefficient
			unsigned uInvA = 0;
			if (eInvLeft == GA::EInv::Rev)
				uInvA = blA.GetReverseSign() & 1;
			else if (eInvLeft == GA::EInv::Conj)
				uInvA = blA.GetConjugateSign() & 1;
			TValue fValASigned = (uInvA) ? -fValA : fValA;

			unsigned uSign, uIndexC;
			TBlade blC;

			xMaskB.ForEachBlade([&](unsigned uIndexB, const TBlade &blB)
								{
						bool bValid;

						if (bLeftToRight)
						{
							bValid = xFuncOp(uSign, blC, blA, blB);
						}
						else
						{
							bValid = xFuncOp(uSign, blC, blB, blA);
						}

						if (bValid && xMaskC.GetIndex(uIndexC, blC))
						{
							// Apply involution sign to B-blade column
							unsigned uInvB = 0;
							if (eInvRight == GA::EInv::Rev)       uInvB = blB.GetReverseSign() & 1;
							else if (eInvRight == GA::EInv::Conj) uInvB = blB.GetConjugateSign() & 1;

							unsigned uFinalSign = (uSign & 1) ^ uInvB;
							if (uFinalSign)
								matA(uIndexC, uIndexB) = -fValASigned;
							else
								matA(uIndexC, uIndexB) = fValASigned;
						} });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Inner-loop helper for <c>_EvalProductMatrix</c> (list-of-multivectors overload).
		///
		/// 	Processes one column uIndexB (blade blB) of the stacked product matrix.  For
		/// 	each blade blA of wListA[0] that yields a valid product blA ∘ blB = blC with
		/// 	blC in xMaskC, the coefficient from every element of wListA is written into the
		/// 	corresponding row of the stacked block:
		/// 	  matA(n * |xMaskC| + indexC, uIndexB) = wListA[n].GetValue(indexA) * sign
		///
		/// 	Called once per blade in xMaskB by the outer loop in the list overload of
		/// 	<c>_EvalProductMatrix</c>.  Not intended for direct use.
		/// </summary>
		///
		/// <exception cref="std::runtime_error">	Thrown on internal index errors. </exception>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <typeparam name="FuncOp">		Product sign/blade callable. </typeparam>
		/// <param name="matA">			[in,out] Stacked product matrix being filled. </param>
		/// <param name="vecwListA">		List of multivectors.  wListA[0] defines the sparsity;
		/// 	all elements provide coefficient values for their respective row blocks. </param>
		/// <param name="uIndexB">			Column index (0-based position of blB in xMaskB). </param>
		/// <param name="blB">				The B-blade corresponding to column uIndexB. </param>
		/// <param name="xMaskC">			Row index space per element (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: blA ∘ blB.  <c>false</c>: blB ∘ blA. </param>
		/// <param name="xFuncOp">			Product-specific sign/blade function. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector, typename FuncOp>
		void _EvalProductMatrix_InnerLoop(CMatrix<typename TMultivector::TValue> &matA,
										  const std::vector<TMultivector> &vecwListA,
										  const unsigned uIndexB,
										  const typename TMultivector::TBlade &blB,
										  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
										  bool bLeftToRight,
										  FuncOp xFuncOp,
										  GA::EInv eInvLeft = GA::EInv::Id,
										  GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivector::TBlade TBlade;
			typedef typename TMultivector::TValue TValue;

			const unsigned uDimC = xMaskC.Count();

			// Apply involution sign to B-blade column (computed once for this column)
			unsigned uInvB = 0;
			if (eInvRight == GA::EInv::Rev)
				uInvB = blB.GetReverseSign() & 1;
			else if (eInvRight == GA::EInv::Conj)
				uInvB = blB.GetConjugateSign() & 1;

			unsigned uSign, uIndexC;
			TBlade blC;
			const TMultivector &wA = vecwListA[0];

			wA.ForEachBladeIndex([&](const TValue &fValA, const TBlade &blA, unsigned uIndexA)
								 {
						bool bValid;

						if (bLeftToRight)
						{
							bValid = xFuncOp(uSign, blC, blA, blB);
						}
						else
						{
							bValid = xFuncOp(uSign, blC, blB, blA);
						}

						if (bValid && xMaskC.GetIndex(uIndexC, blC))
						{
							// Apply involution sign to A-blade
							unsigned uInvA = 0;
							if (eInvLeft == GA::EInv::Rev)       uInvA = blA.GetReverseSign() & 1;
							else if (eInvLeft == GA::EInv::Conj) uInvA = blA.GetConjugateSign() & 1;
							TValue fSignMul = (uInvA ^ uInvB) ? TValue(-1) : TValue(1);

							unsigned uMatrixRowOffset = 0;
							if (uSign)
							{
								ForEach(vecwListA, [&](const TMultivector& wX)
										{
											matA(uMatrixRowOffset + uIndexC, uIndexB) = -fSignMul * wX.GetValue(uIndexA);
											uMatrixRowOffset += uDimC;
										});
							}
							else
							{
								ForEach(vecwListA, [&](const TMultivector& wX)
										{
											matA(uMatrixRowOffset + uIndexC, uIndexB) = fSignMul * wX.GetValue(uIndexA);
											uMatrixRowOffset += uDimC;
										});
							}
						} });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the geometric product matrix for A acting on xMaskB, output restricted to xMaskC.
		///
		/// 	Computes M where M[k, j] encodes the contribution of input blade j in xMaskB to
		/// 	output blade k in xMaskC under left- or right-multiplication by A:
		/// 	  (A * X)^k = ∑_j M[k, j] · x^j     (bLeftToRight = true)
		/// 	  (X * A)^k = ∑_j M[k, j] · x^j     (bLeftToRight = false)
		///
		/// 	Solving M · vec(X) = vec(Y) for vec(X) yields X such that A * X = Y (or X * A = Y).
		/// 	This is the mechanism used internally by <c>GA::Inverse</c> for the case Y = 1.
		///
		/// 	Call <c>EvalProductBladeMask_GP</c> first to obtain a suitable xMaskC when the
		/// 	output subspace is not known in advance.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <param name="matA">			[out] Product matrix of size |xMaskC| × |xMaskB|. </param>
		/// <param name="wA">				The fixed-coefficient multivector A. </param>
		/// <param name="xMaskB">			Column index space — subspace of the unknown X. </param>
		/// <param name="xMaskC">			Row index space — desired output subspace. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A * X.  <c>false</c>: X * A. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductMatrix_GP(CMatrix<typename TMultivector::TValue> &matA,
								  const TMultivector &wA,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								  bool bLeftToRight = true,
								  GA::EInv eInvLeft = GA::EInv::Id,
								  GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;
			try
			{
				_EvalProductMatrix(matA, wA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								   { return GA::GPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix geometric product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the geometric product matrix from a list of multivectors (stacked rows).
		///
		/// 	Builds a stacked product matrix whose row blocks correspond to elements of
		/// 	wListA.  See <c>_EvalProductMatrix</c> (list overload) for the full description
		/// 	of the stacked layout and intended use (overdetermined / least-squares systems).
		/// </summary>
		///
		/// <typeparam name="TMultivectorX">	Multivector type. </typeparam>
		/// <param name="matA">			[out] Stacked matrix of size (|wListA|·|xMaskC|) × |xMaskB|. </param>
		/// <param name="wListA">			List of multivectors; wListA[0] defines the sparsity. </param>
		/// <param name="xMaskB">			Column index space (subspace of the common unknown X). </param>
		/// <param name="xMaskC">			Row index space per element (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: element * X.  <c>false</c>: X * element. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivectorX>
		void EvalProductMatrixArray_GP(CMatrix<typename TMultivectorX::TValue> &matA,
									   const std::vector<TMultivectorX> &wListA,
									   const GA::CBladeMask<typename TMultivectorX::TBlade> &xMaskB,
									   const GA::CBladeMask<typename TMultivectorX::TBlade> &xMaskC,
									   bool bLeftToRight = true,
									   GA::EInv eInvLeft = GA::EInv::Id,
									   GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivectorX::TValue TValue;
			typedef typename TMultivectorX::TBlade TBlade;

			try
			{
				_EvalProductMatrix(matA, wListA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								   { return GA::GPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from geometric product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the geometric product matrix for A restricted to xMaskA, acting on xMaskB.
		///
		/// 	Same as the 2-mask overload of <c>EvalProductMatrix_GP</c> but iterates over
		/// 	xMaskA instead of all non-zero blades of wA.  Blades of A outside xMaskA are
		/// 	ignored; blades inside xMaskA that are absent from wA contribute zero columns.
		/// 	Use when A inhabits a known sub-algebra (e.g. even sub-algebra for rotors).
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <param name="matA">			[out] Product matrix of size |xMaskC| × |xMaskB|. </param>
		/// <param name="wA">				The fixed-coefficient multivector A. </param>
		/// <param name="xMaskA">			Blade mask restricting which blades of A participate. </param>
		/// <param name="xMaskB">			Column index space (unknown subspace). </param>
		/// <param name="xMaskC">			Row index space (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: A * X.  <c>false</c>: X * A. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductMatrix_GP(CMatrix<typename TMultivector::TValue> &matA,
								  const TMultivector &wA,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskA,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								  bool bLeftToRight = true,
								  GA::EInv eInvLeft = GA::EInv::Id,
								  GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				_EvalProductMatrix(matA, wA, xMaskA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								   { return GA::GPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from geometric product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the inner product matrix for A acting on xMaskB, output restricted to xMaskC.
		///
		/// 	Same structure as <c>EvalProductMatrix_GP</c> but uses the inner product sign
		/// 	function (<c>GA::IPSign</c>).  The inner product reduces grade: output blades in
		/// 	xMaskC will in general be of lower grade than input blades in xMaskB.
		/// 	Solving M · vec(X) = vec(Y) yields X such that A | X = Y (or X | A = Y).
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <param name="matA">			[out] Product matrix of size |xMaskC| × |xMaskB|. </param>
		/// <param name="wA">				The fixed-coefficient multivector A. </param>
		/// <param name="xMaskB">			Column index space — subspace of the unknown X. </param>
		/// <param name="xMaskC">			Row index space — desired output subspace. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A | X.  <c>false</c>: X | A. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductMatrix_IP(CMatrix<typename TMultivector::TValue> &matA,
								  const TMultivector &wA,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								  bool bLeftToRight = true,
								  GA::EInv eInvLeft = GA::EInv::Id,
								  GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				_EvalProductMatrix(matA, wA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								   { return GA::IPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from inner product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the inner product matrix from a list of multivectors (stacked rows).
		///
		/// 	Builds a stacked product matrix for the inner product.  See
		/// 	<c>EvalProductMatrixArray_GP</c> for the full description of the stacked layout.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <param name="matA">			[out] Stacked matrix of size (|wListA|·|xMaskC|) × |xMaskB|. </param>
		/// <param name="wListA">			List of multivectors; wListA[0] defines the sparsity. </param>
		/// <param name="xMaskB">			Column index space (subspace of the common unknown X). </param>
		/// <param name="xMaskC">			Row index space per element (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: element | X.  <c>false</c>: X | element. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductMatrixArray_IP(CMatrix<typename TMultivector::TValue> &matA,
									   const std::vector<TMultivector> &wListA,
									   const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
									   const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
									   bool bLeftToRight = true,
									   GA::EInv eInvLeft = GA::EInv::Id,
									   GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				_EvalProductMatrix(matA, wListA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								   { return GA::IPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from inner product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the inner product matrix for A restricted to xMaskA, acting on xMaskB.
		///
		/// 	Same as the 2-mask overload of <c>EvalProductMatrix_IP</c> but iterates over
		/// 	xMaskA instead of all non-zero blades of wA.  See <c>EvalProductMatrix_GP</c>
		/// 	(3-mask overload) for the rationale behind the xMaskA restriction.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <param name="matA">			[out] Product matrix of size |xMaskC| × |xMaskB|. </param>
		/// <param name="wA">				The fixed-coefficient multivector A. </param>
		/// <param name="xMaskA">			Blade mask restricting which blades of A participate. </param>
		/// <param name="xMaskB">			Column index space (unknown subspace). </param>
		/// <param name="xMaskC">			Row index space (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: A | X.  <c>false</c>: X | A. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductMatrix_IP(CMatrix<typename TMultivector::TValue> &matA,
								  const TMultivector &wA,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskA,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								  bool bLeftToRight = true,
								  GA::EInv eInvLeft = GA::EInv::Id,
								  GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				_EvalProductMatrix(matA, wA, xMaskA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								   { return GA::IPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from inner product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the outer (wedge) product matrix for A acting on xMaskB, output restricted to xMaskC.
		///
		/// 	Same structure as <c>EvalProductMatrix_GP</c> but uses the outer product sign
		/// 	function (<c>GA::OPSign</c>).  The outer product raises grade: output blades in
		/// 	xMaskC will in general be of higher grade than input blades in xMaskB.
		/// 	Solving M · vec(X) = vec(Y) yields X such that A ^ X = Y (or X ^ A = Y).
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <param name="matA">			[out] Product matrix of size |xMaskC| × |xMaskB|. </param>
		/// <param name="wA">				The fixed-coefficient multivector A. </param>
		/// <param name="xMaskB">			Column index space — subspace of the unknown X. </param>
		/// <param name="xMaskC">			Row index space — desired output subspace. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A ^ X.  <c>false</c>: X ^ A. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductMatrix_OP(CMatrix<typename TMultivector::TValue> &matA,
								  const TMultivector &wA,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								  bool bLeftToRight = true,
								  GA::EInv eInvLeft = GA::EInv::Id,
								  GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				_EvalProductMatrix(matA, wA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								   { return GA::OPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from outer product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the outer product matrix from a list of multivectors (stacked rows).
		///
		/// 	Builds a stacked product matrix for the outer product.  See
		/// 	<c>EvalProductMatrixArray_GP</c> for the full description of the stacked layout.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <param name="matA">			[out] Stacked matrix of size (|wListA|·|xMaskC|) × |xMaskB|. </param>
		/// <param name="wListA">			List of multivectors; wListA[0] defines the sparsity. </param>
		/// <param name="xMaskB">			Column index space (subspace of the common unknown X). </param>
		/// <param name="xMaskC">			Row index space per element (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: element ^ X.  <c>false</c>: X ^ element. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductMatrixArray_OP(CMatrix<typename TMultivector::TValue> &matA,
									   const std::vector<TMultivector> &wListA,
									   const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
									   const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
									   bool bLeftToRight = true,
									   GA::EInv eInvLeft = GA::EInv::Id,
									   GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				_EvalProductMatrix(matA, wListA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								   { return GA::OPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from outer product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build the outer product matrix for A restricted to xMaskA, acting on xMaskB.
		///
		/// 	Same as the 2-mask overload of <c>EvalProductMatrix_OP</c> but iterates over
		/// 	xMaskA instead of all non-zero blades of wA.  See <c>EvalProductMatrix_GP</c>
		/// 	(3-mask overload) for the rationale behind the xMaskA restriction.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type. </typeparam>
		/// <param name="matA">			[out] Product matrix of size |xMaskC| × |xMaskB|. </param>
		/// <param name="wA">				The fixed-coefficient multivector A. </param>
		/// <param name="xMaskA">			Blade mask restricting which blades of A participate. </param>
		/// <param name="xMaskB">			Column index space (unknown subspace). </param>
		/// <param name="xMaskC">			Row index space (output subspace). </param>
		/// <param name="bLeftToRight">	<c>true</c>: A ^ X.  <c>false</c>: X ^ A. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductMatrix_OP(CMatrix<typename TMultivector::TValue> &matA,
								  const TMultivector &wA,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskA,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								  const GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								  bool bLeftToRight = true,
								  GA::EInv eInvLeft = GA::EInv::Id,
								  GA::EInv eInvRight = GA::EInv::Id)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				_EvalProductMatrix(matA, wA, xMaskA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								   { return GA::OPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from outer product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build a diagonal product matrix encoding the reverse sign for each blade in xMask.
		///
		/// 	The reverse of a blade of grade k introduces a sign (-1)^(k(k-1)/2),
		/// 	i.e. grades 2 and 3 mod 4 are negated.  The result is a square
		/// 	|xMask| × |xMask| diagonal matrix where M[i,i] = (+1 or -1).
		///
		/// 	Unlike <c>EvalProductMatrix_GP</c>, this function does not contract with a
		/// 	multivector; it encodes only the grade-dependent sign changes of the reverse
		/// 	operation on the blade subspace defined by xMask.
		/// </summary>
		///
		/// <typeparam name="TValue">	Coefficient value type. </typeparam>
		/// <typeparam name="TBlade">	Blade type. </typeparam>
		/// <param name="matA">	[out] Diagonal matrix of size |xMask| × |xMask| filled with ±1. </param>
		/// <param name="xMask">	Blade mask defining the index space. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TValue, typename TBlade>
		void EvalProductMatrix_Reverse(CMatrix<TValue> &matA,
									   const GA::CBladeMask<TBlade> &xMask)
		{
			try
			{
				const unsigned uDim = xMask.Count();
				matA.SetSize(uDim, uDim);
				matA.Zero();

				xMask.ForEachBlade([&](unsigned uIndex, const TBlade &bl)
								   {
						unsigned uSign = bl.GetReverseSign();
						matA(uIndex, uIndex) = (uSign & 1) ? TValue(-1) : TValue(1); });
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating reverse product matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Build a diagonal product matrix encoding the conjugate sign for each blade in xMask.
		///
		/// 	The Clifford conjugate of a blade introduces a sign
		/// 	(-1)^(k(k-1)/2 + r) where k is the grade and r is the count of
		/// 	negative-metric basis vectors in the blade.  In a pure Euclidean
		/// 	algebra (r = 0) this reduces to the reverse.
		///
		/// 	The result is a square |xMask| × |xMask| diagonal matrix where
		/// 	M[i,i] = (+1 or -1).  Use when constructing linear systems that
		/// 	involve conjugate operations on the unknown X.
		/// </summary>
		///
		/// <typeparam name="TValue">	Coefficient value type. </typeparam>
		/// <typeparam name="TBlade">	Blade type. </typeparam>
		/// <param name="matA">	[out] Diagonal matrix of size |xMask| × |xMask| filled with ±1. </param>
		/// <param name="xMask">	Blade mask defining the index space. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TValue, typename TBlade>
		void EvalProductMatrix_Conjugate(CMatrix<TValue> &matA,
										 const GA::CBladeMask<TBlade> &xMask)
		{
			try
			{
				const unsigned uDim = xMask.Count();
				matA.SetSize(uDim, uDim);
				matA.Zero();

				xMask.ForEachBlade([&](unsigned uIndex, const TBlade &bl)
								   {
						unsigned uSign = bl.GetConjugateSign();
						matA(uIndex, uIndex) = (uSign & 1) ? TValue(-1) : TValue(1); });
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating conjugate product matrix", xEx);
			}
		}

	} // namespace GA
} // namespace Tan
