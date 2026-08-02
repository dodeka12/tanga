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

#include <stdlib.h>
#include "Tan.Core/Defines.h"

namespace Tan
{
	template<typename TValue>
	class CValuePrecision
	{
	public:

		__HOSTDEV__ CValuePrecision() { }
		__HOSTDEV__ ~CValuePrecision() { }

		CValuePrecision(const TValue& dPrec)
		{
			m_dPrec = dPrec;
		}

		CValuePrecision(const CValuePrecision<TValue>& xValPrec)
		{
			*this = xValPrec;
		}

		__HOSTDEV__ TValue DefaultPrecision();

		__HOSTDEV__ void Reset()
		{
			m_dPrec = DefaultPrecision();	//std::numeric_limits<TValue>::epsilon();
		}

		__HOSTDEV__ CValuePrecision<TValue>& operator=(const CValuePrecision<TValue>& xValPrec)
		{
			m_dPrec = xValPrec.m_dPrec;
			return *this;
		}

		__HOSTDEV__ void SetValuePrecision(const TValue& dPrec)
		{
			m_dPrec = dPrec;
		}

		__HOSTDEV__ TValue GetValuePrecision() const
		{
			return m_dPrec;
		}

		__HOSTDEV__ bool IsZero(const TValue& dA) const
		{
			return dA >= -m_dPrec && dA <= m_dPrec;
		}

		__HOSTDEV__ bool IsEqual(const TValue& dA, const TValue& dB) const
		{
			return ::abs(dA - dB) <= m_dPrec;
		}

		__HOSTDEV__ bool IsUnity(const TValue& dA) const
		{
			return IsEqual(dA, TValue(1));
		}

		__HOSTDEV__ int Compare(const TValue& dA, const TValue& dB) const
		{
			TValue dDiff = dA - dB;
			if (dDiff < -m_dPrec)
			{
				return -1;
			}
			else if (dDiff > m_dPrec)
			{
				return 1;
			}
			else
			{
				return 0;
			}
		}

	protected:

		TValue m_dPrec;
	};
}
