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
/// \file Matrix_BladeMask.h
///
/// \brief Blade-mask prediction — compute output blade masks for GA products.
///
/// Functions to collect blade ids from multivectors into \c CBladeMask instances
/// and to predict which output blades a given product A ∘ X can produce, given
/// blade masks for A and X.  Includes inverse blade-mask prediction (given A and C,
/// what can X be?).
///
/// \sa Matrix_Product.h, Matrix_MapToBladeMask.h
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

namespace Tan
{
	namespace GA
	{
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Collect the set of blades present in a multivector into a blade mask.
		///
		/// 	A <c>CBladeMask</c> is a compact ordered set of blade ids that defines an index
		/// 	space for the coefficient vector of a multivector.  <c>EvalBladeMask</c> is
		/// 	typically the first step before building a product matrix: it establishes which
		/// 	blades will be the row and column indices of that matrix.
		///
		/// 	The mask is reset before scanning — any previously stored entries are discarded.
		///
		/// 	When <c>bOnlyNonZeroComps</c> is <c>true</c> only blades whose stored coefficient
		/// 	is non-zero (as determined by the multivector's own <c>IsZero</c> predicate) are
		/// 	inserted.  Set it to <c>false</c> to include structural zero entries — for example
		/// 	when scanning a freshly allocated <c>CDynamicMultivector</c> that has not been
		/// 	pruned and still carries zero-valued blades that must participate in the system.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type.  Must expose <c>TBlade</c>,
		/// 	<c>TValue</c>, <c>ForEachBlade</c>, and <c>IsZero</c>. </typeparam>
		/// <param name="xMask">				[out] Mask to populate.  Existing entries are cleared first. </param>
		/// <param name="wA">					Source multivector whose blades are collected. </param>
		/// <param name="bOnlyNonZeroComps">	If <c>true</c>, skip blades with a zero coefficient. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalBladeMask(GA::CBladeMask<typename TMultivector::TBlade> &xMask, const TMultivector &wA, bool bOnlyNonZeroComps)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			xMask.Reset();
			wA.ForEachBlade([&](const TValue &fValA, const TBlade &blA)
							{
						if (!bOnlyNonZeroComps || !wA.IsZero(fValA))
						{
							xMask.Insert(blA);
						} });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the set of output blades that a binary GA product A ∘ X can produce,
		/// 	given the blades present in A and a blade mask for X.
		///
		/// 	A GA product can be understood as a tensor contraction with product tensor O:
		/// 	  c^k = ∑_{i,j} a^i · x^j · O^k_{ij}
		/// 	Given fixed blade sets for A and X, this function finds every blade k for which
		/// 	at least one valid (i, j) pair exists.  The result is the smallest superset of
		/// 	blades that any A ∘ X product can ever occupy — the minimum necessary row index
		/// 	space (xMaskC) for the product matrix.
		///
		/// 	When <c>bLeftToRight</c> is <c>true</c> the product is evaluated as A ∘ X (A on
		/// 	the left, so the A-index is contracted).  When <c>false</c>, the evaluation is
		/// 	X ∘ A (A on the right, so the B-index is contracted).
		///
		/// 	When <c>bComplete</c> is <c>true</c> the function iterates to the fixed point.
		/// 	Each pass expands the working set by applying A to the accumulated output of
		/// 	the previous pass, then feeds that result back as the new xMaskB.  The final
		/// 	result is the union of all blades reachable by 1, 2, 3, … applications of A:
		/// 	  S = (A \u2218 xMaskB) ∪ (A ∘ A ∘ xMaskB) ∪ ...
		/// 	until no new blades appear.  This is the minimal subspace closed under the
		/// 	repeated left- (or right-) multiplication by A's blades — ensuring the
		/// 	product matrix built from it is square and self-consistent.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type.  Must expose <c>TBlade</c>,
		/// 	<c>TValue</c>, and <c>ForEachBlade</c>. </typeparam>
		/// <typeparam name="FuncOp">			Callable with signature
		/// 	<c>bool(unsigned&amp; uSign, TBlade&amp; blC, const TBlade&amp; blA, const TBlade&amp; blB)</c>.
		/// 	Returns <c>true</c> when blA ∘ blB is a valid product blade, writing the result
		/// 	into <c>blC</c> and the geometric sign (0 = positive, 1 = negative) into <c>uSign</c>. </typeparam>
		/// <param name="xMaskC">		[out] Output blade mask — the set of blades reachable by A ∘ X. </param>
		/// <param name="wA">			The fixed-coefficient operand (left or right depending on bLeftToRight). </param>
		/// <param name="xMaskB">		Blade mask representing the subspace of the unknown X. </param>
		/// <param name="bLeftToRight">	<c>true</c>: compute A ∘ X.  <c>false</c>: compute X ∘ A. </param>
		/// <param name="bComplete">		<c>true</c>: iterate to the fixed-point sub-algebra closure. </param>
		/// <param name="xFuncOp">		Product-specific sign/blade function (GP, IP, or OP). </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector, typename FuncOp>
		void _EvalProductBladeMask(GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
								   const TMultivector &wA,
								   const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
								   bool bLeftToRight,
								   bool bComplete,
								   FuncOp xFuncOp)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			// Find all possible result blades
			xMaskC.Reset();

