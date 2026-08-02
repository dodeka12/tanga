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

#include "EvalPrimesAlgo1.h"

#include "Tan.Core/IntrinsicFunctions.h"

#include "Tan.Math/Congruence.h"

#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/String.h"

#include "Tan.GA/Matrix_MapToBladeMask.h"
#include "Tan.GA/Algo.h"

#include "Test_Crypt_Func.h"

using namespace Tan;

static const unsigned c_uVectorSpaceDim = 5;

typedef int64_t TValue;
typedef Tan::CCongruence_HMod<TValue> TCongruence;
typedef GA::CBlade<c_uVectorSpaceDim, 0>::TBlade TBlade;
typedef GA::SValueBlade<TValue, TBlade> TE;
typedef Tan::CMatrix<TValue> TMatrix;
typedef GA::CBladeMask<TBlade> TMask;
typedef GA::CDynamicMultivector<TValue, TBlade> TDynMV;

static const unsigned int c_uAlgDim = TDynMV::AlgebraDimension;

std::set<TValue> setPrimes;

int Test_Crypt_02()
{
	EvalPrimes(setPrimes, TValue(100000));


	TValue tHalfRange = 4;
	TValue tR         = 2 * tHalfRange + 1;

	TValue tModA = 11;	// tHalfRange * tHalfRange * tHalfRange * c_uAlgDim * c_uAlgDim / 64;
	//tModA = EvalNextHigherPrime(2 * tModA + 1);	// *setPrimes.lower_bound(tModA);

	TValue tModB = tModA * tHalfRange * tHalfRange * c_uAlgDim;
	tModB = EvalNextHigherPrime(2 * tModB + 1);	// *setPrimes.lower_bound(tModB);	// EvalNextHigherPrime(tModB);

	TValue tModC = (tModB / 2) * tHalfRange * c_uAlgDim;		// EvalNextHigherPrime(tModB * 2 + 1);
	tModC = EvalNextHigherPrime(2 * tModC + 1);		// *setPrimes.lower_bound(tModC);

	printf("tModA: %" PRId64 ", tModB %" PRId64 ", tModC %" PRId64 "\n\n", tModA, tModB, tModC);

	TCongruence xModA(tModA);
	TCongruence xModB(tModB);
	TCongruence xModC(tModC);

	//int64_t iValA = 1;
	//int64_t iValB = 1;

	//iValA <<= 31;
	//iValB <<= 32;
	//iValB  *= -1;

	//bool bOverflow = Tan::Intrinsics::ProductWillOverflow(iValA, iValB);
	//int64_t iValC  = iValA * iValB;

	try
	{
		std::default_random_engine xRandomEngine;
		std::uniform_int_distribution<TValue> xRandomDistribution(-tHalfRange, tHalfRange);
		auto xRandom = std::bind(xRandomDistribution, xRandomEngine);
		TValue tVal = xRandomDistribution(xRandomEngine);

		TDynMV wF, wFi, wFia, wG, wGi;
		TDynMV wE, wEic, wEib, wEia;

		Tan::GA::EResult eRes, eRes2, eRes3;
		
		int iTrial = 0;
		do
		{
			if (iTrial > 10)
				return -1;

			GenRanMV(wF, xRandom);
			PMV(wF);

			eRes = Tan::GA::Inverse(wFi, wF, xModB);
			PrintResult(eRes);

			eRes2 = Tan::GA::Inverse(wFia, wF, xModA);
			PrintResult(eRes2);

			++iTrial;
		}
		while (eRes != Tan::GA::EResult::Success || eRes2 != Tan::GA::EResult::Success);

		PMV(wF);


		wFi.Prune();
		PMV(wFi);

		wFia.Prune();
		PMV(wFia);

		printf("\n\n");

		do
		{
			GenRanMV(wE, xRandom);
			eRes = Tan::GA::Inverse(wEic, wE, xModC);
			PrintResult(eRes);

			eRes2 = Tan::GA::Inverse(wEib, wE, xModB);
			PrintResult(eRes2);

			eRes3 = Tan::GA::Inverse(wEia, wE, xModA);
			PrintResult(eRes3);
		}
		while (eRes != Tan::GA::EResult::Success || eRes2 != Tan::GA::EResult::Success || eRes3 != Tan::GA::EResult::Success);

		PMV(wE);

		wEic.Prune();
		PMV(wEic);

		wEib.Prune();
		PMV(wEib);

		wEia.Prune();
		PMV(wEia);

		printf("\n\n");

		GenRanMV(wG, xRandom);
		PMV(wG);

		TDynMV wGa;
		wGa = tModA * wG;
		GA::Congruence(wGa, xModB);
		PMV(wGa);

		TDynMV wFi_Ga;
		GA::GP_Congruence(wFi_Ga, wFi, wGa, xModB);
		PMV(wFi_Ga);

		TDynMV wFi_Ga_a = wFi_Ga;
		GA::Congruence(wFi_Ga_a, xModA);
		PMV(wFi_Ga_a);

		TDynMV wEic_Fi_Ga;
		//GA::GP(wEic_Fi_Ga, wEic, wFi_Ga);
		//PMV(wEic_Fi_Ga);
		//GA::Congruence(wEic_Fi_Ga, xCongruenceC);
		GA::GP(wEic_Fi_Ga, wEic, wFi_Ga);
		//GA::GP_Congruence(wEic_Fi_Ga, wEic, wFi_Ga, xCongruenceC);
		PMV(wEic_Fi_Ga);

		//TDynMV wX;
		//GA::GP(wX, wE, wEic);
		////GA::GP_Congruence(wX, wE, wEic_Fi_Ga, xCongruenceC);
		//PMV(wX);
		//GA::Congruence(wX, xCongruenceC);
		//PMV(wX);

		//return 0;
		printf("--------------------------------------------------\n\n");

		TDynMV wL, wM;
		GenRanMV(wL, xRandom);
		//wL << TE(1, E(2));	// << TE(1, E(1) | E(2));
		PMV(wL);

		// The message
		GenRanMV(wM, xRandom);
		//wM << TE(1, 0) << TE(1, E(0)) << TE(1, E(1));
		//GA::Congruence(wM, xCongruenceA);
		PMV(wM);

		// ////////////////////////////////////////////////////////////////////////////////
		// Definitions:
		// '*' denotes geometric product.
		// - tModA, tModB: Modulus values.
		// - wF, wG: Random multivectors chosen by Alice.
		// - wGa: wG * tModA. wG multiplied with the smaller modulus value.
		// - wL: Random multivector chosen by Bob.
		// - wM: The message that is to be sent from Alice to Bob.
		// -
		// Conditions to make en- and decryption work:
		// - '==' means that the multivectors have to have the same value component-wise.
		// - tModA < tModB. Still have to work out the exact condition.
		// - wGa mod tModB == wGa. That is, the modulus with tModB does not change the values of wGa.
		// - (wGa * wL) mod tModB == (wGa * wL).
		// - (wE * wF * wM) mod tModB == (wE * wF * wM).
		// - (wFi * wGa) mod tModB != (wFi * wGa).

		//TDynMV wFi_Ga_L;
		//GA::GP(wFi_Ga_L, wFi_Ga, wL);
		//PMV(wFi_Ga_L);
		//GA::Congruence(wFi_Ga_L, xCongruenceC);
		//PMV(wFi_Ga_L);

		//TDynMV wF_Fi_Ga;
		//GA::GP(wF_Fi_Ga, wF, wFi_Ga);
		//GA::Congruence(wF_Fi_Ga, xCongruenceB);
		//PMV(wF_Fi_Ga);

		TDynMV wGa_L;
		GA::GP(wGa_L, wGa, wL);
		PMV(wGa_L);

		GA::Congruence(wGa_L, xModB);
		PMV(wGa_L);

		printf("\n=========================================================\n\n");

		//TDynMV wF_Fi;
		//GA::GP(wF_Fi, wF, wFi);
		//PMV(wF_Fi);

		//GA::Congruence(wF_Fi, xCongruenceC);
		//PMV(wF_Fi);

		//GA::Congruence(wF_Fi, xCongruenceB);
		//PMV(wF_Fi);

		TDynMV wFi_Ga_L;
		GA::GP(wFi_Ga_L, wFi_Ga, wL);
		PMVT("(Fi * Ga)_b * L", wFi_Ga_L);

		GA::Congruence(wFi_Ga_L, xModC);
		PMVT("((Fi * Ga)_b * L)_c", wFi_Ga_L);

		TDynMV wF_Fi_Ga_L;
		GA::GP_Congruence(wF_Fi_Ga_L, wF, wFi_Ga_L, xModB);
		PMVT("(F * ((Fi * Ga)_b * L)_c)_b", wF_Fi_Ga_L);

		GA::Congruence(wF_Fi_Ga_L, xModA);
		PMVT("((F * ((Fi * Ga)_b * L)_c)_b)_a", wF_Fi_Ga_L);

		printf("\n=========================================================\n\n");

		TDynMV wEic_Fi_Ga_L;
		GA::GP_Congruence(wEic_Fi_Ga_L, wEic_Fi_Ga, wL, xModC);
		PMVT("((Ei * (Fi * Ga)_b)_c * L)_c", wEic_Fi_Ga_L);

		TDynMV wE_Eic_Fi_Ga_L;
		GA::GP_Congruence(wE_Eic_Fi_Ga_L, wE, wEic_Fi_Ga_L, xModC);
		PMVT("(E * ((Ei * (Fi * Ga)_b)_c * L)_c)_c", wE_Eic_Fi_Ga_L);

		GA::Congruence(wE_Eic_Fi_Ga_L, xModB);
		PMVT("((E * ((Ei * (Fi * Ga)_b)_c * L)_c)_c)_b", wE_Eic_Fi_Ga_L);

		TDynMV wF_E_Eic_Fi_Ga_L;
		GA::GP_Congruence(wF_E_Eic_Fi_Ga_L, wF, wE_Eic_Fi_Ga_L, xModB);
		PMVT("(F * (E * ((Ei * (Fi * Ga)_b)_c * L)_c)_c)_b", wF_E_Eic_Fi_Ga_L);

		GA::Congruence(wF_E_Eic_Fi_Ga_L, xModA);
		PMVT("((F * (E * ((Ei * (Fi * Ga)_b)_c * L)_c)_c)_b)_a", wF_E_Eic_Fi_Ga_L);

		//return 0;

		printf("\n=========================================================");
		printf("\n=========================================================\n\n");

		TDynMV wQ = wEic_Fi_Ga;
		GA::GP_Congruence(wQ, wEic_Fi_Ga, wL, xModC);
		wQ += wM;
		GA::Congruence(wQ, xModC);
		PMV(wQ);

		TDynMV wQ2;
		GA::GP_Congruence(wQ2, wE, wQ, xModC);
		PMV(wQ2);

		TDynMV wQ2b = wQ2;
		GA::Congruence(wQ2b, xModB);
		PMV(wQ2b);

		TDynMV wQ3b;
		GA::GP_Congruence(wQ3b, wF, wQ2b, xModB);
		PMV(wQ3b);

		TDynMV wQ3;
		GA::GP_Congruence(wQ3, wF, wQ2, xModB);
		PMV(wQ3);

		TDynMV wQ3a = wQ3;
		GA::Congruence(wQ3a, xModA);
		PMV(wQ3a);

		TDynMV wQ4;
		GA::GP_Congruence(wQ4, wFia, wQ3a, xModA);
		PMV(wQ4);

		TDynMV wQ5;
		GA::GP_Congruence(wQ5, wEia, wQ4, xModA);
		PMV(wQ5);

		PMV(wM); 

		TDynMV wTest;
		wTest = wM - wQ5;
		PMV(wTest);
	}
	catch (std::exception& xEx)
	{
		printf("\nEXCEPTION:\n%s\n\n", xEx.what());
		return -1;
	}

	return 0;
}

int main(int, char**) { return Test_Crypt_02(); }
