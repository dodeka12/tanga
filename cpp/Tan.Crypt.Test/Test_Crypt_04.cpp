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
// This example extents the NTRU algorithm in GA to implement a message consistency check.
// https://de.wikipedia.org/wiki/NTRUEncrypt
// ///////////////////////////////////////////////////////////////////////////////////////


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

static const unsigned c_uVectorSpaceDim = 10;

typedef int64_t TValue;
typedef Tan::CCongruence_HMod<TValue> TCongruence;
typedef GA::CBlade<c_uVectorSpaceDim, 0>::TBlade TBlade;
typedef TBlade::TBladeId TBladeId;
typedef GA::SValueBlade<TValue, TBlade> TE;
typedef Tan::CMatrix<TValue> TMatrix;
typedef GA::CBladeMask<TBlade> TMask;
typedef GA::CDynamicMultivector<TValue, TBlade> TDynMV;

static const unsigned int c_uAlgDim = TDynMV::AlgebraDimension;
static const unsigned int c_uMaxBladeCnt = c_uAlgDim / 8;

int main(int _argc, char **_argv)
{

	TValue tHalfRange = 1;
	TValue tR         = 2 * tHalfRange + 1;

	TValue tModA = 3; // EvalNextHigherPrime(2 * tHalfRange);	// tHalfRange * tHalfRange * tHalfRange * c_uAlgDim * c_uAlgDim / 64;
	//tModA = EvalNextHigherPrime(2 * tModA + 1);	// *setPrimes.lower_bound(tModA);

	TValue tModB = tModA * 3; //46;
	//TValue tModB = tModA * tHalfRange * tHalfRange * c_uAlgDim;
	//TValue tModB = 2 * tModA * tHalfRange;
	tModB = EvalNextHigherPrime(2 * tModB + 1);	// *setPrimes.lower_bound(tModB);	// EvalNextHigherPrime(tModB);

	TValue tModC = tModB * 3; //46;
	//TValue tModC = (tModB / 2) * tHalfRange * c_uAlgDim;		// EvalNextHigherPrime(tModB * 2 + 1);
	//TValue tModC = 100000;// tModB * tHalfRange;
	//TValue tModC = tModB * tHalfRange * tHalfRange * c_uAlgDim;
	tModC = EvalNextHigherPrime(2 * tModC + 1);	

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
		std::uniform_int_distribution<TValue> xRanDistValue(-tHalfRange, tHalfRange);
		std::uniform_int_distribution<TBladeId> xRanDistBlade(0, c_uAlgDim-1);
		auto xRanValue = std::bind(xRanDistValue, xRandomEngine);
		auto xRanBlade = std::bind(xRanDistBlade, xRandomEngine);


		TDynMV wF, wFib, wFia, wG, wGib, wH, wHic;
		TDynMV wE, wEic, wEib, wEia;

		Tan::GA::EResult eRes, eRes2, eRes3;
		
		// ////////////////////////////////////////////////////////////////////////////////

		printf("\n====================================\nGenerating F, Fia, Fib:\n");
		int iTrial = 0;
		do
		{
			++iTrial;
			if (iTrial > 10)
				return -1;
			printf("\n> Trial %d:\n", iTrial);

			printf(">> Generate F\n");
			GenRanMV(wF, c_uMaxBladeCnt, xRanValue, xRanBlade);
			//PMV(wF);

			printf(">> Calculate inverse Fia...\n");
			eRes2 = Tan::GA::Inverse(wFia, wF, xModA);
			PrintResult(eRes2);
			if (eRes2 != GA::EResult::Success)
				continue;

			printf(">> Calculate inverse Fib...\n");
			eRes = Tan::GA::Inverse(wFib, wF, xModB);
			PrintResult(eRes);
		}
		while (eRes != Tan::GA::EResult::Success || eRes2 != Tan::GA::EResult::Success);

		//PMV(wF);

		wFib.Prune();
		//PMV(wFib);

		wFia.Prune();
		//PMV(wFia);

		printf("\n\n");

		// ////////////////////////////////////////////////////////////////////////////////
		printf("\n====================================\nGenerating E, Eia, Eib, Eic:\n");
		iTrial = 0;
		do
		{
			++iTrial;
			if (iTrial > 10)
				return -1;
			printf("\n> Trial %d:\n", iTrial);

			printf(">> Generate E\n");
			GenRanMV(wE, c_uMaxBladeCnt, xRanValue, xRanBlade);

			printf(">> Calculate inverse Eia...\n");
			eRes3 = Tan::GA::Inverse(wEia, wE, xModA);
			PrintResult(eRes3);
			if (eRes3 != GA::EResult::Success)
				continue;

			printf(">> Calculate inverse Eib...\n");
			eRes2 = Tan::GA::Inverse(wEib, wE, xModB);
			PrintResult(eRes2);
			if (eRes2 != GA::EResult::Success)
				continue;

			printf(">> Calculate inverse Eic...\n");
			eRes = Tan::GA::Inverse(wEic, wE, xModC);
			PrintResult(eRes);
		} while (eRes != Tan::GA::EResult::Success || eRes2 != Tan::GA::EResult::Success || eRes3 != Tan::GA::EResult::Success);

		//PMV(wE);

		wEic.Prune();
		//PMV(wEic);

		wEib.Prune();
		//PMV(wEib);

		wEia.Prune();
		//PMV(wEia);

		printf("\n\n");

		// ////////////////////////////////////////////////////////////////////////////////

		printf("\n====================================\nGenerating G, Gib:\n");
		iTrial = 0;
		do
		{
			++iTrial;
			if (iTrial > 10)
				return -1;
			printf("\n> Trial %d:\n", iTrial);

			printf(">> Generate G\n");
			GenRanMV(wG, c_uMaxBladeCnt, xRanValue, xRanBlade);

			printf(">> Calculate inverse Gib...\n");
			eRes = Tan::GA::Inverse(wGib, wG, xModB);
			PrintResult(eRes);
		} while (eRes != Tan::GA::EResult::Success);
		//PMV(wG);
		//PMV(wGib);

		printf("\n====================================\nGenerating H, Hic:\n");
		iTrial = 0;
		do
		{
			++iTrial;
			if (iTrial > 10)
				return -1;
			printf("\n> Trial %d:\n", iTrial);

			printf(">> Generate H\n");
			GenRanMV(wH, c_uMaxBladeCnt, xRanValue, xRanBlade);

			printf(">> Calculate inverse Hic...\n");
			eRes = Tan::GA::Inverse(wHic, wH, xModC);
			PrintResult(eRes);
		} while (eRes != Tan::GA::EResult::Success);
		//PMV(wH);
		//PMV(wHic);


		// ////////////////////////////////////////////////////////////////////////////////

		TDynMV wFib_G, wEic_H;

		GA::GP_Congruence(wEic_H, wEic, wH, xModC);
		//printf("Public Key 1:\n");
		//PMV(wEic_H);

		GA::GP_Congruence(wFib_G, wFib, wG, xModB);
		//printf("Public Key 2:\n");
		//PMV(wFib_G);

		printf("--------------------------------------------------\n");
		printf("Encoding\n");
		printf("--------------------------------------------------\n\n");

		TDynMV wEic_H_bK, wFib_G_aM2, wK, wKia, wM, wM2, wK_M;

		printf("\n====================================\nGenerating K, Kia:\n");
		iTrial = 0;
		do
		{
			++iTrial;
			if (iTrial > 10)
				return -1;
			printf("\n> Trial %d:\n", iTrial);

			printf(">> Generate K\n");
			GenRanMV(wK, c_uMaxBladeCnt, xRanValue, xRanBlade);

			printf(">> Calculate inverse Kia...\n");
			eRes = Tan::GA::Inverse(wKia, wK, xModA);
			PrintResult(eRes);
		} while (eRes != Tan::GA::EResult::Success);

		//printf("Random K & Kia:\n");
		//PMV(wK);
		//PMV(wKia);

		GenRanMV(wM, c_uMaxBladeCnt, xRanValue, xRanBlade);
		printf("Message M:\n");
		//PMV(wM);

		GA::GP_Congruence(wM2, wM, wM, xModA);
		//PMV(wM2);

		GA::GP_Congruence(wK_M, wK, wM, xModA);
		//PMV(wK_M);

		GA::GP_Congruence(wFib_G_aM2, wFib_G, tModA * wM2, xModB);
		//PMV(wFib_G_aM2);

		GA::GP_Congruence(wEic_H_bK, wEic_H, tModB * wK, xModC);
		//PMV(wEic_H_bK);

		// ///////////////////////////////////////////////////////
		// Tests
		TDynMV wH_bK, wG_aM2, wH_bK_b, wG_aM2_a;

		GA::GP_Congruence(wH_bK, wE, wEic_H_bK, xModC);
		//PMV(wH_bK);

		// wH_bK mod b should be zero
		wH_bK_b = wH_bK;
		GA::Congruence(wH_bK_b, xModB);
		//PMV(wH_bK_b);

		GA::GP_Congruence(wG_aM2, wF, wFib_G_aM2, xModB);
		// wG_aM2 mod a should be zero
		wG_aM2_a = wG_aM2;
		GA::Congruence(wG_aM2_a, xModA);
		//PMV(wG_aM2_a);


		// ///////////////////////////////////////////////////////

		TDynMV wP1, wP2;
		wP1 = wFib_G_aM2 + wK_M;
		//PMV(wP1);
		GA::Congruence(wP1, xModB);
		//PMV(wP1);

		wP2 = wEic_H_bK + wP1;
		//PMV(wP2);
		GA::Congruence(wP2, xModC);
		//PMV(wP2);

		// //////////////////////////////////////////////////////////
		// Introduce change to encoded message to check consistency mechanism.
		//TDynMV wX;
		//wX << TE(1, E(3));
		//PMV(wX);

		//wP2 += wX;
		//GA::Congruence(wP2, xModC);

		// //////////////////////////////////////////////////////////


		printf("\n--------------------------------------------------\n");
		printf("Decoding\n");
		printf("--------------------------------------------------\n\n");

		TDynMV wTest, wQ1, wQ2, wQ3, wQ4, wQ5, wQ6, wQ7, wQ8, wQ8ia, wQ9;

		// //////////////////////////////////////////////////////////
		// First Step Decoding
		GA::GP_Congruence(wQ1, wE, wP2, xModC);
		//PMV(wQ1);

		GA::GP_Congruence(wQ2, wEib, wQ1, xModB);
		wTest = wQ2 - wP1;
		printf("\nDecoding step 1:\n");
		printf("- Q2 == P1: ");
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("error\n");
		}

		// //////////////////////////////////////////////////////////
		// Second step decoding: extract K*M mod a
		GA::GP_Congruence(wQ3, wF, wQ2, xModB);
		//PMV(wQ3);

		GA::GP_Congruence(wQ4, wFia, wQ3, xModA);
		wTest = wQ4 - wK_M;
		printf("\nDecoding step 2:\n");
		printf("- Q4 == K*M: ");
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("error\n");
		}

		// //////////////////////////////////////////////////////////
		// Third step decoding: extract M*M mod a
		wQ5 = wQ2 - wQ4;
		GA::Congruence(wQ5, xModB);
		wTest = wQ5 - wFib_G_aM2;
		printf("\nDecoding step 3:\n");
		printf("- Q5 == Fib * G * M * M * a: ");
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("error\n");
			//PMV(wQ5);
			//PMV(wFib_G_aM2);
		}

		TDynMV wGib_F;
		GA::GP_Congruence(wGib_F, wGib, wF, xModB);
		GA::GP_Congruence(wQ6, wGib_F, wQ5, xModB);
		wTest = wQ6;
		GA::Congruence(wTest, xModA);
		printf("- CHECK > ((Gib * F * Q5) mod b) mod a is zero: ");
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("fail\n");
		}

		wQ6 /= tModA;
		wTest = wM2 - wQ6;
		printf("- Q6 == M*M: ");
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("error\n");
		}

		// //////////////////////////////////////////////////////////
		// Fourth step decoding: extract K

		wQ7 = wP2 - wQ2;
		GA::Congruence(wQ7, xModC);
		wTest = wEic_H_bK - wQ7;
		printf("\nDecoding step 4:\n");
		printf("- Q7 == Eic * H * K * b: ");
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("error\n");
		}

		TDynMV wHic_E;
		GA::GP_Congruence(wHic_E, wHic, wE, xModC);
		GA::GP_Congruence(wQ8, wHic_E, wQ7, xModC);
		wTest = wQ8;
		GA::Congruence(wTest, xModB);
		printf("- CHECK > ((Hic * E * Q7) mod c) mod b is zero: ");
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("fail\n");
		}

		wQ8 /= tModB;
		wTest = wK - wQ8;
		printf("- Q8 == K: ");
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("error\n");
		}

		// //////////////////////////////////////////////////////////
		// Fifth step decoding: extract M
		printf("\nDecoding step 5:\n");
		printf("- CHECK > Inverting Q8: ");
		eRes = Tan::GA::Inverse(wQ8ia, wQ8, xModA);
		if (eRes == GA::EResult::Success)
		{
			printf("ok\n");
		}
		else
		{
			printf("fail\n");
			PrintResult(eRes);
			printf("\n");
		}

		GA::GP_Congruence(wQ9, wQ8ia, wQ4, xModA);
		wTest = wQ9 - wM;
		printf("- Q9 == M: ");
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("error\n");
		}

		// //////////////////////////////////////////////////////////
		// Sixth step decoding: Check Q9*Q9 mod a == Q6
		printf("\nDecoding step 6:\n");
		printf("- CHECK > Q9 * Q9 mod a == Q6: ");
		GA::GP_Congruence(wTest, wQ9, wQ9, xModA);
		wTest -= wQ6;
		GA::Congruence(wTest, xModA);
		if (GA::IsZero(wTest))
		{
			printf("ok\n");
		}
		else
		{
			printf("fail\n");
		}


	}
	catch (std::exception& xEx)
	{
		printf("\nEXCEPTION:\n%s\n\n", xEx.what());
		return -1;
	}

	return 0;
}