			if (!bComplete)
			{
				wA.ForEachBlade([&](const TValue &fValA, const TBlade &blA)
								{ _EvalProductBladeMask_InnerLoop(xMaskC, blA, xMaskB, bLeftToRight, xFuncOp); });
			}
			else
			{
				GA::CBladeMask<typename TMultivector::TBlade> xNewMaskC, xNewMaskB;
				xNewMaskB = xMaskB;

				do
				{
					xMaskC = xNewMaskC;
					wA.ForEachBlade([&](const TValue &fValA, const TBlade &blA)
									{ _EvalProductBladeMask_InnerLoop(xNewMaskC, blA, xNewMaskB, bLeftToRight, xFuncOp); });
					xNewMaskB = xNewMaskC;
				} while (xMaskC != xNewMaskC);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Collect the set of output blades that a binary GA product A ∘ X can produce,
		/// 	given a blade mask for A and a blade mask for X.
		///
		/// 	This overload takes <c>xMaskA</c> (a <c>CBladeMask</c>) instead of a
		/// 	multivector <c>wA</c>.  It mirrors the 3-mask <c>_EvalProductMatrix</c>
		/// 	overload and is used when only the blade subspace of A is known, without
		/// 	a full multivector instance.
		///
		/// 	See the MV-based overload for the full semantics of <c>bLeftToRight</c>
		/// 	and <c>bComplete</c>.
		/// </summary>
		///
		/// <typeparam name="TBlade">	Blade type. </typeparam>
		/// <typeparam name="FuncOp">	Product sign/blade callable. </typeparam>
		/// <param name="xMaskC">		[out] Output blade mask — blades reachable by A ∘ X. </param>
		/// <param name="xMaskA">		Blade mask of the fixed operand A. </param>
		/// <param name="xMaskB">		Blade mask of the unknown operand X. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A ∘ X.  <c>false</c>: X ∘ A. </param>
		/// <param name="bComplete">		<c>true</c>: iterate to the fixed-point sub-algebra closure. </param>
		/// <param name="xFuncOp">		Product-specific sign/blade function (GP, IP, or OP). </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TBlade, typename FuncOp>
		void _EvalProductBladeMask(GA::CBladeMask<TBlade> &xMaskC,
								   const GA::CBladeMask<TBlade> &xMaskA,
								   const GA::CBladeMask<TBlade> &xMaskB,
								   bool bLeftToRight,
								   bool bComplete,
								   FuncOp xFuncOp)
		{
			xMaskC.Reset();

			if (!bComplete)
			{
				xMaskA.ForEachBlade([&](unsigned, const TBlade &blA)
									{ _EvalProductBladeMask_InnerLoop(xMaskC, blA, xMaskB, bLeftToRight, xFuncOp); });
			}
			else
			{
				GA::CBladeMask<TBlade> xNewMaskC, xNewMaskB;
				xNewMaskB = xMaskB;

				do
				{
					xMaskC = xNewMaskC;
					xMaskA.ForEachBlade([&](unsigned, const TBlade &blA)
										{ _EvalProductBladeMask_InnerLoop(xNewMaskC, blA, xNewMaskB, bLeftToRight, xFuncOp); });
					xNewMaskB = xNewMaskC;
				} while (xMaskC != xNewMaskC);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Inner-loop helper for <c>_EvalProductBladeMask</c>.
		///
		/// 	For a single blade <c>blA</c> taken from A, iterates over every blade in
		/// 	<c>xMaskB</c> and computes their pairwise product via <c>xFuncOp</c>.  Every
		/// 	valid result blade is inserted into <c>xMaskC</c>.
		///
		/// 	Called once per non-zero blade of A by the outer loop in
		/// 	<c>_EvalProductBladeMask</c>.  Not intended for direct use.
		/// </summary>
		///
		/// <typeparam name="TBlade">	Blade type. </typeparam>
		/// <typeparam name="FuncOp">	Product sign/blade callable (same contract as in <c>_EvalProductBladeMask</c>). </typeparam>
		/// <param name="xMaskC">		[in,out] Accumulator for reachable output blades. </param>
		/// <param name="blA">			Single blade of A being processed in this iteration. </param>
		/// <param name="xMaskB">		Blade mask of the X operand. </param>
		/// <param name="bLeftToRight">	<c>true</c>: evaluate blA ∘ blB.  <c>false</c>: evaluate blB ∘ blA. </param>
		/// <param name="xFuncOp">		Product-specific sign/blade function. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TBlade, typename FuncOp>
		void _EvalProductBladeMask_InnerLoop(GA::CBladeMask<TBlade> &xMaskC, const TBlade &blA, const GA::CBladeMask<TBlade> &xMaskB, bool bLeftToRight, FuncOp xFuncOp)
		{
			unsigned uSign;
			TBlade blC;

			xMaskB.ForEachBlade([&](unsigned uIndex, const TBlade &blB)
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

						if (bValid)
						{
							xMaskC.Insert(blC);
						} });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the output blade mask of the geometric product A * X (or X * A).
		///
		/// 	Delegates to <c>_EvalProductBladeMask</c> using <c>GA::GPSign</c>.
		/// 	See <c>_EvalProductBladeMask</c> for the full semantics of <c>bLeftToRight</c>
		/// 	and <c>bComplete</c>.
		///
		/// 	Typical use: call this before <c>EvalProductMatrix_GP</c> to determine the
		/// 	output subspace (xMaskC) that the product matrix must map into.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type exposing <c>TBlade</c> and <c>ForEachBlade</c>. </typeparam>
		/// <param name="xMaskC">		[out] Output blade mask — blades reachable by A * X (or X * A). </param>
		/// <param name="wA">			The fixed-coefficient operand A. </param>
		/// <param name="xMaskB">		Blade mask of the unknown operand X. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A * X.  <c>false</c>: X * A. </param>
		/// <param name="bComplete">		<c>true</c>: iterate to the fixed-point sub-algebra closure. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductBladeMask_GP(GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
									 const TMultivector &wA,
									 const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
									 bool bLeftToRight = true,
									 bool bComplete = false)
		{
			typedef typename TMultivector::TBlade TBlade;

			_EvalProductBladeMask(xMaskC, wA, xMaskB, bLeftToRight, bComplete,
								  [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								  {
									  return GA::GPSign(uSign, blC, blA, blB);
								  });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the output blade mask of the geometric product from a mask for A.
		///
		/// 	Mask-based overload of <c>EvalProductBladeMask_GP</c>.  Takes <c>xMaskA</c>
		/// 	instead of a multivector <c>wA</c>.  Useful when only the blade subspace of
		/// 	A is known, or when A is expressed as a list of basis multivectors.
		/// </summary>
		///
		/// <typeparam name="TBlade">	Blade type. </typeparam>
		/// <param name="xMaskC">		[out] Output blade mask — blades reachable by A * X (or X * A). </param>
		/// <param name="xMaskA">		Blade mask of the fixed operand A. </param>
		/// <param name="xMaskB">		Blade mask of the unknown operand X. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A * X.  <c>false</c>: X * A. </param>
		/// <param name="bComplete">		<c>true</c>: iterate to the fixed-point sub-algebra closure. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TBlade>
		void EvalProductBladeMask_GP(GA::CBladeMask<TBlade> &xMaskC,
									 const GA::CBladeMask<TBlade> &xMaskA,
									 const GA::CBladeMask<TBlade> &xMaskB,
									 bool bLeftToRight = true,
									 bool bComplete = false)
		{
			_EvalProductBladeMask(xMaskC, xMaskA, xMaskB, bLeftToRight, bComplete,
								  [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								  {
									  return GA::GPSign(uSign, blC, blA, blB);
								  });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the output blade mask of the inner product A | X (or X | A).
		///
		/// 	Delegates to <c>_EvalProductBladeMask</c> using <c>GA::IPSign</c>.
		/// 	The inner product reduces grade, so xMaskC will in general contain
		/// 	lower-grade blades than xMaskB.  See <c>_EvalProductBladeMask</c> for the
		/// 	full semantics of <c>bLeftToRight</c> and <c>bComplete</c>.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type exposing <c>TBlade</c> and <c>ForEachBlade</c>. </typeparam>
		/// <param name="xMaskC">		[out] Output blade mask — blades reachable by A | X (or X | A). </param>
		/// <param name="wA">			The fixed-coefficient operand A. </param>
		/// <param name="xMaskB">		Blade mask of the unknown operand X. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A | X.  <c>false</c>: X | A. </param>
		/// <param name="bComplete">		<c>true</c>: iterate to the fixed-point sub-algebra closure. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductBladeMask_IP(GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
									 const TMultivector &wA,
									 const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
									 bool bLeftToRight = true,
									 bool bComplete = false)
		{
			typedef typename TMultivector::TBlade TBlade;

			_EvalProductBladeMask(xMaskC, wA, xMaskB, bLeftToRight, bComplete,
								  [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								  {
									  return GA::IPSign(uSign, blC, blA, blB);
								  });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the output blade mask of the inner product from a mask for A.
		///
		/// 	Mask-based overload of <c>EvalProductBladeMask_IP</c>.  Takes <c>xMaskA</c>
		/// 	instead of a multivector <c>wA</c>.
		/// </summary>
		///
		/// <typeparam name="TBlade">	Blade type. </typeparam>
		/// <param name="xMaskC">		[out] Output blade mask — blades reachable by A | X (or X | A). </param>
		/// <param name="xMaskA">		Blade mask of the fixed operand A. </param>
		/// <param name="xMaskB">		Blade mask of the unknown operand X. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A | X.  <c>false</c>: X | A. </param>
		/// <param name="bComplete">		<c>true</c>: iterate to the fixed-point sub-algebra closure. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TBlade>
		void EvalProductBladeMask_IP(GA::CBladeMask<TBlade> &xMaskC,
									 const GA::CBladeMask<TBlade> &xMaskA,
									 const GA::CBladeMask<TBlade> &xMaskB,
									 bool bLeftToRight = true,
									 bool bComplete = false)
		{
			_EvalProductBladeMask(xMaskC, xMaskA, xMaskB, bLeftToRight, bComplete,
								  [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								  {
									  return GA::IPSign(uSign, blC, blA, blB);
								  });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the output blade mask of the outer (wedge) product A ^ X (or X ^ A).
		///
		/// 	Delegates to <c>_EvalProductBladeMask</c> using <c>GA::OPSign</c>.
		/// 	The outer product raises grade, so xMaskC will in general contain higher-grade
		/// 	blades than either operand.  See <c>_EvalProductBladeMask</c> for the full
		/// 	semantics of <c>bLeftToRight</c> and <c>bComplete</c>.
		/// </summary>
		///
		/// <typeparam name="TMultivector">	Multivector type exposing <c>TBlade</c> and <c>ForEachBlade</c>. </typeparam>
		/// <param name="xMaskC">		[out] Output blade mask — blades reachable by A ^ X (or X ^ A). </param>
		/// <param name="wA">			The fixed-coefficient operand A. </param>
		/// <param name="xMaskB">		Blade mask of the unknown operand X. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A ^ X.  <c>false</c>: X ^ A. </param>
		/// <param name="bComplete">		<c>true</c>: iterate to the fixed-point sub-algebra closure. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		void EvalProductBladeMask_OP(GA::CBladeMask<typename TMultivector::TBlade> &xMaskC,
									 const TMultivector &wA,
									 const GA::CBladeMask<typename TMultivector::TBlade> &xMaskB,
									 bool bLeftToRight = true,
									 bool bComplete = false)
		{
			typedef typename TMultivector::TBlade TBlade;

			_EvalProductBladeMask(xMaskC, wA, xMaskB, bLeftToRight, bComplete,
								  [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								  {
									  return GA::OPSign(uSign, blC, blA, blB);
								  });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the output blade mask of the outer (wedge) product from a mask for A.
		///
		/// 	Mask-based overload of <c>EvalProductBladeMask_OP</c>.  Takes <c>xMaskA</c>
		/// 	instead of a multivector <c>wA</c>.
		/// </summary>
		///
		/// <typeparam name="TBlade">	Blade type. </typeparam>
		/// <param name="xMaskC">		[out] Output blade mask — blades reachable by A ^ X (or X ^ A). </param>
		/// <param name="xMaskA">		Blade mask of the fixed operand A. </param>
		/// <param name="xMaskB">		Blade mask of the unknown operand X. </param>
		/// <param name="bLeftToRight">	<c>true</c>: A ^ X.  <c>false</c>: X ^ A. </param>
		/// <param name="bComplete">		<c>true</c>: iterate to the fixed-point sub-algebra closure. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TBlade>
		void EvalProductBladeMask_OP(GA::CBladeMask<TBlade> &xMaskC,
									 const GA::CBladeMask<TBlade> &xMaskA,
									 const GA::CBladeMask<TBlade> &xMaskB,
									 bool bLeftToRight = true,
									 bool bComplete = false)
		{
			_EvalProductBladeMask(xMaskC, xMaskA, xMaskB, bLeftToRight, bComplete,
								  [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
								  {
									  return GA::OPSign(uSign, blC, blA, blB);
								  });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the maximal set of blades that the unknown X can contain,
		/// 	given the blade masks of the fixed operand A and the result C.
		///
		/// 	For A ∘ X = C, this computes the largest blade mask xMaskB such that every
		/// 	blade in it, when multiplied by some blade in xMaskA, can produce a blade
		/// 	in xMaskC.  Iterates over all 2^D blades of the algebra.
		/// </summary>
		template <typename TBlade, typename FuncOp>
		void _EvalProductBladeMaskInv(GA::CBladeMask<TBlade> &xMaskB,
									  const GA::CBladeMask<TBlade> &xMaskA,
									  const GA::CBladeMask<TBlade> &xMaskC,
									  bool bLeftToRight,
									  FuncOp xFuncOp)
		{
			xMaskB.Reset();
			unsigned uSign;
			TBlade blC;

			for (unsigned uBladeId = 0; uBladeId < TBlade::AlgebraDimension; ++uBladeId)
			{
				TBlade blB(uBladeId);
				bool bFound = false;

				xMaskA.ForEachBladeTest([&](unsigned, const TBlade &blA) -> bool
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

							if (bValid && xMaskC.Contains(blC))
							{
								bFound = true;
								return false;
							}
							return true; });

				if (bFound)
				{
					xMaskB.Insert(blB);
				}
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the maximal B-mask for A * X = C (or X * A = C).
		/// </summary>
		template <typename TBlade>
		void EvalProductBladeMaskInv_GP(GA::CBladeMask<TBlade> &xMaskB,
										const GA::CBladeMask<TBlade> &xMaskA,
										const GA::CBladeMask<TBlade> &xMaskC,
										bool bLeftToRight = true)
		{
			_EvalProductBladeMaskInv(xMaskB, xMaskA, xMaskC, bLeftToRight,
									 [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
									 {
										 return GA::GPSign(uSign, blC, blA, blB);
									 });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the maximal B-mask for A | X = C (or X | A = C).
		/// </summary>
		template <typename TBlade>
		void EvalProductBladeMaskInv_IP(GA::CBladeMask<TBlade> &xMaskB,
										const GA::CBladeMask<TBlade> &xMaskA,
										const GA::CBladeMask<TBlade> &xMaskC,
										bool bLeftToRight = true)
		{
			_EvalProductBladeMaskInv(xMaskB, xMaskA, xMaskC, bLeftToRight,
									 [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
									 {
										 return GA::IPSign(uSign, blC, blA, blB);
									 });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Predict the maximal B-mask for A ^ X = C (or X ^ A = C).
		/// </summary>
		template <typename TBlade>
		void EvalProductBladeMaskInv_OP(GA::CBladeMask<TBlade> &xMaskB,
										const GA::CBladeMask<TBlade> &xMaskA,
										const GA::CBladeMask<TBlade> &xMaskC,
										bool bLeftToRight = true)
		{
			_EvalProductBladeMaskInv(xMaskB, xMaskA, xMaskC, bLeftToRight,
									 [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
									 {
										 return GA::OPSign(uSign, blC, blA, blB);
									 });
		}

	} // namespace GA
} // namespace Tan
