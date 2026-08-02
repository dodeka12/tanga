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
#include <algorithm>
#include <iostream>
#include <vector>

#include "Tan.Core/Defines.h"
#include "Tan.Core/Array.h"

#include "ValuePrecision.h"
//#define TAN_MATH_RANGE_CHECK

namespace Tan
{
	template<class _TValue>
	class CMatrix : public CArray<_TValue>, public CValuePrecision<_TValue>
	{
	public:

		typedef _TValue TValue;
		typedef CMatrix<TValue> TThis;
		typedef CArray<TValue> TArray;
		typedef typename TArray::TIterator TIterator;
		typedef typename TArray::TConstIterator TConstIterator;
		typedef typename TArray::TIdx TIdx;
		typedef CValuePrecision<_TValue> TValPrec;

	protected:
		TIdx m_nRowDimIdx;
		TIdx m_nColDimIdx;

	public:
		CMatrix()
		{
			m_nRowDimIdx = 0;
			m_nColDimIdx = 1;
		}

		CMatrix(TValue fPrec) : CValuePrecision<TValue>(fPrec)
		{
			TValPrec::SetValuePrecision(fPrec);

			m_nRowDimIdx = 0;
			m_nColDimIdx = 1;
		}

		CMatrix(TThis&& matA) = default;
		TThis& operator= (TThis&& matA) = default;

		CMatrix(const TThis& matA) = default;
		TThis& operator= (const TThis& matA) = default;


		CMatrix(size_t nRowCnt, size_t nColCnt) : CArray<TValue>({nRowCnt, nColCnt})
		{
			m_nRowDimIdx = 0;
			m_nColDimIdx = 1;
		}

		CMatrix(size_t nRowCnt, size_t nColCnt, const std::initializer_list<TValue>& xData)
			: CArray<TValue>({nRowCnt, nColCnt}, xData)
		{
			m_nRowDimIdx = 0;
			m_nColDimIdx = 1;
		}

		// ////////////////////////////////////////////////////////////
		// ////////////////////////////////////////////////////////////
		void Resize(size_t nRowCnt, size_t nColCnt)
		{
			try
			{
				std::vector<size_t> lSize;

				if (IsTranspose())
				{
					lSize = { nColCnt, nRowCnt };
				}
				else
				{
					lSize = { nRowCnt, nColCnt };
				}

				if (TArray::GetTotalSize() == 0)
				{
					TArray::SetSize(lSize);
				}
				else
				{
					TArray::Resize(lSize);
				}
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error resizing matrix:", xEx);
			}
		}

