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
#include <algorithm>

#include "Tan.Core/Defines.h"
#include "Tan.Math/ValuePrecision.h"

#include "MV_Operators.h"

namespace Tan
{
	namespace GA
	{
		template<typename _TValue, typename _TBlade>
		struct SValueBlade
		{
			typedef _TValue TValue;
			typedef _TBlade TBlade;

			SValueBlade()
			{
			}

			SValueBlade(const TValue& _fValue, const TBlade& _xBlade)
			{
				fValue = _fValue;
				xBlade = _xBlade;
			}

			SValueBlade(const TValue& _fValue, const unsigned& uBlade)
			{
				fValue = _fValue;
				xBlade = TBlade(uBlade);
			}

			TValue fValue;
			TBlade xBlade;
		};

		template<typename _TValue, typename _TBlade>
		class CDynamicMultivector : public CValuePrecision<_TValue>
		{
		public:

			typedef _TValue TValue;
			typedef _TBlade TBlade;
			typedef CDynamicMultivector<TValue, TBlade> TMultivector;
			typedef SValueBlade<TValue, TBlade> TValueBlade;

			static const unsigned AlgebraDimension     = TBlade::AlgebraDimension;
			static const unsigned VectorSpaceDimension = TBlade::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = TBlade::VectorSpaceSignature;

		protected:

			typedef std::map<TBlade, TValue> TMap;
			typedef typename std::map<TBlade, TValue>::iterator TIter;
			typedef typename std::map<TBlade, TValue>::const_iterator TConstIter;
			typedef std::pair<TBlade, TValue> TPair;
			typedef CValuePrecision<_TValue> TValPrec;

		protected:

			std::map<TBlade, TValue> m_mapBladeValue;

		public:

			CDynamicMultivector()
			{
				TValPrec::Reset();
				Reset();
			}

			CDynamicMultivector(TValue fPrecision)
			{
				TValPrec::SetValuePrecision(fPrecision);
				Reset();
			}

			CDynamicMultivector(const TMultivector& wA)
			{
				TValPrec::SetValuePrecision(wA.GetValuePrecision());
				*this = wA;
			}

			template<typename TMultivectorA>
			CDynamicMultivector(const TMultivectorA& wA)
			{
				TValPrec::SetValuePrecision(wA.GetValuePrecision());
				*this = wA;
			}

			CDynamicMultivector(const SValueBlade<TValue, TBlade>& xData)
			{
				CValuePrecision<TValue>::Reset();
				*this << xData;
			}

			CDynamicMultivector(const SValueBlade<TValue, TBlade>& xData, TValue fPrec)
			{
				TValPrec::SetValuePrecision(fPrec);
				*this << xData;
			}

			CDynamicMultivector(const TBlade& _xBlade)
			{
				CValuePrecision<TValue>::Reset();
				AddValueBlade(TValue(1), _xBlade);
			}

			CDynamicMultivector(const TBlade& _xBlade, TValue fPrec)
			{
				TValPrec::SetValuePrecision(fPrec);
				AddValueBlade(TValue(1), _xBlade);
			}

			CDynamicMultivector(const TValue& _fValue, const TBlade& _xBlade)
			{
				CValuePrecision<TValue>::Reset();
				AddValueBlade(_fValue, _xBlade);
			}

			CDynamicMultivector(const TValue& _fValue, const TBlade& _xBlade, TValue fPrec)
			{
				TValPrec::SetValuePrecision(fPrec);
				AddValueBlade(_fValue, _xBlade);
			}

			template<typename TMultivectorX>
			CDynamicMultivector(const TBlade& blA, const TMultivectorX& wB)
			{
				TValPrec::SetValuePrecision(wB.GetValuePrecision());
				TMultivector wA(TValue(1), blA, wB.GetValuePrecision());

				GA::GP(*this, wA, wB);
			}

			template<typename TMultivectorX>
			CDynamicMultivector(const TValue& fValue, const TBlade& blA, const TMultivectorX& wB)
			{
				SetValuePrecision(wB.GetValuePrecision());
				TMultivector wA(fValue, blA, wB.GetValuePrecision());

				GA::GP(*this, wA, wB);
			}

			TMultivector& operator=(const TMultivector& wA)
			{
				CValuePrecision<TValue>::operator=(wA);
				m_mapBladeValue = wA.m_mapBladeValue;
				return *this;
			}

