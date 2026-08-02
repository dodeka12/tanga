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

#include <cstdio>
#include <string>

#include "Tan.Math/ValuePrecision.h"

#include "DynamicMultivector.h"
#include "SubspaceBasis.h"
#include "SubspaceMask.h"
#include "MV_Operators.h"

namespace Tan
{
	namespace GA
	{
		template<typename _TValue, typename _TBlade>
		class CMultivectorStyle : public CSubspaceBasis<_TValue, _TBlade>
		{
		public:

			typedef _TValue TValue;
			typedef _TBlade TBlade;
			typedef CSubspaceBasis<_TValue, _TBlade> TBase;
			typedef typename TBase::TMultivector TMultivector;
			typedef CMultivectorStyle<_TValue, _TBlade> TStyle;
			typedef TBase TBasis;
			typedef CSubspaceMask<TBasis> TMask;

		public:

			static const unsigned AlgebraDimension     = TBlade::AlgebraDimension;
			static const unsigned VectorSpaceDimension = TBlade::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = TBlade::VectorSpaceSignature;

		public:

			struct SPairName
			{
				SPairName()
				{
				}

				SPairName(const TMultivector& _mvBlade, const char* pcName)
					: xPair(_mvBlade), sName(pcName)
				{
				}

				SPairName(const TMultivector& _mvBlade, const std::string& _sName)
					: xPair(_mvBlade), sName(_sName)
				{
				}

				SPairName(const TValue& _fValue, const TBlade& _xBlade, const std::string& _sName, const TValue& fPrec)
					: xPair(_fValue, _xBlade, fPrec), sName(_sName)
				{
				}

				SPairName(const TValue& _fValue, const TBlade& _xBlade, const char* pcName, const TValue& fPrec)
					: xPair(_fValue, _xBlade, fPrec), sName(pcName)
				{
				}

				SPairName(const TBlade& _xBlade, const char* pcName, const TValue& fPrec)
					: xPair(TValue(1), _xBlade, fPrec), sName(pcName)
				{
				}

				SPairName(const TBlade& _xBlade, const TMultivector& wA, const char* pcName)
					: xPair(TValue(1), _xBlade, wA.GetValuePrecision()), sName(pcName)
				{
					TMultivector wB;
					GA::GP(wB, xPair.wBlade, wA);
					xPair.wBlade = wB;
				}

				SPairName(const TValue& _fValue, const TBlade& _xBlade, const TMultivector& wA, const char* pcName)
					: xPair(_fValue, _xBlade, wA.GetValuePrecision()), sName(pcName)
				{
					TMultivector wB;
					GA::GP(wB, xPair.wBlade, wA);
					xPair.wBlade = wB;
				}

				typename TBasis::SBladePair xPair;
				std::string sName;
			};

		public:

			CMultivectorStyle()
				: TBase()
			{
			}

			CMultivectorStyle(const TValue& fPrec)
				: TBase(fPrec)
			{
			}

			void Reset()
			{
				TBase::Reset();
				m_vecNameList.reserve(AlgebraDimension);
				m_vecNameList.resize(0);
			}

			void AddBasisBladeName(const SPairName& xPairName)
			{
				try
				{
					TBase::AddBasisBlade(xPairName.xPair);
					m_vecNameList.push_back(xPairName.sName);
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error adding blade name", xEx);
				}
			}

			TStyle& operator<<(const SPairName& xPairName)
			{
				try
				{
					AddBasisBladeName(xPairName);
					return *this;
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error adding basis blade name", xEx);
				}
			}

			template<typename TMultivectorA>
			std::string ToString(const TMultivectorA& wA) const
			{
				std::string sName = "";

				TBase::ForEachBasisBladeIndex([&](const TMultivector& wBlade, const TMultivector& wRecipBlade, size_t uIndex) -> bool
						{
							return _ToString(sName, wRecipBlade, m_vecNameList[uIndex], wA);
						});

				if (sName.size() == 0)
				{
					sName = "0";
				}

				return sName;
			}

			template<typename TMultivectorA>
			std::string ToString(const std::vector<TMultivectorA>& vecwListA) const
			{
				char pcVal[10];
				std::string sText = "";

				ForEachIndex(vecwListA, [&](const TMultivectorA& wA, size_t uMvIdx)
						{
							snprintf(pcVal, sizeof(pcVal), "%d", (int) uMvIdx);
							sText += pcVal;
							sText += ": ";
							sText += this->ToString(wA);
							sText += "\n";
						});

				return sText;
			}

			std::string ToString(const TBase& xSubBasis) const
			{
				std::string sList = "";

				xSubBasis.ForEachBasisBladeIndex([&](const TMultivector& wBlade, const TMultivector& wRecipBlade, size_t uIdx) -> bool
						{
							char pcVal[10];
							snprintf(pcVal, sizeof(pcVal), "%u", (unsigned) uIdx);

							sList += pcVal;
							sList += " : ";
							sList += this->ToString(wBlade) + "\n";

							sList += pcVal;
							sList += "!: ";
							sList += this->ToString(wRecipBlade) + "\n\n";
							return true;
						});

				return sList;
			}

			std::string ToString(const TMask& xMask, bool bSimple = false) const
			{
				std::string sList = "";

				if (bSimple)
				{
					xMask.ForEachBasisBladePair(*this, [&](size_t uBitIdx, const TMultivector& wBlade, const TMultivector& wRecipBlade) -> bool
							{
								sList += this->ToString(wBlade) + ", ";
								return true;
							});
					sList += "\n";
				}
				else
				{
					xMask.ForEachBasisBladePair(*this, [&](size_t uBitIdx, const TMultivector& wBlade, const TMultivector& wRecipBlade) -> bool
							{
								char pcVal[10];
								snprintf(pcVal, sizeof(pcVal), "%d", (int) uBitIdx);

								sList += pcVal;
								sList += " : ";
								sList += this->ToString(wBlade) + "\n";

								sList += pcVal;
								sList += "!: ";
								sList += this->ToString(wRecipBlade) + "\n\n";
								return true;
							});
				}

				return sList;
			}

		protected:

			template<typename TMultivectorA>
			bool _ToString(std::string& sName, const TMultivector& wRecipBlade, const std::string& sBladeName, const TMultivectorA& wA) const
			{
				static const TValue c_fZero  = TValue(0);
				static const TValue c_fUnity = TValue(1);

				TValue fValue;
				char pcValue[30];

				GA::SP(fValue, wRecipBlade, wA);

				if (this->IsZero(fValue))
				{
					return true;
				}

				if (sName.size() == 0)
				{
					if (fValue < c_fZero)
					{
						sName += "-";
					}
				}
				else
				{
					sName += (fValue < 0 ? " - " : " + ");
				}

				fValue = ::abs(fValue);

				if ((sBladeName.size() == 0) || !TBase::TValPrec::IsEqual(fValue, c_fUnity))
				{
					snprintf(pcValue, sizeof(pcValue), ValueFormatString<TValue>().c_str(), fValue);
					sName += std::string(pcValue);

					if (sBladeName.size() > 0)
					{
						sName += std::string("*");
					}
				}

				sName += sBladeName;
				return true;
			}

		protected:

			std::vector<std::string> m_vecNameList;
		};
	}
}	// .GA
