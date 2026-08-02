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


#include "Tan.Math/ValuePrecision.h"
#include "Tan.Math/FixedVectorTypes.h"

#include "Tan.Core/StdAlgo.h"
#include "Blade.h"

namespace Tan
{
	namespace GA
	{
		// Forward declaration
		template<class TValue, typename TBlade, unsigned t_uSubspaceDimension>
		class _CSubspaceMultivector;

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 multivector.
		/// </summary>
		///
		/// <typeparam name="TValue">				  	Type of the value. </typeparam>
		/// <typeparam name="t_uVectorSpaceDimension">	Type of the vector space dimension. </typeparam>
		/// <typeparam name="t_uVectorSpaceSignature">	Type of the vector space signature. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class _TValue, typename _TBlade>
		class _CMultivector : public CValuePrecision<_TValue>
		{
		public:

			typedef _TValue TValue;
			typedef _TBlade TBlade;
			typedef _CMultivector<TValue, TBlade> TMultivector;
			typedef CValuePrecision<_TValue> TValPrec;

		public:

			static const unsigned AlgebraDimension     = TBlade::AlgebraDimension;
			static const unsigned VectorSpaceDimension = TBlade::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = TBlade::VectorSpaceSignature;

		public:

			_CMultivector(void)
			{
			}

			_CMultivector(TValue fPrecision)
			{
				TValPrec::SetValuePrecision(fPrecision);
				Zero();
			}

			_CMultivector(const TMultivector& wA)
			{
				TValPrec::Reset();
				*this = wA;
			}

