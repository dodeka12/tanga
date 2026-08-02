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

#include <algorithm>
#include <vector>
#include <initializer_list>

#include "Defines.h"
#include "StrideIterator.h"

namespace Tan
{
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// \brief An array.
	///
	/// \author Perwass
	/// 
	///
	/// \tparam	_TValue Type of the value.
	/// \tparam	t_uDim  Type of the dim.
	///
	/// ### remarks Perwass, .
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

	template<typename _TValue>
	class CArray
	{
	public:
		typedef _TValue TValue;
		typedef size_t TIdx;
		typedef CArray<TValue> TThis;
		typedef CStrideIterator<TValue> TIterator;
		typedef CStrideIteratorConst<TValue> TConstIterator;
		typedef std::vector<TValue> TData;
		typedef std::vector<TIdx> TIdxVec;
		typedef std::vector<TIdx> TSizeVec;

	private:
		TData m_vecData;
		TSizeVec m_vecSize;
		TSizeVec m_vecStride;

		size_t m_nDimension;
		size_t m_nTotalSize;

	protected:

		TIdx _GetPos(const TIdxVec& vecPos) const
		{
			TIdx nPos = 0;
			for (TIdx nIdx = 0; nIdx < m_nDimension; ++nIdx)
			{
				nPos += m_vecStride[nIdx] * vecPos[nIdx];
			}

			return nPos;
		}

		TIdxVec _GetPosBegin() const
		{
			TIdxVec vecPos(m_nDimension);
			std::memset(vecPos.data(), 0, m_nDimension * sizeof(TIdx));
			return vecPos;
		}

	public:
		CArray() 
		{
			Reset();
		}
		
		CArray(const TSizeVec& vecSize)
		{
			SetSize(vecSize);
		}

		CArray(const TSizeVec& vecSize, const std::initializer_list<TValue>& xData)
		{
			SetSize(vecSize, xData);
		}

		CArray(const TSizeVec& vecSize, const TValue* pData)
		{
			SetSize(vecSize);
			if (m_nTotalSize > 0)
			{
				memcpy(m_vecData.data(), pData, GetTotalByteSize());
			}
		}

		CArray(TThis&& xA) = default;
		TThis& operator= (TThis&& xA) = default;

		CArray(const TThis& xA) = default;
		TThis& operator= (const TThis& xA) = default;


