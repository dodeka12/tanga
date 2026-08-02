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

#include <string>

#include "Tan.Core/ValueFormatString.h"

#include "Tan.Math/InlineMath.h"
#include "Tan.Math/ValuePrecision.h"

#include "Blade.h"
#include "Multivector.h"
#include "SubspaceBasis.h"
#include "Matrix_MapToSubspace.h"
//#include "Matrix_MapToBladeMask.h"

namespace Tan
{
	namespace GA
	{
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 subspace multivector.
		/// </summary>
		///
		/// <typeparam name="_TValue">			   	Type of the value. </typeparam>
		/// <typeparam name="_TBlade">			   	Type of the blade. </typeparam>
		/// <typeparam name="t_uSubspaceDimension">	Type of the subspace dimension. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class _TValue, typename _TBlade, unsigned t_uSubspaceDimension>
		class _CSubspaceMultivector : public CValuePrecision<_TValue>
		{
		public:

			typedef _TValue TValue;
			typedef _TBlade TBlade;
			typedef _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> TMultivector;
			typedef CValuePrecision<_TValue> TValPrec;
			
		public:

			static const unsigned AlgebraDimension     = TBlade::AlgebraDimension;
			static const unsigned VectorSpaceDimension = TBlade::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = TBlade::VectorSpaceSignature;
			static const unsigned SubspaceDimension    = t_uSubspaceDimension;

		public:

			_CSubspaceMultivector(void)
			{
			}

			_CSubspaceMultivector(TValue fPrecision)
			{
				TValPrec::SetValuePrecision(fPrecision);
				Zero();
			}

			_CSubspaceMultivector(const TMultivector& wA)
			{
				TValPrec::Reset();
				*this = wA;
			}

