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

#define _USE_MATH_DEFINES
#include <math.h>
#include <iostream>
#include <string>

#include "Tan.Core/IntrinsicFunctions.h"

#include "InlineMath.h"
#include "Matrix.h"
#include "Matrix.Enum.h"


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// namespace: Tan
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
namespace Tan
{
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// \brief Functions for Gauss Ellimination on Matrix.
	///
	/// \author Perwass
	/// 
	///
	/// \tparam T Generic type parameter.
	///
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

	template<typename T>
	class CMatrixAlgoGE
	{
	public:

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief
		/// 	Perform Gauss elimination on matrix \a mA in-place. If successful the algorithm returns with \a mA in upper triangular form with respect to the \a
		/// 	vecRowIdx. \a vecRowIdx records any swapping of rows of \a mA. The rows are not actually swapped in \a mA, only the row indices are in \a vecRowIdx.
		/// 	All operations performed on \a mA are also performed on \a mB. The result of this function can be used to calculate the determinant of \a mA, the
		/// 	inverse of \a mA and to solve for \a mX in the equation \a mA * \a mX = \a mB by backsubstitution.
		///
		/// \author Perwass
		/// 
		///
		/// \tparam	TCongruence
		/// 	Type of the congruence class. For floating point values this can be the identity for the congruence map and the reciprocal value for the inverse
		/// 	congruence map. For integer values this can be the modulus.
		/// \param [out]	vecRowIdx The list of row indices that give the row order to make \a mA upper triangular.
		/// \param [in,out]	mA		  The matrix that is to be made upper triangular.
		/// \param [in,out]	mB		  The matrix or vector that is modified according to \a mA.
		/// \param	xCongruence		  The modulus function or an identity function.
		///
		/// \return True if the matrix can be brought into upper triangular form, false if the matrix is singular.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TCongruence>
		static EMatrixResult GaussElimination(std::vector<size_t>& vecRowIdx, Tan::CMatrix<T>& mA, Tan::CMatrix<T>& mB, const TCongruence& xCongruence)
		{
			// Ensure that a possible transposition of matA is represented in memory,
			// since we are not working with iterators here.
			mA.ApplyToMemory();
			mB.ApplyToMemory();

			size_t nRowCntA = mA.GetRowCount();
			size_t nColCntA = mA.GetColCount();
			size_t nColCntB = mB.GetColCount();

			if (nRowCntA != mB.GetRowCount())
			{
				TAN_THROW_RT("Row dimensions of the two matrices given differ.");
			}

			// Initialize the row index list
			vecRowIdx.resize(nRowCntA);

			for (size_t nRowIdx = 0; nRowIdx < nRowCntA; ++nRowIdx)
			{
				vecRowIdx[nRowIdx] = nRowIdx;
			}

			// Loop over all rows of the largest square matrix contained in mA
			size_t nMaxCnt = std::min(nRowCntA, nColCntA);
			for (size_t nMajRowIdx = 0; nMajRowIdx < nMaxCnt; ++nMajRowIdx)
			{
				// find the pivot row, i.e. the row with the largest absolute
				// value in column nMajRowIdx.
				T tMaxRowVal      = 0;
				size_t nMaxRowIdx = nMajRowIdx;
				for (size_t nRowIdx = nMajRowIdx; nRowIdx < nRowCntA; ++nRowIdx)
				{
					T tAbsVal = abs(mA(vecRowIdx[nRowIdx], nMajRowIdx));
					if (tAbsVal > tMaxRowVal)
					{
						tMaxRowVal = tAbsVal;
						nMaxRowIdx = nRowIdx;
					}
				}

				// If the maximum value in column nMajRowIdx is zero
				// the matrix is singular.
				if (tMaxRowVal == 0)
				{
					return EMatrixResult::SingularMatrix;
				}

				// Swap row indices of row nMajRowIdx with the row
				// containing the pivot element.
				if (nMaxRowIdx != nMajRowIdx)
				{
					size_t nIdx = vecRowIdx[nMajRowIdx];
					vecRowIdx[nMajRowIdx] = vecRowIdx[nMaxRowIdx];
					vecRowIdx[nMaxRowIdx] = nIdx;
				}

				// Loop over all rows below pivot row.
				// Add a scaled version of the pivot row to all rows below pivot row
				// to make the column entries in column nMajRowIdx zero.
				for (size_t nRowIdx = nMajRowIdx + 1; nRowIdx < nRowCntA; ++nRowIdx)
				{
					size_t _nRowIdx    = vecRowIdx[nRowIdx];
					size_t _nMajRowIdx = vecRowIdx[nMajRowIdx];

					T* pMajRowData = &mA(_nMajRowIdx, nMajRowIdx);
					T* pRowData    = &mA(_nRowIdx, nMajRowIdx);

					// Calculate factor that pivot row is multiplied with
					// before it is subtracted from the current row nRowIdx.
					T tInv;
					if (!xCongruence.InvMap(tInv, *pMajRowData))
					{
						return EMatrixResult::InvalidComponentInverseCongruence;
					}

					TAN_TEST_PROD_OVERFLOW(*pRowData, tInv);
					
					T tFac;
					xCongruence.Map(tFac, (*pRowData) * tInv);

					// Loop over all columns in current row
					for (size_t nColIdx = nMajRowIdx + 1; nColIdx < nColCntA; ++nColIdx)
					{
						// Multiply and subtract pivot row column from current row column.
						T& tVal = *(++pRowData);

						TAN_TEST_PROD_OVERFLOW(*(pMajRowData + 1), tFac);

						if (!xCongruence.Map(tVal, tVal - (*(++pMajRowData)) * tFac))
						{
							return EMatrixResult::InvalidComponentCongruence;
						}
					}

					// Same operation over all columns of matrix mB.
					pMajRowData = &mB(_nMajRowIdx, 0);
					pRowData    = &mB(_nRowIdx, 0);

					// Loop over all columns in current row in mB
					for (size_t nColIdx = 0; nColIdx < nColCntB; ++nColIdx, ++pRowData, ++pMajRowData)
					{
						TAN_TEST_PROD_OVERFLOW(*pMajRowData, tFac);

						// Multiply and subtract pivot row column from current row column.
						if (!xCongruence.Map((*pRowData), (*pRowData) - (*pMajRowData) * tFac))
						{
							return EMatrixResult::InvalidComponentCongruence;
						}
					}

					mA(_nRowIdx, nMajRowIdx) = T(0);
				}
			}

			// If there are more rows than columns, we have to
			// check that all rows in mB below the largest square matrix
			// are zero. Otherwise, the equation system is inconsistent.
			if (nRowCntA > nColCntA)
			{
				for (size_t nRowIdx = nMaxCnt; nRowIdx < nRowCntA; ++nRowIdx)
				{
					size_t _nRowIdx = vecRowIdx[nRowIdx];

					// Loop over all columns in mB
					T* pRowData = &mB(_nRowIdx, 0);

					for (size_t nColIdx = 0; nColIdx < nColCntB; ++nColIdx, ++pRowData)
					{
						if (*pRowData != T(0))
						{
							return EMatrixResult::InconsistentEquationSystem;
						}
					}
				}
			}

			return EMatrixResult::Success;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief
		/// 	Triangular back-substitution. Expects that \a mA is an upper triangular matrix, for example created by the _GaussElimination() function. \a vecRowIdx
		/// 	gives the order of the rows of \a mA, so that \a mA becomes upper triangular. The matrix \a mB is a matrix from the equation \a mA * \a mX = \a mB,
		/// 	that matches the upper triangular \a mA matrix. The function return mX and mB.
		///
		/// \author Perwass
		/// 
		///
		/// \tparam	TCongruence
		/// 	Type of the congruence class. For floating point values this can be the identity for the congruence map and the reciprocal value for the inverse
		/// 	congruence map. For integer values this can be the modulus.
		/// \param	vecRowIdx   Zero-based index of the vector row.
		/// \param	mA		    The m a.
		/// \param [in,out]	mB  The m b.
		/// \param	xCongruence The congruence.
		///
		/// \return True if it succeeds, false if it fails.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TCongruence>
		static EMatrixResult TriangularBackSub(const std::vector<size_t>& vecRowIdx, Tan::CMatrix<T>& mA, Tan::CMatrix<T>& mB, const TCongruence& xCongruence)
		{
			// Ensure that a possible transposition of matA is represented in memory,
			// since we are not working with iterators here.
			mA.ApplyToMemory();
			mB.ApplyToMemory();

			// Backsubstitution to find vector mX such that mA * mX == mB.
			size_t nRowCntA = mA.GetRowCount();
			size_t nColCntA = mA.GetColCount();
			size_t nColCntB = mB.GetColCount();

			// This back-substitution algorithm only works if the
			// column dimension is smaller or equal to the row dimension.
			if (nColCntA > nRowCntA)
			{
				TAN_THROW_RT("Column dimension higher than row dimension.");
			}

			// Find the dimension of the largest square matrix contained in mA.
			size_t nMaxCnt = std::min(nRowCntA, nColCntA);

			// Back-substitute starting from the bottom row of the largest square
			// matrix in mA.
			for (size_t nInvMajRowIdx = 0; nInvMajRowIdx < nMaxCnt; ++nInvMajRowIdx)
			{
				size_t nMajRowIdx  = nMaxCnt - nInvMajRowIdx - 1;
				size_t _nMajRowIdx = vecRowIdx[nMajRowIdx];

				// Find the inverse of the element in mA at the
				// current diagonal position.
				T tInv;
				if (!xCongruence.InvMap(tInv, mA(_nMajRowIdx, nMajRowIdx)))
				{
					return EMatrixResult::InvalidComponentInverseCongruence;
				}

				// Get pointer to matrix row in mB.
				T* pDataB = &mB(_nMajRowIdx, 0);

				// Divide major row of mB by diagonal element in major row of mA
				for (size_t nColIdxB = 0; nColIdxB < nColCntB; ++nColIdxB, ++pDataB)
				{
					TAN_TEST_PROD_OVERFLOW(*pDataB, tInv);

					if (!xCongruence.Map(*pDataB, (*pDataB) * tInv))
					{
						return EMatrixResult::InvalidComponentCongruence;
					}
				}

				// Loop over all rows above major row, and add a scaled version of
				// the major row to these rows, such that the elements in column
				// nMajRowIdx become zero.
				for (size_t nInvRowIdx = nInvMajRowIdx + 1; nInvRowIdx < nMaxCnt; ++nInvRowIdx)
				{
					size_t nRowIdx  = nMaxCnt - nInvRowIdx - 1;
					size_t _nRowIdx = vecRowIdx[nRowIdx];

					// Find the factor in mA to multiply the major
					// row in mB with.
					// We do not have to explicitly add elements to mA,
					// since mA will implicitly become the identity matrix
					// when we are finished.
					T tFac = mA(_nRowIdx, nMajRowIdx);

					// Get Row Pointers
					T* pDataB    = &mB(_nRowIdx, 0);
					T* pDataBMaj = &mB(_nMajRowIdx, 0);

					// Loop over all columns of mB in current row
					for (size_t nColIdxB = 0; nColIdxB < nColCntB; ++nColIdxB, ++pDataB, ++pDataBMaj)
					{
						TAN_TEST_PROD_OVERFLOW(*pDataBMaj, tFac);

						if (!xCongruence.Map(*pDataB, (*pDataB) - (*pDataBMaj) * tFac))
						{
							return EMatrixResult::InvalidComponentCongruence;
						}
					}
				}
			}

			return EMatrixResult::Success;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Sort the rows of \a mA according to the row index list \a vecRowIdx.
		///
		/// \author Perwass
		/// 
		///
		/// \param [out]	mB The row sorted matrix mA.
		/// \param	vecRowIdx  The row index list.
		/// \param	mA		   The matrix to be sorted.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		static void SortRows(Tan::CMatrix<T>& mB, const std::vector<size_t>& vecRowIdx, Tan::CMatrix<T>& mA)
		{
			// Ensure that a possible transposition of matA is represented in memory,
			// since we are not working with iterators here.
			mA.ApplyToMemory();

			size_t nRowCnt = mA.GetRowCount();
			size_t nColCnt = mA.GetColCount();

			if (vecRowIdx.size() != nRowCnt)
			{
				TAN_THROW_RT("Row index list size is not equal to matrix row count.");
			}

			mB.Resize(nRowCnt, nColCnt);
			if (nColCnt == 1)
			{
				T* pDataB = mB.GetDataPtr();

				for (size_t nRowIdx = 0; nRowIdx < nRowCnt; ++nRowIdx, ++pDataB)
				{
					*pDataB = mA(vecRowIdx[nRowIdx], 0);
				}
			}
			else
			{
				T* pDataB       = mB.GetDataPtr();
				size_t nRowSize = nColCnt * sizeof(T);

				for (size_t nRowIdx = 0; nRowIdx < nRowCnt; ++nRowIdx, pDataB += nColCnt)
				{
					size_t _nRowIdx = vecRowIdx[nRowIdx];

					memcpy(pDataB, &mA(_nRowIdx, 0), nRowSize);
				}
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief The inverse of the given matrix using Gauss Elimination and back-substitution.
		///
		/// \author Perwass
		/// 
		///
		/// \tparam	TCongruence
		/// 	Type of the congruence class. For floating point values this can be the identity for the congruence map and the reciprocal value for the inverse
		/// 	congruence map. For integer values this can be the modulus.
		/// \param [in,out]	matInv The matrix inverse.
		/// \param	_matA		   The matrix a.
		/// \param	xCongruence    The congruence.
		///
		/// \return A Tan::EMatrixResult.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TCongruence>
		static Tan::EMatrixResult Inverse(Tan::CMatrix<T>& matInv, const Tan::CMatrix<T>& _matA, const TCongruence& xCongruence)
		{
			try
			{
				// We need a copy of _matA since the Gauss elimination is done in-place.
				Tan::CMatrix<T> matA(_matA);

				// Ensure that a possible transposition of matA is represented in memory,
				// since we are not working with iterators here.
				matA.ApplyToMemory();


				size_t nRowCntA = matA.GetRowCount();
				size_t nColCntA = matA.GetColCount();

				if ((nRowCntA == 0) || (nColCntA == 0))
				{
					TAN_THROW_RT("The matrix is empty.");
				}

				// Sanity checks on matA
				if (nRowCntA != nColCntA)
				{
					TAN_THROW_RT("Matrix is not square.");
				}

				Tan::EMatrixResult eRes;
				std::vector<size_t> vecRowIdx;

				// The result matrix
				Tan::CMatrix<T> matRes;

				// We want to solve for the identity matrix
				matRes.Resize(nRowCntA, nRowCntA);
				matRes.SetIdentity();

				// Perform the Gauss Elimination.
				// This makes matA upper triangular and modifies matRes accordingly.
				eRes = GaussElimination(vecRowIdx, matA, matRes, xCongruence);
				if (eRes != Tan::EMatrixResult::Success)
				{
					return eRes;
				}

				// The back-substitution now makes matA implicitly to an identity matrix
				// and makes matRes to the inverse of the original matA in the process.
				eRes = TriangularBackSub(vecRowIdx, matA, matRes, xCongruence);
				if (eRes != Tan::EMatrixResult::Success)
				{
					return eRes;
				}

				// If the rows of matA werde implicitly swapped, we now have to apply
				// the swaps to the matRes matrix to obtain the actual inverse matrix.
				SortRows(matInv, vecRowIdx, matRes);

				return Tan::EMatrixResult::Success;
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error inverting matrix", xEx);
			}
		}


	};
}
