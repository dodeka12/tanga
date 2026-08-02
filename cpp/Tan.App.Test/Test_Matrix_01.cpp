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


#include <iostream>

#include "Tan.Math/Matrix.h"
#include "Tan.Math/Matrix.Operators.h"

using namespace Tan;
using namespace std;

typedef double TValue;
typedef Tan::CMatrix<TValue> TMatrix;


void Test_Matrix_01()
{
	TMatrix matA(2, 2, { 1, 2, 3, 4 });
	matA.Resize(3, 4);

	std::cout << "A: " << ToString(matA);

	matA.SetIdentity();
	std::cout << "A: " << ToString(matA);

	matA.Resize(5, 4);
	matA.SetIdentity();
	std::cout << "A: " << ToString(matA);

	matA.Transpose();
	std::cout << "Transpose A: " << ToString(matA);

	TMatrix matB(2, 2, { 1, 2, 3, 4 }), matC(2, 2, { 5, 6, 7, 8 });

	std::cout << ToString(matB);
	std::cout << ToString(matC);

	matA = matB * matC;
	std::cout << "B * C = " << ToString(matA);

	matA = matB * matC.Transpose();
	std::cout << "B * C^T = " << ToString(matA);

	matB.SwapRows(0, 1);
	std::cout << ToString(matB);

	std::cout << "C^T = " << ToString(matC);

	matC.SwapCols(0, 1);
	std::cout << "C^T swap cols 0, 1: " << ToString(matC);

	matC.Negate();
	std::cout << ToString(matC);

	matC.Resize(3, 4);
	std::cout << "C^T to size (3,4): " << ToString(matC);

	matC.Transpose();
	std::cout << "C: " << ToString(matC);

	matA = Square(matC);
	std::cout << "C^T * C = " << ToString(matA);


	///////////////////////////////////////////////////////////////
	// Block Matrix Product
	
	cout << "=====================================================" << endl << endl;


	matA.SetSize(4, 3, { 1, 2, 3, 4, 5, 6,  7, 8, 9, 10, 11, 12 });
	matB.SetSize(2, 6, { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 });
	matB.Transpose();

	cout << "A: " << ToString(matA) << endl;
	cout << "B: " << ToString(matB) << endl;


	MatrixBlockProduct(matC, matA, matB, 2);

	cout << "C: " << ToString(matC) << endl;

	// Test whether it is correct by extracting 
	// the corresponding sub-matrices and taking their product.
	TMatrix matA1, matB1, matC1;

	matA1 = matA.GetSubMatrix(0, 0, 2, 3);
	matB1 = matB.GetSubMatrix(0, 0, 3, 2);

	cout << "A1: " << ToString(matA1) << endl;
	cout << "B1: " << ToString(matB1) << endl;

	matC1 = matA1 * matB1;
	cout << "C1: " << ToString(matC1) << endl;

	TMatrix matA2, matB2, matC2;

	matA2 = matA.GetSubMatrix(2, 0, 2, 3);
	matB2 = matB.GetSubMatrix(3, 0, 3, 2);

	cout << "A2: " << ToString(matA2) << endl;
	cout << "B2: " << ToString(matB2) << endl;

	matC2 = matA2 * matB2;
	cout << "C2: " << ToString(matC2) << endl;

	// Test SetSubMatrix function
	cout << "=====================================================" << endl << endl;

	cout << "A: " << ToString(matA) << endl;

	matA.SetSubMatrix(0, 0, matA2);
	matA.SetSubMatrix(2, 0, matA1);
	cout << "A: " << ToString(matA) << endl;

	matA.SetSubMatrix(1, 1, matC2);
	cout << "A: " << ToString(matA) << endl;

}

int main(int, char**) { Test_Matrix_01(); return 0; }