			_CSubspaceMultivector(const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
			{
				try
				{
					TValPrec::Reset();
					Create(vBladeList);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace multivector", xEx);
				}
			}

			_CSubspaceMultivector(const tvec<TValue, t_uSubspaceDimension>& vA, const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
			{
				try
				{
					TValPrec::Reset();
					Create(vA, vBladeList);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace multivector", xEx);
				}
			}

			_CSubspaceMultivector(const TValue(&pvalData)[t_uSubspaceDimension], const TBlade(&pBladeList)[t_uSubspaceDimension])
			{
				try
				{
					TValPrec::Reset();
					Create(pvalData, pBladeList);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace multivector", xEx);
				}
			}

			_CSubspaceMultivector(const CSubspaceBasis<TValue, TBlade>& xSubspace)
			{
				try
				{
					SetValuePrecision(xSubspace.GetValuePrecision());
					Create(xSubspace);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace multivector", xEx);
				}
			}

			_CSubspaceMultivector(const tvec<TValue, t_uSubspaceDimension>& vA, const CSubspaceBasis<TValue, TBlade>& xSubspace)
			{
				try
				{
					SetValuePrecision(xSubspace.GetValuePrecision());
					Create(vA, xSubspace);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace multivector", xEx);
				}
			}

			TMultivector& operator=(const TMultivector& wA)
			{
				TValPrec::operator=(wA);

				//#ifdef _DEBUG
				//	TAN_ASSERT(wA.IsValid());
				//#endif
				MemCpy(m_pBladeList, wA.m_pBladeList);
				MemCpy(m_pvalData, wA.m_pvalData);

				return *this;
			}

			template<typename TMultivectorA>
			TMultivector& operator=(const TMultivectorA& wA)
			{
				try
				{
					TValPrec::operator=(wA);
					Create(wA);
					return *this;
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error assigning multivector", xEx);
				}
			}

			bool IsValid() const
			{
				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx)
				{
					if (m_pBladeList[uIdx].GetId() >= AlgebraDimension)
					{
						return false;
					}
				}

				for (unsigned uIdxA = 0; uIdxA < SubspaceDimension; ++uIdxA)
				{
					for (unsigned uIdxB = uIdxA + 1; uIdxB < SubspaceDimension; ++uIdxB)
					{
						if (m_pBladeList[uIdxA].GetId() == m_pBladeList[uIdxB].GetId())
						{
							return false;
						}
					}
				}

				return true;
			}

			void Zero()
			{
				MemSet(m_pvalData, TValue(0));
			}

			void Reset()
			{
				Zero();
			}

			template<typename TMultivectorA>
			void Create(const TMultivectorA& wA)
			{
				Zero();

				wA.ForEachBlade([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							if (!SetValueBlade(fValA, blA))
							{
								TAN_THROW_RT("Invalid source multvector");
							}

							return true;
						});
			}

			void Create(const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
			{
				MemCpy(m_pBladeList, vBladeList.v);
				MemSet(m_pvalData, TValue(0));
			}

			void Create(const tvec2<TValue>& vA, const tvec2<TBlade>& vBladeList)
			{
				TAN_STATIC_ASSERT(t_uSubspaceDimension == 2);

				MemCpy<TBlade, 2>(m_pBladeList, &vBladeList.x);
				MemCpy<TValue, 2>(m_pvalData, &vA.x);
			}

			void Create(const tvec2<TValue>& vA, const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
			{
				TAN_STATIC_ASSERT(t_uSubspaceDimension == 2);

				MemCpy<TBlade>(m_pBladeList, vBladeList.v);
				MemCpy<TValue, 2>(m_pvalData, &vA.x);
			}

			void Create(const tvec3<TValue>& vA, const tvec3<TBlade>& vBladeList)
			{
				TAN_STATIC_ASSERT(t_uSubspaceDimension == 3);

				MemCpy<TBlade, 3>(m_pBladeList, &vBladeList.x);
				MemCpy<TValue, 3>(m_pvalData, &vA.x);
			}

			void Create(const tvec3<TValue>& vA, const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
			{
				TAN_STATIC_ASSERT(t_uSubspaceDimension == 3);

				MemCpy<TBlade>(m_pBladeList, vBladeList.v);
				MemCpy<TValue, 3>(m_pvalData, &vA.x);
			}

			void Create(const tvec<TValue, t_uSubspaceDimension>& vA, const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
			{
				MemCpy(m_pBladeList, vBladeList.v);
				MemCpy(m_pvalData, vA.v);
			}

			void Create(const TValue(&pvalData)[t_uSubspaceDimension], const TBlade(&pBladeList)[t_uSubspaceDimension])
			{
				MemCpy(m_pBladeList, pBladeList);
				MemCpy(m_pvalData, pvalData);
			}

			void Create(const CSubspaceBasis<TValue, TBlade>& xSubspace)
			{
				CBladeMask<TBlade> xBladeMask;
				EvalBladeMask(xBladeMask, xSubspace);

				if (xBladeMask.Count() != t_uSubspaceDimension)
				{
					TAN_THROW_RT("Subspace has incompatible dimension");
				}

				xBladeMask.ForEachBlade([&](unsigned uBitIdx, const TBlade& blA) -> bool
						{
							m_pBladeList[uBitIdx] = blA;
							m_pvalData[uBitIdx] = TValue(0);
							return true;
						});
			}

			void Create(const tvec<TValue, t_uSubspaceDimension>& vA, const CSubspaceBasis<TValue, TBlade>& xSubspace)
			{
				CBladeMask<TBlade> xBladeMask;
				EvalBladeMask(xBladeMask, xSubspace);

				if (xBladeMask.Count() != t_uSubspaceDimension)
				{
					TAN_THROW_RT("Subspace has incompatible dimension");
				}

				xBladeMask.ForEachBlade([&](unsigned uBitIdx, const TBlade& blA) -> bool
						{
							m_pBladeList[uBitIdx] = blA;
							m_pvalData[uBitIdx] = vA[uBitIdx];
							return true;
						});
			}

			unsigned GetBladeCount() const
			{
				return AlgebraDimension;
			}

			TBlade GetBladeAtIndex(unsigned uIdx) const
			{
				return m_pBladeList[uIdx];
			}

			TValue GetValueAtIndex(unsigned uIdx) const
			{
				return m_pvalData[uIdx];
			}

			// ////////////////////////////////////////////////////////////////////////////////////////////
			template<typename FuncOp>
			void ForEachBlade(FuncOp xFunc)
			{
				TValue* pData  = m_pvalData;
				TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					xFunc(*pData, *pBlade);
				}
			}

			template<typename FuncOp>
			void ForEachBlade(FuncOp xFunc) const
			{
				const TValue* pData  = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					xFunc(*pData, *pBlade);
				}
			}

			template<typename FuncOp>
			void ForEachBladeIndex(FuncOp xFunc)
			{
				TValue* pData        = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					xFunc(*pData, *pBlade, uIdx);
				}
			}

			template<typename FuncOp>
			void ForEachBladeIndex(FuncOp xFunc) const
			{
				const TValue* pData  = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					xFunc(*pData, *pBlade, uIdx);
				}
			}

			template<typename FuncOp>
			void ForEachBladePair(const TMultivector& wA, FuncOp xFunc)
			{
				TValue* pData         = m_pvalData;
				TBlade* pBlade        = m_pBladeList;
				const TValue* pData2  = wA.m_pvalData;
				const TBlade* pBlade2 = wA.m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pData2, ++pBlade, ++pBlade2)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);
					TAN_ASSERT(pBlade2->GetId() < AlgebraDimension);

