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


// ///////////////////////////////////////////////////////////////////////////////////////
// This example demonstrates the basic NTRU algorithm in GA
// https://de.wikipedia.org/wiki/NTRUEncrypt
// ///////////////////////////////////////////////////////////////////////////////////////


#include <stdint.h>
#include <inttypes.h>
#include <random>
#include <chrono>

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

int main(int _argc, char **_argv)
{

	TValue tHalfRange = 1;
	TValue tR         = 2 * tHalfRange + 1;

	TValue tModA = EvalNextHigherPrime(tR);	// tHalfRange * tHalfRange * tHalfRange * c_uAlgDim * c_uAlgDim / 64;
	tHalfRange = (tModA - 1) / 2;

	//tModA = EvalNextHigherPrime(2 * tModA + 1);	// *setPrimes.lower_bound(tModA);

	TValue tModB = tModA * tHalfRange * tHalfRange * c_uAlgDim;
	// TValue tModB = tHalfRange * tHalfRange * c_uAlgDim;
	tModB = EvalNextHigherPrime(tModB);	// *setPrimes.lower_bound(tModB);	// EvalNextHigherPrime(tModB);

	printf("Vector space dim: %d\n", c_uVectorSpaceDim);
	printf("Algebra dimension: %d\n", c_uAlgDim);
	printf("Half range: %" PRId64 "\n", tHalfRange);
	printf("tModA: %" PRId64 ", tModB %" PRId64 "\n\n", tModA, tModB);

	TCongruence xModA(tModA);
	TCongruence xModB(tModB);

	//int64_t iValA = 1;
	//int64_t iValB = 1;

	//iValA <<= 31;
	//iValB <<= 32;
	//iValB  *= -1;

	//bool bOverflow = Tan::Intrinsics::ProductWillOverflow(iValA, iValB);
	//int64_t iValC  = iValA * iValB;

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

	try
	{
		std::default_random_engine xRandomEngine;
		auto iSeed = std::chrono::system_clock::now().time_since_epoch().count();
		xRandomEngine.seed(iSeed);

		std::uniform_int_distribution<TValue> xRandomDistribution(-tHalfRange, tHalfRange);
		auto xRandom = std::bind(xRandomDistribution, xRandomEngine);
		TValue tVal = xRandomDistribution(xRandomEngine);


		TDynMV wF, wFib, wFia, wG, wGi;
		TDynMV wE, wEic, wEib, wEia;

		Tan::GA::EResult eRes, eRes2, eRes3;
		
		int iTrial = 0;
		do
		{
			if (iTrial > 10)
				return -1;

			GenRanMV(wF, xRandom);
			// PMV(wF);

			eRes = Tan::GA::Inverse(wFib, wF, xModB);
			PrintResult(eRes);

			eRes2 = Tan::GA::Inverse(wFia, wF, xModA);
			PrintResult(eRes2);

			++iTrial;
		}
		while (eRes != Tan::GA::EResult::Success || eRes2 != Tan::GA::EResult::Success);

		// PMV(wF);


		wFib.Prune();
		// PMV(wFib);

		wFia.Prune();
		// PMV(wFia);

		printf("\n\n");

		GenRanMV(wG, xRandom);
		// PMV(wG);

		TDynMV wFib_G;
		GA::GP_Congruence(wFib_G, wFib, wG, xModB);
		printf("Public Key:\n");
		// PMV(wFib_G);

		printf("--------------------------------------------------\n");
		printf("Encoding\n");
		printf("--------------------------------------------------\n\n");

		TDynMV wQb, wFib_G_aL, wL, wM;

		GenRanMV(wL, xRandom);
		printf("Random MV:\n");
		// PMV(wL);

		GenRanMV(wM, xRandom);
		printf("Message MV:\n");
		PMV(wM);

		GA::GP(wFib_G_aL, wFib_G, tModA * wL);
		wQb = wFib_G_aL + wM;
		GA::Congruence(wQb, xModB);
		printf("Encoded Message:\n");
		PMV(wQb);

		printf("--------------------------------------------------\n");
		printf("Decoding\n");
		printf("--------------------------------------------------\n\n");

		TDynMV wS1, wS2;

		GA::GP_Congruence(wS1, wF, wQb, xModB);
		printf("Decode Step 1:\n");
		// PMV(wS1);

		GA::GP_Congruence(wS2, wFia, wS1, xModA);
		printf("Decode Step 2:\n");
		// PMV(wS2);

		printf("Original message:\n");
		PMV(wM);

		TDynMV wTest;
		wTest = wM - wS2;
		printf("Test equality of decoded message:\n");
		PMV(wTest);
	}
	catch (std::exception& xEx)
	{
		printf("\nEXCEPTION:\n%s\n\n", xEx.what());
		return -1;
	}

	return 0;
}
