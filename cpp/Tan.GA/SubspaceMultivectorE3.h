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

#include "MultivectorE3.h"
#include "SubspaceMultivector.h"

namespace Tan
{
	namespace GA
	{
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 subspace multivector in GA over 3D Euclidean space.
		/// </summary>
		///
		/// <typeparam name="_TValue">			   	Type of the value. </typeparam>
		/// <typeparam name="t_uSubspaceDimension">	Type of the subspace dimension. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class _TValue, unsigned t_uSubspaceDimension>
		class _CSubspaceMultivectorE3
			: public _CSubspaceMultivector<_TValue, typename _CBasisE3<_TValue>::TBlade, t_uSubspaceDimension>
		{
		public:

			typedef _TValue TValue;
			typedef typename _CBasisE3<_TValue>::TBlade TBlade;
			typedef _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> TBase;
			typedef _CSubspaceMultivectorE3<TValue, t_uSubspaceDimension> TThis;

		public:

			static const unsigned VectorSpaceDimension = _CBasisE3<TValue>::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = _CBasisE3<TValue>::VectorSpaceSignature;
			static const unsigned SubspaceDimension    = t_uSubspaceDimension;

		public:

			_CSubspaceMultivectorE3(void)
			{
			}

			_CSubspaceMultivectorE3(TValue fPrecision)
				: TBase(fPrecision)
			{
			}

			_CSubspaceMultivectorE3(const TBase& wA)
				: TBase(wA)
			{
			}

			// template<typename TMultivectorX>
			// _CSubspaceMultivectorE3(const TMultivectorX& wA)
			// 	: TBase(wA)
			// {
			// }

			_CSubspaceMultivectorE3(const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
				: TBase(vBladeList)
			{
			}

			_CSubspaceMultivectorE3(const tvec<TValue, t_uSubspaceDimension>& vA, const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
				: TBase(vA, vBladeList)
			{
			}

			_CSubspaceMultivectorE3(const TValue(&pvalData)[t_uSubspaceDimension], const TBlade(&pBladeList)[t_uSubspaceDimension])
				: TBase(pvalData, pBladeList)
			{
			}

			TThis& operator=(const TBase& wA)
			{
				TBase::operator=(wA);
				return *this;
			}

			template<typename TMultivectorX>
			TThis& operator=(const TMultivectorX& wA)
			{
				TBase::operator=(wA);
				return *this;
			}
		};

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 subspace multivector in GA over 3D Euclidean space.
		/// </summary>
		///
		/// <typeparam name="_TValue">			   	Type of the value. </typeparam>
		/// <typeparam name="t_uSubspaceDimension">	Type of the subspace dimension. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class _TValue, unsigned t_uSubspaceDimension>
		class CSubspaceMultivectorE3
			: public _CSubspaceMultivectorE3<_TValue, t_uSubspaceDimension>
		{
		public:

			typedef _TValue TValue;
			typedef _CSubspaceMultivectorE3<_TValue, t_uSubspaceDimension> TBase;
			typedef CSubspaceMultivectorE3<_TValue, t_uSubspaceDimension> TThis;
			typedef typename TBase::TBlade TBlade;
			typedef _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> TBaseMultivector;

		public:

			static const unsigned VectorSpaceDimension = _CBasisE3<TValue>::VectorSpaceDimension;
			static const unsigned VectorSpaceSignature = _CBasisE3<TValue>::VectorSpaceSignature;
			static const unsigned SubspaceDimension    = t_uSubspaceDimension;

		public:

			CSubspaceMultivectorE3(void)
			{
				CValuePrecision<TValue>::Reset();
			}

			CSubspaceMultivectorE3(TValue fPrecision)
				: TBase(fPrecision)
			{
			}

			CSubspaceMultivectorE3(const TBaseMultivector& wA)
				: TBase(wA)
			{
			}

			CSubspaceMultivectorE3(const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
				: TBase(vBladeList)
			{
			}

			CSubspaceMultivectorE3(const tvec<TValue, t_uSubspaceDimension>& vA, const tvec<TBlade, t_uSubspaceDimension>& vBladeList)
				: TBase(vA, vBladeList)
			{
			}

			CSubspaceMultivectorE3(const TValue(&pvalData)[t_uSubspaceDimension], const TBlade(&pBladeList)[t_uSubspaceDimension])
				: TBase(pvalData, pBladeList)
			{
			}

			TThis& operator=(const TBaseMultivector& wA)
			{
				TBase::operator=(wA);
				return *this;
			}

			template<typename TMultivectorX>
			TThis& operator=(const TMultivectorX& wA)
			{
				TBase::operator=(wA);
				return *this;
			}
		};
	}
}	// namespace .GA