					if (*pBlade != *pBlade2)
					{
						TAN_THROW_RT("Invalid blade pair");
					}

					xFunc(*pData, *pData2, *pBlade);
				}
			}

			// ////////////////////////////////////////////////////////////////////////////////////////////

			template<typename FuncOp>
			bool ForEachBladeTest(FuncOp xFunc)
			{
				TValue* pData  = m_pvalData;
				TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					if (!xFunc(*pData, *pBlade))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladeTest(FuncOp xFunc) const
			{
				const TValue* pData  = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					if (!xFunc(*pData, *pBlade))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladeIndexTest(FuncOp xFunc)
			{
				TValue* pData        = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					if (!xFunc(*pData, *pBlade, uIdx))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladeIndexTest(FuncOp xFunc) const
			{
				const TValue* pData  = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					if (!xFunc(*pData, *pBlade, uIdx))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladePairTest(const TMultivector& wA, FuncOp xFunc)
			{
				TValue* pData         = m_pvalData;
				TBlade* pBlade        = m_pBladeList;
				const TValue* pData2  = wA.m_pvalData;
				const TBlade* pBlade2 = wA.m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pData, ++pData2, ++pBlade, ++pBlade2)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);
					TAN_ASSERT(pBlade2->GetId() < AlgebraDimension);

					if (*pBlade != *pBlade2)
					{
						TAN_THROW_RT("Invalid blade pair");
					}

					if (!xFunc(*pData, *pData2, *pBlade))
					{
						return false;
					}
				}

				return true;
			}

			// ////////////////////////////////////////////////////////////////////////////////////////////

			bool GetBladeIndex(unsigned& uIndex, const TBlade& blA) const
			{
				const TBlade* pBlade = m_pBladeList;

				for (uIndex = 0; uIndex < SubspaceDimension; ++uIndex, ++pBlade)
				{
					if (blA == *pBlade)
					{
						return true;
					}
				}

				return false;
			}

			void SetValues(const tvec<TValue, t_uSubspaceDimension>& vA)
			{
				MemCpy(m_pvalData, vA.v);
			}

			bool GetValueBlade(TValue& fValue, const TBlade& blA) const
			{
				const TValue* pValue = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pValue, ++pBlade)
				{
					if (blA == *pBlade)
					{
						fValue = *pValue;
						return true;
					}
				}

				return false;
			}

			bool SetValueBlade(const TValue& fValue, const TBlade& blA)
			{
				TValue* pValue       = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pValue, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					if (blA == *pBlade)
					{
						*pValue = fValue;
						return true;
					}
				}

