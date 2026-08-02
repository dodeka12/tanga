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

#include <utility>
#include <vector>

#include "MV_Operators.h"

namespace Tan
{
	namespace GA
	{
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the inverse of a blade.
		///
		/// 	Given a blade A, its inverse is defined as:
		/// 	  A^{-1} = reverse(A) / IP(A, reverse(A))
		///
		/// 	The denominator IP(A, reverse(A)) is a scalar for any blade. If it is zero,
		/// 	the blade is not invertible (e.g. a null blade in a degenerate metric).
		///
		/// 	The caller must ensure that the input multivector is a blade (i.e. the outer
		/// 	product of grade-1 vectors). The behaviour is undefined for general multivectors.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wA">The blade whose inverse is to be computed.</param>
		///
		/// <returns>The inverse blade A^{-1}.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		TMultivector InverseBlade(const TMultivector& wA)
		{
			typedef typename TMultivector::TValue TValue;

			try
			{
				// Compute IP(A, reverse(A)), which yields a scalar for a blade
				TMultivector wIP(wA.GetValuePrecision());
				IP_Reverse(wIP, wA, false, wA, true);

				// Extract the scalar part
				TValue fScalar = Scalar(wIP);

				if (fScalar == TValue(0))
				{
					TAN_THROW_RT("Blade is not invertible: IP(A, reverse(A)) is zero");
				}

				// A^{-1} = reverse(A) / scalar
				TMultivector wRevA = GetReverse(wA);
				return wRevA / fScalar;
			}
			catch (std::exception& xEx)	
			{
				TAN_RETHROW("Error computing blade inverse", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the pseudo-inverse of a blade.
		///
		/// 	Given a blade A, its pseudo-inverse is defined as:
		/// 	  A^{-1} = conjugate(A) / IP(A, conjugate(A))
		///
		/// 	This replaces the reverse with the conjugate, which can be useful in metrics
		/// 	where IP(A, reverse(A)) vanishes but IP(A, conjugate(A)) does not (e.g. for
		/// 	null blades in PGA).
		///
		/// 	The denominator IP(A, conjugate(A)) is a scalar for any blade. If it is zero,
		/// 	the blade is not pseudo-invertible.
		///
		/// 	The caller must ensure that the input multivector is a blade (i.e. the outer
		/// 	product of grade-1 vectors). The behaviour is undefined for general multivectors.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wA">The blade whose pseudo-inverse is to be computed.</param>
		///
		/// <returns>The pseudo-inverse blade.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		TMultivector PseudoInverseBlade(const TMultivector& wA)
		{
			typedef typename TMultivector::TValue TValue;

			try
			{
				// Compute IP(A, conjugate(A)), which yields a scalar for a blade
				TMultivector wIP(wA.GetValuePrecision());
				IP_Conjugate(wIP, wA, false, wA, true);

				// Extract the scalar part
				TValue fScalar = Scalar(wIP);

				if (fScalar == TValue(0))
				{
					TAN_THROW_RT("Blade is not pseudo-invertible: IP(A, conjugate(A)) is zero");
				}

				// Pseudo-inverse = conjugate(A) / scalar
				TMultivector wConjA = GetConjugate(wA);
				return wConjA / fScalar;
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade pseudo-inverse", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Factorize a blade A_k of grade k into k normalized grade-1 vectors.
		///
		/// 	The algorithm:
		/// 	  1. Verify all non-zero elements of wA have the same grade k.
		/// 	  2. Set B = wA.
		/// 	  3. For j = 1 .. k-1:
		/// 	     a. Project all standard basis vectors onto B (using ProjectUnsafe).
		/// 	     b. Select the basis-vector projection with the largest magnitude.
		/// 	     c. Normalize it and store as factor n_j.
		/// 	     d. B = IP(conjugate(n_j), B)  (peel off one factor).
		/// 	  4. Normalize the final B and store as the last factor n_k.
		///
		/// 	Returns a vector of k normalized grade-1 multivectors whose outer product
		/// 	gives the original blade (up to scale).
		///
		/// 	The caller must ensure that wA is a blade (outer product of k vectors).
		/// 	Behaviour is undefined otherwise.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wA">The blade to factorize.</param>
		///
		/// <returns>Vector of k normalized grade-1 multivectors (the factors).</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		std::vector<TMultivector> FactorizeBlade(const TMultivector& wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				// Step 1: Determine the grade k of the blade
				unsigned uGradeK = 0;
				bool bGradeSet = false;

				wA.ForEachBladeTest([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							if (wA.IsZero(fValA))
							{
								return true;
							}

							unsigned uGrade = blA.GetGrade();

							if (!bGradeSet)
							{
								uGradeK = uGrade;
								bGradeSet = true;
							}
							else if (uGrade != uGradeK)
							{
								TAN_THROW_RT("All non-zero components of the blade must be of the same grade");
							}

							return true;
						});

				if (!bGradeSet || uGradeK == 0)
				{
					TAN_THROW_RT("Blade must have grade >= 1");
				}

				std::vector<TMultivector> vecFactors;
				vecFactors.reserve(uGradeK);

				// Build the vector of standard basis vectors (grade-1 blades)
				std::vector<TMultivector> vecBasis;

				for (unsigned uBit = 0; uBit < TMultivector::VectorSpaceDimension; ++uBit)
				{
					TBlade blBasis;
					blBasis.SetBlade(1u << uBit);

					TMultivector wE(wA.GetValuePrecision());
					wE.SetValueBlade(TValue(1), blBasis);
					vecBasis.push_back(std::move(wE));
				}

				// Step 2: Set running blade B = wA
				TMultivector wB(wA);

				// Step 3: Loop j = 1 .. k-1
				for (unsigned uJ = 1; uJ < uGradeK; ++uJ)
				{
					// Project all basis vectors onto B
					std::vector<TMultivector> vecProj;
					ProjectUnsafe(vecProj, wB, vecBasis);

					// Find the projection with the largest magnitude
					TValue fMaxMag = TValue(0);
					size_t uMaxIdx = 0;

					for (size_t uIdx = 0; uIdx < vecProj.size(); ++uIdx)
					{
						TValue fMag = MagnitudeSquared(vecProj[uIdx]);
						if (fMag > fMaxMag)
						{
							fMaxMag = fMag;
							uMaxIdx = uIdx;
						}
					}

					if (fMaxMag == TValue(0))
					{
						TAN_THROW_RT("Cannot factorize blade: largest basis-vector projection has zero magnitude");
					}

					// Normalize the selected projection
					TValue fMag = Magnitude(vecProj[uMaxIdx]);
					TMultivector wN_j = vecProj[uMaxIdx] / fMag;
					vecFactors.push_back(std::move(wN_j));

					// Peel off the factor: B = IP(conjugate(n_j), B)
					TMultivector wNewB(wA.GetValuePrecision());
					IP_Conjugate(wNewB, /* wA = */ vecFactors.back(), /* bConjA = */ true,
													/* wB = */ wB,               /* bConjB = */ false);
					wB = std::move(wNewB);
				}

				// Step 4: Normalize the final B and store as the last factor
				TValue fMagB = Magnitude(wB);

				if (fMagB == TValue(0))
				{
					TAN_THROW_RT("Remaining factor has zero magnitude after peeling off factors");
				}

				TMultivector wB_norm = wB / fMagB;
				vecFactors.push_back(std::move(wB_norm));

				return vecFactors;
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error factorizing blade", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the join of two blades A_k and B_l.
		///
		/// 	The join J is the blade of smallest grade that contains both A_k and B_l,
		/// 	i.e. the span of the union of their factor vectors.
		///
		/// 	Algorithm:
		/// 	  1. Let J be the blade of higher grade, factorize the lower-grade blade
		/// 	     into an orthonormal set {n_j} via FactorizeBlade().
		/// 	  2. Repeat:
		/// 	     a. Reject all n_j from J using RejectUnsafe.
		/// 	     b. Select the rejection with the largest magnitude.
		/// 	     c. If its magnitude is zero (up to precision), normalize J and return.
		/// 	     d. Normalize the selected rejection vector.
		/// 	     e. J = OP(J, normalized rejection vector).
		///
		/// 	The caller must ensure that both wA and wB are blades. Behaviour is
		/// 	undefined otherwise.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wA">The first blade.</param>
		/// <param name="wB">The second blade.</param>
		///
		/// <returns>The join blade J.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		TMultivector Join(const TMultivector& wA, const TMultivector& wB)
		{
			typedef typename TMultivector::TValue TValue;

			try
			{
				// Determine the grade of each blade
				unsigned uGradeA = 0;
				wA.ForEachBladeTest([&](const TValue& fVal, const typename TMultivector::TBlade& bl) -> bool
						{
							if (!wA.IsZero(fVal))
							{
								bl.GetGrade(uGradeA);
								return false;
							}
							return true;
						});

				unsigned uGradeB = 0;
				wB.ForEachBladeTest([&](const TValue& fVal, const typename TMultivector::TBlade& bl) -> bool
						{
							if (!wB.IsZero(fVal))
							{
								bl.GetGrade(uGradeB);
								return false;
							}
							return true;
						});

				// Select the larger blade as J, factorize the smaller one
				TMultivector wJ;
				std::vector<TMultivector> vecN;

				if (uGradeA >= uGradeB)
				{
					wJ = wA;
					vecN = FactorizeBlade(wB);
				}
				else
				{
					wJ = wB;
					vecN = FactorizeBlade(wA);
				}

				TValue fPrecision = wJ.GetValuePrecision();

				while (true)
				{
					// Reject all factor vectors from J
					std::vector<TMultivector> vecRej;
					RejectUnsafe(vecRej, wJ, vecN);

					// Find the rejection with the largest magnitude
					TValue fMaxMag = TValue(0);
					size_t uMaxIdx = 0;

					for (size_t uIdx = 0; uIdx < vecRej.size(); ++uIdx)
					{
						TValue fMag = MagnitudeSquared(vecRej[uIdx]);
						if (fMag > fMaxMag)
						{
							fMaxMag = fMag;
							uMaxIdx = uIdx;
						}
					}

					// If all rejections are zero (up to precision), we are done
					if (fMaxMag <= fPrecision)
					{
						TValue fMagJ = Magnitude(wJ);
						if (fMagJ == TValue(0))
						{
							TAN_THROW_RT("Join result has zero magnitude");
						}
						return wJ / fMagJ;
					}

					// Normalize the selected rejection vector
					TValue fMag = Magnitude(vecRej[uMaxIdx]);
					TMultivector wV = vecRej[uMaxIdx] / fMag;

					// J = OP(J, wV)
					TMultivector wNewJ(wJ.GetValuePrecision());
					OP(wNewJ, wJ, wV);
					wJ = std::move(wNewJ);
				}
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade join", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Factorize a versor V into its scale and a set of normalized grade-1
		/// 	factor vectors {n_j}.
		///
		/// 	A versor is the geometric product of a number of grade-1 vectors.
		/// 	The geometric product scale * n_1 * n_2 * ... * n_m gives V.
		///
		/// 	Algorithm:
		/// 	  1. While the maximum grade of V > 0:
		/// 	     a. A = GetGradeProjection(V, maxGrade)
		/// 	     b. {a_i} = FactorizeBlade(A)
		/// 	     c. Find first a_i with MagnitudeSquared != 0, store as n_j
		/// 	     d. V = GP(V, n_j)
		/// 	  2. Return V_remaining (scalar scale) and {n_j}
		///
		/// 	The caller must ensure that wV is a versor.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wV">The versor to factorize.</param>
		///
		/// <returns>Pair of (scale multivector, vector of factor vectors).</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		std::pair<TMultivector, std::vector<TMultivector>> FactorizeVersor(const TMultivector& wV)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				std::vector<TMultivector> vecFactors;
				TMultivector wRemaining(wV);

				while (true)
				{
					unsigned uMaxGrade = 0;
					bool bHasNonScalar = false;

					wRemaining.ForEachBladeTest([&](const TValue& fVal, const TBlade& bl) -> bool
							{
								if (wRemaining.IsZero(fVal))
									return true;
								unsigned uGrade = bl.GetGrade();
								if (uGrade > 0)
								{
									bHasNonScalar = true;
									if (uGrade > uMaxGrade)
										uMaxGrade = uGrade;
								}
								return true;
							});

					if (!bHasNonScalar)
						break;

					TMultivector wA = GetGradeProjection(wRemaining, uMaxGrade);
					std::vector<TMultivector> vecA = FactorizeBlade(wA);

					TMultivector wN_j;
					bool bFound = false;

					for (size_t uIdx = 0; uIdx < vecA.size(); ++uIdx)
					{
						TValue fMagSq = MagnitudeSquared(vecA[uIdx]);
						if (fMagSq != TValue(0))
						{
							wN_j = vecA[uIdx];
							bFound = true;
							break;
						}
					}

					if (!bFound)
					{
						TAN_THROW_RT("Cannot factorize versor: all factor vectors of max-grade blade are null");
					}

					TValue fMag = Magnitude(wN_j);
					wN_j = wN_j / fMag;
					vecFactors.push_back(wN_j);

					TMultivector wNewV(wRemaining.GetValuePrecision());
					GP(wNewV, wRemaining, wN_j);
					wRemaining = std::move(wNewV);
				}

				TMultivector wScale = GetGradeProjection(wRemaining, 0);

				return std::make_pair(wScale, vecFactors);
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error factorizing versor", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Project a multivector onto a blade without grade validation.
		///
		/// 	Performs proj_{N_l}(A_k) = IP( IP(A_k, conjugate(N_l)), N_l ) directly.
		///
		/// 	The caller must ensure that:
		/// 	  - N_l has components of only one grade (say l).
		/// 	  - Every non-zero component of A_k has grade k with 1 <= k <= l.
		/// 	No checks are performed; behaviour is undefined if these constraints are not met.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wA">The multivector A_k to be projected.</param>
		/// <param name="wN">The blade N_l to project onto.</param>
		///
		/// <returns>The projection of A_k onto N_l.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		TMultivector ProjectUnsafe(const TMultivector& wA, const TMultivector& wN)
		{
			try
			{
				// Step 1: wX = IP(A_k, conjugate(N_l))
				TMultivector wX(wA.GetValuePrecision());
				IP_Conjugate(wX, wA, false, wN, true);

				// Step 2: wResult = IP(wX, N_l)
				TMultivector wResult(wA.GetValuePrecision());
				IP(wResult, wX, wN);

				return wResult;
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade projection", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Project each multivector in a vector onto the same blade, without grade
		/// 	validation.
		///
		/// 	See ProjectUnsafe() for the per-element operation. The output vector is
		/// 	resized to match the input.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="vecwC">	   [out] Result vector of projected multivectors.</param>
		/// <param name="wN">		   The blade N_l to project onto.</param>
		/// <param name="vecwA">   The vector of multivectors to project.</param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		void ProjectUnsafe(std::vector<TMultivector>& vecwC, const TMultivector& wN, const std::vector<TMultivector>& vecwA)
		{
			try
			{
				vecwC.resize(vecwA.size());

				ForEachIndex(vecwA, [&](const TMultivector& wA, size_t uIdx)
						{
							vecwC[uIdx] = ProjectUnsafe(wA, wN);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade projection", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Project a multivector A_k (whose non-zero components have grades 1..k) onto a
		/// 	blade N_l of grade l.
		///
		/// 	The projection is defined as:
		/// 	  proj_{N_l}(A_k) = IP( IP(A_k, conjugate(N_l)), N_l )
		///
		/// 	Validates grade constraints, then delegates to ProjectUnsafe().
		///
		/// 	The caller must ensure that:
		/// 	  - N_l has components of only one grade (say l).
		/// 	  - Every non-zero component of A_k has grade k with 1 <= k <= l.
		///
		/// 	A_k need not be a blade; it may be a general multivector as long as the grade
		/// 	constraints are satisfied.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wA">The multivector A_k to be projected.</param>
		/// <param name="wN">The blade N_l to project onto.</param>
		///
		/// <returns>The projection of A_k onto N_l.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		TMultivector Project(const TMultivector& wA, const TMultivector& wN)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				// Validate that N_l has components of only one grade
				unsigned uGradeN = 0;
				bool bGradeNSet = false;

				wN.ForEachBladeTest([&](const TValue& fValN, const TBlade& blN) -> bool
						{
							if (wN.IsZero(fValN))
							{
								return true;
							}

							unsigned uGrade;
							blN.GetGrade(uGrade);

							if (!bGradeNSet)
							{
								uGradeN = uGrade;
								bGradeNSet = true;
							}
							else if (uGrade != uGradeN)
							{
								TAN_THROW_RT("N_l must have components of only one grade");
							}

							return true;
						});

				// If N_l is zero, return a zero result
				if (!bGradeNSet)
				{
					TMultivector wResult(wA.GetValuePrecision());
					return wResult;
				}

				// Validate that every non-zero element of A_k has grade in [1, uGradeN]
				wA.ForEachBladeTest([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							if (wA.IsZero(fValA))
							{
								return true;
							}

							unsigned uGradeA;
							blA.GetGrade(uGradeA);

							if (uGradeA < 1 || uGradeA > uGradeN)
							{
								TAN_THROW_RT("A_k contains a component whose grade is not in [1, grade(N_l)]");
							}

							return true;
						});

				return ProjectUnsafe(wA, wN);
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade projection", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Project each multivector in a vector onto the same blade, with grade
		/// 	validation.
		///
		/// 	Validates the blade N_l once (not per element). Each element of vecwA is
		/// 	validated and projected. The output vector is resized to match the input.
		///
		/// 	See Project() for grade constraints.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="vecwC">	   [out] Result vector of projected multivectors.</param>
		/// <param name="wN">		   The blade N_l to project onto.</param>
		/// <param name="vecwA">   The vector of multivectors to project.</param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		void Project(std::vector<TMultivector>& vecwC, const TMultivector& wN, const std::vector<TMultivector>& vecwA)
		{
			try
			{
				vecwC.resize(vecwA.size());

				ForEachIndex(vecwA, [&](const TMultivector& wA, size_t uIdx)
						{
							vecwC[uIdx] = Project(wA, wN);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade projection", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the rejection of a multivector from a blade without grade validation.
		///
		/// 	Performs rej_{N_l}(A_k) = A_k - ProjectUnsafe(A_k, N_l) directly.
		///
		/// 	The caller must ensure that:
		/// 	  - N_l has components of only one grade (say l).
		/// 	  - Every non-zero component of A_k has grade k with 1 <= k <= l.
		/// 	No checks are performed; behaviour is undefined if these constraints are not met.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wA">The multivector A_k from which to reject.</param>
		/// <param name="wN">The blade N_l to reject from.</param>
		///
		/// <returns>The rejection of A_k from N_l.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		TMultivector RejectUnsafe(const TMultivector& wA, const TMultivector& wN)
		{
			try
			{
				TMultivector wProj = ProjectUnsafe(wA, wN);
				TMultivector wResult(wA.GetValuePrecision());
				Sub(wResult, wA, wProj);
				return wResult;
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade rejection", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the rejection of each multivector in a vector from the same blade,
		/// 	without grade validation.
		///
		/// 	See RejectUnsafe() for the per-element operation. The output vector is
		/// 	resized to match the input.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="vecwC">	   [out] Result vector of rejected multivectors.</param>
		/// <param name="wN">		   The blade N_l to reject from.</param>
		/// <param name="vecwA">   The vector of multivectors to reject.</param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		void RejectUnsafe(std::vector<TMultivector>& vecwC, const TMultivector& wN, const std::vector<TMultivector>& vecwA)
		{
			try
			{
				vecwC.resize(vecwA.size());

				ForEachIndex(vecwA, [&](const TMultivector& wA, size_t uIdx)
						{
							vecwC[uIdx] = RejectUnsafe(wA, wN);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade rejection", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the rejection of a multivector A_k from a blade N_l.
		///
		/// 	The rejection is the component of A_k that is orthogonal to N_l:
		/// 	  rej_{N_l}(A_k) = A_k - proj_{N_l}(A_k)
		///
		/// 	Validates grade constraints via Project(), then subtracts.
		///
		/// 	The same grade constraints apply as for Project():
		/// 	  - N_l has components of only one grade (say l).
		/// 	  - Every non-zero component of A_k has grade k with 1 <= k <= l.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wA">The multivector A_k from which to reject.</param>
		/// <param name="wN">The blade N_l to reject from.</param>
		///
		/// <returns>The rejection of A_k from N_l.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		TMultivector Reject(const TMultivector& wA, const TMultivector& wN)
		{
			try
			{
				TMultivector wProj = Project(wA, wN);
				TMultivector wResult(wA.GetValuePrecision());
				Sub(wResult, wA, wProj);
				return wResult;
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade rejection", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the rejection of each multivector in a vector from the same blade,
		/// 	with grade validation.
		///
		/// 	See Reject() for the per-element operation (including grade checks). The
		/// 	output vector is resized to match the input.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="vecwC">	   [out] Result vector of rejected multivectors.</param>
		/// <param name="wN">		   The blade N_l to reject from.</param>
		/// <param name="vecwA">   The vector of multivectors to reject.</param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		void Reject(std::vector<TMultivector>& vecwC, const TMultivector& wN, const std::vector<TMultivector>& vecwA)
		{
			try
			{
				vecwC.resize(vecwA.size());

				ForEachIndex(vecwA, [&](const TMultivector& wA, size_t uIdx)
						{
							vecwC[uIdx] = Reject(wA, wN);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade rejection", xEx);
			}
		}
	}
}	// namespace Tan::GA
