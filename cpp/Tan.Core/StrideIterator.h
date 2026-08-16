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

#include "Defines.h"

#if defined(__APPLE__)
#	include <iterator>
#else
namespace std
{
	struct random_access_iterator_tag;
}
#endif

////////////////////////////////////////////////////////////////////////////////////////////////////
/// <summary>	A stride iterator. </summary>
///
/// <remarks>	Perwass, . </remarks>
///
/// <typeparam name="TValue">	Type of the value. </typeparam>
////////////////////////////////////////////////////////////////////////////////////////////////////

template<typename TValue>
class CStrideIterator
{
public:

	typedef std::random_access_iterator_tag iterator_category;
	typedef TValue value_type;
	typedef size_t difference_type;
	typedef TValue* pointer;
	typedef TValue& reference;

public:

	CStrideIterator()
	{
		m_pValue = nullptr;
		m_nStride = 0;
	}

	CStrideIterator(TValue* pValue, difference_type nStride)
	{
		m_pValue = pValue;
		m_nStride = nStride;
		if (m_nStride == 0)
		{
			TAN_THROW_RT("Stride must not be zero.");
		}
	}

	CStrideIterator(const CStrideIterator<TValue>& xIterator)
	{
		*this = xIterator;
	}

	CStrideIterator<TValue>& operator=(const CStrideIterator<TValue>& xIterator)
	{
		m_pValue = xIterator.m_pValue;
		m_nStride = xIterator.m_nStride;
		return *this;
	}

	TValue& operator[](size_t nIdx)
	{
		return m_pValue[nIdx * m_nStride];
	}

	CStrideIterator<TValue>& operator++()
	{
		m_pValue += m_nStride;
		return *this;
	}

	CStrideIterator<TValue>& operator--()
	{
		m_pValue -= m_nStride;
		return *this;
	}

	CStrideIterator<TValue> operator++(int)
	{
		CStrideIterator<TValue> itTemp(*this);
		m_pValue += m_nStride;
		return itTemp;
	}

	CStrideIterator<TValue> operator--(int)
	{
		CStrideIterator<TValue> itTemp(*this);
		m_pValue -= m_nStride;
		return itTemp;
	}

	TValue* operator->()
	{
		return m_pValue;
	}

	TValue& operator*()
	{
		return *m_pValue;
	}

	const TValue& operator*() const
	{
		return *m_pValue;
	}

	bool operator<(const CStrideIterator<TValue>& xIterator) const
	{
		return m_pValue < xIterator.m_pValue;
	}

	bool operator>(const CStrideIterator<TValue>& xIterator) const
	{
		return m_pValue > xIterator.m_pValue;
	}

	bool operator==(const CStrideIterator<TValue>& xIterator) const
	{
		return m_pValue == xIterator.m_pValue;
	}

	bool operator!=(const CStrideIterator<TValue>& xIterator) const
	{
		return m_pValue != xIterator.m_pValue;
	}

	CStrideIterator<TValue>& operator+=(size_t nValue)
	{
		m_pValue += nValue * m_nStride;
		return *this;
	}

	CStrideIterator<TValue>& operator-=(size_t nValue)
	{
		m_pValue -= nValue * m_nStride;
		return *this;
	}

	CStrideIterator<TValue> operator+(size_t nOffset) const
	{
		CStrideIterator<TValue> itA(*this);

		itA += nOffset;
		return itA;
	}

	CStrideIterator<TValue> operator-(size_t nOffset) const
	{
		CStrideIterator<TValue> itA(*this);

		itA -= nOffset;
		return itA;
	}

	//size_t operator-(const CStrideIterator<TValue>& xItB) const
	//{
	//	size_t nPosA = size_t(m_pValue);
	//	size_t nPosB = size_t(xItB.m_pValue);
	//	if (nPosA < nPosB)
	//	{
	//		TAN_THROW_RT("Difference of iterators is negative");
	//	}

	//	size_t nSep = (nPosA - nPosB) / sizeof(TValue);
	//	return nSep;
	//}

	TValue* GetDataPtr()
	{
		return m_pValue;
	}

	const TValue* GetDataPtr() const
	{
		return m_pValue;
	}

protected:

	TValue* m_pValue;
	difference_type m_nStride;
};