				return false;
			}

			bool AddValueBlade(const TValue& fValue, const TBlade& blA)
			{
				TValue* pValue       = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pValue, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					if (blA == *pBlade)
					{
						*pValue += fValue;
						return true;
					}
				}

				return false;
			}

			bool SubValueBlade(const TValue& fValue, const TBlade& blA)
			{
				TValue* pValue       = m_pvalData;
				const TBlade* pBlade = m_pBladeList;

				for (unsigned uIdx = 0; uIdx < SubspaceDimension; ++uIdx, ++pValue, ++pBlade)
				{
					TAN_ASSERT(pBlade->GetId() < AlgebraDimension);

					if (blA == *pBlade)
					{
						*pValue -= fValue;
						return true;
					}
				}

				return false;
			}

			TMultivector& Negate()
			{
				ForEachBlade([this](TValue& fValA, const TBlade& blA) -> bool
						{
							fValA = -fValA;
							return true;
						});

				return *this;
			}

			TMultivector operator-() const
			{
				TMultivector wB(*this);
				ForEachBlade([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							wB.SetValueBlade(-fValA, blA);
							return true;
						});

				return wB;
			}

			TMultivector& operator+=(const TMultivector& wA)
			{
				for (unsigned i = 0; i < t_uSubspaceDimension; ++i)
				{
					TAN_ASSERT(m_pBladeList[i] == wA.m_pBladeList[i]);
					m_pvalData[i] += wA.m_pvalData[i];
				}

				return *this;
			}

			TMultivector& operator-=(const TMultivector& wA)
			{
				for (unsigned i = 0; i < t_uSubspaceDimension; ++i)
				{
					TAN_ASSERT(m_pBladeList[i] == wA.m_pBladeList[i]);
					m_pvalData[i] -= wA.m_pvalData[i];
				}

				return *this;
			}

			TMultivector& operator*=(const TValue& fValue)
			{
				ForEachBlade([&](TValue& fValA, const TBlade& blA) -> bool
						{
							fValA *= fValue;
							return true;
						});

				return *this;
			}

			TMultivector& operator/=(const TValue& fValue)
			{
				ForEachBlade([&](TValue& fValA, const TBlade& blA)  -> bool
						{
							fValA /= fValue;
							return true;
						});

				return *this;
			}

			TMultivector& operator%=(const TValue& valMod)
			{
				ForEachBlade([&](TValue& fValA, const TBlade& blA)  -> bool
						{
							fValA = hmod(fValA, valMod);
							return true;
						});

				return *this;
			}

		protected:

			// List of actual blades in subspace. Maximum number of blades is the algebra dimension.
			TBlade m_pBladeList[SubspaceDimension];

			// The list of scalars corresponding to the blades in the blade list.
			TValue m_pvalData[SubspaceDimension];
		};

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 subspace multivector.
		/// </summary>
		///
		/// <typeparam name="_TValue">			   	Type of the value. </typeparam>
		/// <typeparam name="_TBlade">			   	Type of the blade. </typeparam>
		/// <typeparam name="t_uSubspaceDimension">	Type of the subspace dimension. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class _TValue, typename _TBlade, unsigned t_uSubspaceDimension>
		class CSubspaceMultivector : public _CSubspaceMultivector<_TValue, _TBlade, t_uSubspaceDimension>
		{
		public:

			typedef _TValue TValue;
			typedef _TBlade TBlade;
			typedef CValuePrecision<TValue> TValPrec;
			typedef _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> _TMultivector;
			typedef _TMultivector TBase;
			typedef CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> TMultivector;

		public:

			CSubspaceMultivector(void)
			{
				TValPrec::Reset();
				TBase::Zero();
			}

			CSubspaceMultivector(TValue fPrecision)
			{
				TValPrec::SetValuePrecision(fPrecision);
				TBase::Zero();
			}

			CSubspaceMultivector(const _TMultivector& wA)
			{
				TValPrec::Reset();
				*this = wA;
			}

			CSubspaceMultivector(const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
			{
				try
				{
					TValPrec::Reset();
					TBase::Create(vBladeList);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace multivector", xEx);
				}
			}

			CSubspaceMultivector(const tvec<TValue, t_uSubspaceDimension>& vA, const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
			{
				try
				{
					TValPrec::Reset();
					TBase::Create(vA, vBladeList);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace multivector", xEx);
				}
			}

			CSubspaceMultivector(const TValue(&pvalData)[t_uSubspaceDimension], const TBlade(&pBladeList)[t_uSubspaceDimension])
			{
				try
				{
					TValPrec::Reset();
					TBase::Create(pvalData, pBladeList);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating subspace multivector", xEx);
				}
			}

			TMultivector& operator=(const _TMultivector& wA)
			{
				_TMultivector::operator=(wA);
				return *this;
			}

			template<typename TMultivectorA>
			TMultivector& operator=(const TMultivectorA& wA)
			{
				try
				{
					TValPrec::operator=(wA);
					TBase::Create(wA);
					return *this;
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error assigning subspace multivector", xEx);
				}
			}
		};
	}
}	// namespace Tan.GA