		void Reset()
		{
			m_vecData.resize(0);
			m_vecData.shrink_to_fit();

			m_vecStride.resize(0);
			m_vecSize.resize(0);
			m_nTotalSize = 0;
			m_nDimension = 0;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Sets a new size of the array without moving or resetting present components.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="vecSize">	Size of the vector. </param>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		void SetSize(const TSizeVec& vecSize)
		{
			m_nDimension = vecSize.size();
			if (m_nDimension == 0)
			{
				Reset();
				return;
			}

			
			m_vecSize = vecSize;

			m_vecStride.resize(m_nDimension);
			size_t nStride = 1;
			for (size_t nIdx = 0; nIdx < m_nDimension; ++nIdx)
			{
				m_vecStride[m_nDimension - nIdx - 1] = nStride;
				nStride *= m_vecSize[m_nDimension - nIdx - 1];
			}

			m_nTotalSize = nStride;
			if (m_nTotalSize == 0)
			{
				Reset();
				return;
			}

			m_vecData.resize(m_nTotalSize);
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Sets a size.
		///
		/// \author Perwass
		/// 
		///
		/// \param	vecSize Size of the vector.
		/// \param	xData   The data.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		void SetSize(const TSizeVec& vecSize, const std::initializer_list<TValue>& xData)
		{
			SetSize(vecSize);
			SetData(xData);
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Sets a data.
		///
		/// \author Perwass
		/// 
		///
		/// \param	xData The data.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		void SetData(const std::initializer_list<TValue>& xData)
		{
			if (m_nTotalSize != xData.size())
			{
				TAN_THROW_RT("Container has invalid size.");
			}

			typename TData::iterator itEl = m_vecData.begin();
			for (TValue tValue : xData)
			{
				*itEl = tValue;
				++itEl;
			}
		}


		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Resizes the array while keeping those components in place that are within the size of the
		/// 	new array.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="vecSize">	Size of the vector. </param>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		void Resize(const TSizeVec& vecSize)
		{
			if (m_nDimension != vecSize.size())
			{
				TAN_THROW_RT("Can only resize to array of same dimension");
			}

			// Copy this to temp array
			TThis xA(*this);
			
			// Make this of new size
			SetSize(vecSize);

			// If the new size is zero, then we are finished here
			if (m_nTotalSize == 0)
			{
				return;
			}

			// Set all components of new array to zero.
			Zero();

			// Copy old elements to new array, while keeping the component positions.
			// Use vecPos to store the current position in the array.
			// Use vecCnt to store the minimum size per dimension of old and new array.
			TIdxVec vecPos(m_nDimension);
			TSizeVec vecCnt(m_nDimension);
			for (TIdx nIdx = 0; nIdx < m_nDimension; ++nIdx)
			{
				vecPos[nIdx] = 0;
				vecCnt[nIdx] = std::min(m_vecSize[nIdx], xA.m_vecSize[nIdx]);
			}

			// Loop over all but the last dimension to copy elements
			// from old to new array.
			TIdx nDim;
			do 
			{
				TIterator itEl = Begin(vecPos, m_nDimension - 1);
				TIterator itElA = xA.Begin(vecPos, m_nDimension - 1);
				memcpy(itEl.GetDataPtr(), itElA.GetDataPtr(), vecCnt[m_nDimension - 1] * sizeof(TValue));

				for (nDim = 0; nDim < m_nDimension-1; ++nDim)
				{
					++vecPos[nDim];
					if (vecPos[nDim] >= vecCnt[nDim])
					{
						vecPos[nDim] = 0;
					}
					else
					{
						break;
					}
				}
			} 
			while (nDim < m_nDimension-1);

		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets the size. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	The size. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		const TSizeVec& GetSize() const
		{
			return m_vecSize;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets a size. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="nIdx">	The index. </param>
		///
		/// <returns>	The size. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TIdx GetSize(TIdx nIdx) const
		{
			TAN_ASSERT(nIdx < m_nDimension);
			return m_vecSize[nIdx];
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets the stride. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	The stride. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		const TSizeVec& GetStride() const
		{
			return m_vecStride;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets total size. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	The total size. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		size_t GetTotalSize() const
		{
			return m_nTotalSize;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets total byte size. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	The total byte size. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		size_t GetTotalByteSize() const
		{
			return m_nTotalSize * sizeof(TValue);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets data pointer. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	null if it fails, else the data pointer. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TValue* GetDataPtr()
		{
			return m_vecData.data();
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets data pointer. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <returns>	null if it fails, else the data pointer. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		const TValue* GetDataPtr() const
		{
			return m_vecData.data();
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Zeroes this object.
		///
		/// \author Perwass
		/// 
		///
		/// ### remarks Perwass, .
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		void Zero()
		{
			if (m_nTotalSize > 0)
			{
				memset(m_vecData.data(), 0, GetTotalByteSize());
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Query if this object is empty.
		///
		/// \author Perwass
		/// 
		///
		/// \return true if empty, false if not.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		bool IsEmpty() const
		{
			return GetTotalSize() == 0;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief Query if 'itEl' is in range.
		///
		/// \author Perwass
		/// 
		///
		/// \tparam	_TIterator Type of the iterator.
		/// \param [in,out]	itEl The iterator el.
		///
		/// \return true if in range, false if not.
		///
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename _TIterator>
		bool IsInRange(_TIterator& itEl) const
		{
			size_t nFront = size_t(m_vecData.data());
			size_t nBack = size_t(&m_vecData[m_nTotalSize-1]);
			size_t nPos = size_t(itEl.GetDataPtr());
			if (nFront > nPos || nPos > nBack)
			{
				return false;
			}
			return true;
		}


		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Query if 'vecPos' is in range. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="vecPos">	The vector position. </param>
		///
		/// <returns>	true if in range, false if not. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		bool IsInRange(const TIdxVec& vecPos) const
		{
			if (vecPos.size() != m_nDimension)
			{
				TAN_THROW_RT("Position array is not of correct size");
			}

			for (TIdx nIdx = 0; nIdx < m_nDimension; ++nIdx)
			{
				if (vecPos[nIdx] >= m_vecSize[nIdx])
				{
					return false;
				}
			}

			return true;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets an index. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="itEl">	[in,out] The iterator el. </param>
		///
		/// <returns>	The index. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename _TIterator>
		TIdxVec GetIndex(_TIterator& itEl) const
		{
			size_t nFront = size_t(m_vecData.data());
			size_t nBack = size_t(&m_vecData[m_nTotalSize-1]);
			size_t nPos = size_t(itEl.GetDataPtr());
			if (nFront > nPos || nPos > nBack)
			{
				TAN_THROW_RT("Iterator not in range");
			}

			TIdxVec vecPos(m_nDimension);

			size_t nDiff = (nPos - nFront) / sizeof(TValue);
			for (TIdx nIdx = 0; nIdx < m_nDimension; ++nIdx)
			{
				size_t nVal = nDiff / m_vecStride[nIdx];
				nDiff -= nVal * m_vecStride[nIdx];
				vecPos[nIdx] = nVal;
			}

			return vecPos;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets an index. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="itEl">	[in,out] The iterator el. </param>
		/// <param name="nDim">	The dim. </param>
		///
		/// <returns>	The index. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename _TIterator>
		TIdx GetIndex(_TIterator& itEl, TIdx nDim) const
		{
			TAN_ASSERT(nDim < m_nDimension);

			size_t nFront = size_t(m_vecData.data());
			size_t nBack = size_t(&m_vecData[m_nTotalSize - 1]);
			size_t nPos = size_t(itEl.GetDataPtr());
			if (nFront > nPos || nPos > nBack)
			{
				TAN_THROW_RT("Iterator not in range");
			}

			size_t nDiff = (nPos - nFront) / sizeof(TValue);
			size_t nVal;
			for (TIdx nIdx = 0; nIdx <= nDim; ++nIdx)
			{
				nVal = nDiff / m_vecStride[nIdx];
				nDiff -= nVal * m_vecStride[nIdx];
			}

			return nVal;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets a component. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="vecPos">	The vector position. </param>
		///
		/// <returns>	The component. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TValue& GetComp(const TIdxVec& vecPos)
		{
			TIdx nPos = _GetPos(vecPos);
			TAN_ASSERT(nPos < GetTotalSize());

			return m_vecData[nPos];
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Gets a component. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="vecPos">	The vector position. </param>
		///
		/// <returns>	The component. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		const TValue& GetComp(const TIdxVec& vecPos) const
		{
			TIdx nPos = _GetPos(vecPos);
			TAN_ASSERT(nPos < GetTotalSize());

			return m_vecData[nPos];
		}


		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Return iterator that starts at the beginning of the array and steps in the given
		/// 	dimension.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="nDim">	The dim. </param>
		///
		/// <returns>	The iterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TIterator Begin(TIdx nDim)
		{
			TAN_ASSERT(nDim < m_nDimension);

			return TIterator(m_vecData.data(), m_vecStride[nDim]);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Returns the iterator that starts at itBegin and steps in the given dimension.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="itBegin">	[in,out] The iterator begin. </param>
		/// <param name="nDim">   	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TIterator Begin(TIterator& itBegin, TIdx nDim)
		{
			TAN_ASSERT(nDim < m_nDimension);
			TAN_ASSERT(IsInRange(itBegin));

			return TIterator(itBegin.GetDataPtr(), m_vecStride[nDim]);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Returns the iterator for dimension nDim that starts at the position given by vecPos.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="vecPos">	The vector position. </param>
		/// <param name="nDim">  	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TIterator Begin(const TIdxVec& vecPos, TIdx nDim)
		{
			TAN_ASSERT(nDim < m_nDimension);

			if (vecPos.size() != m_nDimension)
			{
				TAN_THROW_RT("Position array is not of correct size");
			}

			return TIterator(m_vecData.data() + _GetPos(vecPos), m_vecStride[nDim]);
		}


		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Ends the given n dim. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="nDim">	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TIterator End(TIdx nDim)
		{
			TAN_ASSERT(nDim < m_nDimension);

			TIdx nEnd = m_vecStride[nDim] * m_vecSize[nDim];
			return TIterator(m_vecData.data() + nEnd, m_vecStride[nDim]);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	The end iterator for iterator itBegin in dimension nDim. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="itBegin">	[in,out] The iterator begin. </param>
		/// <param name="nDim">   	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TIterator End(TIterator& itEl, TIdx nDim)
		{
			TAN_ASSERT(nDim < m_nDimension);
			TAN_ASSERT(IsInRange(itEl));

			TIdx nIdx = GetIndex(itEl, nDim);

			return TIterator(itEl.GetDataPtr() + (m_vecSize[nDim] - nIdx) * m_vecStride[nDim], m_vecStride[nDim]);

			//TPosition vecPos = GetIndex(itEl);
			//vecPos[nDim] = m_vecSize[nDim];

			//return TIterator(m_vecData.data() + _GetPos(vecPos), m_vecStride[nDim]);
		}


		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Ends for. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="vecPos">	The vector position. </param>
		/// <param name="nDim">  	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TIterator End(const TIdxVec& vecPos, TIdx nDim)
		{
			TAN_ASSERT(nDim < m_nDimension);
			TAN_ASSERT(IsInRange(vecPos));

			TIdxVec vecNewPos(vecPos);
			vecNewPos[nDim] = m_vecSize[nDim];

			return TIterator(m_vecData.data() + _GetPos(vecNewPos), m_vecStride[nDim]);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Return iterator that starts at the beginning of the array and steps in the given
		/// 	dimension.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="nDim">	The dim. </param>
		///
		/// <returns>	The iterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TConstIterator ConstBegin(TIdx nDim) const
		{
			TAN_ASSERT(nDim < m_nDimension);

			return TConstIterator(m_vecData.data(), m_vecStride[nDim]);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Returns the iterator that starts at itBegin and steps in the given dimension.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="itBegin">	[in,out] The iterator begin. </param>
		/// <param name="nDim">   	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TConstIterator ConstBegin(const TConstIterator& itBegin, TIdx nDim) const
		{
			TAN_ASSERT(nDim < m_nDimension);

			return TConstIterator(itBegin.GetDataPtr(), m_vecStride[nDim]);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Returns the iterator that starts at itBegin and steps in the given dimension.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="itBegin">	The iterator begin. </param>
		/// <param name="nDim">   	The dim. </param>
		///
		/// <returns>	A TConstIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TConstIterator ConstBegin(const TIterator& itBegin, TIdx nDim) const
		{
			TAN_ASSERT(nDim < m_nDimension);

			return TConstIterator(itBegin.GetDataPtr(), m_vecStride[nDim]);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Returns the iterator for dimension nDim that starts at the position given by vecPos.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="vecPos">	The vector position. </param>
		/// <param name="nDim">  	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TConstIterator ConstBegin(const TIdxVec& vecPos, TIdx nDim) const
		{
			TAN_ASSERT(nDim < m_nDimension);

			if (vecPos.size() != m_nDimension)
			{
				TAN_THROW_RT("Position array is not of correct size");
			}

			TIdx nPos = 0;
			for (TIdx nIdx = 0; nIdx < m_nDimension; ++nIdx)
			{
				nPos += m_vecStride[nIdx] * vecPos[nIdx];
			}

			return TConstIterator(&m_vecData[nPos], m_vecStride[nDim]);
		}


		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Ends the given n dim. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="nDim">	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TConstIterator ConstEnd(TIdx nDim) const
		{
			TAN_ASSERT(nDim < m_nDimension);

			TIdx nEnd = m_vecStride[nDim] * m_vecSize[nDim];
			return TConstIterator(m_vecData.data() + nEnd, m_vecStride[nDim]);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	The end iterator for iterator itBegin in dimension nDim. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="itBegin">	[in,out] The iterator begin. </param>
		/// <param name="nDim">   	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TConstIterator ConstEnd(TConstIterator& itEl, TIdx nDim) const
		{
			TAN_ASSERT(nDim < m_nDimension);
			TAN_ASSERT(IsInRange(itEl));

			TIdx nIdx = GetIndex(itEl, nDim);
			return TConstIterator(itEl.GetDataPtr() + (m_vecSize[nDim] - nIdx) * m_vecStride[nDim], m_vecStride[nDim]);
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Constant end for. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="itBegin">	[in,out] The iterator begin. </param>
		/// <param name="nDim">   	The dim. </param>
		///
		/// <returns>	A TConstIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TConstIterator ConstEnd(TIterator& itEl, TIdx nDim) const
		{
			TAN_ASSERT(nDim < m_nDimension);
			TAN_ASSERT(IsInRange(itEl));

			TIdx nIdx = GetIndex(itEl, nDim);
			return TConstIterator(itEl.GetDataPtr() + (m_vecSize[nDim] - nIdx) * m_vecStride[nDim], m_vecStride[nDim]);
		}


		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Ends for. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="vecPos">	The vector position. </param>
		/// <param name="nDim">  	The dim. </param>
		///
		/// <returns>	A TIterator. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		TConstIterator ConstEnd(const TIdxVec& vecPos, TIdx nDim) const
		{
			TAN_ASSERT(nDim < m_nDimension);
			TAN_ASSERT(IsInRange(vecPos));

			TIdxVec vecNewPos(vecPos);
			vecNewPos[nDim] = m_vecSize[nDim];

			return TConstIterator(m_vecData.data() + _GetPos(vecNewPos), m_vecStride[nDim]);
		}

	};


} // namespace Tan