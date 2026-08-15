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
#pragma once

#include <cstdint>

#ifdef _MSC_VER
#	include <intrin.h>
#	include <nmmintrin.h>
#else
#	if defined(__x86_64__) || defined(__i386__)
#		include <x86intrin.h>
#		include <nmmintrin.h>
#	endif

	// GCC/Clang equivalents for MSVC bit-scan intrinsics.
	// Returns non-zero if a set bit was found, 0 if value is zero.
	inline unsigned char _BitScanReverse(unsigned long* idx, uint32_t val)
	{
		if (val == 0u) return 0;
		*idx = 31u - static_cast<unsigned long>(__builtin_clz(val));
		return 1;
	}

	inline unsigned char _BitScanReverse64(unsigned long* idx, uint64_t val)
	{
		if (val == 0u) return 0;
		*idx = 63u - static_cast<unsigned long>(__builtin_clzll(val));
		return 1;
	}
#endif

namespace Tan
{
	namespace Intrinsics
	{
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Calculate the number of bits set to 1 in the given value.
		/// </summary>
		///
		/// <param name="uValue"> The value. </param>
		///
		/// <returns> The total number of bits set to 1. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		inline unsigned CountOneBits(const unsigned& uValue)
		{
#ifdef _MSC_VER
			return _mm_popcnt_u32(uValue);
#else
			return __builtin_popcount(uValue);
#endif
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief
		/// 	Product will overflow
		///
		/// \param	iA	Zero-based index of a.
		/// \param	iB	Zero-based index of the b.
		///
		/// \return True if it succeeds, false if it fails.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		inline bool ProductWillOverflow(const int32_t& iA, const int32_t& iB)
		{
			uint32_t uA = static_cast<uint32_t>(iA < 0 ? -iA : iA);
			uint32_t uB = static_cast<uint32_t>(iB < 0 ? -iB : iB);

			unsigned long uMsbIdxA = 0, uMsbIdxB = 0;

			if (_BitScanReverse(&uMsbIdxA, uA) == 0 || _BitScanReverse(&uMsbIdxB, uB) == 0)
			{
				return false;
			}

			if (uMsbIdxA + uMsbIdxB >= 31)
			{
				return true;
			}

			return false;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief
		/// 	Product will overflow
		///
		/// \param	iA	Zero-based index of a.
		/// \param	iB	Zero-based index of the b.
		///
		/// \return True if it succeeds, false if it fails.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		inline bool ProductWillOverflow(const int64_t& iA, const int64_t& iB)
		{
			uint64_t uA = static_cast<uint64_t>(iA < 0 ? -iA : iA);
			uint64_t uB = static_cast<uint64_t>(iB < 0 ? -iB : iB);

			unsigned long uMsbIdxA = 0, uMsbIdxB = 0;

			if (_BitScanReverse64(&uMsbIdxA, uA) == 0 || _BitScanReverse64(&uMsbIdxB, uB) == 0)
			{
				return false;
			}

			if (uMsbIdxA + uMsbIdxB >= 63)
			{
				return true;
			}

			return false;
		}

		inline bool ProductWillOverflow(const float& fA, const float& iB)
		{
			// NOT IMPLEMENTED YET
			return false;
		}

		inline bool ProductWillOverflow(const double& fA, const double& iB)
		{
			// NOT IMPLEMENTED YET
			return false;
		}


		inline bool SumWillOverflow(const int32_t& iA, const int32_t& iB)
		{
			if ((iA < 0 && iB > 0) || (iA > 0 && iB < 0))
			{
				return false;
			}

			uint32_t uA = static_cast<uint32_t>(iA < 0 ? -iA : iA);
			uint32_t uB = static_cast<uint32_t>(iB < 0 ? -iB : iB);

			unsigned long uMsbIdxA = 0, uMsbIdxB = 0;

			if (_BitScanReverse64(&uMsbIdxA, uA) == 0 || _BitScanReverse64(&uMsbIdxB, uB) == 0)
			{
				return false;
			}

			if ((uMsbIdxA > uMsbIdxB ? uMsbIdxA : uMsbIdxB) >= 30)
			{
				return true;
			}

			return false;
		}


		inline bool SumWillOverflow(const int64_t& iA, const int64_t& iB)
		{
			if ((iA < 0 && iB > 0) || (iA > 0 && iB < 0))
			{
				return false;
			}

			uint64_t uA = static_cast<uint64_t>(iA < 0 ? -iA : iA);
			uint64_t uB = static_cast<uint64_t>(iB < 0 ? -iB : iB);

			unsigned long uMsbIdxA = 0, uMsbIdxB = 0;

			if (_BitScanReverse64(&uMsbIdxA, uA) == 0 || _BitScanReverse64(&uMsbIdxB, uB) == 0)
			{
				return false;
			}

			if ((uMsbIdxA > uMsbIdxB ? uMsbIdxA : uMsbIdxB) >= 62)
			{
				return true;
			}

			return false;
		}

		inline bool SumWillOverflow(const float& iA, const float& iB)
		{
			// NOT IMPLEMENTED
			return false;
		}

		inline bool SumWillOverflow(const double& iA, const double& iB)
		{
			// NOT IMPLEMENTED
			return false;
		}


	}
}
