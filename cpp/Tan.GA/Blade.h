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
		template <unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
		class CBlade
		{
		public:
			using TBlade = CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>;
			using TBladeId = uint32_t;

		public:
			static const unsigned VectorSpaceDimension = t_uVectorSpaceDimension;
			static const unsigned VectorSpaceSignature = t_uVectorSpaceSignature;
			static const unsigned AlgebraDimension = (((unsigned int)1) << t_uVectorSpaceDimension);
			static const unsigned HighestBit = (((unsigned int)1) << (t_uVectorSpaceDimension - 1));
			static const unsigned PseudoScalarId = AlgebraDimension - 1;

		protected:
			TBladeId m_uBlade;

		public:
			CBlade(void)
			{
			}

			CBlade(const unsigned &uBlade)
			{
				m_uBlade = uBlade;
			}

			CBlade(const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &blA)
			{
				*this = blA;
			}

			CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &operator=(const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &blA)
			{
				m_uBlade = blA.m_uBlade;
				return *this;
			}

			void Reset()
			{
				m_uBlade = 0;
			}

			unsigned GetId() const
			{
				return m_uBlade;
			}

			static TBlade GetPseudoScalar()
			{
				return TBlade(PseudoScalarId);
			}

			unsigned GetReverseSign(unsigned &uGrade) const
			{
				GetGrade(uGrade);
				uGrade = uGrade >> 1;
				uGrade = uGrade & 1;
				return uGrade;
			}

			unsigned GetReverseSign() const
			{
				unsigned uGrade;
				return GetReverseSign(uGrade);
			}

			void GetGrade(unsigned &uGrade) const
			{
#ifndef __CUDACC__
				uGrade = Tan::Intrinsics::CountOneBits(m_uBlade);
#else
				uGrade = 0;
				_CountOneBits<HighestBit>(uGrade, m_uBlade);
#endif
			}

			unsigned GetGrade() const
			{
				unsigned uGrade;
				GetGrade(uGrade);
				return uGrade;
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Returns the number of negative squaring base vectors in the blade.
			/// </summary>
			///
			/// <param name="uGrade">	[in,out] The grade. </param>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			void GetGradeNeg(unsigned &uGrade, unsigned &uGradeNeg) const
			{
				uGrade = 0;
				uGradeNeg = 0;

				_EvalGradeNeg<HighestBit>(uGrade, uGradeNeg, m_uBlade);
			}

			unsigned GetGradeNeg() const
			{
				unsigned uGrade, uGradeNeg;
				GetGradeNeg(uGrade, uGradeNeg);
				return uGradeNeg;
			}

			unsigned GetConjugateSign(unsigned &uGrade, unsigned &uGradeNeg) const
			{
				GetGradeNeg(uGrade, uGradeNeg);

				return ((uGrade >> 1) & 1) ^ (uGradeNeg & 1);
			}

			unsigned GetConjugateSign() const
			{
				unsigned uGrade, uGradeNeg;
				return GetConjugateSign(uGrade, uGradeNeg);
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Gets the unsigned complement blade: the bitwise complement within
			/// 	the algebra (blade_id XOR pseudoscalar_id), with no sign change on
			/// 	the coefficient.
			///
			/// 	This is an involution: complement(complement(A)) = A for all
			/// 	dimensions and signatures, both in blade identity and coefficient
			/// 	value.
			///
			/// 	This is a purely combinatorial operation, NOT the Clifford dual.
			/// 	Use GetDual() for the geometrically correct dual ★A = A · I⁻¹.
			/// </summary>
			///
			/// <param name="blComplement">	[in,out] The complement blade mask.</param>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			void GetComplement(CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &blComplement) const
			{
				const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> blPS(GetPseudoScalar());
				blComplement.SetBlade(m_uBlade ^ blPS.GetId());
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Gets the unsigned complement blade and applies it to a coefficient
			/// 	value.  The blade is the bitwise complement within the algebra; the
			/// 	coefficient is unchanged.
			///
			/// 	complement(complement(A)) = A for all dimensions and signatures.
			/// </summary>
			///
			/// <typeparam name="TValue">	Type of the coefficient.</typeparam>
			/// <param name="fValue">	[in,out] The coefficient value (unchanged).</param>
			/// <param name="blComplement">	[in,out] The complement blade mask.</param>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			template <typename TValue>
			void GetComplement(TValue &fValue, CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &blComplement) const
			{
				// unsigned complement: only the blade changes, coefficient keeps its value
				GetComplement(blComplement);
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Gets the sign of the signed dual of this blade.
			///
			/// 	The signed dual is defined as ★A = A · I⁻¹, where the blade mask
			/// 	is the bitwise complement and the coefficient sign accounts for the
			/// 	geometric product with the inverse pseudoscalar.
			///
			/// 	The dual-of-dual may introduce a sign change depending on dimension
			/// 	and signature: ★★A = (−1)^(D(D−1)/2 + s) · A.
			/// </summary>
			///
			/// <param name="uSign"> 	[in,out] The sign (0 = positive, 1 = negative).</param>
			/// <param name="blDual">	[in,out] The dual blade mask.</param>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			void GetDualSign(unsigned &uSign, CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &blDual) const
			{
				const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> blPS(GetPseudoScalar());
				uSign = 0;

				GPSign(uSign, blDual, *this, blPS);
				uSign ^= blPS.GetConjugateSign();
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Gets the signed dual ★A = A · I⁻¹ of this blade.
			///
			/// 	The coefficient value is modified by the sign computed in
			/// 	GetDualSign(). The blade mask is the bitwise complement.
			///
			/// 	Use GetComplement() for the unsigned complement that is involutive
			/// 	for all dimensions and signatures.
			/// </summary>
			///
			/// <typeparam name="TValue">	Type of the coefficient.</typeparam>
			/// <param name="fValue">	[in,out] The coefficient value (may change sign).</param>
			/// <param name="blDual">	[in,out] The dual blade mask.</param>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			template <typename TValue>
			void GetDual(TValue &fValue, CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &blDual) const
			{
				unsigned uSign = 0;
				GetDualSign(uSign, blDual);

				if ((uSign & 1) != 0)
				{
					fValue = -fValue;
				}
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Gets the sign of the left dual I · A of this blade.
			///
			/// 	The left dual multiplies by the pseudoscalar from the left:
			/// 	I · A.  No inverse is used, so no conjugate sign correction
			/// 	is needed.  This is simpler than the (right) dual for algebras
			/// 	where the pseudoscalar is not invertible (e.g. PGA).
			/// </summary>
			///
			/// <param name="uSign"> 	[in,out] The sign (0 = positive, 1 = negative).</param>
			/// <param name="blDual">	[in,out] The left dual blade mask.</param>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			void GetLeftDualSign(unsigned &uSign, CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &blDual) const
			{
				const CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> blPS(GetPseudoScalar());
				uSign = 0;

				GPSign(uSign, blDual, blPS, *this);
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Gets the left dual I · A of this blade.
			///
			/// 	The coefficient value is modified by the sign computed in
			/// 	GetLeftDualSign(). The blade mask is the bitwise complement.
			/// 	No pseudoscalar inverse is used — this is direct left
			/// 	multiplication by I.
			/// </summary>
			///
			/// <typeparam name="TValue">	Type of the coefficient.</typeparam>
			/// <param name="fValue">	[in,out] The coefficient value (may change sign).</param>
			/// <param name="blDual">	[in,out] The left dual blade mask.</param>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			template <typename TValue>
			void GetLeftDual(TValue &fValue, CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &blDual) const
			{
				unsigned uSign = 0;
				GetLeftDualSign(uSign, blDual);

				if ((uSign & 1) != 0)
				{
					fValue = -fValue;
				}
			}

			void SetBlade(unsigned uBlade)
			{
				m_uBlade = uBlade;
			}

			void SetBaseVector(unsigned uBaseVectorIndex)
			{
				m_uBlade |= (1 << uBaseVectorIndex);
			}

			template <unsigned uDim>
			void SetBaseVector(unsigned (&puBaseVectorIndexList)[uDim])
			{
				for (unsigned i = 0; i < uDim; ++i)
				{
					SetBaseVector(puBaseVectorIndexList[i]);
				}
			}

			CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature> &operator++()
			{
				++m_uBlade;
				return *this;
			}

		protected:
			template <unsigned t_uBit>
			void _CountOneBits(unsigned &uCount, const unsigned &uBlade) const
			{
				if ((uBlade & t_uBit) != 0)
				{
					++uCount;
				}

				if constexpr ((t_uBit >> 1) != 0)
				{
					_CountOneBits<(t_uBit >> 1)>(uCount, uBlade);
				}
			}

			template <unsigned t_uBit>
			void _EvalGradeNeg(unsigned &uGrade, unsigned &uGradeNeg, const unsigned &uBlade) const
			{
				const unsigned uValue = (uBlade & t_uBit);

				if (uValue != 0)
				{
					++uGrade;
					if ((uValue & t_uVectorSpaceSignature) != 0)
					{
						++uGradeNeg;
					}
				}

				if constexpr ((t_uBit >> 1) != 0)
				{
					_EvalGradeNeg<(t_uBit >> 1)>(uGrade, uGradeNeg, uBlade);
				}
			}
		};
	}
} // namespace Tan.GA
