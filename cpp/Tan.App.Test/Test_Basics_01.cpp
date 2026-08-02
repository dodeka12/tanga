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



#include <stdint.h>
#include <inttypes.h>
#include <random>


#include "Tan.Core/IntrinsicFunctions.h"

#include "Tan.Math/Congruence.h"

#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/String.h"

#include "Tan.GA/Matrix_MapToBladeMask.h"
#include "Tan.GA/Algo.h"

#include "Test_Crypt_Func.h"

using namespace Tan;

static const unsigned c_uVectorSpaceDim = 3;

typedef int64_t TValue;
typedef Tan::CCongruence_HMod<TValue> TCongruence;
typedef GA::CBlade<c_uVectorSpaceDim, 0>::TBlade TBlade;
typedef GA::SValueBlade<TValue, TBlade> TE;
typedef Tan::CMatrix<TValue> TMatrix;
typedef GA::CBladeMask<TBlade> TMask;
typedef GA::CDynamicMultivector<TValue, TBlade> TDynMV;

static const unsigned int c_uAlgDim = TDynMV::AlgebraDimension;

int main(int _argc, char **_argv)
{

	TValue tHalfRange = 2;

	TValue tModA = 3;
	TValue tModB = 5;
	TValue tModC = 11;

	printf("tModA: %" PRId64 ", tModB %" PRId64 ", tModC %" PRId64 "\n\n", tModA, tModB, tModC);

	TCongruence xModA(tModA);
	TCongruence xModB(tModB);
	TCongruence xModC(tModC);

	try
	{
		std::default_random_engine xRandomEngine;
		std::uniform_int_distribution<TValue> xRandomDistribution(-tHalfRange, tHalfRange);
		auto xRandom = std::bind(xRandomDistribution, xRandomEngine);
		TValue tVal = xRandomDistribution(xRandomEngine);

		TDynMV wF, wFib, wFia, wG, wGi, wL;
		TDynMV wE, wEic, wEib, wEia;

		Tan::GA::EResult eRes, eRes2, eRes3;
		
		int iTrial = 0;
		do
		{
			if (iTrial > 10)
				return -1;

			GenRanMV(wF, xRandom);
			PMV(wF);

			eRes = Tan::GA::Inverse(wFib, wF, xModB);
			PrintResult(eRes);

			eRes2 = Tan::GA::Inverse(wFia, wF, xModA);
			PrintResult(eRes2);

			++iTrial;
		}
		while (eRes != Tan::GA::EResult::Success || eRes2 != Tan::GA::EResult::Success);

		PMV(wF);

		wFib.Prune();
		PMV(wFib);

		wFia.Prune();
		PMV(wFia);

		TDynMV wF_Fia;
		GA::GP(wF_Fia, wF, wFia);
		PMV(wF_Fia);

		TDynMV wI_b;
		GA::GP_Congruence(wI_b, wF, wFib, xModB);
		PMV(wI_b);

		printf("\n\n");
		// return 0;

		GenRanMV(wG, xRandom);
		PMV(wG);

		TDynMV wG_a;
		wG_a = wG * tModA;
		PMV(wG_a);

		TDynMV wFib_G_a;
		GA::GP_Congruence(wFib_G_a, wFib, wG_a, xModB);
		PMV(wFib_G_a);

		TDynMV wF_Fib_G_a;
		GA::GP_Congruence(wF_Fib_G_a, wF, wFib_G_a, xModB);
		PMV(wF_Fib_G_a);

		////////////////////////////////////

		TDynMV wF_G;
		GA::GP_Congruence(wF_G, wF, wG, xModB);
		PMV(wF_G);

		TDynMV wFia_F_G;
		GA::GP_Congruence(wFia_F_G, wFia, wF_G, xModA);
		PMV(wFia_F_G);

		TDynMV wTest;
		wTest = wFia_F_G - wG;
		PMV(wTest);



	}
	catch (std::exception& xEx)
	{
		printf("\nEXCEPTION:\n%s\n\n", xEx.what());
		return -1;
	}

	return 0;
}
