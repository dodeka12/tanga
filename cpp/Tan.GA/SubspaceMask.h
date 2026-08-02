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

#include "Tan.Core/IntrinsicFunctions.h"

namespace Tan
{
	namespace GA
	{
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 subspace mask.
		/// </summary>
		///
		/// <typeparam name="T">	Generic type parameter. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename _TSubspaceBasis>
		class CSubspaceMask
		{
		public:

			typedef _TSubspaceBasis TSubspaceBasis;
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TBlade TBlade;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			typedef typename TSubspaceBasis::SBladePair TBladePair;
			typedef CSubspaceMask<TSubspaceBasis> TThis;

			static const unsigned AlgebraDimension  = TBlade::AlgebraDimension;
			static const unsigned cm_uMaskDim       = ((AlgebraDimension >> 5) + (AlgebraDimension % 32 ? 1 : 0));	// Algebra Dimension / 32 + 1
			static const unsigned cm_uTopMaskBitCnt = (AlgebraDimension >= 32 ? 32 : AlgebraDimension);

		public:

			CSubspaceMask()
			{
				Reset();
			}

			CSubspaceMask(const CSubspaceMask<TSubspaceBasis>& xMask)
			{
				*this = xMask;
			}

			CSubspaceMask<TSubspaceBasis>& operator=(const CSubspaceMask<TSubspaceBasis>& xMask)
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

			template<typename TMultivectorX>
			void Insert(const TMultivectorX& wBlade, const TSubspaceBasis& xBasis)
			{
				xBasis.ForEachBasisBladeIndex([&](const TMultivector& wBasisBlade, const TMultivector& wBasisRecip, size_t nBladeIdx) -> bool
						{
							_SetMaskBits(wBlade, wBasisRecip, unsigned(nBladeIdx));
							return true;
						});
			}

			void Insert(const TSubspaceBasis& xSubspace, const TSubspaceBasis& xBasis)
			{
				xSubspace.ForEachBasisBlade([&](const TMultivector& wBasisBlade, const TMultivector& wBasisRecip) -> bool
						{
							Insert(wBasisBlade, xBasis);
							return true;
						});
			}

			template<typename FuncOp>
			void ForEachBasisBladePair(const TSubspaceBasis& xBasis, FuncOp xFunc) const
			{
				unsigned uBladeIdx      = 0;
				const unsigned* puValue = m_puMask;
				for (unsigned uIdx = 0, uBitIdx = 0; uIdx < cm_uMaskDim; ++uIdx, ++puValue)
				{
					for (unsigned uSubBitIdx = 0, uBit = 1; uSubBitIdx < cm_uTopMaskBitCnt; ++uSubBitIdx, uBit <<= 1, ++uBladeIdx)
					{
						if ((uBit & *puValue) != 0)
						{
							xFunc(uBitIdx, xBasis[uBladeIdx].wBlade, xBasis[uBladeIdx].wRecipBlade);
							++uBitIdx;
						}
					}
				}
			}

			template<typename FuncOp>
			bool ForEachBasisBladePairTest(const TSubspaceBasis& xBasis, FuncOp xFunc) const
			{
				unsigned uBladeIdx      = 0;
				const unsigned* puValue = m_puMask;
				for (unsigned uIdx = 0, uBitIdx = 0; uIdx < cm_uMaskDim; ++uIdx, ++puValue)
				{
					for (unsigned uSubBitIdx = 0, uBit = 1; uSubBitIdx < cm_uTopMaskBitCnt; ++uSubBitIdx, uBit <<= 1, ++uBladeIdx)
					{
						if ((uBit & *puValue) != 0)
						{
							if (!xFunc(uBitIdx, xBasis[uBladeIdx].wBlade, xBasis[uBladeIdx].wRecipBlade))
							{
								return false;
							}

							++uBitIdx;
						}
					}
				}

				return true;
			}

			bool GetMaskBitIndex(unsigned& uMaskBitIdx, const TMultivector& wBasisBlade, const TSubspaceBasis& xBasis) const
			{
				TValue fValue;
				unsigned uMaskIdx;
				unsigned uBitMask;
				unsigned uBladeIdx;

				if (xBasis.ForEachBasisBladeIndexTest([&](const TMultivector& wBlade, const TMultivector& wRecipBlade, size_t uIdx) -> bool
						    {
							    GA::SP(fValue, wBlade, wRecipBlade);
							    if (!wRecipBlade.IsZero(fValue))
							    {
								    uBladeIdx = unsigned(uIdx);
								    return false;
							    }

							    return true;
						    }))
				{
					TAN_THROW_RT("Basis blade is not in given basis.");
				}

				_GetMaskIdxBit(uMaskIdx, uBitMask, uBladeIdx);

				uMaskBitIdx = 0;
				const unsigned* puValue = m_puMask;
				for (unsigned uIdx = 0; uIdx < uMaskIdx; ++uIdx, ++puValue)
				{
					uMaskBitIdx += Intrinsics::CountOneBits(*puValue);
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
						++uMaskBitIdx;
					}
				}

				TAN_THROW_RT("Corrupted CSubspaceMask instance");
			}

		protected:

			void _GetMaskIdxBit(unsigned& uMaskIdx, unsigned& uBitMask, const unsigned& uBladeIdx) const
			{
				uMaskIdx = uBladeIdx >> 5;
				uBitMask = (1 << (uBladeIdx & 31));
			}

			template<typename TMultivectorX>
			void _SetMaskBits(const TMultivectorX& wBlade, const TMultivector& wRecipBlade, unsigned uBladeIdx)
			{
				TValue fValue;
				GA::SP(fValue, wBlade, wRecipBlade);

				if (!wRecipBlade.IsZero(fValue))
				{
					unsigned uMaskIdx, uBitMask;
					_GetMaskIdxBit(uMaskIdx, uBitMask, uBladeIdx);
					m_puMask[uMaskIdx] |= uBitMask;
				}
			}

		protected:

			unsigned m_puMask[cm_uMaskDim];
		};
	}
}	// .GA