			template<typename TMultivectorA>
			TMultivector& operator=(const TMultivectorA& wA)
			{
				// TODO catch exception
				CValuePrecision<TValue>::operator=(wA);
				Create(wA);
				return *this;
			}

			template<typename TMultivectorA>
			void Create(const TMultivectorA& wA)
			{
				Reset();

				wA.ForEachBlade([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							if (!SetValueBlade(fValA, blA))
							{
								TAN_THROW_RT("Invalid source multivector");
							}

							return true;
						});
			}

			void Zero()
			{
				ForEachBlade([&](TValue& fValue, const TBlade& blA) -> bool
						{
							_SetValue(fValue, 0);
							return true;
						});
			}

			bool IsValid() const
			{
				return true;
			}

			template<typename TValue2>
			void _SetValue(TValue& fValTrg, const TValue2& fValSrc)
			{
				fValTrg = TValue(fValSrc);
			}

			void Reset()
			{
				m_mapBladeValue.clear();
			}

			void Prune()
			{
				TIter itEl = m_mapBladeValue.begin();
				while (itEl != m_mapBladeValue.end())
				{
					if (TValPrec::IsZero(itEl->second))
					{
						m_mapBladeValue.erase(itEl);
						itEl = m_mapBladeValue.begin();
					}
					else
					{
						++itEl;
					}
				}
			}

			unsigned GetBladeCount() const
			{
				return unsigned(m_mapBladeValue.size());
			}

			TBlade GetBlade(unsigned uIdx) const
			{
				TConstIter itEl = m_mapBladeValue.find(TBlade(uIdx));
				if (itEl == m_mapBladeValue.end())
				{
					TAN_THROW_RT("Invalid blade index");
				}

				return itEl->first;
			}

			TValue GetValue(unsigned uIdx) const
			{
				TConstIter itEl = m_mapBladeValue.find(TBlade(uIdx));
				if (itEl == m_mapBladeValue.end())
				{
					TAN_THROW_RT("Invalid blade index");
				}

				return itEl->second;
			}

			bool GetBladeIndex(unsigned& uIndex, const TBlade& blA) const
			{
				TConstIter itEl = m_mapBladeValue.find(blA);
				if (itEl == m_mapBladeValue.end())
				{
					return false;
				}

				uIndex = blA.GetId();
				return true;
			}

			bool GetValueBlade(TValue& fValue, const TBlade& blA) const
			{
				TConstIter itEl = m_mapBladeValue.find(blA);
				if (itEl == m_mapBladeValue.end())
				{
					return false;
				}

				fValue = itEl->second;
				return true;
			}

			bool SetValueBlade(const TValue& fValue, const TBlade& blA)
			{
				m_mapBladeValue[blA] = fValue;

				return true;
			}

			bool AddValueBlade(const TValue& fValue, const TBlade& blA)
			{
				if (this->IsZero(fValue))
				{
					return true;
				}

				TIter itEl = m_mapBladeValue.find(blA);
				if (itEl == m_mapBladeValue.end())
				{
					m_mapBladeValue[blA] = fValue;
				}
				else
				{
					TAN_TEST_SUM_OVERFLOW(fValue, itEl->second);

					itEl->second += fValue;
				}

				return true;
			}

			template<typename TCongruence>
			bool AddValueBlade(const TValue& _fValue, const TBlade& blA, const TCongruence& xCongruence)
			{
				TValue fValue;
				xCongruence.Map(fValue, _fValue);

				if (this->IsZero(fValue))
				{
					return true;
				}

				TIter itEl = m_mapBladeValue.find(blA);
				if (itEl == m_mapBladeValue.end())
				{
					m_mapBladeValue[blA] = fValue;
				}
				else
				{
					TAN_TEST_SUM_OVERFLOW(fValue, itEl->second);

					fValue += itEl->second;
					xCongruence.Map(itEl->second, fValue);
				}

				return true;
			}

			bool SubValueBlade(const TValue& fValue, const TBlade& blA)
			{
				if (this->IsZero(fValue))
				{
					return true;
				}

				TIter itEl = m_mapBladeValue.find(blA);
				if (itEl == m_mapBladeValue.end())
				{
					m_mapBladeValue[blA] = -fValue;
				}
				else
				{
					itEl->second -= fValue;
				}

				return true;
			}

			TMultivector& Negate()
			{
				ForEachBlade([this](TValue& fValA, const TBlade& blA)
						{
							fValA = -fValA;
						});

				return *this;
			}