		// ////////////////////////////////////////////////////////////
		void SetSize(size_t nRowCnt, size_t nColCnt)
		{
			try
			{
				std::vector<size_t> lSize;

				if (IsTranspose())
				{
					lSize = { nColCnt, nRowCnt };
				}
				else
				{
					lSize = { nRowCnt, nColCnt };
				}

				TArray::SetSize(lSize);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error resizing matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Set Size of matrix and data.
		///
		/// \author Perwass
		/// 
		///
		/// \param	nRowCnt Number of rows.
		/// \param	nColCnt Number of cols.
		/// \param	xData   The data.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		void SetSize(size_t nRowCnt, size_t nColCnt, const std::initializer_list<TValue>& xData)
		{
			try
			{
				SetSize(nRowCnt, nColCnt);
				SetData(xData);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error resizing matrix and setting data", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Sets data of matrix
		///
		/// \author Perwass
		/// 
		///
		/// \param	xData The data.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		void SetData(const std::initializer_list<TValue>& xData)
		{
			try
			{
				TArray::SetData(xData);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error setting matrix data", xEx);
			}
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets row count. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	The row count. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		size_t GetRowCount() const
		{
			if (TArray::IsEmpty())
			{
				return 0;
			}

			return TArray::GetSize(m_nRowDimIdx);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets col count. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	The col count. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		size_t GetColCount() const
		{
			if (TArray::IsEmpty())
			{
				return 0;
			}

			return TArray::GetSize(m_nColDimIdx);
		}



		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Access matrix component. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="nRow">	The row. </param>
		/// <param name="nCol">	The col. </param>
		///
		/// <returns>	The result of the operation. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		const TValue& operator()(const size_t nRow, const size_t nCol) const
		{
			TAN_ASSERT(nRow < GetRowCount() && nCol < GetColCount());

			if (IsTranspose())
			{
				return *(TArray::GetDataPtr() + (nCol * GetRowCount() + nRow));
			}
			else
			{
				return *(TArray::GetDataPtr() + (nRow * GetColCount() + nCol));
			}
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Access matrix component. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="nRow">	The row. </param>
		/// <param name="nCol">	The col. </param>
		///
		/// <returns>	The result of the operation. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TValue& operator()(const size_t nRow, const size_t nCol)
		{
			TAN_ASSERT(nRow < GetRowCount() && nCol < GetColCount());

			if (IsTranspose())
			{
				return *(TArray::GetDataPtr() + (nCol * GetRowCount() + nRow));
			}
			else
			{
				return *(TArray::GetDataPtr() + (nRow * GetColCount() + nCol));
			}
		}

		// /////////////////////////////////////////////////////////////////////////////////////
		// Iterating functions
		template<typename FuncOp>
		void ForEachComp(FuncOp xFunc)
		{
			// The data is row-ordered in memory, so we need to take the 
			// iterator that walks along a row.
			TIterator itEl = TArray::Begin(1);
			TIterator itEnd = itEl + TArray::GetTotalSize();

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(*itEl);
			}
		}

		template<typename FuncOp>
		void ForEachComp(FuncOp xFunc) const
		{
			TConstIterator itEl = TArray::ConstBegin(1);
			TConstIterator itEnd = itEl + TArray::GetTotalSize();

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(*itEl);
			}
		}


		template<typename FuncOp>
		bool ForEachCompTest(FuncOp xFunc)
		{
			TIterator itEl = TArray::Begin(1);
			TIterator itEnd = itEl + TArray::GetTotalSize();

			for (; itEl != itEnd; ++itEl)
			{
				if (!xFunc(*itEl))
				{
					return false;
				}
			}

			return true;
		}

		template<typename FuncOp>
		bool ForEachCompTest(FuncOp xFunc) const
		{
			TConstIterator itEl = TArray::ConstBegin(1);
			TConstIterator itEnd = itEl + TArray::GetTotalSize();

			for (; itEl != itEnd; ++itEl)
			{
				if (!xFunc(*itEl))
				{
					return false;
				}
			}

			return true;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief For each component pair of this matrix and the given matrix. The function iterates row-wise over both matrices and calls
		/// 	   the given function for each component pair at the same (row, col) position in both matrices.
		///
		/// \author Perwass
		/// 
		///
		/// \tparam	TValueB Type of the value b.
		/// \tparam	FuncOp  Type of the function operation.
		/// \param	matB  The matrix b.
		/// \param	xFunc The function.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TValueB, typename FuncOp>
		void ForEachCompPair(const CMatrix<TValueB>& matB, FuncOp xFunc)
		{
			if (!IsEqualSize(matB))
			{
				TAN_THROW_RT("Matrices are not of same size");
			}

			typedef CMatrix<TValueB> TThisB;

			TIterator itRowA = BeginRows();
			TIterator itRowEndA = itRowA + GetRowCount();

			typename TThisB::TConstIterator itRowB = ConstBeginRows();

			for (; itRowA != itRowEndA; ++itRowA, ++itRowB)
			{
				TIterator itRowColA = BeginCols(itRowA);
				TIterator itRowColEndA = itRowColA + GetColCount();

				typename TThisB::TConstIterator itRowColB = ConstBeginCols(itRowB);
				for (; itRowColA != itRowColEndA; ++itRowColA, ++itRowColB)
				{
					xFunc(*itRowColA, *itRowColB);
				}
			}
		}

		template<typename TValueB, typename FuncOp>
		void ForEachCompPair(const CMatrix<TValueB>& matB, FuncOp xFunc) const
		{
			if (!IsEqualSize(matB))
			{
				TAN_THROW_RT("Matrices are not of same size");
			}

			typedef CMatrix<TValueB> TThisB;

			TConstIterator itRowA = ConstBeginRows();
			TConstIterator itRowEndA = itRowA + GetRowCount();

			typename TThisB::TConstIterator itRowB = ConstBeginRows();

			for (; itRowA != itRowEndA; ++itRowA, ++itRowB)
			{
				TConstIterator itRowColA = ConstBeginCols(itRowA);
				TConstIterator itRowColEndA = itRowColA + GetColCount();

				typename TThisB::TConstIterator itRowColB = ConstBeginCols(itRowB);
				for (; itRowColA != itRowColEndA; ++itRowColA, ++itRowColB)
				{
					xFunc(*itRowColA, *itRowColB);
				}
			}
		}

		template<typename TValueB, typename FuncOp>
		bool ForEachCompPairTest(const CMatrix<TValueB>& matB, FuncOp xFunc)
		{
			if (!IsEqualSize(matB))
			{
				TAN_THROW_RT("Matrices are not of same size");
			}

			typedef CMatrix<TValueB> TThisB;

			TIterator itRowA = BeginRows();
			TIterator itRowEndA = itRowA + GetRowCount();

			typename TThisB::TConstIterator itRowB = ConstBeginRows();

			for (; itRowA != itRowEndA; ++itRowA, ++itRowB)
			{
				TIterator itRowColA = BeginCols(itRowA);
				TIterator itRowColEndA = itRowColA + GetColCount();

				typename TThisB::TConstIterator itRowColB = ConstBeginCols(itRowB);
				for (; itRowColA != itRowColEndA; ++itRowColA, ++itRowColB)
				{
					if (!xFunc(*itRowColA, *itRowColB))
					{
						return false;
					}
				}
			}

			return true;
		}

		template<typename TValueB, typename FuncOp>
		bool ForEachCompPairTest(const CMatrix<TValueB>& matB, FuncOp xFunc) const
		{
			if (!IsEqualSize(matB))
			{
				TAN_THROW_RT("Matrices are not of same size");
			}

			typedef CMatrix<TValueB> TThisB;

			TConstIterator itRowA = ConstBeginRows();
			TConstIterator itRowEndA = itRowA + GetRowCount();

			typename TThisB::TConstIterator itRowB = ConstBeginRows();

			for (; itRowA != itRowEndA; ++itRowA, ++itRowB)
			{
				TConstIterator itRowColA = ConstBeginCols(itRowA);
				TConstIterator itRowColEndA = itRowColA + GetColCount();

				typename TThisB::TConstIterator itRowColB = ConstBeginCols(itRowB);
				for (; itRowColA != itRowColEndA; ++itRowColA, ++itRowColB)
				{
					if (!xFunc(*itRowColA, *itRowColB))
					{
						return false;
					}
				}
			}

			return true;
		}


		template<typename FuncOp>
		void ForEachRow(FuncOp xFunc)
		{
			TIterator itEl = BeginRows();
			TIterator itEnd = itEl + GetRowCount();

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(itEl);
			}
		}

		template<typename FuncOp>
		void ForEachCol(FuncOp xFunc)
		{
			TIterator itEl = BeginCols();
			TIterator itEnd = itEl + GetColCount();

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(itEl);
			}
		}

		template<typename FuncOp>
		void ForEachRow(FuncOp xFunc) const
		{
			TConstIterator itEl = ConstBeginRows();
			TConstIterator itEnd = itEl + GetRowCount();

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(itEl);
			}
		}

		template<typename FuncOp>
		void ForEachCol(FuncOp xFunc) const
		{
			TConstIterator itEl = ConstBeginCols();
			TConstIterator itEnd = itEl + GetColCount();

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(itEl);
			}
		}


		template<typename FuncOp>
		void ForEachRow(TIterator& itStart, TIdx nRowCnt, FuncOp xFunc)
		{
			TIterator itEl = BeginRows(itStart);
			TIterator itEnd = itEl + nRowCnt;

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(itEl);
			}
		}

		template<typename FuncOp>
		void ForEachCol(TIterator& itStart, TIdx nColCnt, FuncOp xFunc)
		{
			TIterator itEl = BeginCols(itStart);
			TIterator itEnd = itEl + nColCnt;

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(itEl);
			}
		}

