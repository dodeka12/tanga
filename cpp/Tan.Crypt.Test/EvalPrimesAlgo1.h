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

#include <stdint.h>
#include <inttypes.h>
#include <set>

template<typename T>
void EvalPrimes(std::set<T>& setPrimes, const T& tMaxValue)
{
	uint64_t nTotalIter = 0;

	setPrimes = { 2, 3, 5, 7, 11, 13 };

	for (T tValue = 15; tValue < tMaxValue; tValue += 2)
	{
		bool bIsPrime = true;

		T tDiv = tValue / 2;
		for (T tPrime : setPrimes)
		{
			++nTotalIter;

			if (tPrime > tDiv)
			{
				break;
			}

			if (tValue % tPrime == 0)
			{
				bIsPrime = false;
				break;
			}

			tDiv = tValue / tPrime;
		}

		if (bIsPrime)
		{
			setPrimes.insert(tValue);
		}
	}

	printf("Eval Primes total iterations: %" PRIu64 "\n\n", nTotalIter);
}
