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

#include "BasisP3.h"
#include "Multivector.h"

namespace Tan
{
	namespace GA
	{
		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Repesents a multivector in 3D Euclidean space.
		/// 			</summary>
		///
		/// <remarks>	Perwass, . </remarks>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename _TValue>
		class _CMultivectorP3 : public _CMultivector<_TValue, typename _CBasisP3<_TValue>::TBlade>
		{
		public:

			typedef _TValue TValue;
			typedef _CBasisP3<_TValue> TBasis;
			typedef typename TBasis::TBlade TBlade;
			typedef _CMultivectorP3<TValue> TThis;
			typedef _CMultivector<TValue, TBlade> TBase;

		public:

			static const unsigned VectorSpaceDimension = TBasis::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = TBasis::VectorSpaceSignature;

			static const unsigned uSc = TBasis::uSc;
			static const unsigned uE1 = TBasis::uE1;
			static const unsigned uE2 = TBasis::uE2;
			static const unsigned uE3 = TBasis::uE3;
			static const unsigned uE4 = TBasis::uE4;
			static const unsigned uPs = TBasis::uPs;

		public:

			_CMultivectorP3(void)
			{
			}

			_CMultivectorP3(TValue fPrecision)
				: TBase(fPrecision)
			{
			}

			_CMultivectorP3(const TBase& wA)
			{
				CValuePrecision<TValue>::Reset();
				*this = wA;
			}

			template<unsigned t_uSubspaceDimension>
			_CMultivectorP3(const CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
				: TBase(wA)
			{
			}

			_CMultivectorP3(const tvec<TValue, TBlade::AlgebraDimension>& vA)
				: TBase(vA)
			{
			}

			_CMultivectorP3(const TValue(&pvalData)[TBlade::AlgebraDimension])
				: TBase(pvalData)
			{
			}

			template<unsigned t_uDim>
			_CMultivectorP3(const TValue(&pvalData)[t_uDim], const unsigned(&pBladeList)[t_uDim])
				: TBase(pvalData, pBladeList)
			{
			}

			TThis& operator=(const TBase& wA)
			{
				TBase::operator=(wA);
				return *this;
			}

			template<unsigned t_uSubspaceDimension>
			TThis& operator=(const CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
			{
				TBase::operator=(wA);
				return *this;
			}

			template<typename TMultivectorA>
			TThis& operator=(const TMultivectorA& wA)
			{
				TBase::operator=(wA);
				return *this;
			}
		};

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 multivector n 3.
		/// </summary>
		///
		/// <typeparam name="_TValue">	Type of the value. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename _TValue>
		class CMultivectorP3 : public _CMultivectorP3<_TValue>
		{
		public:

			typedef _TValue TValue;
			typedef _CBasisP3<_TValue> TBasis;
			typedef typename TBasis::TBlade TBlade;
			typedef _CMultivector<TValue, TBlade> TMultivector;
			typedef _CMultivectorP3<TValue> TBase;
			typedef CMultivectorP3<TValue> TThis;

		public:

			static const unsigned VectorSpaceDimension = TBasis::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = TBasis::VectorSpaceSignature;

			static const unsigned uSc = TBasis::uSc;
			static const unsigned uE1 = TBasis::uE1;
			static const unsigned uE2 = TBasis::uE2;
			static const unsigned uE3 = TBasis::uE3;
			static const unsigned uE4 = TBasis::uE4;
			static const unsigned uPs = TBasis::uPs;

		public:

			CMultivectorP3(void)
			{
				CValuePrecision<TValue>::Reset();
			}

			CMultivectorP3(TValue fPrecision)
				: TBase(fPrecision)
			{
			}

			CMultivectorP3(const TMultivector& wA)
			{
				CValuePrecision<TValue>::Reset();
				*this = wA;
			}

			template<unsigned t_uSubspaceDimension>
			CMultivectorP3(const CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
				: TBase(wA)
			{
			}

			CMultivectorP3(const tvec<TValue, TBlade::AlgebraDimension>& vA)
				: TBase(vA)
			{
			}

			CMultivectorP3(const TValue(&pvalData)[TBlade::AlgebraDimension])
				: TBase(pvalData)
			{
			}

			template<unsigned t_uDim>
			CMultivectorP3(const TValue(&pvalData)[t_uDim], const unsigned(&pBladeList)[t_uDim])
				: TBase(pvalData, pBladeList)
			{
			}

			TThis& operator=(const TMultivector& wA)
			{
				TBase::operator=(wA);
				return *this;
			}

			template<unsigned t_uSubspaceDimension>
			TThis& operator=(const CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
			{
				TBase::operator=(wA);
				return *this;
			}

			template<typename TMultivectorA>
			TThis& operator=(const TMultivectorA& wA)
			{
				TBase::operator=(wA);
				return *this;
			}
		};
	}
}	// .GA