		template<typename FuncOp>
		void ForEachRow(TConstIterator& itStart, TIdx nRowCnt, FuncOp xFunc) const
		{
			TConstIterator itEl = ConstBeginRows(itStart);
			TConstIterator itEnd = itEl + nRowCnt;

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(itEl);
			}
		}

		template<typename FuncOp>
		void ForEachCol(TConstIterator& itStart, TIdx nColCnt, FuncOp xFunc) const
		{
			TConstIterator itEl = ConstBeginCols(itStart);
			TConstIterator itEnd = itEl + nColCnt;

			for (; itEl != itEnd; ++itEl)
			{
				xFunc(itEl);
			}
		}


		TIterator BeginRows()
		{
			return TArray::Begin(m_nRowDimIdx);
		}

		TIterator BeginCols()
		{
			return TArray::Begin(m_nColDimIdx);
		}

		TConstIterator ConstBeginRows() const
		{
			return TArray::ConstBegin(m_nRowDimIdx);
		}

		TConstIterator ConstBeginCols() const
		{
			return TArray::ConstBegin(m_nColDimIdx);
		}


		TIterator BeginRows(TIterator& itEl)
		{
			return TArray::Begin(itEl, m_nRowDimIdx);
		}

		TIterator BeginCols(TIterator& itEl)
		{
			return TArray::Begin(itEl, m_nColDimIdx);
		}

