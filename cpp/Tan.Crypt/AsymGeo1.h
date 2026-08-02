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

#include <vector>
#include <cstdint>

namespace Tan
{
	namespace Crypt
	{
		class CAsymGeo1
		{
		public:
			struct SPublicKey
			{
				uint32_t uVectorSpaceDimension;
				int64_t iValueHalfRange;
				int64_t iModulus;

				std::vector<int64_t> vecValue;
				std::vector<uint32_t> vecBladeIdx;
			};

			struct SPrivateKey
			{
				uint32_t uVectorSpaceDimension;
				int64_t iValueHalfRange;

				int64_t iModulusA;
				int64_t iModulusB;
				int64_t iModulusC;

				std::vector<int64_t> vecValueF;
				std::vector<uint32_t> vecBladeIdxF;
				std::vector<int64_t> vecValueE;
				std::vector<uint32_t> vecBladeIdxE;
			};

		public:
			typedef int64_t TValue;
			typedef uint32_t TBladeIdx;

		protected:
			

		public:
			CAsymGeo1();
			~CAsymGeo1();

			bool CreateKeyPair(unsigned uVecSpcDim, TValue tValueHalfRange, TValue tModulusMinOffset);
		};


	} // namespace Crypt
} // namespace Tan
