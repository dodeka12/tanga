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

#include <cstdio>
#include <string>
#include <iostream>

#include "Matrix.h"
#include "Tan.Core/ValueFormatString.h"

namespace Tan
{
	////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>	Addition operator. </summary>
	///
	/// <remarks>	Perwass, . </remarks>
	///
	/// <typeparam name="TValue">	Type of the value. </typeparam>
	/// <param name="matA">	The matrix a. </param>
	/// <param name="matB">	The matrix b. </param>
	///
	/// <returns>	The result of the operation. </returns>
	////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	CMatrix<TValue> operator+(const CMatrix<TValue>& matA, const CMatrix<TValue>& matB)
	{
		TAN_ASSERT(matA.IsEqualSize(matB));
		
		CMatrix<TValue> matC(matA);
		matC += matB;

		return matC;
	}

	////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>	Subtraction operator. </summary>
	///
	/// <remarks>	Perwass, . </remarks>
	///
	/// <typeparam name="TValue">	Type of the value. </typeparam>
	/// <param name="matLeftOp"> 	The matrix left operation. </param>
	/// <param name="matRightOp">	The matrix right operation. </param>
	///
	/// <returns>	The result of the operation. </returns>
	////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	CMatrix<TValue> operator-(const CMatrix<TValue>& matA, const CMatrix<TValue>& matB)
	{
		TAN_ASSERT(matA.IsEqualSize(matB));

		CMatrix<TValue> matC(matA);
		matC -= matB;

		return matC;
	}

	////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>	Multiplication operator. </summary>
	///
	/// <remarks>	Perwass, . </remarks>
	///
	/// <typeparam name="TValue">	Type of the value. </typeparam>
	/// <param name="matA">	The matrix a. </param>
	/// <param name="matB">	The matrix b. </param>
	///
	/// <returns>	The result of the operation. </returns>
	////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	CMatrix<TValue> operator*(const CMatrix<TValue>& matA, const CMatrix<TValue>& matB)
	{
		TAN_ASSERT(matA.GetColCount() == matB.GetRowCount());

		CMatrix<TValue> matC(matA.GetRowCount(), matB.GetColCount());

		typename CMatrix<TValue>::TIterator itRowC = matC.BeginRows();

		matA.ForEachRow([&](typename CMatrix<TValue>::TConstIterator& itRowA)
		{
			typename CMatrix<TValue>::TIterator itRowColC = matC.BeginCols(itRowC);
			matB.ForEachCol([&](typename CMatrix<TValue>::TConstIterator& itColB)
			{
				typename CMatrix<TValue>::TConstIterator itRowColA = matA.ConstBeginCols(itRowA);
				typename CMatrix<TValue>::TConstIterator itEndRowColA = itRowColA + matA.GetColCount();
				typename CMatrix<TValue>::TConstIterator itColRowB = matB.ConstBeginRows(itColB);

				TValue tSum = TValue(0);
				for (; itRowColA != itEndRowColA; ++itRowColA, ++itColRowB)
				{
					//std::cout << "A: " << std::to_string(*itRowColA);
					//std::cout << ", B: " << std::to_string(*itColRowB) << std::endl;
					tSum += *itRowColA * *itColRowB;
				}
				//std::cout << std::endl;
				*itRowColC = tSum;
				++itRowColC;
			});

			++itRowC;
		});

		return matC;
	}

	////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>	Multiplication operator. </summary>
	///
	/// <remarks>	Perwass, . </remarks>
	///
	/// <typeparam name="TValue">	Type of the value. </typeparam>
	/// <param name="matA">   	The matrix left operation. </param>
	/// <param name="tScalar">	The scalar. </param>
	///
	/// <returns>	The result of the operation. </returns>
	////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	CMatrix<TValue> operator*(const CMatrix<TValue>& matA, const TValue& tScalar)
	{
		CMatrix<TValue> matB(matA);
		matB *= tScalar;
		return matB;
	}

