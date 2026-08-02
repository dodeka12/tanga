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
// Testing of typical magnitude of largest element in product of two MVs.
// ///////////////////////////////////////////////////////////////////////////////////////

#include <stdint.h>
#include <random>
#include <fstream>


#include "Tan.Core/IntrinsicFunctions.h"

#include "Tan.Math/Congruence.h"

#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/String.h"

#include "Tan.GA/Matrix_MapToBladeMask.h"
#include "Tan.GA/Algo.h"


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

#include "Test_Crypt_Func.h"

int Test_Basics_02()
{

	TValue tHalfRange = 1;
	size_t nSampleCount = 10000;

	printf("Vector Space Dim: %d\n", c_uVectorSpaceDim);
	printf("Algebra Dim: %d\n", c_uAlgDim);
	printf("Max Blade Count: %d\n", c_uMaxBladeCnt);
	printf("Component value half range: %ld\n", tHalfRange);

	try
	{
		std::default_random_engine xRandomEngine;
		std::uniform_int_distribution<TValue> xRanDistValue(-tHalfRange, tHalfRange);
		std::uniform_int_distribution<TBladeId> xRanDistBlade(0, c_uAlgDim-1);
		auto xRanValue = std::bind(xRanDistValue, xRandomEngine);
		auto xRanBlade = std::bind(xRanDistBlade, xRandomEngine);

		Tan::GA::EResult eRes, eRes2, eRes3;
		
		// ////////////////////////////////////////////////////////////////////////////////
		TDynMV wA, wB, wC;
		std::map<TValue, size_t> mapMaxValHist, mapValHist;
		mapValHist[0] = 0;

		for (size_t nIdx = 0; nIdx < nSampleCount; ++nIdx)
		{
			if (c_uMaxBladeCnt == c_uAlgDim)
			{
				GenRanMV(wA, xRanValue);
				GenRanMV(wB, xRanValue);
			}
			else
			{
				GenRanMV(wA, c_uMaxBladeCnt, xRanValue, xRanBlade);
				GenRanMV(wB, c_uMaxBladeCnt, xRanValue, xRanBlade);
			}

			GA::GP(wC, wA, wB);
			wC.Prune();
			//mapValHist[0] += c_uAlgDim - wC.GetBladeCount();

			TValue tMaxVal = 0;
			wC.ForEachBlade([&tMaxVal, &mapValHist](TValue tVal, TBlade tBlade)
			{
				//auto itEl = mapValHist.find(tVal);
				//if (itEl == mapValHist.end())
				//{
				//	mapValHist[tVal] = 1;
				//}
				//else
				//{
				//	++(itEl->second);
				//}

				TValue tAbsVal = abs(tVal);
				tMaxVal = (tMaxVal > tAbsVal ? tMaxVal : tAbsVal);
			});

			auto itEl = mapMaxValHist.find(tMaxVal);
			if (itEl == mapMaxValHist.end())
			{
				mapMaxValHist[tMaxVal] = 1;
			}
			else
			{
				++(itEl->second);
			}
		}

		//printf("Value Histogram:\n\n");
		//for( auto xD : mapValHist)
		//{
		//	printf("%3d; %5d\n", xD.first, xD.second);
		//}
		//printf("\n\n");

		std::string sDir = "";
		std::string sName = "GA_Dist_VD" + std::to_string(c_uVectorSpaceDim) 
			+ "_HR" + std::to_string(tHalfRange)
			+ "_BC" + std::to_string(c_uMaxBladeCnt)
			+ "_SC" + std::to_string(nSampleCount);
		std::string sFilename = sDir + sName + ".csv";
		std::ofstream xFile(sFilename);

		xFile << "Vec Dim;" << c_uVectorSpaceDim << '\n';
		xFile << "Algo Dim;" << c_uAlgDim << '\n';
		xFile << "Half Range;" << tHalfRange << '\n';
		xFile << "Max Blade Count;" << c_uMaxBladeCnt << '\n';
		xFile << "Sample Size;" << nSampleCount << '\n';

		xFile << "\nMaximum Value Histogram\n" << "Value;Count\n";

		printf("Maximum Value Histogram:\n\n");
		for (auto xD : mapMaxValHist)
		{
			printf("%3ld -> %5zu\n", xD.first, xD.second);
			xFile << xD.first << ";" << xD.second << "\n";
		}
		printf("\n");

	}
	catch (std::exception& xEx)
	{
		printf("\nEXCEPTION:\n%s\n\n", xEx.what());
		return -1;
	}

	return 0;
}

int main(int, char**) { return Test_Basics_02(); }
