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


#include <random>
#include <set>

#include "Tan.GA/Enum.h"
#include "Tan.Math/InlineMath.h"

#define PMAT(theMat) printf(#theMat ": %s\n\n", Tan::ToString(theMat, "%2d").c_str())

#define PMV(theMV) theMV.Prune(); printf(#theMV " (%d): %s\n\n", theMV.GetBladeCount(), ToString(theMV).c_str())
#define PMVT(theText, theMV) theMV.Prune(); printf("%s: " #theMV " (%d): %s\n\n", theText, theMV.GetBladeCount(), ToString(theMV).c_str())

#define E(theDim) (1 << theDim)

void PrintResult(Tan::GA::EResult eRes);

template< typename TDynMV, typename TRandom>
void GenRanMV(TDynMV& wR, TRandom& xRandom)
{
	wR.Zero();
	for (unsigned uBladeIdx = 0; uBladeIdx < TDynMV::AlgebraDimension; ++uBladeIdx)
	{
		typename TDynMV::TValue tRan = xRandom();
		wR.AddValueBlade(tRan, uBladeIdx);
	}

	wR.Prune();
}

template< typename TDynMV, typename TRanValue, typename TRanBlade>
void GenRanMV(TDynMV& wR, size_t nBladeCnt, TRanValue& xRanValue, TRanBlade& xRanBlade)
{
	using TBladeId = typename TDynMV::TBlade::TBladeId;
	using TValue = typename TDynMV::TValue;

	std::set<TBladeId> setBlades;

	do 
	{
		setBlades.insert(xRanBlade());
	} while (setBlades.size() < nBladeCnt);

	wR.Zero();
	for (TBladeId tBlade : setBlades)
	{
		TValue tRan;
		while ((tRan = xRanValue()) == TValue(0));

		wR.AddValueBlade(tRan, tBlade);
	}

	wR.Prune();
}


template<typename TValue>
TValue EvalNextHigherPrime(TValue tValue)
{
	TValue tGcd   = 0;
	TValue tPrime = tValue - 2 + (tValue % 2 == 0 ? 1 : 0);

	bool bIsPrime = true;
	do
	{
		TValue tDivider;
		tPrime += 2;
		bIsPrime = true;

		for (tDivider = 2; tDivider <= tPrime / tDivider; ++tDivider)
		{
			if (tPrime % tDivider == 0)
			{
				bIsPrime = false;
				break;
			}
		}
	}
	while (!bIsPrime);

	return tPrime;
}

template<typename TValue>
TValue EvalCoveringPrimeMod(TValue tModA, size_t nProdCnt, size_t nAlgebraDimension)
{
	TValue tMaxVal = tModA * (tModA / 2);

	for (size_t nProdIdx = 0; nProdIdx < nProdCnt; ++nProdIdx)
	{
		tMaxVal *= (tModA / 2) * TValue(nAlgebraDimension);
	}

	if (tMaxVal < 0)
	{
		TAN_THROW_RT("Overflow while calculating covering prime modulus.");
	}

	return EvalNextHigherPrime(tMaxVal * 2 + 1);
}
