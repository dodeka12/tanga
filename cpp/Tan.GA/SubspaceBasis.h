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

#include "Tan.Math/ValuePrecision.h"
#include "Tan.Math/Matrix.h"
#include "Tan.Math/Matrix.Algo.SVD.h"

#include "Multivector.h"
#include "DynamicMultivector.h"
#include "BladeMask.h"
#include "Matrix_MapToBladeMask.h"
#include "MV_Operators.h"

namespace Tan
{
	namespace GA
	{
		template<typename _TValue, typename _TBlade>
		class CSubspaceBasis : public CValuePrecision<_TValue>
		{
		public:

			typedef _TValue TValue;
			typedef _TBlade TBlade;
			typedef CSubspaceBasis<_TValue, _TBlade> TThis;
			typedef CDynamicMultivector<_TValue, _TBlade> TMultivector;
			typedef CValuePrecision<_TValue> TValPrec;

			static const unsigned AlgebraDimension     = TBlade::AlgebraDimension;
			static const unsigned VectorSpaceDimension = TBlade::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = TBlade::VectorSpaceSignature;

		public:

			struct SBladePair
			{
			public:

				SBladePair()
				{
				}

				SBladePair(const SBladePair& xPair)
				{
					*this = xPair;
				}

				SBladePair(const TMultivector& _mvBlade)
					: wBlade(_mvBlade)
				{
				}

				SBladePair(const TValue& _fValue, const TBlade& _xBlade, const TValue& fPrec)
					: wBlade(_fValue, _xBlade, fPrec)
				{
				}

				SBladePair(const TBlade& _xBlade, const TValue& fPrec)
					: wBlade(TValue(1), _xBlade, fPrec)
				{
				}

				SBladePair(const TBlade& _xBlade, const TMultivector& wA)
					: wBlade(TValue(1), _xBlade, wA.GetValuePrecision())
				{
					TMultivector wB;
					GA::GP(wB, wBlade, wA);
					wBlade = wB;
				}

				SBladePair(const TValue& _fValue, const TBlade& _xBlade, const TMultivector& wA)
					: wBlade(_fValue, _xBlade, wA.GetValuePrecision())
				{
					TMultivector wB;
					GA::GP(wB, wBlade, wA);
					wBlade = wB;
				}

				SBladePair& operator=(const SBladePair& xPair)
				{
					wBlade      = xPair.wBlade;
					wRecipBlade = xPair.wRecipBlade;
					return *this;
				}

			public:

				/// <summary>	The basis blade. </summary>
				TMultivector wBlade;

				/// <summary>	The reciprocal basis blade. </summary>
				TMultivector wRecipBlade;
			};

		public:

			CSubspaceBasis()
			{
				try
				{
					CValuePrecision<TValue>::Reset();
					Reset();
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace basis", xEx);
				}
			}

			CSubspaceBasis(const TThis& xBasis)
			{
				TValPrec::SetValuePrecision(xBasis.GetValuePrecision());
				*this = xBasis;
			}

			CSubspaceBasis(const TValue& fPrec)
			{
				try
				{
					Reset();
					TValPrec::SetValuePrecision(fPrec);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace basis", xEx);
				}
			}

			TThis& operator=(const TThis& xBasis)
			{
				m_vecBasis = xBasis.m_vecBasis;
				return *this;
			}

			void Reset()
			{
				try
				{
					m_vecBasis.reserve(VectorSpaceDimension);
					m_vecBasis.resize(0);

					m_bIsMatrixBasisValid = false;
					m_xBladeMask.Reset();
					m_matBasis.SetSize(0, 0);
					m_matRecipBasis.SetSize(0, 0);
					m_matSubspace.SetSize(0, 0);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error resetting subspace basis", xEx);
				}
			}

			const SBladePair& operator[](unsigned uBladeIdx) const
			{
				#if defined(_DEBUG)
					if (uBladeIdx >= m_vecBasis.size())
					{
						TAN_THROW_RT("Invalid basis blade index");
					}

				#endif
				return m_vecBasis[uBladeIdx];
			}