			template<unsigned t_uSubspaceDimension>
			_CMultivector(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
			{
				TValPrec::Reset();
				Create(wA);
			}

			_CMultivector(const tvec<TValue, AlgebraDimension>& vA)
			{
				TValPrec::Reset();
				Create(vA);
			}

			_CMultivector(const TValue(&pvalData)[AlgebraDimension])
			{
				TValPrec::Reset();
				Create(pvalData);
			}

			template<unsigned t_uDim>
			_CMultivector(const TValue(&pvalData)[t_uDim], const unsigned(&pBladeList)[t_uDim])
			{
				TValPrec::Reset();
				Create(pvalData, pBladeList);
			}

			TMultivector& operator=(const TMultivector& wA)
			{
				TValPrec::operator=(wA);
				MemCpy(m_pvalData, wA.m_pvalData);

				return *this;
			}

			template<typename TMultivectorA>
			TMultivector& operator=(const TMultivectorA& wA)
			{
				TValPrec::operator=(wA);
				Create(wA);
				return *this;
			}

			void Zero()
			{
				MemSet(m_pvalData, TValue(0));
			}

			void Reset()
			{
				Zero();
			}

			bool IsValid() const
			{
				return true;
			}

			unsigned GetBladeCount() const
			{
				return AlgebraDimension;
			}

			template<typename TMultivectorA>
			void Create(const TMultivectorA& wA)
			{
				Zero();

				wA.ForEachBlade([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							m_pvalData[blA.GetId()] = fValA;
							return true;
						});
			}


			void Create(const TValue(&pvalData)[AlgebraDimension])
			{
				MemCpy(m_pvalData, pvalData);
			}

			void Create(const tvec<TValue, AlgebraDimension>& vA)
			{
				MemCpy(m_pvalData, vA.v);
			}

			template<unsigned t_uDim>
			void Create(const TValue(&pvalData)[t_uDim], const unsigned(&pBladeList)[t_uDim])
			{
				Zero();
				for (unsigned uIdx = 0; uIdx < t_uDim; ++uIdx)
				{
					m_pvalData[pBladeList[uIdx]] = pvalData[uIdx];
				}
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
				TMultivector wB;
				ForEachBlade([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							wB.SetValueBlade(-fValA, blA);
							return true;
						});

				return wB;
			}

			TMultivector& operator+=(const TMultivector& wB)
			{
				ForEachBladePair(wB, [&](TValue& fValA, const TValue& fValB, TBlade& blA) -> bool
						{
							fValA += fValB;
							return true;
						});

				return *this;
			}

			template<unsigned t_uSubspaceDimension>
			TMultivector& operator+=(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
			{
				_ASSERTE(wA.IsValid());

				wA.ForEachBlade([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							m_pvalData[blA.GetId()] += fValA;
							return true;
						});
				return *this;
			}

			template<typename TMultivectorA>
			TMultivector& operator+=(const TMultivectorA& wA)
			{
				wA.ForEachBlade([this](const TValue& fValA, const TBlade& blA) -> bool
						{
							AddValueBlade(fValA, blA);
							return true;
						});
				return *this;
			}

			TMultivector& operator-=(const TMultivector& wB)
			{
				ForEachBladePair(wB, [&](TValue& fValA, const TValue& fValB, const TBlade& blA) -> bool
						{
							fValA -= fValB;
							return true;
						});

				return *this;
			}

			template<unsigned t_uSubspaceDimension>
			TMultivector& operator-=(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
			{
				_ASSERTE(wA.IsValid());

				wA.ForEachBlade([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							m_pvalData[blA.GetId()] -= fValA;
							return true;
						});
				return *this;
			}

			template<typename TMultivectorA>
			TMultivector& operator-=(const TMultivectorA& wA)
			{
				wA.ForEachBlade([this](const TValue& fValA, const TBlade& blA) -> bool
						{
							SubValueBlade(fValA, blA);
							return true;
						});
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

			TValue* GetDataPtr()
			{
				return m_pvalData;
			}

			const TValue* GetDataPtr() const
			{
				return m_pvalData;
			}

			// //////////////////////////////////////////////////////////////////////////////

			template<typename FuncOp>
			void ForEachBlade(FuncOp xFunc)
			{
				TValue* pData = m_pvalData;
				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData)
				{
					xFunc(*pData, TBlade(uIdx));
				}
			}

			template<typename FuncOp>
			void ForEachBlade(FuncOp xFunc) const
			{
				const TValue* pData = m_pvalData;
				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData)
				{
					xFunc(*pData, TBlade(uIdx));
				}
			}

			template<typename FuncOp>
			void ForEachBladeIndex(FuncOp xFunc)
			{
				TValue* pData = m_pvalData;
				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData)
				{
					xFunc(*pData, TBlade(uIdx), uIdx);
				}
			}

			template<typename FuncOp>
			void ForEachBladeIndex(FuncOp xFunc) const
			{
				const TValue* pData = m_pvalData;
				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData)
				{
					xFunc(*pData, TBlade(uIdx), uIdx);
				}
			}

			template<typename FuncOp>
			void ForEachBladePair(const TMultivector& wA, FuncOp xFunc)
			{
				TValue* pData        = m_pvalData;
				const TValue* pData2 = wA.m_pvalData;

				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData, ++pData2)
				{
					xFunc(*pData, *pData2, TBlade(uIdx));
				}
			}

			// //////////////////////////////////////////////////////////////////////////////