			TMultivector operator-() const
			{
				TMultivector wB;
				ForEachBlade([&](const TValue& fValA, const TBlade& blA)
						{
							wB.SetValueBlade(-fValA, blA);
						});

				return wB;
			}

			TMultivector& operator+=(const SValueBlade<TValue, TBlade>& xData)
			{
				AddValueBlade(xData.fValue, xData.xBlade);
				return *this;
			}

			TMultivector& operator<<(const SValueBlade<TValue, TBlade>& xData)
			{
				AddValueBlade(xData.fValue, xData.xBlade);
				return *this;
			}

			template<typename TMultivectorA>
			TMultivector& operator+=(const TMultivectorA& wA)
			{
				wA.ForEachBlade([this](const TValue& fValA, const TBlade& blA)
						{
							AddValueBlade(fValA, blA);
						});
				return *this;
			}

			template<typename TMultivectorA>
			TMultivector& operator-=(const TMultivectorA& wA)
			{
				wA.ForEachBlade([this](const TValue& fValA, const TBlade& blA)
						{
							SubValueBlade(fValA, blA);
						});
				return *this;
			}

			TMultivector& operator*=(const TValue& fValue)
			{
				ForEachBlade([&](TValue& fValA, const TBlade& blA)
						{
							fValA *= fValue;
						});

				return *this;
			}

			TMultivector& operator/=(const TValue& fValue)
			{
				ForEachBlade([&](TValue& fValA, const TBlade& blA) 
						{
							fValA /= fValue;
						});

				return *this;
			}


			template<typename FuncOp>
			void ForEachBlade(FuncOp xFunc)
			{
				TIter itEnd = m_mapBladeValue.end();
				for (TIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					xFunc(itEl->second, itEl->first);
				}
			}

			template<typename FuncOp>
			void ForEachBlade(FuncOp xFunc) const
			{
				TConstIter itEnd = m_mapBladeValue.end();
				for (TConstIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					xFunc(itEl->second, itEl->first);
				}
			}

			template<typename FuncOp>
			void ForEachBladeIndex(FuncOp xFunc)
			{
				TIter itEnd = m_mapBladeValue.end();
				for (TIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					xFunc(itEl->second, itEl->first, itEl->first.GetId());
				}
			}

			template<typename FuncOp>
			void ForEachBladeIndex(FuncOp xFunc) const
			{
				TConstIter itEnd = m_mapBladeValue.end();
				for (TConstIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					xFunc(itEl->second, itEl->first, itEl->first.GetId());
				}
			}

			template<typename FuncOp>
			void ForEachBladePair(const TMultivector& wA, FuncOp xFunc)
			{
				TValue fValA;
				TIter itEnd = m_mapBladeValue.end();
				for (TIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					if (!wA.GetValueBlade(fValA, itEl->first))
					{
						fValA = TValue(0);
					}

					xFunc(itEl->second, fValA, itEl->first);
				}
			}

			// //////////////////////////////////////////////////////////////////////////

			template<typename FuncOp>
			bool ForEachBladeTest(FuncOp xFunc)
			{
				TIter itEnd = m_mapBladeValue.end();
				for (TIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					if (!xFunc(itEl->second, itEl->first))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladeTest(FuncOp xFunc) const
			{
				TConstIter itEnd = m_mapBladeValue.end();
				for (TConstIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					if (!xFunc(itEl->second, itEl->first))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladeIndexTest(FuncOp xFunc)
			{
				TIter itEnd = m_mapBladeValue.end();
				for (TIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					if (!xFunc(itEl->second, itEl->first, itEl->first.GetId()))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladeIndexTest(FuncOp xFunc) const
			{
				TConstIter itEnd = m_mapBladeValue.end();
				for (TConstIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					if (!xFunc(itEl->second, itEl->first, itEl->first.GetId()))
					{
						return false;
					}
				}

				return true;
			}

			template<typename FuncOp>
			bool ForEachBladePairTest(const TMultivector& wA, FuncOp xFunc)
			{
				TValue fValA;
				TIter itEnd = m_mapBladeValue.end();
				for (TIter itEl = m_mapBladeValue.begin(); itEl != itEnd; ++itEl)
				{
					if (!wA.GetValueBlade(fValA, itEl->first))
					{
						fValA = TValue(0);
					}

					if (!xFunc(itEl->second, fValA, itEl->first))
					{
						return false;
					}
				}

				return true;
			}

		};
	}
}	// .GA
