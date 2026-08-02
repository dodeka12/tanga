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

namespace Tan
{
	namespace GA
	{
		enum class EResult
		{
			Success = 0,
			NotInvertible,
			InvalidComponentCongruence,
			InvalidComponentInverseCongruence,
		};

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Involution type applied to a multivector operand.
		/// </summary>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		enum class EInv : unsigned
		{
			Id = 0,	 ///< Identity – no involution
			Rev = 1, ///< Reverse:
			///< rev(blade) = (-1)^(k(k-1)/2) * blade
			Conj = 2, ///< Clifford conjugate:
					  ///< conj(blade) = rev(blade) * (-1)^r, where r = count of negative‑metric basis vectors
		};
	} // namespace GA
} // namespace Tan