	////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>	Division operator. </summary>
	///
	/// <remarks>	Perwass, . </remarks>
	///
	/// <typeparam name="TValue">	Type of the value. </typeparam>
	/// <param name="matA">   	The matrix a. </param>
	/// <param name="tScalar">	The scalar. </param>
	///
	/// <returns>	The result of the operation. </returns>
	////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	CMatrix<TValue> operator/(const CMatrix<TValue>& matA, const TValue& tScalar)
	{
		CMatrix<TValue> matB(matA);
		matB /= tScalar;
		return matB;
	}


	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	Calculates a block-wise matrix product.
	/// 	Suppose matrix A has dimensions (N*p, q) and matrix B has dimensions (N*q, r), then this function calculates
	/// 	the matrix products of block A[(i*p,0)->(i*p + p-1, q-1)] * B[(i*q, 0)->(i*q + q-1, r-1)].
	/// 	The resultant matrix C has dimensions (N*p, r).
	/// </summary>
	///
	/// <typeparam name="typename TValue">	Type of the typename t value. </typeparam>
	/// <param name="matC">	   	[in,out] The mat c. </param>
	/// <param name="matA">	   	The mat a. </param>
	/// <param name="matB">	   	The mat b. </param>
	/// <param name="uColCntA">	The col count a. </param>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<typename TValue>
	void MatrixBlockProduct(CMatrix<TValue>& matC, const CMatrix<TValue>& matA, const CMatrix<TValue>& matB, const size_t uBlockCount)
	{
		typedef CMatrix<TValue> TMatrix;

		try
		{
			const size_t uRowCntA = matA.GetRowCount();
			const size_t uColCntA = matA.GetColCount();
			const size_t uRowCntB = matB.GetRowCount();
			const size_t uColCntB = matB.GetColCount();

			if (uRowCntA % uBlockCount != 0)
			{
				TAN_THROW_RT("Row count of matrix A is incompatible with block count.");
			}

			if (uRowCntB % uBlockCount != 0)
			{
				TAN_THROW_RT("Row count of matrix B is incompatible with block count.");
			}

			const size_t uBlockRowCntB = uRowCntB / uBlockCount;

			if (uBlockRowCntB != uColCntA)
			{
				TAN_THROW_RT("Block row count of matrix B is incompatible to column count of matrix A");
			}

			const size_t uRowCntC = uRowCntA;
			const size_t uColCntC = uColCntB;
			const size_t uBlockRowCntA = uRowCntA / uBlockCount;
			matC.SetSize(uRowCntC, uColCntC);

			typename TMatrix::TConstIterator itRowBlockA = matA.ConstBeginRowBlock(uBlockRowCntA);
			typename TMatrix::TConstIterator itRowBlockB = matB.ConstBeginRowBlock(uBlockRowCntB);
			typename TMatrix::TIterator itRowBlockC = matC.BeginRowBlock(uBlockRowCntA);
			typename TMatrix::TConstIterator itRowBlockEndA = itRowBlockA + uBlockCount;

			// Loop over row blocks
			for (; itRowBlockA != itRowBlockEndA; ++itRowBlockA, ++itRowBlockB, ++itRowBlockC)
			{
				typename TMatrix::TIterator itRowC = matC.BeginRows(itRowBlockC);

				matA.ForEachRow(itRowBlockA, uBlockRowCntA, [&](typename TMatrix::TConstIterator& itRowA)
				{
					typename TMatrix::TIterator itRowColC = matC.BeginCols(itRowC);
					matB.ForEachCol(itRowBlockB, matB.GetColCount(), [&](typename TMatrix::TConstIterator& itColB)
					{
						typename TMatrix::TConstIterator itRowColA = matA.ConstBeginCols(itRowA);
						typename TMatrix::TConstIterator itEndRowColA = itRowColA + matA.GetColCount();
						typename TMatrix::TConstIterator itColRowB = matB.ConstBeginRows(itColB);

						TValue tSum = TValue(0);
						for (; itRowColA != itEndRowColA; ++itRowColA, ++itColRowB)
						{
							//std::cout << "A: " << std::to_string(*itRowColA);
							//std::cout << ", B: " << std::to_string(*itColRowB) << std::endl;
							tSum += *itRowColA * *itColRowB;
						}
						//std::cout << std::endl;
						*itRowColC = tSum;
						++itRowColC;
					});

					++itRowC;
				});
			}
		}
		catch (std::exception& xEx)
		{
			TAN_RETHROW("Error calculating matrix block product", xEx);
		}
	}

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// \brief This function calculates A^T * A, where A is the given matrix and A^T denotes the transpose.
	///
	/// \author Perwass
	/// 
	///
	/// \tparam	TValue Generic type parameter.
	/// \param	matA The other matrix.
	///
	/// \return A CMatrix<TValue>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	CMatrix<TValue> Square(const CMatrix<TValue>& matA)
	{
		const size_t nLeftRowCnt = matA.GetColCount();
		const size_t nLeftColCnt = matA.GetRowCount();
		const size_t nRightColCnt = matA.GetColCount();

		CMatrix<TValue> matC(nLeftRowCnt, nRightColCnt);

		typename CMatrix<TValue>::TIterator itRowC = matC.BeginRows();

		matA.ForEachCol([&](typename CMatrix<TValue>::TConstIterator& itRowA)
		{
			typename CMatrix<TValue>::TIterator itRowColC = matC.BeginCols(itRowC);
			matA.ForEachCol([&](typename CMatrix<TValue>::TConstIterator& itColB)
			{
				typename CMatrix<TValue>::TConstIterator itRowColA = matA.ConstBeginRows(itRowA);
				typename CMatrix<TValue>::TConstIterator itEndRowColA = itRowColA + matA.GetRowCount();
				typename CMatrix<TValue>::TConstIterator itColRowB = matA.ConstBeginRows(itColB);

				TValue tSum = TValue(0);
				for (; itRowColA != itEndRowColA; ++itRowColA, ++itColRowB)
				{
					//std::cout << "A: " << std::to_string(*itRowColA);
					//std::cout << ", B: " << std::to_string(*itColRowB) << std::endl;
					tSum += *itRowColA * *itColRowB;
				}
				//std::cout << std::endl;
				*itRowColC = tSum;
				++itRowColC;
			});

			++itRowC;
		});

		return matC;
	}




	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	Convert this object into a string representation.
	/// </summary>
	///
	/// <typeparam name="typename TValue">	Type of the typename t. </typeparam>
	/// <param name="matA">	   	The mat a. </param>
	/// <param name="pcFormat">	The PC format. </param>
	///
	/// <returns>	The given data converted to a std::string. </returns>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<typename TValue>
	std::string ToString(const CMatrix<TValue>& matA, const char* pcFormat = nullptr)
	{
		if (matA.IsEmpty())
		{
			return std::string("||");
		}

		std::string sText = "";
		std::string sFormat;
		char pcValue[30];

		if (pcFormat == nullptr)
		{
			sFormat = Tan::ValueFormatString<TValue>();
			pcFormat = sFormat.c_str();
		}

		const unsigned uRowCnt = (unsigned)matA.GetRowCount();
		const unsigned uColCnt = (unsigned)matA.GetColCount();

		snprintf(pcValue, sizeof(pcValue), "[%u, %u]\n", uRowCnt, uColCnt);
		sText += pcValue;

		matA.ForEachRow([&](typename CMatrix<TValue>::TConstIterator& itRow)
		{
			typename CMatrix<TValue>::TConstIterator itRowCol = matA.ConstBeginCols(itRow);
			typename CMatrix<TValue>::TConstIterator itRowColEnd = itRowCol + matA.GetColCount();

			for (; itRowCol != itRowColEnd; ++itRowCol)
			{
				snprintf(pcValue, sizeof(pcValue), pcFormat, *itRowCol);
				sText += " | ";
				sText += pcValue;
			}

			sText += " |\n";
		});

		return sText;
	}


} // namespace Tan