			const TMultivector& GetBasisBlade(unsigned uBladeIdx) const
			{
				#if defined(_DEBUG)
					if (uBladeIdx >= m_vecBasis.size())
					{
						TAN_THROW_RT("Invalid basis blade index");
					}

				#endif
				return m_vecBasis[uBladeIdx].wBlade;
			}

			const TMultivector& GetRecipBasisBlade(unsigned uBladeIdx) const
			{
				#if defined(_DEBUG)
					if (uBladeIdx >= m_vecBasis.size())
					{
						TAN_THROW_RT("Invalid basis blade index");
					}

				#endif
				return m_vecBasis[uBladeIdx].wRecipBlade;
			}

			////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>	Inserts the basis blade described by wBlade. This function tests whether
			/// 			the new basis blade wBlade is linearly independent of the current basis.
			/// 			If it is linearly independent, it is added to the basis. Otherwise, the blade
			/// 			is ignored.
			/// 			</summary>
			///
			/// <remarks>	Perwass, . </remarks>
			///
			/// <param name="wBlade">	The mv blade. </param>
			////////////////////////////////////////////////////////////////////////////////////////////////////

			void InsertBasisBlade(const TMultivector& wBlade)
			{
				if (!IsLinearlyDependent(wBlade))
				{
					AddBasisBlade(wBlade);
				}
			}

			void AddBasisBlade(const SBladePair& xPair)
			{
				try
				{
					m_vecBasis.push_back(xPair);
					m_bIsMatrixBasisValid = false;
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error adding basis blade", xEx);
				}
			}

			void AddBasisBlade(const TMultivector& wBlade)
			{
				try
				{
					m_vecBasis.push_back(SBladePair(wBlade));
					m_bIsMatrixBasisValid = false;
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error adding basis blade", xEx);
				}
			}

			TThis& operator<<(const SBladePair& xPair)
			{
				AddBasisBlade(xPair);
				return *this;
			}

			bool IsLinearlyDependent(const TMultivector& wBlade)
			{
				try
				{
					CMatrix<TValue> matBlade, matA;

					// If the basis is empty, then no blade is linearly dependent
					if (m_vecBasis.size() == 0)
					{
						return false;
					}

					// Update Basis and reciprocal basis matrices
					_UpdateBasisMatrices();

					// Convert input blade to column vector based on the blade mask for this basis.
					ToMatrix(matBlade, wBlade, m_xBladeMask);

					// Test whether matBlade lies in the null-space of m_matSubspace.
					matA = m_matSubspace * matBlade;

					return matA.IsZero();
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error checking for linear dependency", xEx);
				}
			}

			void EvalReciprocalBasis()
			{
				TValue fValue = TValue(1);
				try
				{
					_UpdateBasisMatrices();

					// The rows of matR are now the reciprocal multivectors
					ForEachIndex(m_vecBasis, [&](SBladePair& xPair, size_t nRowIdx)
							{
								xPair.wRecipBlade.Reset();
								m_xBladeMask.ForEachBlade([&](unsigned uColIdx, const TBlade& blA) -> bool
										{
											fValue = m_matRecipBasis(unsigned(nRowIdx), uColIdx);
											xPair.wRecipBlade.SetValueBlade(fValue, blA);
											return true;
										});

								#ifdef _DEBUG	////////////////////////////////////////////////////////////////////////////////
									// Test that reciprocal blade is correct
									_TestReciprocalBlade(xPair.wRecipBlade, unsigned(nRowIdx));
								#endif	//////////////////////////////////////////////////////////////////////////////////////
							});
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error evaluating reciprocal basis", xEx);
				}
			}

			bool IsValid()
			{
				#ifdef _DEBUG	////////////////////////////////////////////////////////////////////////////////
					try
					{
						// The rows of matR are now the reciprocal multivectors
						ForEachIndex(m_vecBasis, [&](SBladePair& xPair, size_t nIndex)
								{
									// Test that reciprocal blade is correct
									_TestReciprocalBlade(xPair.wRecipBlade, unsigned(nIndex));
								});
					}
					catch (std::exception&)
					{
						return false;
					}
				#endif	//////////////////////////////////////////////////////////////////////////////////////
				return true;
			}

