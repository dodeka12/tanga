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
		/// 	NOTE: the pseudo-inverse is an inverse only w.r.t. the inner product /
		/// 	scalar projection (<A . A^{-1}>_0 = 1), NOT w.r.t. the geometric product
		/// 	(A * A^{-1} = 1 + higher grades) except in a positive-definite metric, where
		/// 	it coincides with the ordinary inverse reverse(A) / IP(A, reverse(A)).  A null
		/// 	(degenerate) blade has no geometric inverse at all; the pseudo-inverse is the
		/// 	only reciprocal such a blade has.  Use InverseBlade() only for non-degenerate
		/// 	blades, where a geometric inverse exists.
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
		/// 	The algorithm (metric-free, so valid for null blades too):
		/// 	  1. Verify all non-zero elements of wA have the same grade k.
		/// 	  2. Set B = wA.
		/// 	  3. Repeat while the grade of B is >= 2:
		/// 	     a. Find a factor a of B: probe each coordinate blade E of grade
		/// 	        one less than B and take a = E << B (Option A).  This always
		/// 	        succeeds for a genuine blade; otherwise solve a ^ B == 0 by
		/// 	        Gaussian elimination (Option B, metric-free fallback).
		/// 	     b. Choose a partner b with a . b != 0 (a itself if non-null, else
		/// 	        any basis vector with non-zero scalar product).
		/// 	     c. B = IP(b, B) / SP(a, b)  (peel off one factor, null-safe).
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
				unsigned uGradeB = uGradeK;

				// Step 3: Peel off one factor at a time (null-safe, metric-free).
				while (uGradeB > 1)
				{
					// Option A: probe every coordinate blade E of grade (uGradeB-1);
					// a = E << B is a factor of B (grade 1).  This always succeeds
					// for a genuine blade.
					TMultivector wAFactor;
					bool bFound = false;

					for (unsigned uId = 1; uId < (1u << TMultivector::VectorSpaceDimension); ++uId)
					{
						TBlade bl;
						bl.SetBlade(uId);

						unsigned uGrade;
						bl.GetGrade(uGrade);

						if (uGrade != uGradeB - 1)
						{
							continue;
						}

						TMultivector wE(wA.GetValuePrecision());
						wE.SetValueBlade(TValue(1), bl);

						TMultivector wV(wA.GetValuePrecision());
						IP(wV, wE, wB);

						if (!wV.IsZero(MagnitudeSquared(wV)))
						{
							wAFactor = std::move(wV);
							bFound = true;
							break;
						}
					}

					// Option B (fallback; should not trigger for a genuine blade):
					// solve a ^ B == 0 for one non-trivial a via elimination on
					// the linear map a -> a ^ B.
					if (!bFound)
					{
						const unsigned uGradeK1 = uGradeB + 1;

						std::vector<unsigned> vecRowIds;
						for (unsigned uId = 1; uId < (1u << TMultivector::VectorSpaceDimension); ++uId)
						{
							TBlade bl;
							bl.SetBlade(uId);

							unsigned uGrade;
							bl.GetGrade(uGrade);

							if (uGrade == uGradeK1)
							{
								vecRowIds.push_back(uId);
							}
						}

						const size_t nRows = vecRowIds.size();
						const size_t nCols = (size_t)TMultivector::VectorSpaceDimension;

						std::vector<std::vector<TValue>> M(nRows, std::vector<TValue>(nCols, TValue(0)));

						for (size_t c = 0; c < nCols; ++c)
						{
							TMultivector wWedge(wA.GetValuePrecision());
							OP(wWedge, vecBasis[c], wB);

							for (size_t r = 0; r < nRows; ++r)
							{
								TBlade bl;
								bl.SetBlade(vecRowIds[r]);

								TValue fVal;
								if (!wWedge.GetValueBlade(fVal, bl))
								{
									fVal = TValue(0);
								}
								M[r][c] = fVal;
							}
						}

						const TValue fPrec = wB.GetValuePrecision();
						auto xAbs = [](const TValue& v) -> TValue { return (v < TValue(0)) ? -v : v; };
						auto xIsZero = [&](const TValue& v) -> bool { return v >= -fPrec && v <= fPrec; };

						std::vector<size_t> vecPivotRow(nCols, 0);
						std::vector<bool> vecIsPivotCol(nCols, false);

						size_t uRow = 0;
						for (size_t uCol = 0; uCol < nCols && uRow < nRows; ++uCol)
						{
							size_t uPiv = uRow;
							for (size_t r = uRow + 1; r < nRows; ++r)
							{
								if (xAbs(M[r][uCol]) > xAbs(M[uPiv][uCol]))
								{
									uPiv = r;
								}
							}

							if (xIsZero(M[uPiv][uCol]))
							{
								continue;
							}

							std::swap(M[uRow], M[uPiv]);

							TValue fPiv = M[uRow][uCol];
							for (size_t c = uCol; c < nCols; ++c)
							{
								M[uRow][c] /= fPiv;
							}

							for (size_t r = 0; r < nRows; ++r)
							{
								if (r == uRow)
								{
									continue;
								}

								TValue f = M[r][uCol];
								if (xIsZero(f))
								{
									continue;
								}

								for (size_t c = uCol; c < nCols; ++c)
								{
									M[r][c] -= f * M[uRow][c];
								}
							}

							vecIsPivotCol[uCol] = true;
							vecPivotRow[uCol] = uRow;
							++uRow;
						}

						int iFreeCol = -1;
						for (size_t c = 0; c < nCols; ++c)
						{
							if (!vecIsPivotCol[c])
							{
								iFreeCol = (int)c;
								break;
							}
						}

						if (iFreeCol >= 0)
						{
							std::vector<TValue> vecX(nCols, TValue(0));
							vecX[(size_t)iFreeCol] = TValue(1);

							for (size_t c = 0; c < nCols; ++c)
							{
								if (vecIsPivotCol[c])
								{
									vecX[c] = -M[vecPivotRow[c]][(size_t)iFreeCol];
								}
							}

							TMultivector wResult(wA.GetValuePrecision());
							for (size_t c = 0; c < nCols; ++c)
							{
								if (!xIsZero(vecX[c]))
								{
									TBlade bl;
									bl.SetBlade(1u << c);
									wResult.SetValueBlade(vecX[c], bl);
								}
							}

							if (!wResult.IsZero(MagnitudeSquared(wResult)))
							{
								wAFactor = std::move(wResult);
								bFound = true;
							}
						}
					}

					if (!bFound)
					{
						TAN_THROW_RT("Cannot factorize blade: no factor vector found");
					}

					// Choose a partner b with a . b != 0 (a itself if non-null).
					TValue fAA;
					SP(fAA, wAFactor, wAFactor);

					TMultivector wPartner;
					bool bPartnerFound = false;

					if (!wAFactor.IsZero(fAA))
					{
						wPartner = wAFactor;
						bPartnerFound = true;
					}
					else
					{
						for (size_t uIdx = 0; uIdx < vecBasis.size(); ++uIdx)
						{
							TValue fAB;
							SP(fAB, wAFactor, vecBasis[uIdx]);

							if (!wAFactor.IsZero(fAB))
							{
								wPartner = vecBasis[uIdx];
								bPartnerFound = true;
								break;
							}
						}
					}

					if (!bPartnerFound)
					{
						TAN_THROW_RT("Cannot factorize blade: factor has no non-null partner vector");
					}

					// Peel off the factor: B = IP(b, B) / SP(a, b).
					TValue fDenom;
					SP(fDenom, wAFactor, wPartner);

					TMultivector wPeeled(wA.GetValuePrecision());
					IP(wPeeled, wPartner, wB);

					TMultivector wNewB = wPeeled / fDenom;
					wB = std::move(wNewB);

					// Normalize the extracted factor and store it.
					TValue fMagA = Magnitude(wAFactor);
					vecFactors.push_back(wAFactor / fMagA);

					--uGradeB;
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
		/// 	Algorithm (metric-free, so also valid when J is a null blade):
		/// 	  1. Let J be the blade of higher grade, factorize the lower-grade blade
		/// 	     into a factor set {n_j} via FactorizeBlade().
		/// 	  2. Repeat until every factor is contained in J:
		/// 	     a. For each remaining n_j compute OP(J, n_j).
		/// 	     b. Select the n_j with the largest |OP(J, n_j)|^2.
		/// 	     c. If it is zero (up to precision), normalize J and return.
		/// 	     d. Otherwise set J = OP(J, n_j) and drop n_j from the set.
		///
		/// 	The wedge test OP(J, n_j) = 0 decides containment without using the
		/// 	metric, unlike the former projection/rejection approach, which is
		/// 	undefined when J is a null (degenerate) blade (e.g. conformal points).
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

				// If either blade is a scalar (grade 0), it spans the trivial
				// subspace, so the join is just the other blade, normalized.
				// Handle this before FactorizeBlade(), which requires grade >= 1.
				if (uGradeA == 0 || uGradeB == 0)
				{
					const TMultivector& wResult = (uGradeA == 0) ? wB : wA;
					TValue fMag = Magnitude(wResult);
					if (fMag == TValue(0))
					{
						TAN_THROW_RT("Join result has zero magnitude");
					}
					return wResult / fMag;
				}

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

				// Metric-free join: factor n_j is contained in J iff OP(J, n_j) == 0.
				// This avoids projection/rejection, which is undefined for null blades
				// (e.g. conformal points in N3).  Each step grows J by the factor that
				// is most linearly independent of it (largest |OP(J, n_j)|^2), mirroring
				// the former largest-rejection selection for numerical conditioning.
				while (true)
				{
					TValue fMaxMag = TValue(0);
					size_t uMaxIdx = 0;

					for (size_t uIdx = 0; uIdx < vecN.size(); ++uIdx)
					{
						TMultivector wWedge(wJ.GetValuePrecision());
						OP(wWedge, wJ, vecN[uIdx]);

						TValue fMag = MagnitudeSquared(wWedge);
						if (fMag > fMaxMag)
						{
							fMaxMag = fMag;
							uMaxIdx = uIdx;
						}
					}

					// If every remaining factor is already contained in J, we are done
					if (fMaxMag <= fPrecision)
					{
						TValue fMagJ = Magnitude(wJ);
						if (fMagJ == TValue(0))
						{
							TAN_THROW_RT("Join result has zero magnitude");
						}
						return wJ / fMagJ;
					}

					// Grow J by the selected factor: J = OP(J, n_j)
					TValue fMag = Magnitude(vecN[uMaxIdx]);
					TMultivector wV = vecN[uMaxIdx] / fMag;

					TMultivector wNewJ(wJ.GetValuePrecision());
					OP(wNewJ, wJ, wV);
					wJ = std::move(wNewJ);

					// The selected factor is now contained in J; drop it from the set
					vecN.erase(vecN.begin() + uMaxIdx);
				}
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade join", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the meet of two blades A_k and B_l.
		///
		/// 	The meet M is the blade of largest grade contained in both A_k and
		/// 	B_l, i.e. the intersection of their subspaces.
		///
		/// 	It is computed via the signed dual and the join:
		/// 	  meet(A, B) = dual( join( dual(A), dual(B) ) )
		///
		/// 	where dual(X) = X . I^{-1} (the same Dual() used elsewhere). The
		/// 	result is defined up to scale and sign, matching the Join()
		/// 	convention, and is normalized to unit magnitude.
		///
		/// 	The caller must ensure that both wA and wB are blades. Behaviour is
		/// 	undefined otherwise.
		/// </summary>
		///
		/// <typeparam name="TMultivector">Type of the multivector.</typeparam>
		/// <param name="wA">The first blade.</param>
		/// <param name="wB">The second blade.</param>
		///
		/// <returns>The meet blade M.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector>
		TMultivector Meet(const TMultivector& wA, const TMultivector& wB)
		{
			typedef typename TMultivector::TValue TValue;

			try
			{
				// meet(A, B) = dual( join( dual(A), dual(B) ) )
				TMultivector wDualA(wA.GetValuePrecision());
				Dual(wDualA, wA);

				TMultivector wDualB(wB.GetValuePrecision());
				Dual(wDualB, wB);

				TMultivector wJoin = Join(wDualA, wDualB);

				TMultivector wMeet(wJoin.GetValuePrecision());
				Dual(wMeet, wJoin);

				// Normalize the result, like Join().
				TValue fMag = Magnitude(wMeet);
				if (fMag == TValue(0))
				{
					TAN_THROW_RT("Meet result has zero magnitude");
				}

				return wMeet / fMag;
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error computing blade meet", xEx);
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

					// Pick the first factor with a non-zero geometric norm
					// (a . a != 0), so the geometric-product peel below does not
					// vanish.  (For a null factor a, the grade-(m-1) part of
					// GP(V, a) is zero, which skips a factor.)  A null blade of
					// grade >= 2 always has a non-null factor in a non-degenerate
					// metric; only a null vector (grade 1) has none.
					for (size_t uIdx = 0; uIdx < vecA.size(); ++uIdx)
					{
						TValue fNorm;
						SP(fNorm, vecA[uIdx], vecA[uIdx]);

						if (!vecA[uIdx].IsZero(fNorm))
						{
							wN_j = vecA[uIdx];
							bFound = true;
							break;
						}
					}

					if (!bFound)
					{
						// Only a null vector (grade 1) has no non-null factor;
						// use it directly as the last factor.
						wN_j = vecA[0];
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
		/// 	The "Unsafe" suffix means this routine performs no validation of the
		/// 	grade preconditions below; the safe variant Project() checks them and
		/// 	then delegates here.
		///
		/// 	Performs proj_{N_l}(A_k) = (A_k . N_l) N_l^{-1}, where
		/// 	N_l^{-1} = reverse(N_l) / IP(N_l, reverse(N_l)) is the ordinary
		/// 	blade inverse.  For a non-degenerate blade this is the correct
		/// 	orthogonal projection.  For a null (degenerate) blade no geometric
		/// 	inverse exists; the pseudo-inverse
		/// 	conjugate(N_l) / IP(N_l, conjugate(N_l)) is used as a fallback, but
		/// 	it is an inverse only w.r.t. the inner product (<N_l . P>_0 = 1),
		/// 	not the geometric product, so it does not give a true projection
		/// 	onto a null blade.
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
			typedef typename TMultivector::TValue TValue;

			try
			{
				// Step 1: compute the inverse of the blade.  Step 3 multiplies it
				// with a geometric product (GP), so it must be the true geometric
				// inverse where one exists (a contraction would be equivalent here,
				// since IP(A, N) is a sub-blade of N):
				//   - Non-degenerate blade: N^{-1} = reverse(N) / IP(N, reverse(N)).
				//   - Null blade: no geometric inverse exists.  The pseudo-inverse
				//     conjugate(N) / IP(N, conjugate(N)) is an inverse only w.r.t.
				//     the inner product (<N . P>_0 = 1), not the geometric product,
				//     so it cannot give a true projection onto a null blade; it is
				//     kept as a best-effort fallback for contraction-based callers
				//     (e.g. FactorizeVersor).
				TMultivector wNorm(wN.GetValuePrecision());
				IP_Reverse(wNorm, wN, false, wN, true);
				TValue fNorm = Scalar(wNorm);

				TMultivector wNInv;
				if (wN.IsZero(fNorm))
				{
					wNInv = PseudoInverseBlade(wN);
				}
				else
				{
					wNInv = InverseBlade(wN);
				}

				// Step 2: wX = IP(A_k, N_l)   (symmetric inner product)
				//         == (A_k . N_l); this is a scalar when grade(A) == grade(N).
				TMultivector wX(wA.GetValuePrecision());
				IP(wX, wA, wN);

				// Step 3: wResult = GP(wX, N_l^{-1})  == (A_k . N_l) N_l^{-1}
				//         The geometric product (not IP) is required here because
				//         the symmetric inner product gives IP(scalar, blade) == 0.
				TMultivector wResult(wA.GetValuePrecision());
				GP(wResult, wX, wNInv);

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
		/// 	  proj_{N_l}(A_k) = (A_k . N_l) N_l^{-1}
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
