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


// Congruence classes
//
#pragma once

#include <functional>

#include "Tan.Core/Defines.h"
#include "InlineMath.h"

namespace Tan
{
	template<typename T>
	class CCongruence_Float
	{
	public:

		CCongruence_Float()
		{ }

		bool Map(T& tResult, const T& tValue) const
		{
			tResult = tValue;
			return true;
		}

		bool InvMap(T& tResult, const T& tValue) const
		{
			if (tValue == T(0))
			{
				return false;
			}

			tResult = T(1) / tValue;
			return true;
		}
	};

	template<typename T>
	class CCongruence_HMod
	{
	public:

		CCongruence_HMod()
		{
			m_tMod = T(1);
		}

		CCongruence_HMod(T tMod)
		{
			m_tMod = tMod;
		}

		bool Map(T& tResult, const T& tValue) const
		{
			tResult = Tan::hmod(tValue, m_tMod);
			return true;
		}

		bool InvMap(T& tResult, const T& tValue) const
		{
			tResult = Tan::hmod_inv(tValue, m_tMod);

			return tResult != T(0);
		}

	private:

		T m_tMod;
	};
}
