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


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Standard template algorithms.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#pragma once

namespace Tan
{
	template<typename TContainer, typename TFunctor>
	void ForEach(TContainer& xContainer, TFunctor Functor)
	{
		typename TContainer::iterator itEl, itEnd = xContainer.end();
		for (itEl = xContainer.begin(); itEl != itEnd; ++itEl)
		{
			Functor(*itEl);
		}
	}

	template<typename TContainer, typename TFunctor>
	void ForEach(const TContainer& xContainer, TFunctor Functor)
	{
		typename TContainer::const_iterator itEl, itEnd = xContainer.cend();
		for (itEl = xContainer.cbegin(); itEl != itEnd; ++itEl)
		{
			Functor(*itEl);
		}
	}

	template<typename TContainer, typename TFunctor>
	void ForEachIndex(TContainer& xContainer, TFunctor Functor)
	{
		size_t nIdx;
		typename TContainer::iterator itEl, itEnd = xContainer.end();
		for (itEl = xContainer.begin(), nIdx = 0; itEl != itEnd; ++itEl, ++nIdx)
		{
			Functor(*itEl, nIdx);
		}
	}

	template<typename TContainer, typename TFunctor>
	void ForEachIndex(const TContainer& xContainer, TFunctor Functor)
	{
		size_t nIdx;
		typename TContainer::const_iterator itEl, itEnd = xContainer.cend();
		for (itEl = xContainer.cbegin(), nIdx = 0; itEl != itEnd; ++itEl, ++nIdx)
		{
			Functor(*itEl, nIdx);
		}
	}

	template<typename TContainer, typename TFunctor>
	void ForEachPair(TContainer& xContainer, TFunctor Functor)
	{
		typename TContainer::iterator itEl, itEnd = xContainer.end();
		for (itEl = xContainer.begin(); itEl != itEnd; ++itEl)
		{
			Functor(itEl->first, itEl->second);
		}
	}

	template<typename TContainer, typename TFunctor>
	void ForEachPair(const TContainer& xContainer, TFunctor Functor)
	{
		typename TContainer::const_iterator itEl, itEnd = xContainer.cend();
		for (itEl = xContainer.cbegin(); itEl != itEnd; ++itEl)
		{
			Functor(itEl->first, itEl->second);
		}
	}

	template<typename TContainerA, typename TContainerB, typename TFunctor>
	void ForEachPair(TContainerA& xContainerA, TContainerB& xContainerB, TFunctor Functor)
	{
		typename TContainerA::iterator itElA  = xContainerA.begin();
		typename TContainerA::iterator itEndA = xContainerA.end();
		typename TContainerB::iterator itElB  = xContainerB.begin();

		for (; itElA != itEndA; ++itElA, ++itElB)
		{
			Functor(*itElA, *itElB);
		}
	}

	template<typename TContainerA, typename TContainerB, typename TFunctor>
	void ForEachPair(const TContainerA& xContainerA, const TContainerB& xContainerB, TFunctor Functor)
	{
		typename TContainerA::const_iterator itElA  = xContainerA.begin();
		typename TContainerA::const_iterator itEndA = xContainerA.end();
		typename TContainerB::const_iterator itElB  = xContainerB.begin();

		for (; itElA != itEndA; ++itElA, ++itElB)
		{
			Functor(*itElA, *itElB);
		}
	}

	template<typename TContainerA, typename TContainerB, typename TFunctor>
	void ForEachPairIndex(TContainerA& xContainerA, TContainerB& xContainerB, TFunctor Functor)
	{
		size_t nIdx                  = 0;
		typename TContainerA::iterator itElA  = xContainerA.begin();
		typename TContainerA::iterator itEndA = xContainerA.end();
		typename TContainerB::iterator itElB  = xContainerB.begin();

		for (; itElA != itEndA; ++itElA, ++itElB, ++nIdx)
		{
			Functor(*itElA, *itElB, nIdx);
		}
	}

	template<typename TContainerA, typename TContainerB, typename TFunctor>
	void ForEachPairIndex(const TContainerA& xContainerA, const TContainerB& xContainerB, TFunctor Functor)
	{
		size_t nIdx                        = 0;
		typename TContainerA::const_iterator itElA  = xContainerA.begin();
		typename TContainerA::const_iterator itEndA = xContainerA.end();
		typename TContainerB::const_iterator itElB  = xContainerB.begin();

		for (; itElA != itEndA; ++itElA, ++itElB, ++nIdx)
		{
			Functor(*itElA, *itElB, nIdx);
		}
	}

	template<typename TContainerA, typename TContainerB, typename TFunctor>
	void Transform(TContainerA& xContainerA, const TContainerB& xContainerB, TFunctor Functor)
	{
		typename TContainerA::iterator itElA       = xContainerA.begin();
		typename TContainerA::iterator itEndA      = xContainerA.end();
		typename TContainerB::const_iterator itElB = xContainerB.begin();

		for (; itElA != itEndA; ++itElA, ++itElB)
		{
			Functor(*itElA, *itElB);
		}
	}