		TConstIterator ConstBeginRows(TConstIterator& itEl) const
		{
			return TArray::ConstBegin(itEl, m_nRowDimIdx);
		}

		TConstIterator ConstBeginCols(TConstIterator& itEl) const
		{
			return TArray::ConstBegin(itEl, m_nColDimIdx);
		}


		TIterator BeginRows(TIdx nRowIdx, TIdx nColIdx)
		{
			return TArray::Begin(_GetIndexVector(nRowIdx, nColIdx), m_nRowDimIdx);
		}

		TIterator BeginCols(TIdx nRowIdx, TIdx nColIdx)
		{
			return TArray::Begin(_GetIndexVector(nRowIdx, nColIdx), m_nColDimIdx);
		}

		TConstIterator ConstBeginRows(TIdx nRowIdx, TIdx nColIdx) const
		{
			return TArray::ConstBegin(_GetIndexVector(nRowIdx, nColIdx), m_nRowDimIdx);
		}

		TConstIterator ConstBeginCols(TIdx nRowIdx, TIdx nColIdx) const
		{
			return TArray::ConstBegin(_GetIndexVector(nRowIdx, nColIdx), m_nColDimIdx);
		}

		TIterator BeginRowBlock(TIdx nRowCnt)
		{
			if (IsTranspose())
			{
				return TIterator(TArray::GetDataPtr(), nRowCnt);
			}
			else
			{
				return TIterator(TArray::GetDataPtr(), nRowCnt * GetColCount());
			}
		}

		TIterator BeginColBlock(TIdx nColCnt)
		{
			if (IsTranspose())
			{
				return TIterator(TArray::GetDataPtr(), nColCnt * GetRowCount());
			}
			else
			{
				return TIterator(TArray::GetDataPtr(), nColCnt);
			}
		}

		TConstIterator ConstBeginRowBlock(TIdx nRowCnt) const
		{
			if (IsTranspose())
			{
				return TConstIterator(TArray::GetDataPtr(), nRowCnt);
			}
			else
			{
				return TConstIterator(TArray::GetDataPtr(), nRowCnt * GetColCount());
			}
		}

		TConstIterator ConstBeginColBlock(TIdx nColCnt) const
		{
			if (IsTranspose())
			{
				return TConstIterator(TArray::GetDataPtr(), nColCnt * GetRowCount());
			}
			else
			{
				return TConstIterator(TArray::GetDataPtr(), nColCnt);
			}
		}


		TIterator BeginDiagonal()
		{
			return TIterator(TArray::GetDataPtr(), TArray::GetSize(1)+1);
		}

		TIterator EndDiagonal()
		{
			return TIterator(TArray::GetDataPtr() + (TArray::GetSize(1) + 1) * std::min(GetRowCount(), GetColCount()), TArray::GetSize(1) + 1);
		}

		TConstIterator ConstBeginDiagonal() const
		{
			return TConstIterator(TArray::GetDataPtr(), TArray::GetSize(1) + 1);
		}

