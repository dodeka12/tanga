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

#include "Enum.h"

#include "Tan.Math/Matrix.h"
#include "Tan.Math/Matrix.Algo.GE.h"

#include "MV_Operators.h"
#include "DynamicMultivector.h"
#include "Matrix_MapToBladeMask.h"

namespace Tan
{
	namespace GA
	{
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief
		/// 	Calculates the inverse of a multivector by using a matrix representation and solving for a linear equation system
		/// 	using Gauss Elimination.
		///
		/// \tparam	TMultivector	Type of the multivector.
		/// \tparam	TCongruence	Type of the congruence class. For floating point values this can be the identity for the congruence
		/// 					map and the reciprocal value for the inverse congruence map. For integer values this can be the modulus.
		/// \param [out]	wInv	The inverse multivector.
		/// \param	_wA				The multivector.
		/// \param	xCongruence 	The congruence class.
		///
		/// \return .
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TMultivector, typename TCongruence>
		Tan::GA::EResult Inverse(TMultivector& wInv, const TMultivector& _wA, const TCongruence& xCongruence)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;
			typedef GA::SValueBlade<TValue, TBlade> TE;
			typedef GA::CBladeMask<TBlade> TMask;
			typedef Tan::GA::CDynamicMultivector<TValue, TBlade> TDynMV;
			typedef Tan::CMatrix<TValue> TMatrix;
			typedef Tan::CMatrixAlgoGE<TValue> TMatAlgoGE;

			try
			{
				if (Tan::GA::IsZero(_wA))
				{
					return Tan::GA::EResult::NotInvertible;
				}

				// Create result multivector as scalar 1.
				TDynMV wSc;
				wSc.Zero();
				wSc << TE(TValue(1), 0);

				// Apply congruence operation to all elements of the multivector
				TDynMV wA(_wA);
				if (!Congruence(wA, xCongruence))
				{
					return EResult::InvalidComponentCongruence;
				}

				// /////////////////////////////////////////////
				// Evaluate the multivector mask that we have to
				// use for calculating the inverse.
				// This is the smallest sub-algebra that contains
				// any number of recursive geometric products of elements
				// of the sub-space of wA.
				TMask xMaskA, xMaskB, xResMask;
				GA::EvalBladeMask(xMaskA, wA, true);
				xMaskB = xMaskA;

				// Have to find blade mask that covers the full sub-algebra
				// spanned by wA when multiplied with itself.
				GA::EvalProductBladeMask_GP(xResMask, wA, xMaskB, true, true);
				xMaskA = xMaskB = xResMask;

				// Evaluate the product matrix of wA
				TMatrix matA;
				GA::EvalProductMatrix_GP(matA, wA, xMaskA, xMaskB, xResMask);

				TMatrix matAi;
				TMatrix matRes;
				std::vector<size_t> vecRowIdx;

				// Map the scalar multivector to a compatible matrix representation.
				// This will become the result vector we are solving for.
				GA::ToMatrix(matRes, wSc, xResMask);

				// Perform the Gauss Elimination algorithm.
				Tan::EMatrixResult eRes = TMatAlgoGE::GaussElimination(vecRowIdx, matA, matRes, xCongruence);

				switch (eRes)
				{
				case Tan::EMatrixResult::SingularMatrix:
					return EResult::NotInvertible;

				case Tan::EMatrixResult::InconsistentEquationSystem:
					return EResult::NotInvertible;

				case EMatrixResult::InvalidComponentCongruence:
					return EResult::InvalidComponentCongruence;

				case EMatrixResult::InvalidComponentInverseCongruence:
					return EResult::InvalidComponentInverseCongruence;
				}

				eRes = TMatAlgoGE::TriangularBackSub(vecRowIdx, matA, matRes, xCongruence);

				switch (eRes)
				{
				case EMatrixResult::InvalidComponentCongruence:
					return EResult::InvalidComponentCongruence;

				case EMatrixResult::InvalidComponentInverseCongruence:
					return EResult::InvalidComponentInverseCongruence;
				}

				// Apply the row swaps that were introduced implicitly
				// during the Gauss Elimination.
				TMatAlgoGE::SortRows(matAi, vecRowIdx, matRes);

				// Convert the matrix solution back to a multivector.
				GA::ToMultivector(wInv, matAi, xMaskB);
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error in multivector inverse calculation.", xEx);
			}

			return EResult::Success;
		}
	}	// namespace GA
}	// namespace Tan
