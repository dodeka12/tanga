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


#include "Tan.Math/Congruence.h"

#include "Tan.GA/BasisE3.h"
#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/String.h"
#include "Tan.GA/Algo.h"

int Test_ModMVRing()
{
	using namespace Tan;

	typedef int TValue;
	typedef GA::CBlade<5, 0>::TBlade TBlade;
	typedef GA::SValueBlade<TValue, TBlade> TE;
	typedef GA::CDynamicMultivector<TValue, TBlade> TDynMV;
	typedef CCongruence_HMod<TValue> TCongruence;

	static const unsigned uSc = 0;
	static const unsigned uE1 = (1 << 0);
	static const unsigned uE2 = (1 << 1);
	static const unsigned uE3 = (1 << 2);
	static const unsigned uE4 = (1 << 3);
	static const unsigned uE5 = (1 << 4);

	static const unsigned uPs = (uE1 | uE2 | uE3 | uE4);

	TDynMV wA, wB, wC, wAm, wA2m, wAm2m, wBprev, wBprev2;

	wA.AddValueBlade(1, TBlade(uE1));
	wA.Zero();

	// This multivector with m = 29 generates ring of 707.278 elements.
	// with m = 61 it generates ring of 4.615.278 elements.
	//wA << TE(1, uSc) << TE(1, uE1) << TE(1, uE4) << TE(1, uE3 | uE1) << TE(1, uE1 | uE2) << TE(1, uE3 | uE5);

	wA << TE(1, uSc) << TE(1, uE3) << TE(1, uE1 | uE2);	// << TE(1, uE4) << TE(1, uE3 | uE1) << TE(1, uE1 | uE2) << TE(1, uE3 | uE5);
	printf("wA: %s\n", ToString(wA).c_str());

	int iMod = 3;
	TCongruence xMod(iMod);

	wAm = GetCongruence(wA, xMod);

	printf("wA mod %d: %s\n", iMod, ToString(wAm).c_str());

	GA::GP(wA2m, wA, wA);
	Congruence(wA2m, xMod);
	printf("(wA * wA) mod %d: %s\n", iMod, ToString(wA2m).c_str());

	GA::GP(wAm2m, wAm, wAm);
	Congruence(wAm2m, xMod);
	printf("(wAm * wAm) mod %d: %s\n", iMod, ToString(wAm2m).c_str());

	printf("\n\n============================\n\n");
	wB      = wAm;
	wBprev  = wB;
	wBprev2 = wB;

	int i = 0;
	while (true)
	{
		printf("%03d: %s\n", i, ToString(wB).c_str());

		GA::GP(wC, wB, wA);
		wB = GetCongruence(wC, xMod);

		if (GA::IsZero(wB - wAm))
		{
			printf("\n>>> %03d: %s\n", i - 1, ToString(wBprev2).c_str());
			printf("\n>>> %03d: %s\n", i, ToString(wBprev).c_str());
			printf(">>> Closed Ring.\n");
			GA::GP(wC, wA2m, wBprev2);
			Congruence(wC, xMod);
			printf("%s\n", ToString(wC).c_str());

			break;
		}
		else if (GA::IsZero(wB))
		{
			printf("\n>>> %03d: %s\n", i - 1, ToString(wBprev2).c_str());
			printf("\n>>> %03d: %s\n", i, ToString(wBprev).c_str());
			printf(">>> NULL Ring.\n");
			break;
		}

		wBprev2 = wBprev;
		wBprev  = wB;
		++i;
	}

	//wB = wA * 3.0f;
	//printf("wB: %s\n", ToString(wB).c_str());

	//GA::GP(wB, wA, wA);
	//printf("wB: %s\n", ToString(wC).c_str());

	//GA::Dual(wA, wC);
	//printf("*wC: %s\n", ToString(wA).c_str());

	return 0;
}

int main(int, char**) { return Test_ModMVRing(); }
