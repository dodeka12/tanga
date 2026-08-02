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

#include "BasisN3.h"
#include "Multivector.h"

namespace Tan
{
	namespace GA
	{
		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Repesents a multivector in the conformal space embedding of 3D Euclidean space.
		/// 			Take e5 to have a negative signature. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template<typename _TValue>
		class _CMultivectorN3 : public _CMultivector<_TValue, typename _CBasisN3<_TValue>::TBlade>
		{
		public:

			typedef _TValue TValue;
			typedef _CBasisN3<_TValue> TBasis;
			typedef typename TBasis::TBlade TBlade;
			typedef _CMultivectorN3<TValue> TThis;
			typedef _CMultivector<TValue, TBlade> TBase;

		public:

			static const unsigned VectorSpaceDimension = TBasis::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = TBasis::VectorSpaceSignature;

			static const unsigned uSc = TBasis::uSc;
			static const unsigned uE1 = TBasis::uE1;
			static const unsigned uE2 = TBasis::uE2;
			static const unsigned uE3 = TBasis::uE3;
			static const unsigned uEp = TBasis::uEp;
			static const unsigned uEm = TBasis::uEm;
			static const unsigned uPs = TBasis::uPs;

		public:

			_CMultivectorN3(void)
			{
			}

			_CMultivectorN3(TValue fPrecision)
				: TBase(fPrecision)
			{
			}

			_CMultivectorN3(const TBase& wA)
			{
				CValuePrecision<TValue>::Reset();
				*this = wA;
			}

			template<unsigned t_uSubspaceDimension>
			_CMultivectorN3(const CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
				: TBase(wA)
			{
			}

			_CMultivectorN3(const tvec<TValue, TBlade::AlgebraDimension>& vA)
				: TBase(vA)
			{
			}

			_CMultivectorN3(const TValue(&pvalData)[TBlade::AlgebraDimension])
				: TBase(pvalData)
			{
			}

			template<unsigned t_uDim>
			_CMultivectorN3(const TValue(&pvalData)[t_uDim], const unsigned(&pBladeList)[t_uDim])
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
		class CMultivectorN3 : public _CMultivectorN3<_TValue>
		{
		public:

			static const unsigned VectorSpaceDimension = CBasisN3<_TValue>::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = CBasisN3<_TValue>::VectorSpaceSignature;

			static const unsigned uSc = CBasisN3<_TValue>::uSc;
			static const unsigned uE1 = CBasisN3<_TValue>::uE1;
			static const unsigned uE2 = CBasisN3<_TValue>::uE2;
			static const unsigned uE3 = CBasisN3<_TValue>::uE3;
			static const unsigned uEp = CBasisN3<_TValue>::uEp;
			static const unsigned uEm = CBasisN3<_TValue>::uEm;
			static const unsigned uPs = CBasisN3<_TValue>::uPs;

		public:

			typedef _TValue TValue;
			typedef typename CBasisN3<_TValue>::TBlade TBlade;
			typedef _CMultivector<TValue, TBlade> TMultivector;
			typedef _CMultivectorN3<TValue> TBase;
			typedef CMultivectorN3<TValue> TThis;

		public:

			CMultivectorN3(void)
			{
				CValuePrecision<TValue>::Reset();
			}

			CMultivectorN3(TValue fPrecision)
				: TBase(fPrecision)
			{
			}

			CMultivectorN3(const TMultivector& wA)
			{
				CValuePrecision<TValue>::Reset();
				*this = wA;
			}

			template<unsigned t_uSubspaceDimension>
			CMultivectorN3(const CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension>& wA)
				: TBase(wA)
			{
			}

			CMultivectorN3(const tvec<TValue, TBlade::AlgebraDimension>& vA)
				: TBase(vA)
			{
			}

			CMultivectorN3(const TValue(&pvalData)[TBlade::AlgebraDimension])
				: TBase(pvalData)
			{
			}

			template<unsigned t_uDim>
			CMultivectorN3(const TValue(&pvalData)[t_uDim], const unsigned(&pBladeList)[t_uDim])
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