			template<typename FuncOp>
			void ForEachBasisBlade(FuncOp xFunc)
			{
				ForEach(m_vecBasis, [&](SBladePair& xPair)
						{
							xFunc(xPair.wBlade, xPair.wRecipBlade);
						});
			}

			template<typename FuncOp>
			void ForEachBasisBladeIndex(FuncOp xFunc)
			{
				ForEachIndex(m_vecBasis, [&](SBladePair& xPair, size_t uIndex)
						{
							xFunc(xPair.wBlade, xPair.wRecipBlade, uIndex);
						});
			}

			template<typename FuncOp>
			void ForEachBasisBlade(FuncOp xFunc) const
			{
				ForEach(m_vecBasis, [&](const SBladePair& xPair)
						{
							xFunc(xPair.wBlade, xPair.wRecipBlade);
						});
			}

			template<typename FuncOp>
			void ForEachBasisBladeIndex(FuncOp xFunc) const
			{
				ForEachIndex(m_vecBasis, [&](const SBladePair& xPair, size_t uIndex)
						{
							xFunc(xPair.wBlade, xPair.wRecipBlade, uIndex);
						});
			}

			template<typename FuncOp>
			bool ForEachBasisBladeTest(FuncOp xFunc)
			{
				return ForEachTest(m_vecBasis, [&](SBladePair& xPair) -> bool
						{
							return xFunc(xPair.wBlade, xPair.wRecipBlade);
						});
			}

			template<typename FuncOp>
			bool ForEachBasisBladeIndexTest(FuncOp xFunc)
			{
				return ForEachIndexTest(m_vecBasis, [&](SBladePair& xPair, size_t uIndex) -> bool
						{
							return xFunc(xPair.wBlade, xPair.wRecipBlade, uIndex);
						});
			}

			template<typename FuncOp>
			bool ForEachBasisBladeTest(FuncOp xFunc) const
			{
				return ForEachTest(m_vecBasis, [&](const SBladePair& xPair) -> bool
						{
							return xFunc(xPair.wBlade, xPair.wRecipBlade);
						});
			}

			template<typename FuncOp>
			bool ForEachBasisBladeIndexTest(FuncOp xFunc) const
			{
				return ForEachIndexTest(m_vecBasis, [&](const SBladePair& xPair, size_t nIndex) -> bool
						{
							return xFunc(xPair.wBlade, xPair.wRecipBlade, nIndex);
						});
			}

		protected:

			void _UpdateBasisMatrices()
			{
				try
				{
					if (!m_bIsMatrixBasisValid)
					{
						_EvalBasisMatrices();
					}
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error updating basis matrices", xEx);
				}
			}