	template<typename TContainerA, typename TContainerB, typename TFunctor>
	void TransformIndex(TContainerA& xContainerA, const TContainerB& xContainerB, TFunctor Functor)
	{
		size_t nIdx                       = 0;
		typename TContainerA::iterator itElA       = xContainerA.begin();
		typename TContainerA::iterator itEndA      = xContainerA.end();
		typename TContainerB::const_iterator itElB = xContainerB.begin();

		for (; itElA != itEndA; ++itElA, ++itElB, ++nIdx)
		{
			Functor(*itElA, *itElB, nIdx);
		}
	}

	template<typename TContainer, typename TFunctor>
	bool ForEachTest(TContainer& xContainer, TFunctor Functor)
	{
		typename TContainer::iterator itEl, itEnd = xContainer.end();
		for (itEl = xContainer.begin(); itEl != itEnd; ++itEl)
		{
			if (!Functor(*itEl))
			{
				return false;
			}
		}

		return true;
	}

	template<typename TContainer, typename TFunctor>
	bool ForEachTest(const TContainer& xContainer, TFunctor Functor)
	{
		typename TContainer::const_iterator itEl, itEnd = xContainer.end();
		for (itEl = xContainer.begin(); itEl != itEnd; ++itEl)
		{
			if (!Functor(*itEl))
			{
				return false;
			}
		}

		return true;
	}

	template<typename TContainer, typename TFunctor>
	bool ForEachIndexTest(TContainer& xContainer, TFunctor Functor)
	{
		size_t nIdx;
		typename TContainer::iterator itEl, itEnd = xContainer.end();
		for (itEl = xContainer.begin(), nIdx = 0; itEl != itEnd; ++itEl, ++nIdx)
		{
			if (!Functor(*itEl, nIdx))
			{
				return false;
			}
		}

		return true;
	}

	template<typename TContainer, typename TFunctor>
	bool ForEachIndexTest(const TContainer& xContainer, TFunctor Functor)
	{
		size_t nIdx;
		typename TContainer::const_iterator itEl, itEnd = xContainer.end();
		for (itEl = xContainer.begin(), nIdx = 0; itEl != itEnd; ++itEl, ++nIdx)
		{
			if (!Functor(*itEl, nIdx))
			{
				return false;
			}
		}

		return true;
	}

	template<typename TContainer, typename TObject>
	bool Contains(const TContainer& xContainer, const TObject& xObject)
	{
		return xContainer.find(xObject) != xContainer.end();
	}

	template<typename TContainer, typename TObject>
	bool Contains(typename TContainer::iterator& itEl, TContainer& xContainer, const TObject& xObject)
	{
		return (itEl = xContainer.find(xObject)) != xContainer.end();
	}

	template<typename TContainer, typename TObject>
	bool Contains(typename TContainer::const_iterator& itEl, const TContainer& xContainer, const TObject& xObject)
	{
		return (itEl = xContainer.find(xObject)) != xContainer.end();
	}


	template<typename T, size_t t_nCount>
	void MemCpy(T* pTrg, const T* pSrc)
	{
		for (size_t nIdx = 0; nIdx < t_nCount; ++nIdx, ++pTrg, ++pSrc)
		{
			*pTrg = *pSrc;
		}
	}

	template<typename T, size_t t_uTrgCount, size_t t_nSrcCount>
	void MemCpy(T(&pTrg)[t_uTrgCount], const T(&pSrc)[t_nSrcCount])
	{
		TAN_STATIC_ASSERT((t_uTrgCount >= t_nSrcCount));

		T* _pTrg = pTrg;
		const T* _pSrc = pSrc;

		for (size_t nIdx = 0; nIdx < t_nSrcCount; ++nIdx, ++_pTrg, ++_pSrc)
		{
			*_pTrg = *_pSrc;
		}
	}

	template<typename T>
	void MemCpy(T* pTrg, const T* pSrc, size_t nCount)
	{
		for (size_t nIdx = 0; nIdx < nCount; ++nIdx, ++pTrg, ++pSrc)
		{
			*pTrg = *pSrc;
		}
	}

	template<typename T, size_t t_nCount>
	void MemSet(T* pTrg, const T& tValue)
	{
		for (size_t nIdx = 0; nIdx < t_nCount; ++nIdx, ++pTrg)
		{
			*pTrg = tValue;
		}
	}

	template<typename T, size_t t_nCount>
	void MemSet(T(&pTrg)[t_nCount], const T& tValue)
	{
		T* _pTrg = pTrg;

		for (size_t nIdx = 0; nIdx < t_nCount; ++nIdx, ++_pTrg)
		{
			*_pTrg = tValue;
		}
	}

	template<typename T>
	void MemSet(T* pTrg, const T& tValue, size_t nCount)
	{
		for (size_t nIdx = 0; nIdx < nCount; ++nIdx, ++pTrg)
		{
			*pTrg = tValue;
		}
	}

}
