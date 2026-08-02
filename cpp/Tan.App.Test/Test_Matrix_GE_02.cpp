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
#include <iostream>

#include "Tan.Math/Congruence.h"

#include "Tan.Math/Matrix.h"
#include "Tan.Math/Matrix.Operators.h"
#include "Tan.Math/Matrix.Algo.GE.h"

using namespace Tan;
using namespace std;

typedef int64_t TValue;
typedef Tan::CMatrix<TValue> TMatrix;
typedef Tan::CMatrixAlgoGE<TValue> TAlgoGE;
typedef Tan::CCongruence_HMod<TValue> TCongruence;

void Test_Matrix_GE_02()
{
	try
	{
		TValue tModA = 7;
		TCongruence xModA(tModA);
		TMatrix matA(2, 2, { 1, 2, 3, 4 });
		TMatrix matAi;

		cout << "A: " << ToString(matA) << endl;

		EMatrixResult eRes = TAlgoGE::Inverse(matAi, matA, xModA);
		cout << "Inverse result: " << ToString(eRes) << endl << endl;

		if (eRes == EMatrixResult::Success)
		{
			cout << "A^-1: " << ToString(matAi) << endl;

			TMatrix matR = matA * matAi;
			cout << "A * A^-1 = " << ToString(matR) << endl;

			matR.CompCongruence(xModA);
			cout << "A * A^-1 mod " << to_string(tModA) << " = " << ToString(matR) << endl;
		}
	}
	catch (std::exception& xEx)
	{
		cout << "EXCEPTION: " << endl;
		cout << xEx.what() << endl;
	}
}

int main(int, char**) { Test_Matrix_GE_02(); return 0; }