			void _EvalBasisMatrices()
			{
				try
				{
					CMatrix<TValue> matAt, matB, matR, matI;
					unsigned uRowCnt, uColCnt;

					// Reset the blade mask
					m_xBladeMask.Reset();

					// The ColCnt is the number of basis multivectors.
					uColCnt = unsigned(m_vecBasis.size());

					if (uColCnt == 0)
					{
						m_matBasis.SetSize(0, 0);
						m_matRecipBasis.SetSize(0, 0);
						m_matSubspace.SetSize(0, 0);
						m_bIsMatrixBasisValid = false;
						return;
					}

					// The RowCnt is the number of canonical basis blades used in
					// all basis multivectors combined.
					ForEach(m_vecBasis, [&](const SBladePair& xPair)
							{
								xPair.wBlade.ForEachBlade([&](const TValue& fValA, const TBlade& blA) -> bool
										{
											m_xBladeMask.Insert(blA);
											return true;
										});
							});

					uRowCnt = m_xBladeMask.Count();

					// Set matrix to appropriate size
					m_matBasis.SetSize(uRowCnt, uColCnt);
					m_matBasis.Zero();

					// Now fill matrix
					ForEachIndex(m_vecBasis, [&](const SBladePair& xPair, size_t nColIdx)
							{
								m_xBladeMask.ForEachBlade([&](unsigned uRowIdx, const TBlade& blA) -> bool
										{
											_SetBasisMatrixElement(m_matBasis, uRowIdx, unsigned(nColIdx), blA, xPair.wBlade);
											return true;
										});
							});

					// Calculate (A^T * A)^-1 A^T to find reciprocal multivectors
					matAt = m_matBasis;
					matAt.Transpose();

					matB  = matAt;
					matB = matB * m_matBasis;

					m_matRecipBasis  = CMatrixAlgoSVD<TValue>::Inverse(matB, TValPrec::GetValuePrecision());
					m_matRecipBasis = m_matRecipBasis * matAt;

					// Calculate m_matSubspace = m_matBasis * m_matRecipBasis - I
					m_matSubspace = m_matBasis * m_matRecipBasis;
					for (unsigned uIdx = 0; uIdx < uRowCnt; ++uIdx)
					{
						m_matSubspace(uIdx, uIdx) -= TValue(1);
					}

					m_bIsMatrixBasisValid = true;
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error evaluating basis matrices", xEx);
				}
			}

			void _SetBasisMatrixElement(CMatrix<TValue>& matA, unsigned uRowIdx, unsigned uColIdx, const TBlade& blA, const TMultivector& wBlade)
			{
				TValue fValue = TValue(0);
				GA::ScalarProductOperator(fValue, TValue(1), blA, wBlade);
				matA(uRowIdx, uColIdx) = fValue;
			}

			void _BasisOuterProductLessOne(TMultivector& wA, unsigned uGapIndex)
			{
				try
				{
					TMultivector wC;

					wA.Reset();
					ForEachBasisBladeIndex([&](const TMultivector& wBlade, const TMultivector& wRecipBlade, size_t nIndex) -> bool
							{
								if (unsigned(nIndex) != uGapIndex)
								{
									GA::OP(wC, wA, wBlade);
									wA = wC;
								}

								return true;
							});
					wA.Prune();
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error calculating basis outer product", xEx);
				}
			}

			void _TestReciprocalBlade(const TMultivector& wRecipBlade, size_t nIndex) const
			{
				ForEachBasisBladeIndex([&](const TMultivector& wTestBlade, const TMultivector& wTestRecipBlade, size_t uTestIndex) -> bool
						{
							_TestReciprocalSingle(wTestBlade, uTestIndex, wRecipBlade, nIndex);
							return true;
						});
			}

			void _TestReciprocalSingle(const TMultivector& wBlade, size_t nIndex, const TMultivector& wRecipBlade, size_t nRecipIndex) const
			{
				TValue fScalar;
				GA::SP(fScalar, wRecipBlade, wBlade);

				if ((nRecipIndex == nIndex) && !this->IsUnity(fScalar))
				{
					TAN_THROW_RT("Inner product of reciprocal blade with its basis blade does not result in unity");
				}
				else if ((nRecipIndex != nIndex) && !this->IsZero(fScalar))
				{
					TAN_THROW_RT("Inner product of reciprocal blade with a different basis blade does not result in zero");
				}
			}

		protected:

			std::vector<SBladePair> m_vecBasis;

			/// <summary>	Flag whether m_xBladeMask, m_matBasis and m_matRecipBasis are up to date. </summary>
			bool m_bIsMatrixBasisValid;

			/// <summary>	The list of canonical blades used in the basis. </summary>
			CBladeMask<TBlade> m_xBladeMask;

			CMatrix<TValue> m_matBasis;
			CMatrix<TValue> m_matRecipBasis;

			/// <summary>	The right null-space of this matrix is the subspace spanned
			/// 			by the basis in terms of the canonical basis blades.
			/// 			That is, m_matSubspace = m_matBasis * m_matRecipBasis - I. </summary>
			CMatrix<TValue> m_matSubspace;
		};
	}
}	// .GA
