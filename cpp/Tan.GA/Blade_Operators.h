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

#include <string>
#include <cstdint>

#include "Tan.Core/Defines.h"
#include "Tan.Core/IntrinsicFunctions.h"


namespace Tan
{
	namespace GA
	{
		template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature> class CBlade;

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Calculate geometric product and sign of product.
		/// </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <param name="uSign">	[in,out] The sign. </param>
		/// <param name="blC">  	[in,out] The bl c. </param>
		/// <param name="blA">  	The bl a. </param>
		/// <param name="blB">  	The bl b. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TBlade>
		bool GPSign(unsigned& uSign, TBlade& blC, const TBlade& blA, const TBlade& blB)
		{
			static const unsigned c_uSignature = TBlade::VectorSpaceSignature;

			// Calculate content of resultant blade without sign
			blC.SetBlade(blA.GetId() ^ blB.GetId());

			// Calculate sign changes due to signature of vector space
			unsigned uSig = c_uSignature & blA.GetId() & blB.GetId();

			// Calculate sign of resultant blade
			unsigned uS, uShift;

			// Find potential sign changes for all elements in blA
			//uShift = blA.GetBlade() << 1;
			uS     = 0;
			uShift = 0;
			for (unsigned i = TBlade::VectorSpaceDimension - 1; i > 0; --i)
			{
				uShift = (uShift << 1) | ((blA.GetId() >> i) & 1);
				uS    ^= uShift;
			}

			// Use only sign changes for those elements in blB that are actually present
			uS &= blB.GetId();

			#ifndef __CUDACC__
				unsigned uCnt = 0;

				// Count all bits in uS. If the number is even the sign is positive and otherwise negative.
				uCnt = Intrinsics::CountOneBits(uS);
				uS   = (uCnt & 1);

				// Count all bits in uSig. If the number is even the sign is positive and otherwise negative.
				uCnt = Intrinsics::CountOneBits(uSig);
				uSig = (uCnt & 1);
			#else
				unsigned uShift2;

				// XOR all bits in uS. This is the final sign.
				uShift = uS;
				// XOR all bits in sign changes due to signature
				uShift2 = uSig;

				for (unsigned i = 0; i < TBlade::VectorSpaceDimension - 1; ++i)
				{
					uShift >>= 1;
					uS      ^= uShift;

					uShift2 >>= 1;
					uSig     ^= uShift2;
				}

			#endif

			// Combine sign changes due to signature and base element swaps.
			uS ^= uSig;

			// Lowest bit of uS indicates whether blade product introduces a -1
			uSign = (uS & 1);

			return true;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Geometric Product of two blades
		/// </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <param name="valC">	[in,out] The value c. </param>
		/// <param name="blC"> 	[in,out] The bl c. </param>
		/// <param name="valA">	The value a. </param>
		/// <param name="blA"> 	The bl a. </param>
		/// <param name="valB">	The value b. </param>
		/// <param name="blB"> 	The bl b. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class TValueC, class TValueA, class TValueB, typename TBlade>
		bool GP(TValueC& valC, TBlade& blC, const TValueA& valA, const TBlade& blA, const TValueB& valB, const TBlade& blB)
		{
			unsigned uSign;
			if (!GPSign(uSign, blC, blA, blB))
			{
				return false;
			}

			// Lowest bit of uS indicates whether blade product introduces a -1
			TValueC valASign;

			if ((uSign & 1))
			{
				valASign = -TValueC(valA);
			}
			else
			{
				valASign = TValueC(valA);
			}

			TAN_TEST_PROD_OVERFLOW(TValueC(valA), TValueC(valB));

			valC = valASign * TValueC(valB);
			return true;
		}

		template<class TValueC, class TValueA, class TValueB, typename TBlade, typename TCongruence>
		bool GP(TValueC& valC, TBlade& blC, const TValueA& valA, const TBlade& blA, const TValueB& valB, const TBlade& blB, const TCongruence& xCongruence)
		{
			unsigned uSign;
			if (!GPSign(uSign, blC, blA, blB))
			{
				return false;
			}

			// Lowest bit of uS indicates whether blade product introduces a -1
			TValueC valASign;

			if ((uSign & 1))
			{
				valASign = -TValueC(valA);
			}
			else
			{
				valASign = TValueC(valA);
			}

			TValueC valTemp = valASign;
			xCongruence.Map(valASign, valTemp);

			TAN_TEST_PROD_OVERFLOW(TValueC(valA), TValueC(valB));

			xCongruence.Map(valC, valASign * TValueC(valB));
			return true;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	IP sign.
		/// </summary>
		///
		/// <typeparam name="typename TBlade">	Type of the typename t blade. </typeparam>
		/// <param name="uSign">	[in,out] The sign. </param>
		/// <param name="blC">  	[in,out] The bl c. </param>
		/// <param name="blA">  	The bl a. </param>
		/// <param name="blB">  	The bl b. </param>
		///
		/// <returns>	True if it succeeds, false if it fails. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TBlade>
		bool IPSign(unsigned& uSign, TBlade& blC, const TBlade& blA, const TBlade& blB)
		{
			// Check whether one of the blades is a scalar
			if ((blA.GetId() == 0) || (blB.GetId() == 0))
			{
				// Return zero blade
				return false;
			}

			// Check whether one blade is completely contained within the other
			const unsigned uValue = blA.GetId() & blB.GetId();

			// If this is not the case, then the result is zero.
			if ((uValue != blA.GetId()) && (uValue != blB.GetId()))
			{
				return false;
			}

			// If one blade is completely contained in the other and neither is
			// a scalar, then the result is equal to that of the geometric product.
			return GPSign(uSign, blC, blA, blB);
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Inner Product
		/// </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <param name="valC">	[in,out] The value c. </param>
		/// <param name="blC"> 	[in,out] The bl c. </param>
		/// <param name="valA">	The value a. </param>
		/// <param name="blA"> 	The bl a. </param>
		/// <param name="valB">	The value b. </param>
		/// <param name="blB"> 	The bl b. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class TValueC, class TValueA, class TValueB, typename TBlade>
		bool IP(TValueC& valC, TBlade& blC, const TValueA& valA, const TBlade& blA, const TValueB& valB, const TBlade& blB)
		{
			unsigned uSign;
			if (!IPSign(uSign, blC, blA, blB))
			{
				return false;
			}

			// Lowest bit of uS indicates whether blade product introduces a -1
			TValueC valASign;

			if ((uSign & 1))
			{
				valASign = -TValueC(valA);
			}
			else
			{
				valASign = TValueC(valA);
			}

			valC = valASign * TValueC(valB);
			return true;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	The outer product.
		/// </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <typeparam name="typename TBlade">	Type of the typename t blade. </typeparam>
		/// <param name="uSign">	[in,out] The value c. </param>
		/// <param name="blC">  	[in,out] The bl c. </param>
		/// <param name="blA">  	The bl a. </param>
		/// <param name="blB">  	The bl b. </param>
		///
		/// <returns>	True if it succeeds, false if it fails. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TBlade>
		bool OPSign(unsigned& uSign, TBlade& blC, const TBlade& blA, const TBlade& blB)
		{
			// Check whether blades are disjunct
			const unsigned uValue = blA.GetId() & blB.GetId();

			// If this is not the case, then the result is zero.
			if (uValue != 0)
			{
				blC.Reset();
				return false;
			}

			// If the blades are disjunct,
			// then the result is equal to that of the geometric product.
			return GPSign(uSign, blC, blA, blB);
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	The outer product.
		/// </summary>
		///
		/// <typeparam name="TValueC">		  	Type of the value c. </typeparam>
		/// <typeparam name="TValueA">		  	Type of the value a. </typeparam>
		/// <typeparam name="TValueB">		  	Type of the value b. </typeparam>
		/// <typeparam name="typename TBlade">	Type of the typename t blade. </typeparam>
		/// <param name="valC">	[in,out] The value c. </param>
		/// <param name="blC"> 	[in,out] The bl c. </param>
		/// <param name="valA">	The value a. </param>
		/// <param name="blA"> 	The bl a. </param>
		/// <param name="valB">	The value b. </param>
		/// <param name="blB"> 	The bl b. </param>
		///
		/// <returns>	True if it succeeds, false if it fails. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class TValueC, class TValueA, class TValueB, typename TBlade>
		bool OP(TValueC& valC, TBlade& blC, const TValueA& valA, const TBlade& blA, const TValueB& valB, const TBlade& blB)
		{
			unsigned uSign;
			if (!OPSign(uSign, blC, blA, blB))
			{
				valC = TValueC(0);
				blC.Reset();
				return false;
			}

			// Lowest bit of uS indicates whether blade product introduces a -1
			TValueC valASign;

			if ((uSign & 1))
			{
				valASign = -TValueC(valA);
			}
			else
			{
				valASign = TValueC(valA);
			}

			valC = valASign * TValueC(valB);
			return true;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief
		/// 	Return the sign introduced when commuting the two blades. That is, A B = sign B A.
		///
		/// \tparam	TBlade Type of the blade.
		/// \param	blA	The first blade.
		/// \param	blB	The second blade.
		///
		/// \return The sign when interchanging A and B wrt. the geometric product.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TBlade>
		unsigned GetCommuteSign(const TBlade& blA, const TBlade& blB)
		{
			// The blade that is contained in both blades.
			const unsigned uCommon = blA.GetId() & blB.GetId();

			// The number of elements that both blades have in common
			const unsigned uCommonCnt = Intrinsics::CountOneBits(uCommon);

			//// The blade uniquely contained in blade A.
			//const unsigned uUniqueA = blA.GetId() & (~uCommon);

			//// The number of elements that are uniquely contained in blade A
			//const unsigned uUniqueACnt = Intrinsics::CountOneBits(uUniqueA);

			// The total number of elements in blade A
			const unsigned uBitCntA = Intrinsics::CountOneBits(blA.GetId());

			// The total number of elements in blade B
			const unsigned uBitCntB = Intrinsics::CountOneBits(blB.GetId());

			// The number of basis element commutes, each of which introduces a '-1'.
			// Therefore, if uSign is odd, the resultant sign is negative, otherwise positive.
			//const unsigned uSign = uUniqueACnt * uBitCntB + uCommonCnt * (uBitCntB - 1);
			//const unsigned uSign = (uUniqueACnt + uCommonCnt) * uBitCntB - uCommonCnt;
			const unsigned uSign = uBitCntA * uBitCntB - uCommonCnt;

			// The resultant sign.
			return uSign & 1;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Equality operator on blades. </summary>
		///
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <param name="blA">	The bl a. </param>
		/// <param name="blB">	The bl b. </param>
		///
		/// <returns>	The result of the operation. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
		bool operator==(const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blA, const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blB)
		{
			return blA.GetId() == blB.GetId();
		}

		template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
		bool operator!=(const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blA, const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blB)
		{
			return blA.GetId() != blB.GetId();
		}

		template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
		bool operator<(const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blA, const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blB)
		{
			return blA.GetId() < blB.GetId();
		}

		template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
		bool operator>(const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blA, const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blB)
		{
			return blA.GetId() > blB.GetId();
		}

		template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
		bool operator<=(const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blA, const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blB)
		{
			return blA.GetId() <= blB.GetId();
		}

		template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
		bool operator>=(const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blA, const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>& blB)
		{
			return blA.GetId() >= blB.GetId();
		}
	}
}	// namespace Tan.GA
