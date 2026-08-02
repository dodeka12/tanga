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

#include "Tan.Core/Defines.h"
#include "Tan.Core/IntrinsicFunctions.h"
#include "Tan.Core/StdAlgo.h"

namespace Tan
{
	namespace GA
	{
		template<typename T>
		class CBladeMask
		{
		public:

			typedef T TBlade;
			static const unsigned cm_uMaskDim       = ((TBlade::AlgebraDimension >> 5) + (TBlade::AlgebraDimension % 32 ? 1 : 0));	// Algebra Dimension / 32 + 1
			static const unsigned cm_uTopMaskBitCnt = (TBlade::AlgebraDimension >= 32 ? 32 : TBlade::AlgebraDimension);

		public:

			CBladeMask()
			{
				Reset();
			}

			CBladeMask(const CBladeMask<TBlade>& xMask)
			{
				*this = xMask;
			}

			CBladeMask<TBlade>& operator=(const CBladeMask<TBlade>& xMask)
			{
				MemCpy(m_puMask, xMask.m_puMask);
				return *this;
			}

			void Reset()
			{
				MemSet(m_puMask, 0U);
			}

			unsigned Count() const
			{
				unsigned uSum           = 0;
				const unsigned* puValue = m_puMask;

				for (unsigned uIdx = 0; uIdx < cm_uMaskDim; ++uIdx, ++puValue)
				{
					uSum += Intrinsics::CountOneBits(*puValue);
				}

				return uSum;
			}

			CBladeMask<TBlade>& operator<<(unsigned uBladeId)
			{
				Insert(TBlade(uBladeId));
				return *this;
			}

			CBladeMask<TBlade>& operator<<(const TBlade& blA)
			{
				Insert(blA);
				return *this;
			}

			bool Contains(const TBlade& blA) const
			{
				unsigned uMaskIdx;
				unsigned uBitMask;

				_GetMaskIdxBit(uMaskIdx, uBitMask, blA);
				return (m_puMask[uMaskIdx] & uBitMask) != 0;
			}

			void Insert(const TBlade& blA)
			{
				unsigned uMaskIdx;
				unsigned uBitMask;

				_GetMaskIdxBit(uMaskIdx, uBitMask, blA);
				m_puMask[uMaskIdx] |= uBitMask;
			}

			template<typename FuncOp>
			void ForEachBlade(FuncOp xFunc) const
			{
				TBlade blA(0U);
				const unsigned* puValue = m_puMask;
				for (unsigned uIdx = 0, uBitIdx = 0; uIdx < cm_uMaskDim; ++uIdx, ++puValue)
				{
					for (unsigned uSubBitIdx = 0, uBit = 1; uSubBitIdx < cm_uTopMaskBitCnt; ++uSubBitIdx, uBit <<= 1, ++blA)
					{
						if ((uBit & *puValue) != 0)
						{
							xFunc(uBitIdx, blA);
							++uBitIdx;
						}
					}
				}
			}

			template<typename FuncOp>
			bool ForEachBladeTest(FuncOp xFunc) const
			{
				TBlade blA(0U);
				const unsigned* puValue = m_puMask;
				for (unsigned uIdx = 0, uBitIdx = 0; uIdx < cm_uMaskDim; ++uIdx, ++puValue)
				{
					for (unsigned uSubBitIdx = 0, uBit = 1; uSubBitIdx < cm_uTopMaskBitCnt; ++uSubBitIdx, uBit <<= 1, ++blA)
					{
						if ((uBit & *puValue) != 0)
						{
							if (!xFunc(uBitIdx, blA))
							{
								return false;
							}

							++uBitIdx;
						}
					}
				}

				return true;
			}

			bool GetIndex(unsigned& uBladeIdx, const TBlade& blA) const
			{
				unsigned uMaskIdx;
				unsigned uBitMask;

				_GetMaskIdxBit(uMaskIdx, uBitMask, blA);

				uBladeIdx = 0;
				const unsigned* puValue = m_puMask;
				for (unsigned uIdx = 0; uIdx < uMaskIdx; ++uIdx, ++puValue)
				{
					uBladeIdx += Intrinsics::CountOneBits(*puValue);
				}

				unsigned uBit         = 1;
				const unsigned& uMask = m_puMask[uMaskIdx];

				for (unsigned uIdx = 0; uIdx < cm_uTopMaskBitCnt; ++uIdx, uBit <<= 1)
				{
					if ((uBit & uBitMask) != 0)
					{
						if ((uBit & uMask) != 0)
						{
							return true;
						}
						else
						{
							return false;
						}
					}

					if ((uBit & uMask) != 0)
					{
						++uBladeIdx;
					}
				}

				TAN_THROW_RT("Corrupted CBladeMask instance");
			}

			bool operator==(const CBladeMask<T>& xMask)
			{
				for (unsigned uIdx = 0; uIdx < cm_uMaskDim; ++uIdx)
				{
					if (m_puMask[uIdx] != xMask.m_puMask[uIdx])
					{
						return false;
					}
				}

				return true;
			}

			bool operator!=(const CBladeMask<T>& xMask)
			{
				return !operator==(xMask);
			}

		protected:

			void _GetMaskIdxBit(unsigned& uMaskIdx, unsigned& uBitMask, const TBlade& blA) const
			{
				const unsigned& uMaskPos = blA.GetId();
				uMaskIdx = uMaskPos >> 5;
				uBitMask = (1 << (uMaskPos & 31));
			}

		protected:

			unsigned m_puMask[cm_uMaskDim];
		};
	}
}	// .GA
