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



#include <cstdint>
#include <string>
#include <iostream>

#include "Tan.Core/Array.h"

typedef int64_t TValue;
typedef Tan::CArray<TValue> TArray;

void Test_Array()
{
	using namespace std;

	TArray aX({ 2, 2, 2 }, { 1, 2, 3, 4, 5, 6, 7, 8 });
	TArray aY;

	aX.Resize({ 3, 3, 3 });

	TArray::TIterator itEl0 = aX.Begin(0);
	TArray::TIterator itEnd0 = aX.End(0);

	for (; itEl0 != itEnd0; ++itEl0)
	{
		TArray::TIterator itEl1 = aX.Begin(itEl0, 1);
		TArray::TIterator itEnd1 = itEl1 + aX.GetSize(1);

		for (; itEl1 != itEnd1; ++itEl1)
		{
			TArray::TIterator itEl2 = aX.Begin(itEl1, 2);
			TArray::TIterator itEnd2 = itEl2 + aX.GetSize(2);

			for (; itEl2 != itEnd2; ++itEl2)
			{
				cout << to_string(*itEl2) << ", ";
			}

			cout << std::endl;
		}
		cout << std::endl << std::endl;
	}
	cout << std::endl;

}

int main(int, char**) { Test_Array(); return 0; }