////////////////////////////////////////////////////////////////////////////////////////////////////
/// <summary>	A receive random access value iterator constant. </summary>
///
/// <remarks>	Perwass, . </remarks>
///
/// <typeparam name="TValue">	Type of the value. </typeparam>
////////////////////////////////////////////////////////////////////////////////////////////////////

template<typename TValue>
class CStrideIteratorConst
{
public:

	typedef std::random_access_iterator_tag iterator_category;
	typedef const TValue value_type;
	typedef size_t difference_type;
	typedef const TValue* pointer;
	typedef const TValue& reference;

public:

	CStrideIteratorConst()
	{
		m_pValue = nullptr;
		m_nStride = 0;
	}

	CStrideIteratorConst(const TValue* pValue, difference_type nStride)
	{
		m_pValue = pValue;
		m_nStride = nStride;
		if (m_nStride == 0)
		{
			TAN_THROW_RT("Stride must not be zero.");
		}

	}

	CStrideIteratorConst(const CStrideIteratorConst<TValue>& xIterator)
	{
		*this = xIterator;
	}

	CStrideIteratorConst& operator=(const CStrideIteratorConst<TValue>& xIterator)
	{
		m_pValue = xIterator.m_pValue;
		m_nStride = xIterator.m_nStride;
		return *this;
	}

	CStrideIteratorConst& operator=(const CStrideIterator<TValue>& xIterator)
	{
		m_pValue = xIterator.GetDataPtr();
		m_nStride = xIterator.m_nStride;
		return *this;
	}

	const TValue& operator[](size_t nIdx)
	{
		return m_pValue[nIdx * m_nStride];
	}

	CStrideIteratorConst<TValue>& operator++()
	{
		m_pValue += m_nStride;
		return *this;
	}

	CStrideIteratorConst<TValue>& operator--()
	{
		m_pValue += m_nStride;
		return *this;
	}

	CStrideIteratorConst<TValue> operator++(int)
	{
		CStrideIteratorConst<TValue> itTemp(*this);
		m_pValue += m_nStride;
		return itTemp;
	}

	CStrideIteratorConst<TValue> operator--(int)
	{
		CStrideIteratorConst<TValue> itTemp(*this);
		m_pValue += m_nStride;
		return itTemp;
	}

	const TValue* operator->()
	{
		return m_pValue;
	}

	const TValue& operator*()
	{
		return *m_pValue;
	}

	const TValue& operator*() const
	{
		return *m_pValue;
	}

	bool operator<(const CStrideIterator<TValue>& xIterator) const
	{
		return m_pValue < xIterator.m_pValue;
	}

	bool operator>(const CStrideIterator<TValue>& xIterator) const
	{
		return m_pValue > xIterator.m_pValue;
	}

	bool operator==(const CStrideIteratorConst<TValue>& xIterator) const
	{
		return m_pValue == xIterator.m_pValue;
	}

	bool operator!=(const CStrideIteratorConst<TValue>& xIterator) const
	{
		return m_pValue != xIterator.m_pValue;
	}

	CStrideIteratorConst<TValue>& operator+=(size_t nValue)
	{
		m_pValue += nValue * m_nStride;
		return *this;
	}

	CStrideIteratorConst<TValue>& operator-=(size_t nValue)
	{
		m_pValue -= nValue * m_nStride;
		return *this;
	}

	CStrideIteratorConst<TValue> operator+(size_t nOffset) const
	{
		CStrideIteratorConst<TValue> itA(*this);

		itA += nOffset;
		return itA;
	}

	CStrideIteratorConst<TValue> operator-(size_t nOffset) const
	{
		CStrideIteratorConst<TValue> itA(*this);

		itA -= nOffset;
		return itA;
	}

	//size_t operator-(const CStrideIteratorConst& xItB) const
	//{
	//	size_t nPosA = size_t(m_pValue);
	//	size_t nPosB = size_t(xItB.m_pValue);
	//	if (nPosA < nPosB)
	//	{
	//		TAN_THROW_RT("Difference of iterators is negative");
	//	}

	//	size_t nSep = (nPosA - nPosB) / sizeof(TValue);
	//	return nSep;
	//}

	const TValue* GetDataPtr()
	{
		return m_pValue;
	}

	const TValue* GetDataPtr() const
	{
		return m_pValue;
	}

protected:

	const TValue* m_pValue;
	difference_type m_nStride;
};
