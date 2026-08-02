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

#include <stdio.h>
#define _USE_MATH_DEFINES
#include <cmath>
#include <random>

#include "Tan.GA/MultivectorE3.h"
#include "Tan.GA/BasisE3.h"
#include "Tan.GA/MV_Blade_Ops.h"

using namespace Tan;

typedef double TValue;
typedef GA::CBasisE3<TValue> TBasis;
typedef GA::CBlade<3, 0> TBlade;
typedef GA::CMultivector<TValue, TBlade> TMultivector;

static int g_iErrors = 0;

#define TEST_ASSERT(cond, msg) \
	if (!(cond)) \
	{ \
		printf("FAIL: %s (line %d)\n", msg, __LINE__); \
		++g_iErrors; \
		return; \
	}

static TBasis g_basis(TValue(1e-10));

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test InverseBlade with a Euclidean vector
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_InverseBlade()
{
	printf("Test_InverseBlade: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wInv = GA::InverseBlade(wE1);

	TMultivector wChk(TValue(1e-10));
	GA::GP(wChk, wE1, wInv);
	TValue fScalar = GA::Scalar(wChk);
	TEST_ASSERT(std::abs(double(fScalar - TValue(1))) < 1e-8, "Scalar part of e1 * inv(e1) should be 1");

	TMultivector wProjected = GA::GetGradeProjection(wChk, 0);
	TMultivector wDiff(TValue(1e-10));
	GA::Sub(wDiff, wChk, wProjected);
	TValue fMag = GA::Magnitude(wDiff);
	TEST_ASSERT(fMag < TValue(1e-8), "Non-scalar parts of e1 * inv(e1) should be zero");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test InverseBlade with a bivector (e1 ^ e2)
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_InverseBlade_Bivector()
{
	printf("Test_InverseBlade_Bivector: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE2 = g_basis.E2();

	TMultivector wBivec(TValue(1e-10));
	GA::OP(wBivec, wE1, wE2);

	TMultivector wInv = GA::InverseBlade(wBivec);

	TMultivector wChk(TValue(1e-10));
	GA::GP(wChk, wBivec, wInv);

	TValue fScalar = GA::Scalar(wChk);
	TEST_ASSERT(std::abs(double(fScalar - TValue(1))) < 1e-8, "Scalar part of biv * inv(biv) should be 1");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test PseudoInverseBlade with a Euclidean vector (same as inverse in E3)
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_PseudoInverseBlade()
{
	printf("Test_PseudoInverseBlade: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wInv = GA::PseudoInverseBlade(wE1);

	TMultivector wChk(TValue(1e-10));
	GA::GP(wChk, wE1, wInv);

	TValue fScalar = GA::Scalar(wChk);
	TEST_ASSERT(std::abs(double(fScalar - TValue(1))) < 1e-8, "Scalar part of e1 * pseudoInv(e1) should be 1");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test Project: project a vector onto a bivector (e1+e2 projected onto e1^e2)
/// For a full-rank projection with k<l, the result should be the original vector.
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_Project_Vector_onto_Bivector()
{
	printf("Test_Project_Vector_onto_Bivector: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE2 = g_basis.E2();

	// N = e1 ^ e2 (a bivector, grade 2)
	TMultivector wN(TValue(1e-10));
	GA::OP(wN, wE1, wE2);

	// A = e1 + e2 (grade 1 vectors within the subspace of N)
	TMultivector wA = wE1 + wE2;

	TMultivector wProj = GA::Project(wA, wN);

	// proj_{N}(A) should recover A since A lies entirely in the span of N
	TMultivector wDiff(TValue(1e-10));
	GA::Sub(wDiff, wProj, wA);

	TValue fMag = GA::Magnitude(wDiff);
	TEST_ASSERT(fMag < TValue(1e-8), "Project of e1+e2 onto bivector e1^e2 should recover e1+e2");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test Project: project a vector onto a bivector using ProjectUnsafe (verify raw formula)
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_ProjectUnsafe_Vector_onto_Bivector()
{
	printf("Test_ProjectUnsafe_Vector_onto_Bivector: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE2 = g_basis.E2();

	TMultivector wN(TValue(1e-10));
	GA::OP(wN, wE1, wE2);

	TMultivector wProj = GA::ProjectUnsafe(wE1, wN);

	TMultivector wDiff(TValue(1e-10));
	GA::Sub(wDiff, wProj, wE1);

	TValue fMag = GA::Magnitude(wDiff);
	TEST_ASSERT(fMag < TValue(1e-8), "ProjectUnsafe of e1 onto e1^e2 should be e1");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test Reject: reject a vector from a bivector (component orthogonal to the plane)
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_Reject_Vector_From_Bivector()
{
	printf("Test_Reject_Vector_From_Bivector: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE2 = g_basis.E2();
	TMultivector wE3 = g_basis.E3();

	// N = e1 ^ e2
	TMultivector wN(TValue(1e-10));
	GA::OP(wN, wE1, wE2);

	// A = e1 + e2 + e3 — e3 is orthogonal to N
	TMultivector wA = wE1 + wE2 + wE3;

	TMultivector wRej = GA::Reject(wA, wN);

	// The rejection should be the e3 component
	TMultivector wDiff(TValue(1e-10));
	GA::Sub(wDiff, wRej, wE3);

	TValue fMag = GA::Magnitude(wDiff);
	TEST_ASSERT(fMag < TValue(1e-8), "Reject of e1+e2+e3 from e1^e2 should be e3");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test Project + Reject reconstruction
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_Project_Reject_Reconstruction()
{
	printf("Test_Project_Reject_Reconstruction: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE2 = g_basis.E2();
	TMultivector wE3 = g_basis.E3();

	TMultivector wA = wE1 * TValue(2) + wE2 * TValue(3) + wE3 * TValue(4);
	TMultivector wN = wE3;

	TMultivector wProj = GA::Project(wA, wN);
	TMultivector wRej = GA::Reject(wA, wN);

	TMultivector wSum(TValue(1e-10));
	GA::Add(wSum, wProj, wRej);

	TMultivector wDiff(TValue(1e-10));
	GA::Sub(wDiff, wSum, wA);

	TValue fMag = GA::Magnitude(wDiff);
	TEST_ASSERT(fMag < TValue(1e-8), "Proj+Rej should reconstruct A");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test FactorizeBlade: factorize a bivector e1^e2 into two orthogonal vectors
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_FactorizeBlade()
{
	printf("Test_FactorizeBlade: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE2 = g_basis.E2();

	TMultivector wBivec(TValue(1e-10));
	GA::OP(wBivec, wE1, wE2);

	std::vector<TMultivector> vecFactors = GA::FactorizeBlade(wBivec);

	TEST_ASSERT(vecFactors.size() == 2, "Bivector should factor into 2 vectors");

	TMultivector wReconstruct(TValue(1e-10));
	GA::OP(wReconstruct, vecFactors[0], vecFactors[1]);

	TMultivector wIP(TValue(1e-10));
	GA::IP_Reverse(wIP, wReconstruct, false, wBivec, true);

	TValue fScalar = GA::Scalar(wIP);
	TValue fMagOrig = GA::Magnitude(wBivec);
	TValue fMagRecon = GA::Magnitude(wReconstruct);

	TValue fExpected = fMagOrig * fMagRecon;
	TEST_ASSERT(std::abs(double(fScalar - fExpected)) < 1e-8,
			"Factorized vectors should reconstruct original blade (up to scale)");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test Join: join of two vectors that span a plane
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_Join()
{
	printf("Test_Join: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE2 = g_basis.E2();

	TMultivector wJoin = GA::Join(wE1, wE2);

	TMultivector wRej1 = GA::Reject(wE1, wJoin);
	TValue fMagRej1 = GA::Magnitude(wRej1);
	TEST_ASSERT(fMagRej1 < TValue(1e-8), "Rejection of e1 from Join(e1,e2) should be zero");

	TMultivector wRej2 = GA::Reject(wE2, wJoin);
	TValue fMagRej2 = GA::Magnitude(wRej2);
	TEST_ASSERT(fMagRej2 < TValue(1e-8), "Rejection of e2 from Join(e1,e2) should be zero");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test Join: join of disjoint vectors (e1 and e3)
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_Join_Disjoint()
{
	printf("Test_Join_Disjoint: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE3 = g_basis.E3();

	TMultivector wJoin = GA::Join(wE1, wE3);

	TMultivector wRej1 = GA::Reject(wE1, wJoin);
	TValue fMagRej1 = GA::Magnitude(wRej1);
	TEST_ASSERT(fMagRej1 < TValue(1e-8), "Join(e1,e3) should contain e1");

	TMultivector wRej3 = GA::Reject(wE3, wJoin);
	TValue fMagRej3 = GA::Magnitude(wRej3);
	TEST_ASSERT(fMagRej3 < TValue(1e-8), "Join(e1,e3) should contain e3");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test ProjectUnsafe vector overload: project basis vectors onto bivector e1^e2
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_ProjectUnsafe_Vector()
{
	printf("Test_ProjectUnsafe_Vector: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE2 = g_basis.E2();
	TMultivector wE3 = g_basis.E3();

	// N = e1^e2
	TMultivector wN(TValue(1e-10));
	GA::OP(wN, wE1, wE2);

	std::vector<TMultivector> vecInput;
	vecInput.push_back(wE1);
	vecInput.push_back(wE2);
	vecInput.push_back(wE3);

	std::vector<TMultivector> vecProj;
	GA::ProjectUnsafe(vecProj, wN, vecInput);

	TEST_ASSERT(vecProj.size() == 3, "Output should have 3 elements");

	// proj_{e1^e2}(e1) = e1 (e1 lies in the plane)
	TMultivector wDiff(TValue(1e-10));
	GA::Sub(wDiff, vecProj[0], wE1);
	TValue fMag0 = GA::Magnitude(wDiff);
	TEST_ASSERT(fMag0 < TValue(1e-8), "proj_{e1^e2}(e1) should be e1");

	// proj_{e1^e2}(e2) = e2
	GA::Sub(wDiff, vecProj[1], wE2);
	TValue fMag1 = GA::Magnitude(wDiff);
	TEST_ASSERT(fMag1 < TValue(1e-8), "proj_{e1^e2}(e2) should be e2");

	// proj_{e1^e2}(e3) = 0 (e3 is orthogonal to the plane)
	TValue fMag2 = GA::Magnitude(vecProj[2]);
	TEST_ASSERT(fMag2 < TValue(1e-8), "proj_{e1^e2}(e3) should be zero");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test FactorizeVersor: factorize the versor e1 * e2 (a bivector as a simple versor)
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_FactorizeVersor()
{
	printf("Test_FactorizeVersor: ");

	TMultivector wE1 = g_basis.E1();
	TMultivector wE2 = g_basis.E2();

	// V = e1 * e2 (geometric product = e1^e2 since e1 and e2 are orthogonal)
	TMultivector wV(TValue(1e-10));
	GA::GP(wV, wE1, wE2);

	auto xResult = GA::FactorizeVersor(wV);
	TMultivector wScale = xResult.first;
	std::vector<TMultivector> vecFactors = xResult.second;

	// Should have 2 factors for a bivector versor
	TEST_ASSERT(vecFactors.size() >= 2, "Versor e1*e2 should produce at least 2 factors");

	// Reconstruct: factors are extracted from right to left, so reconstruct in REVERSE order
	TMultivector wReconstruct(wScale);
	for (int iIdx = (int)vecFactors.size() - 1; iIdx >= 0; --iIdx)
	{
		TMultivector wTmp(wV.GetValuePrecision());
		GA::GP(wTmp, wReconstruct, vecFactors[(size_t)iIdx]);
		wReconstruct = std::move(wTmp);
	}

	TMultivector wDiff(wV.GetValuePrecision());
	GA::Sub(wDiff, wReconstruct, wV);

	TValue fMag = GA::Magnitude(wDiff);
	TEST_ASSERT(fMag < TValue(1e-8), "Reconstructed versor should equal original V");

	printf("PASS\n");
}

//////////////////////////////////////////////////////////////////////////////////////////////////
/// Test FactorizeVersor in G(5): 4 random vectors, GP them, factorize, reconstruct
//////////////////////////////////////////////////////////////////////////////////////////////////
void Test_FactorizeVersor_G5()
{
	printf("Test_FactorizeVersor_G5: ");

	typedef GA::CBlade<5, 0> TBlade5;
	typedef GA::CMultivector<double, TBlade5> TMV5;

	std::default_random_engine xRng(42);
	std::uniform_real_distribution<double> xDist(-2.0, 2.0);

	TMV5 wV(1e-10);
	wV.SetValueBlade(1.0, TBlade5(0));  // start with scalar 1

	// Create 4 random vectors and multiply them
	for (int i = 0; i < 4; ++i)
	{
		TMV5 wVec(1e-10);
		for (unsigned uBit = 0; uBit < 5; ++uBit)
		{
			double fVal = xDist(xRng);
			if (std::abs(fVal) > 1e-12)
			{
				wVec.AddValueBlade(fVal, TBlade5(1u << uBit));
			}
		}

		TMV5 wTmp(1e-10);
		GA::GP(wTmp, wV, wVec);
		wV = std::move(wTmp);
	}

	auto xResult = GA::FactorizeVersor(wV);
	TMV5 wScale = xResult.first;
	std::vector<TMV5> vecFactors = xResult.second;

	// Reconstruct in reverse order
	TMV5 wReconstruct = wScale;
	for (int iIdx = (int)vecFactors.size() - 1; iIdx >= 0; --iIdx)
	{
		TMV5 wTmp(1e-10);
		GA::GP(wTmp, wReconstruct, vecFactors[(size_t)iIdx]);
		wReconstruct = std::move(wTmp);
	}

	TMV5 wDiff(1e-10);
	GA::Sub(wDiff, wReconstruct, wV);

	double fMag = GA::Magnitude(wDiff);
	TEST_ASSERT(fMag < 1e-4, "G(5) random versor reconstruction should match original");

	printf("PASS\n");
}

int main(int argc, char** argv)
{
	Test_InverseBlade();
	Test_InverseBlade_Bivector();
	Test_PseudoInverseBlade();
	Test_Project_Vector_onto_Bivector();
	Test_ProjectUnsafe_Vector_onto_Bivector();
	Test_Reject_Vector_From_Bivector();
	Test_Project_Reject_Reconstruction();
	Test_FactorizeBlade();
	Test_Join();
	Test_Join_Disjoint();
	Test_ProjectUnsafe_Vector();
	Test_FactorizeVersor();
	Test_FactorizeVersor_G5();

	printf("\n---\n");
	if (g_iErrors == 0)
	{
		printf("All tests passed.\n");
	}
	else
	{
		printf("%d tests failed.\n", g_iErrors);
	}

	return g_iErrors;
}