		TConstIterator ConstEndDiagonal() const
		{
			return TConstIterator(TArray::GetDataPtr(), (TArray::GetSize(1) + 1) * std::min(GetRowCount(), GetColCount()));
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Sets matrix to identity matrix, if non-quadratic, then upper left is identity.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		void SetIdentity()
		{
			Zero();
			TIterator itEl = BeginDiagonal();
			TIterator itEnd = EndDiagonal();

			for (; itEl != itEnd; ++itEl)
			{
				*itEl = TValue(1);
			}
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets the trace of the matrix. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	A TValue. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TValue Trace() const
		{
			TConstIterator itEl = ConstBeginDiagonal();
			TConstIterator itEnd = ConstEndDiagonal();

			TValue tTrace = TValue(0);
			for (; itEl != itEnd; ++itEl)
			{
				tTrace += *itEl;
			}

			return tTrace;
		}

		// /////////////////////////////////////////////////////////////////////////////////////
		// Set all components to zero
		void Zero()
		{
			TAN_ASSERT(TArray::GetDataPtr() != nullptr);

			if (TArray::GetTotalByteSize() == 0)
			{
				return;
			}

			memset((void*) TArray::GetDataPtr(), 0, TArray::GetTotalByteSize());
		}



		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Negates this object. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		void Negate()
		{
			ForEachComp([](TValue &tValue)
			{
				tValue = -tValue;
			});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Query if this matrix is transposed with respect to its memory representation. When applying the Transpose() function to the matrix
		/// 	   only the m_nRowDimIdx and m_nColDimIdx variables swap their values. When accessing the matrix components via the
		/// 	   iterators the matrix is effectively transposed without changing its representation in memory.
		///
		/// \author Perwass
		/// 
		///
		/// \return true if transpose, false if not.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		bool IsTranspose() const
		{
			return m_nRowDimIdx == 1;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Query if this object is zero. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	true if zero, false if not. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		bool IsZero() const
		{
			ForEachCompTest([this](const TValue& tValue)
			{
				if (!CValuePrecision<TValue>::IsZero(tValue))
				{
					return false;
				}

				return true;
			});

			return true;
		}


		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Query if all components of matrix are numbers.
		///
		/// \author Perwass
		/// 
		///
		/// \tparam	TValue Type of the value.
		///
		/// \return true if number, false if not.
		///
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TValue>
		bool IsNumber() const
		{
			return ForEachCompTest([](const TValue& tValue)
			{
				if (!IsNumber(tValue))
				{
					return false;
				}
				return true;

			});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Query if all components of the matrix are finite numbers.
		///
		/// \author Perwass
		/// 
		///
		/// \tparam	TValue Type of the value.
		///
		/// \return true if finite number, false if not.
		///
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TValue>
		bool IsFiniteNumber() const
		{
			return ForEachCompTest([](const TValue& tValue)
			{
				if (!IsFiniteNumber(tValue))
				{
					return false;
				}
				return true;

			});
		}



		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Query if 'matB' is equal size. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="matB">	The matrix b. </param>
		///
		/// <returns>	true if equal size, false if not. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		bool IsEqualSize(const TThis& matB) const
		{
			return (GetRowCount() == matB.GetRowCount() && GetColCount() == matB.GetColCount());
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Magnitude squared. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	A TValue. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TValue MagnitudeSquared() const
		{
			TValue tMagSq = 0;

			ForEachComp([&tMagSq](const TValue &tValue)
			{
				tMagSq += tValue * tValue;
			});

			return tMagSq;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Performs transpose of this matrix in memory and returns result.
		///
		/// \author Perwass
		/// 
		///
		/// \return The transpose.
		///
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		CMatrix<TValue> GetTranspose() const
		{
			CMatrix<TValue> matB(GetColCount(), GetRowCount());

			TIterator itColB = matB.BeginCols();
			ForEachRow([&](TConstIterator& itRowA)
			{
				TIterator itColRowB = matB.BeginRows(itColB);
				TConstIterator itRowColA = ConstBeginCols(itRowA);
				TConstIterator itRowColEndA = itRowColA + GetColCount();

				for (; itRowColA != itRowColEndA; ++itRowColA, ++itColRowB)
				{
					*itColRowB = *itRowColA;
				}

				++itColB;
			});

			return matB;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Transposes this matrix. This function only indicates that the matrix is transposed but does not change its
		/// 	   representation in memory. Use the function ApplyToMemory() to actually represent transposition in memory.
		///
		/// \author Perwass
		/// 
		///
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		TThis& Transpose()
		{
			if (IsTranspose())
			{
				m_nRowDimIdx = 0;
				m_nColDimIdx = 1;
			}
			else
			{
				m_nRowDimIdx = 1;
				m_nColDimIdx = 0;
			}

			return *this;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Applies a transposition of this matrix that is only represented by iterators to memory.
		///
		/// \author Perwass
		/// 
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		void ApplyToMemory()
		{
			if (!IsTranspose())
			{
				return;
			}

			// transpose back
			Transpose();

			// Now get the transpose in memory
			*this = GetTranspose();
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Set all vecValues A(ij) smaller than fPrec*max( abs(A(ij)) ) to zero. 100*fPrec gives
		/// 	relative threshold in percent.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="tPrec">	The prec. </param>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		void TinyToZero(TValue tPrec = TValue(0))
		{
			TAN_ASSERT(TArray::GetTotalSize() > 0);

			if (tPrec <= TValue(0))
			{
				tPrec = Tan::CValuePrecision<TValue>::DefaultPrecision();
			}

			TValue tBig = TValue(0);
			TValue tH;

			ForEachComp([&](TValue& tValue)
			{
				if ((tH = _Abs(tValue)) > tBig)
				{
					tBig = tH;
				}
			});

			tBig *= tPrec;
			ForEachComp([&](TValue& tValue)
			{
				if (_Abs(tValue) <= tBig)
				{
					tValue = TValue(0);
				}
			});

		}


		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Invert components of matrix. Zero vecValues are set to inf. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="tInf"> 	The inf. </param>
		/// <param name="tPrec">	The prec. </param>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		CMatrix<TValue>& CompInvert(TValue tInf, TValue tPrec = TValue(0))
		{
			TAN_ASSERT(TArray::GetTotalSize() > 0);

			if (tPrec <= TValue(0))
			{
				tPrec = CValuePrecision<TValue>::GetValuePrecision();
			}

			ForEachComp([&](TValue& tValue)
			{
				if (!_IsZero(tValue, tPrec))
				{
					tValue = TValue(1) / tValue;
				}
				else
				{
					tValue = tInf;
				}

			});

			return *this;
		}


		// /////////////////////////////////////////////////////////////////////////////////////
		// returns the componentwise product

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Component multiply. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="matB">	The matrix b. </param>
		///
		/// <returns>	A CMatrix&lt;TValue&gt; </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TThis& CompMultiply(const TThis& matB) 
		{
			if (!IsEqualSize(matB))
			{
				TAN_THROW_RT("Matrix dimensions do not agree");
			}

			ForEachCompPair(matB, [](TValue& tValA, const TValue& tValB)
			{
				tValA *= tValB;
			});

			return *this;
		}


		//////////////////////////// Arithmetic ////////////////////

		TThis& operator+=(const TThis& matB)
		{
			if (!IsEqualSize(matB))
			{
				TAN_THROW_RT("Matrix dimensions do not agree");
			}

			ForEachCompPair(matB, [](TValue& tValA, const TValue& tValB)
			{
				tValA += tValB;
			});

			return *this;
		}

		TThis& operator+=(const TValue& tScalar)
		{
			ForEachComp([&tScalar](TValue& tValue)
			{
				tValue += tScalar;
			});

			return *this;
		}


		TThis& operator-=(const CMatrix<TValue>& matB)
		{
			if (!IsEqualSize(matB))
			{
				TAN_THROW_RT("Matrix dimensions do not agree");
			}

			ForEachCompPair(matB, [](TValue& tValA, const TValue& tValB)
			{
				tValA -= tValB;
			});

			return *this;
		}

		TThis& operator-=(const TValue& tScalar)
		{
			ForEachComp([&tScalar](TValue& tValue)
			{
				tValue -= tScalar;
			});

			return *this;
		}


		TThis& operator*=(const TValue& tScalar)
		{
			ForEachComp([&tScalar](TValue& tValue)
			{
				tValue *= tScalar;
			});

			return *this;
		}


		TThis& operator/=(const TValue& tScalar)
		{
			ForEachComp([&tScalar](TValue& tValue)
			{
				tValue /= tScalar;
			});

			return *this;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Transpose of matrix. Indicates that the matrix is transposed and the returns a copy.
		///
		/// \author Perwass
		/// 
		///
		/// \return The result of the operation.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		TThis operator~()
		{
			TThis matA(*this);

			matA.Transpose();
			return matA;
		}

		///////////////////////////////////////////////////////////////////

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Applies the given congruence map to each component.
		///
		/// \author Perwass
		/// 
		///
		/// \tparam	TCongruence Type of the congruence.
		/// \param	xCongruence The congruence.
		///
		/// \return Reference to this.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TCongruence>
		TThis& CompCongruence(const TCongruence& xCongruence)
		{
			ForEachComp([&xCongruence](TValue& tValue)
			{
				TValue _tValue = tValue;
				if (!xCongruence.Map(tValue, _tValue))
				{
					TAN_THROW_RT("Error applying congruence map to matrix component");
				}
			});

			return *this;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Attempts to apply the given inverse congruence map to each component.
		///
		/// \author Perwass
		/// 
		///
		/// \tparam	TCongruence Type of the congruence.
		/// \param	xCongruence The congruence.
		///
		/// \return true if it succeeds, false if it fails.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename TCongruence>
		bool TryCompInverseCongruence(const TCongruence& xCongruence)
		{
			return ForEachCompTest([&xCongruence](TValue& tValue)
			{
				TValue _tValue = tValue;
				if (!xCongruence.InvMap(tValue, _tValue))
				{
					return false;
				}

				return true;
			});
		}


		///////////////////////////////////////////////////////////////////
		template<class TValueB>
		CMatrix<TValue>& CastMemberType(const CMatrix<TValueB>& matB)
		{
			try
			{
				if (matB.GetTotalSize() == 0)
				{
					TArray::Reset();
				}
				else
				{
					SetSize(matB.GetRowCount(), matB.GetColCount());
					ForEachCompPair(matB, [](TValue& tValA, const TValueB& tValB)
					{
						tValA = TValue(tValB);
					});
				}
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error casting matrix component types", xEx);
			}

			return *this;
		}



		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Makes a diagonal matrix out of a single row or single column matrix. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TThis& VectorToDiagonal()
		{
			try
			{
				TAN_ASSERT(TArray::GetTotalSize() > 0);

				TIdx nRowCnt = GetRowCount();
				TIdx nColCnt = GetColCount();

				if ((nRowCnt > 1) && (nColCnt > 1))
				{
					TAN_THROW_RT("Invalid matrix size");
				}

				CMatrix<TValue> matB(*this);

				TIdx nSize = (nRowCnt == 1 ? nColCnt : nRowCnt);
				SetSize(nSize, nSize);
				Zero();

				TIterator itEl = BeginDiagonal();
				TIterator itEnd = EndDiagonal();

				TIterator itElB = (nRowCnt == 1 ? matB.BeginCols() : matB.BeginRows());
				for (; itEl != itEnd; ++itEl, ++itElB)
				{
					*itEl = *itElB;
				}
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error transforming vector to diagonal matrix", xEx);
			}

			return *this;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Makes a column vector out of the diagonal. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TThis& DiagonalToVector()
		{
			TAN_ASSERT(TArray::GetTotalSize() > 0);

			TIdx nRowCnt = GetRowCount();
			TIdx nColCnt = GetColCount();

			TIdx nSize = std::min(nRowCnt, nColCnt);

			TThis matB(nSize, 1);

			TIterator itEl = BeginDiagonal();
			TIterator itEnd = EndDiagonal();

			TIterator itElB = matB.BeginRows();

			for (; itEl != itEnd; ++itEl, ++itElB)
			{
				*itEl = *itElB;
			}

			*this = matB;

			return *this;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Swap cols. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="nColA">	The col a. </param>
		/// <param name="nColB">	The col b. </param>
		///
		/// <returns>	A TThis&amp; </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TThis& SwapCols(TIdx nColA, TIdx nColB)
		{
			if (nColA == nColB)
			{
				return *this;
			}

			TAN_ASSERT(nColA < GetColCount());
			TAN_ASSERT(nColB < GetColCount());

			std::vector<TIdx> lSizeA, lSizeB;

			if (IsTranspose())
			{
				lSizeA = { nColA, 0 };
				lSizeB = { nColB, 0 };
			}
			else
			{
				lSizeA = { 0, nColA };
				lSizeB = { 0, nColB };
			}

			TIterator itColA = this->Begin(lSizeA, m_nRowDimIdx);
			TIterator itColB = this->Begin(lSizeB, m_nRowDimIdx);
			TIterator itColEndA = itColA + GetRowCount();

			TValue tValue;
			for (; itColA != itColEndA; ++itColA, ++itColB)
			{
				tValue = *itColA;
				*itColA = *itColB;
				*itColB = tValue;
			}

			return *this;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Swap rows. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="nRowA">	The row a. </param>
		/// <param name="nRowB">	The row b. </param>
		///
		/// <returns>	A TThis&amp; </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TThis& SwapRows(TIdx nRowA, TIdx nRowB)
		{
			if (nRowA == nRowB)
			{
				return *this;
			}

			TAN_ASSERT(nRowA < GetRowCount());
			TAN_ASSERT(nRowB < GetRowCount());

			std::vector<TIdx> lSizeA, lSizeB;

			if (IsTranspose())
			{
				lSizeA = { 0, nRowA };
				lSizeB = { 0, nRowB };
			}
			else
			{
				lSizeA = { nRowA, 0 };
				lSizeB = { nRowB, 0 };
			}

			TIterator itRowA = this->Begin(lSizeA, m_nColDimIdx);
			TIterator itRowB = this->Begin(lSizeB, m_nColDimIdx);
			TIterator itRowEndA = itRowA + GetColCount();

			TValue tValue;
			for (; itRowA != itRowEndA; ++itRowA, ++itRowB)
			{
				tValue = *itRowA;
				*itRowA = *itRowB;
				*itRowB = tValue;
			}

			return *this;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Gets sub matrix.
		///
		/// \author Perwass
		/// 
		///
		/// \param	nRowStartIdx Zero-based index of the row start.
		/// \param	nColStartIdx Zero-based index of the col start.
		/// \param	nRowCnt		 Number of rows.
		/// \param	nColCnt		 Number of cols.
		///
		/// \return The sub matrix.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		TThis GetSubMatrix(TIdx nRowStartIdx, TIdx nColStartIdx, TIdx nRowCnt, TIdx nColCnt)
		{
			if (nRowStartIdx + nRowCnt - 1 >= GetRowCount()
				|| nColStartIdx + nColCnt - 1 >= GetColCount())
			{
				TAN_THROW_RT("Sub matrix range out of bounds");
			}

			TThis matB(nRowCnt, nColCnt);

			TIterator itRowA = BeginRows(nRowStartIdx, nColStartIdx);
			TIterator itRowEndA = itRowA + nRowCnt;
			TIterator itRowB = matB.BeginRows();

			for (; itRowA != itRowEndA; ++itRowA, ++itRowB)
			{
				TIterator itRowColA = BeginCols(itRowA);
				TIterator itRowColEndA = itRowColA + nColCnt;
				TIterator itRowColB = matB.BeginCols(itRowB);

				for (; itRowColA != itRowColEndA; ++itRowColA, ++itRowColB)
				{
					*itRowColB = *itRowColA;
				}
			}

			return matB;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Sets sub matrix.
		///
		/// \author Perwass
		/// 
		///
		/// \param	nRowStartIdx Zero-based index of the row start.
		/// \param	nColStartIdx Zero-based index of the col start.
		/// \param	matB		 The matrix b.
		///
		/// \return A TThis&.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		TThis& SetSubMatrix(TIdx nRowStartIdx, TIdx nColStartIdx, const TThis& matB)
		{
			if (nRowStartIdx + matB.GetRowCount() - 1 >= GetRowCount()
				|| nColStartIdx + matB.GetColCount() - 1 >= GetColCount())
			{
				TAN_THROW_RT("Sub matrix range out of bounds");
			}

			TIterator itRowA = BeginRows(nRowStartIdx, nColStartIdx);
			TIterator itRowEndA = itRowA + matB.GetRowCount();
			TConstIterator itRowB = matB.ConstBeginRows();

			for (; itRowA != itRowEndA; ++itRowA, ++itRowB)
			{
				TIterator itRowColA = BeginCols(itRowA);
				TIterator itRowColEndA = itRowColA + matB.GetColCount();
				TConstIterator itRowColB = matB.ConstBeginCols(itRowB);

				for (; itRowColA != itRowColEndA; ++itRowColA, ++itRowColB)
				{
					*itRowColA = *itRowColB;
				}
			}

			return *this;
		}


	protected:

		TValue _Abs(TValue tValue)
		{
			return tValue < TValue(0) ? -tValue : tValue;
		}

		bool _IsZero(TValue tValue, TValue tPrec)
		{
			return (_Abs(tValue) < _Abs(tPrec));
		}

		std::vector<TIdx> _GetIndexVector(TIdx nRowIdx, TIdx nColIdx) const
		{
			if (IsTranspose())
			{
				return std::vector<TIdx>({ nColIdx, nRowIdx });
			}
			else
			{
				return std::vector<TIdx>({ nRowIdx, nColIdx });
			}
		}
	};	// class


}	// namespace

#include "Matrix.Operators.h"