			template<typename FuncOp>
			bool ForEachBladeTest(FuncOp xFunc)
			{
				TValue* pData = m_pvalData;
				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData)
				{
					if (!xFunc(*pData, TBlade(uIdx)))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladeTest(FuncOp xFunc) const
			{
				const TValue* pData = m_pvalData;
				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData)
				{
					if (!xFunc(*pData, TBlade(uIdx)))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladeIndexTest(FuncOp xFunc)
			{
				TValue* pData = m_pvalData;
				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData)
				{
					if (!xFunc(*pData, TBlade(uIdx), uIdx))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladeIndexTest(FuncOp xFunc) const
			{
				const TValue* pData = m_pvalData;
				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData)
				{
					if (!xFunc(*pData, TBlade(uIdx), uIdx))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladePairTest(const TMultivector& wA, FuncOp xFunc)
			{
				TValue* pData        = m_pvalData;
				const TValue* pData2 = wA.m_pvalData;

				for (unsigned uIdx = 0; uIdx < AlgebraDimension; ++uIdx, ++pData, ++pData2)
				{
					if (!xFunc(*pData, *pData2, TBlade(uIdx)))
					{
						return false;
					}
				}

				return true;
			}

			// //////////////////////////////////////////////////////////////////////////////

			TBlade GetBlade(unsigned uIdx) const
			{
				return TBlade(uIdx);
			}

			TValue GetValue(unsigned uIdx) const
			{
				return m_pvalData[uIdx];
			}

			bool GetBladeIndex(unsigned& uIndex, const TBlade& blA) const
			{
				uIndex = blA.GetId();
				return true;
			}

			bool GetValueBlade(TValue& fValue, const TBlade& blA) const
			{
				//if ( blA.GetId() > AlgebraDimension )
				//	return false;

				fValue = m_pvalData[blA.GetId()];
				return true;
			}

			bool SetValueBlade(const TValue& fValue, const TBlade& blA)
			{
				//if ( blA.GetId() > AlgebraDimension )
				//	return false;

				m_pvalData[blA.GetId()] = fValue;
				return true;
			}

			bool AddValueBlade(const TValue& fValue, const TBlade& blA)
			{
				//if ( blA.GetId() > AlgebraDimension )
				//	return false;

				m_pvalData[blA.GetId()] += fValue;
				return true;
			}

			bool SubValueBlade(const TValue& fValue, const TBlade& blA)
			{
				//if ( blA.GetId() > AlgebraDimension )
				//	return false;

				m_pvalData[blA.GetId()] -= fValue;
				return true;
			}

		protected:

			TValue m_pvalData[AlgebraDimension];
		};

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 multivector.
		/// </summary>
		///
		/// <typeparam name="_TValue">	Type of the value. </typeparam>
		/// <typeparam name="_TBlade">	Type of the blade. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class _TValue, typename _TBlade>
		class CMultivector : public _CMultivector<_TValue, _TBlade>
		{
		public:

			typedef _TValue TValue;
			typedef _TBlade TBlade;
			typedef CMultivector<TValue, TBlade> TMultivector;
			typedef _CMultivector<TValue, TBlade> _TMultivector;
			typedef CValuePrecision<_TValue> TValPrec;

		public:

			CMultivector(void)
			{
				TValPrec::Reset();
			}

			CMultivector(TValue fPrecision)
			{
				TValPrec::SetValuePrecision(fPrecision);
				_TMultivector::Zero();
			}

			CMultivector(const _TMultivector& wA)
			{
				TValPrec::Reset();
				*this = wA;
			}

			template<unsigned t_uSubspaceDimension>
			CMultivector(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
			{
				TValPrec::Reset();
				_TMultivector::Create(wA);
			}

			CMultivector(const tvec<TValue, _TMultivector::AlgebraDimension>& vA)
			{
				TValPrec::Reset();
				_TMultivector::Create(vA);
			}

			CMultivector(const TValue(&pvalData)[_TMultivector::AlgebraDimension])
			{
				TValPrec::Reset();
				_TMultivector::Create(pvalData);
			}

			template<unsigned t_uDim>
			CMultivector(const TValue(&pvalData)[t_uDim], const unsigned(&pBladeList)[t_uDim])
			{
				TValPrec::Reset();
				Create(pvalData, pBladeList);
			}

			TMultivector& operator=(const _TMultivector& wA)
			{
				_TMultivector::operator=(wA);
				return *this;
			}

			template<typename TMultivectorA>
			TMultivector& operator=(const TMultivectorA& wA)
			{
				TValPrec::operator=(wA);
				_TMultivector::Create(wA);
				return *this;
			}
		};
	}
}	// namespace Tan.GA
