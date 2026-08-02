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

#include "Tan.Core/ValueFormatString.h"

#include "Multivector.h"
#include "MV_Operators.h"
#include "SubspaceBasis.h"

namespace Tan
{
	namespace GA
	{
		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Convert this CBlade into a string representation. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="uGrade">	The grade. </param>
		/// <param name="blA">   	The bl a. </param>
		///
		/// <returns>	uGrade as a std::string. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
		std::string ToString(unsigned& uGrade, const GA::CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blA)
		{
			typedef GA::CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> TBlade;

			std::string sName = "E";
			char pcValue[10];
			unsigned uShift;
			const unsigned uBlade = blA.GetId();

			uGrade = 0;

			if (uBlade == 0)
			{
				sName = "";
				return sName;
			}

			uShift = uBlade;
			for (unsigned i = 0; i < TBlade::VectorSpaceDimension; ++i)
			{
				if ((uShift & 1))
				{
					snprintf(pcValue, sizeof(pcValue), "%d", i + 1);
					sName += std::string(pcValue);
					++uGrade;
				}

				uShift >>= 1;
			}

			return sName;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Convert this object into a string representation. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="blA">	The bl a. </param>
		///
		/// <returns>	blA as a std::string. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
		std::string ToString(const GA::CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blA)
		{
			unsigned uGrade;
			return ToString(uGrade, blA);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Convert this object into a string representation. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="wA">	The mv a. </param>
		///
		/// <returns>	wA as a std::string. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TMultivector>
		std::string ToString(const TMultivector& wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			std::string sName = "";
			std::string sBlade;
			std::string psGradeName[TMultivector::VectorSpaceDimension];
			std::string psSign[TMultivector::VectorSpaceDimension];
			unsigned uGrade;
			char pcValue[30];
			TValue fValue;

			if (IsScalar(wA))
			{
				if (wA.GetValueBlade(fValue, TBlade(0)))
				{
					snprintf(pcValue, sizeof(pcValue), ValueFormatString<TValue>().c_str(), fValue);
				}
				else
				{
					snprintf(pcValue, sizeof(pcValue), ValueFormatString<TValue>().c_str(), TValue(0));
				}

				sName = std::string(pcValue);
			}
			else
			{
				if (!wA.GetValueBlade(fValue, TBlade(0)))
				{
					fValue = TValue(0);
				}

				if (!wA.IsZero(fValue))
				{
					TValue fAbsVal = ::abs(fValue);
					snprintf(pcValue, sizeof(pcValue), ValueFormatString<TValue>().c_str(), fAbsVal);
					if (fValue < TValue(0))
					{
						sName = "-";
					}
					else
					{
						sName = "";
					}
					sName += std::string(pcValue);
				}

				wA.ForEachBlade([&](const TValue& fValA, const TBlade& blA) -> bool
						{
							if (blA.GetId() == 0)
							{
								return true;
							}

							if (!wA.IsZero(fValA))
							{
								sBlade = ToString(uGrade, blA);

								if (psGradeName[uGrade - 1].size() > 0)
								{
									psGradeName[uGrade - 1] += (fValA < 0 ? " - " : " + ");
								}
								else
								{
									psSign[uGrade - 1] = (fValA < 0 ? "-" : "+");
								}

								fValue = ::abs(fValA);

								if (!wA.IsEqual(fValue, TValue(1)))
								{
									snprintf(pcValue, sizeof(pcValue), ValueFormatString<TValue>().c_str(), fValue);
									psGradeName[uGrade - 1] += std::string(pcValue) + "*";
								}

								psGradeName[uGrade - 1] += sBlade;
							}

							return true;
						});

				for (uGrade = 0; uGrade < TMultivector::VectorSpaceDimension; ++uGrade)
				{
					if (psGradeName[uGrade].size() == 0)
					{
						continue;
					}

					if (sName.size() > 0)
					{
						sName += " " + psSign[uGrade] + " ";
					}
					else if (psSign[uGrade] == "-")
					{
						sName += psSign[uGrade];
					}

					sName += psGradeName[uGrade];
				}
			}

			return sName;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Convert this object into a string representation. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="xSubBasis">	The sub basis. </param>
		///
		/// <returns>	xSubBasis as a std::string. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TValue, typename TBlade>
		std::string ToString(const CSubspaceBasis<TValue, TBlade>& xSubBasis)
		{
			typedef typename CSubspaceBasis<TValue, TBlade>::TMultivector TMultivector;
			std::string sList = "";

			xSubBasis.ForEachBasisBladeIndex([&](const TMultivector& wA, const TMultivector& wRecipA, size_t uIdx)
					{
						char pcVal[10];
						snprintf(pcVal, sizeof(pcVal), "%zu", uIdx);

						sList += pcVal;
						sList += ": ";
						sList += ToString(wA) + "\n";
					});

			return sList;
		}

		template<typename TValue>
		std::string ToString(const tvec3<TValue>& vA)
		{
			char pcText[100];

			std::string sText = "";
			snprintf(pcText, sizeof(pcText), "(%g, %g, %g)", vA.x, vA.y, vA.z);
			sText = pcText;
			return sText;
		}

		template<typename TValue>
		std::string ToString(const std::vector < tvec3 < TValue >>& vecListA)
		{
			char pcValue[30];
			std::string sText = "";

			ForEachIndex(vecListA, [&](const tvec3<TValue>& vA, size_t uIndex)
					{
						snprintf(pcValue, sizeof(pcValue), "%d", (int) uIndex);
						sText += pcValue;
						sText += ": ";
						sText += GA::ToString(vA);
						sText += "\n";
					});

			return sText;
		}
	}
}	// .GA
