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


// Vector Math functions for CUDA

#pragma once

// Include definition of sqrt if standard C compiler compiles this code
#if !defined(__NVCC__)
	#include <math.h>
#endif

#include "Tan.Core/Defines.h"
#include "InlineMath.h"
#include "FixedVectorTypes.h"

namespace Tan
{

	///////////////////////////////////////////////////////////////////////
	/// Scalar Product

	template<class T>
	__HDINL__ T dot(const tvec1<T>& vA, const tvec1<T>& vB)
	{
		return vA.x * vB.x;
	}

	template<class T>
	__HDINL__ T dot(const tvec2<T>& vA, const tvec2<T>& vB)
	{
		return vA.x * vB.x + vA.y * vB.y;
	}

	template<class T>
	__HDINL__ T dot(const tvec3<T>& vA, const tvec3<T>& vB)
	{
		return vA.x * vB.x + vA.y * vB.y + vA.z * vB.z;
	}

	template<class T>
	__HDINL__ T dot(const tvec4<T>& vA, const tvec4<T>& vB)
	{
		return vA.x * vB.x + vA.y * vB.y + vA.z * vB.z + vA.w * vB.w;
	}

	template<class T, const int t_iDim>
	__HDINL__ T dot(const tvec<T, t_iDim>& vA, const tvec<T, t_iDim>& vB)
	{
		return sum(vA * vB);
	}

	///////////////////////////
#if defined(__NVCC__)

	template<class T>
	__HDINL__ T dot(const float1& vA, const tvec1<T>& vB)
	{
		return vA.x * vB.x;
	}

	template<class T>
	__HDINL__ T dot(const float2& vA, const tvec2<T>& vB)
	{
		return vA.x * vB.x + vA.y * vB.y;
	}

	template<class T>
	__HDINL__ T dot(const float3& vA, const tvec3<T>& vB)
	{
		return vA.x * vB.x + vA.y * vB.y + vA.z * vB.z;
	}

	template<class T>
	__HDINL__ T dot(const float4& vA, const tvec4<T>& vB)
	{
		return vA.x * vB.x + vA.y * vB.y + vA.z * vB.z + vA.w * vB.w;
	}
	///////////////////////////

	template<class T>
	__HDINL__ T dot(const tvec1<T>& vA, const float1& vB)
	{
		return vA.x * vB.x;
	}

	template<class T>
	__HDINL__ T dot(const tvec2<T>& vA, const float2& vB)
	{
		return vA.x * vB.x + vA.y * vB.y;
	}

	template<class T>
	__HDINL__ T dot(const tvec3<T>& vA, const float3& vB)
	{
		return vA.x * vB.x + vA.y * vB.y + vA.z * vB.z;
	}

	template<class T>
	__HDINL__ T dot(const tvec4<T>& vA, const float4& vB)
	{
		return vA.x * vB.x + vA.y * vB.y + vA.z * vB.z + vA.w * vB.w;
	}

	///////////////////////////

	template<class T>
	__HDINL__ T dot(const float1& vA, const float1& vB)
	{
		return vA.x * vB.x;
	}

	template<class T>
	__HDINL__ T dot(const float2& vA, const float2& vB)
	{
		return vA.x * vB.x + vA.y * vB.y;
	}

	template<class T>
	__HDINL__ T dot(const float3& vA, const float3& vB)
	{
		return vA.x * vB.x + vA.y * vB.y + vA.z * vB.z;
	}

	template<class T>
	__HDINL__ T dot(const float4& vA, const float4& vB)
	{
		return vA.x * vB.x + vA.y * vB.y + vA.z * vB.z + vA.w * vB.w;
	}
#endif

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	Squares the given value.
	/// </summary>
	///
	/// <typeparam name="T">	Generic type parameter. </typeparam>
	/// <param name="tA">	The value. </param>
	///
	/// <returns>	The squared value. </returns>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T>
	__HDINL__ T square(const T& tA)
	{
		return tA * tA;
	}

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	Calculates square of each component of given vector (tvec1). This is a simple multiplication.
	/// </summary>
	///
	/// <typeparam name="T">	Generic type parameter. </typeparam>
	/// <param name="vA">  	The vector. </param>
	///
	/// <returns>	Square vector. </returns>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T>
	__HDINL__ tvec1<T> square(const tvec1<T>& vA)
	{
		return tvec1<T>(vA.x * vA.x);
	}

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	Calculates square of each component of given vector (tvec2). This is a simple multiplication.
	/// </summary>
	///
	/// <typeparam name="T">	Generic type parameter. </typeparam>
	/// <param name="vA">  	The vector. </param>
	///
	/// <returns>	Square vector. </returns>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T>
	__HDINL__ tvec2<T> square(const tvec2<T>& vA)
	{
		return tvec2<T>(vA.x * vA.x, vA.y * vA.y);
	}

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	Calculates square of each component of given vector (tvec3). This is a simple multiplication.
	/// </summary>
	///
	/// <typeparam name="T">	Generic type parameter. </typeparam>
	/// <param name="vA">  	The vector. </param>
	///
	/// <returns>	Square vector. </returns>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T>
	__HDINL__ tvec3<T> square(const tvec3<T>& vA)
	{
		return tvec3<T>(vA.x * vA.x, vA.y * vA.y, vA.z * vA.z);
	}

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	Calculates square of each component of given vector (tvec4). This is a simple multiplication.
	/// </summary>
	///
	/// <typeparam name="T">	Generic type parameter. </typeparam>
	/// <param name="vA">  	The vector. </param>
	///
	/// <returns>	Square vector. </returns>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T>
	__HDINL__ tvec4<T> square(const tvec4<T>& vA)
	{
		return tvec4<T>(vA.x * vA.x, vA.y * vA.y, vA.z * vA.z, vA.w * vA.w);
	}

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	Calculates square of each component of given vector (tvec). This is a simple multiplication.
	/// </summary>
	///
	/// <typeparam name="T">	Generic type parameter. </typeparam>
	/// <param name="vA">  	The vector. </param>
	///
	/// <returns>	Square vector. </returns>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> square(const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = vA.v[i] * vA.v[i];
		}

		return vX;
	}

	/////////////////////////////////////////////////////////////////////
	// SQRT

	template<class T>
	__HDINL__ tvec1<T> sqrt(const tvec1<T>& vA)
	{
		return tvec1<T>(::sqrt(vA.x));
	}

	template<class T>
	__HDINL__ tvec2<T> sqrt(const tvec2<T>& vA)
	{
		return tvec2<T>(::sqrt(vA.x), ::sqrt(vA.y));
	}

	template<class T>
	__HDINL__ tvec3<T> sqrt(const tvec3<T>& vA)
	{
		return tvec3<T>(::sqrt(vA.x), ::sqrt(vA.y), ::sqrt(vA.z));
	}

	template<class T>
	__HDINL__ tvec4<T> sqrt(const tvec4<T>& vA)
	{
		return tvec4<T>(::sqrt(vA.x), ::sqrt(vA.y), ::sqrt(vA.z), ::sqrt(vA.w));
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> sqrt(const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = ::sqrt(vA.v[i]);
		}

		return vX;
	}

	///////////////////////////////////////////////////////////////////////
	// Length Square

	template<class T>
	__HDINL__ T length_square(const tvec1<T>& vA)
	{
		return vA.x * vA.x;
	}

	template<class T>
	__HDINL__ T length_square(const tvec2<T>& vA)
	{
		return vA.x * vA.x + vA.y * vA.y;
	}

	template<class T>
	__HDINL__ T length_square(const tvec3<T>& vA)
	{
		return vA.x * vA.x + vA.y * vA.y + vA.z * vA.z;
	}

	template<class T>
	__HDINL__ T length_square(const tvec4<T>& vA)
	{
		return vA.x * vA.x + vA.y * vA.y + vA.z * vA.z + vA.w * vA.w;
	}

	template<class T, const int t_iDim>
	__HDINL__ T length_square(const tvec<T, t_iDim>& vA)
	{
		return dot(vA, vA);
	}

	///////////////////////////////////////////////////////////////////////
	// Length

	template<class T>
	__HDINL__ T length(const tvec1<T>& vA)
	{
		return vA.x;
	}

	template<class T>
	__HDINL__ T length(const tvec2<T>& vA)
	{
		return ::sqrt(vA.x * vA.x + vA.y * vA.y);
	}

	template<class T>
	__HDINL__ T length(const tvec3<T>& vA)
	{
		return ::sqrt(vA.x * vA.x + vA.y * vA.y + vA.z * vA.z);
	}

	template<class T>
	__HDINL__ T length(const tvec4<T>& vA)
	{
		return ::sqrt(vA.x * vA.x + vA.y * vA.y + vA.z * vA.z + vA.w * vA.w);
	}

	template<class T, const int t_iDim>
	__HDINL__ T length(const tvec<T, t_iDim>& vA)
	{
		return ::sqrt(dot(vA, vA));
	}


#if defined(__NVCC__)

	__HDINL__ float length(const float1& vA)
	{
		return vA.x;
	}

	__HDINL__ float length(const float2& vA)
	{
		return ::sqrt(vA.x * vA.x + vA.y * vA.y);
	}

	__HDINL__ float length(const float3& vA)
	{
		return ::sqrt(vA.x * vA.x + vA.y * vA.y + vA.z * vA.z);
	}

	__HDINL__ float length(const float4& vA)
	{
		return ::sqrt(vA.x * vA.x + vA.y * vA.y + vA.z * vA.z + vA.w * vA.w);
	}

#endif
	///////////////////////////////////////////////////////////////////////
	// CrossRatio

	// get cross ratio of points A->B->C->D

	template<class T>
	__HDINL__ T CrossRatio(const tvec2<T>& vecA, const tvec2<T>& vecB, const tvec2<T>& vecC, const tvec2<T>& vecD)
	{
		const float fAC = length(vecC - vecA);
		const float fBD = length(vecD - vecB);
		const float fBC = length(vecC - vecB);
		const float fAD = length(vecD - vecA);

		return fAC * fBD / (fBC * fAD);
	}

	///////////////////////////////////////////////////////////////////////
	// Distance

	template<class T>
	__HDINL__ T distance(const tvec1<T>& vA, const tvec1<T>& vB)
	{
		return length(vA - vB);
	}

	template<class T>
	__HDINL__ T distance(const tvec2<T>& vA, const tvec2<T>& vB)
	{
		return length(vA - vB);
	}

	template<class T>
	__HDINL__ T distance(const tvec3<T>& vA, const tvec3<T>& vB)
	{
		return length(vA - vB);
	}

	template<class T>
	__HDINL__ T distance(const tvec4<T>& vA, const tvec4<T>& vB)
	{
		return length(vA - vB);
	}

	template<class T, const int t_iDim>
	__HDINL__ T distance(const tvec<T, t_iDim>& vA, const tvec<T, t_iDim>& vB)
	{
		return length(vA - vB);
	}

	///////////////////////////////////////////////////////////////////////
	// Distance Square

	template<class T>
	__HDINL__ T distance_square(const tvec1<T>& vA, const tvec1<T>& vB)
	{
		return sum(square(vA - vB));
	}

	template<class T>
	__HDINL__ T distance_square(const tvec2<T>& vA, const tvec2<T>& vB)
	{
		return sum(square(vA - vB));
	}

	template<class T>
	__HDINL__ T distance_square(const tvec3<T>& vA, const tvec3<T>& vB)
	{
		return sum(square(vA - vB));
	}

	template<class T>
	__HDINL__ T distance_square(const tvec4<T>& vA, const tvec4<T>& vB)
	{
		return sum(square(vA - vB));
	}

	template<class T, const int t_iDim>
	__HDINL__ T distance_square(const tvec<T, t_iDim>& vA, const tvec<T, t_iDim>& vB)
	{
		return sum(square(vA - vB));
	}

	/////////////////////////////////////////////////////////////////////
	// Determinant of matrix created from a number of vectors

	template<class T>
	__HDINL__ T det(const tvec1<T>& vA)
	{
		return vA.x;
	}

	template<class T>
	__HDINL__ T det(const tvec2<T>& vA, const tvec2<T>& vB)
	{
		return vA.x * vB.y - vA.y * vB.x;
	}

	template<class T>
	__HDINL__ T det(const tvec3<T>& vA, const tvec3<T>& vB, const tvec3<T>& vC)
	{
		return vA.x * (vB.y * vC.z - vB.z * vA.y)
			   + vA.y * (vB.z * vC.x - vB.x * vC.z)
			   + vA.z * (vB.x * vC.y - vB.y * vC.x);
	}

	/////////////////////////////////////////////////////////////////////
	// Normalize

	template<class TVec>
	__HDINL__ TVec normalize(const TVec& vA)
	{
		return vA / length(vA);
	}

	/////////////////////////////////////////////////////////////////////
	// POW

	template<class T>
	__HDINL__ tvec1<T> pow(const tvec1<T>& vA, T tPow)
	{
		return tvec1<T>(::pow(vA.x, tPow));
	}

	template<class T>
	__HDINL__ tvec2<T> pow(const tvec2<T>& vA, T tPow)
	{
		return tvec2<T>(::pow(vA.x, tPow), ::pow(vA.y, tPow));
	}

	template<class T>
	__HDINL__ tvec3<T> pow(const tvec3<T>& vA, T tPow)
	{
		return tvec3<T>(::pow(vA.x, tPow), ::pow(vA.y, tPow), ::pow(vA.z, tPow));
	}

	template<class T>
	__HDINL__ tvec4<T> pow(const tvec4<T>& vA, T tPow)
	{
		return tvec4<T>(::pow(vA.x, tPow), ::pow(vA.y, tPow), ::pow(vA.z, tPow), ::pow(vA.w, tPow));
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> pow(const tvec<T, t_iDim>& vA, T tPow)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = ::pow(vA.v[i], tPow);
		}

		return vX;
	}

	/////////////////////////////////////////////////////////////////////
	/// Floor

	template<class T>
	__HDINL__ tvec1<T> floor(const tvec1<T>& vA)
	{
		return tvec1<T>(T(::floor(vA.x)));
	}

	template<class T>
	__HDINL__ tvec2<T> floor(const tvec2<T>& vA)
	{
		return tvec2<T>(T(::floor(vA.x)), T(::floor(vA.y)));
	}

	template<class T>
	__HDINL__ tvec3<T> floor(const tvec3<T>& vA)
	{
		return tvec3<T>(T(::floor(vA.x)), T(::floor(vA.y)), T(::floor(vA.z)));
	}

	template<class T>
	__HDINL__ tvec4<T> floor(const tvec4<T>& vA)
	{
		return tvec4<T>(T(::floor(vA.x)), T(::floor(vA.y)), T(::floor(vA.z)), T(::floor(vA.w)));
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> floor(const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = ::floor(vA.v[i]);
		}

		return vX;
	}

	/////////////////////////////////////////////////////////////////////
	/// Ceiling

	template<class T>
	__HDINL__ tvec1<T> ceil(const tvec1<T>& vA)
	{
		return tvec1<T>(T(::ceil(vA.x)));
	}

	template<class T>
	__HDINL__ tvec2<T> ceil(const tvec2<T>& vA)
	{
		return tvec2<T>(T(::ceil(vA.x)), T(::ceil(vA.y)));
	}

	template<class T>
	__HDINL__ tvec3<T> ceil(const tvec3<T>& vA)
	{
		return tvec3<T>(T(::ceil(vA.x)), T(::ceil(vA.y)), T(::ceil(vA.z)));
	}

	template<class T>
	__HDINL__ tvec4<T> ceil(const tvec4<T>& vA)
	{
		return tvec4<T>(T(::ceil(vA.x)), T(::ceil(vA.y)), T(::ceil(vA.z)), T(::ceil(vA.w)));
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> ceil(const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = ::ceil(vA.v[i]);
		}

		return vX;
	}

	/////////////////////////////////////////////////////////////////////
	/// Abs

	template<class T>
	__HDINL__ tvec1<T> abs(const tvec1<T>& vA)
	{
		return tvec1<T>(T(::abs(vA.x)));
	}

	template<class T>
	__HDINL__ tvec2<T> abs(const tvec2<T>& vA)
	{
		return tvec2<T>(T(::abs(vA.x)), T(::abs(vA.y)));
	}

	template<class T>
	__HDINL__ tvec3<T> abs(const tvec3<T>& vA)
	{
		return tvec3<T>(T(::abs(vA.x)), T(::abs(vA.y)), T(::abs(vA.z)));
	}

	template<class T>
	__HDINL__ tvec4<T> abs(const tvec4<T>& vA)
	{
		return tvec4<T>(T(::abs(vA.x)), T(::abs(vA.y)), T(::abs(vA.z)), T(::abs(vA.w)));
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> abs(const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = ::abs(vA.v[i]);
		}

		return vX;
	}

	/////////////////////////////////////////////////////////////////////
	/// Round vector to given number of decimal places

	template<class T>
	__HDINL__ tvec1<T> round(const tvec1<T>& vA, int iDec)
	{
		return tvec1<T>(T(round(vA.x, iDec)));
	}

	template<class T>
	__HDINL__ tvec2<T> round(const tvec2<T>& vA, int iDec)
	{
		return tvec2<T>(T(round(vA.x, iDec)), T(round(vA.y, iDec)));
	}

	template<class T>
	__HDINL__ tvec3<T> round(const tvec3<T>& vA, int iDec)
	{
		return tvec3<T>(T(round(vA.x, iDec)), T(round(vA.y, iDec)), T(round(vA.z, iDec)));
	}

	template<class T>
	__HDINL__ tvec4<T> round(const tvec4<T>& vA, int iDec)
	{
		return tvec4<T>(T(round(vA.x, iDec)), T(round(vA.y, iDec)), T(round(vA.z, iDec)), T(round(vA.w, iDec)));
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> round(const tvec<T, t_iDim>& vA, int iDec)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = round(vA.v[i], iDec);
		}

		return vX;
	}

	/////////////////////////////////////////////////////////////////////
	/// Round floating point to integer

	template<class T>
	__HDINL__ tvec1<int> rint(const tvec1<T>& vA)
	{
		return tvec1<int>(rint(vA.x));
	}

	template<class T>
	__HDINL__ tvec2<int> rint(const tvec2<T>& vA)
	{
		return tvec2<int>(rint(vA.x), rint(vA.y));
	}

	template<class T>
	__HDINL__ tvec3<int> rint(const tvec3<T>& vA)
	{
		return tvec3<int>(rint(vA.x), rint(vA.y), rint(vA.z));
	}

	template<class T>
	__HDINL__ tvec4<int> rint(const tvec4<T>& vA)
	{
		return tvec4<int>(rint(vA.x), rint(vA.y), rint(vA.z), rint(vA.w));
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<int, t_iDim> rint(const tvec<T, t_iDim>& vA)
	{
		tvec<int, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = rint(vA.v[i]);
		}

		return vX;
	}

	/////////////////////////////////////////////////////////////////////
	/// Clamp vector to given range

	template<class T>
	__HDINL__ tvec1<T> clamp(const tvec1<T>& vA, T tMin, T tMax)
	{
		return tvec1<T>(clamp(vA.x, tMin, tMax));
	}

	template<class T>
	__HDINL__ tvec2<T> clamp(const tvec2<T>& vA, T tMin, T tMax)
	{
		return tvec2<T>(clamp(vA.x, tMin, tMax), clamp(vA.y, tMin, tMax));
	}

	template<class T>
	__HDINL__ tvec3<T> clamp(const tvec3<T>& vA, T tMin, T tMax)
	{
		return tvec3<T>(clamp(vA.x, tMin, tMax), clamp(vA.y, tMin, tMax), clamp(vA.z, tMin, tMax));
	}

	template<class T>
	__HDINL__ tvec4<T> clamp(const tvec4<T>& vA, T tMin, T tMax)
	{
		return tvec4<T>(clamp(vA.x, tMin, tMax), clamp(vA.y, tMin, tMax), clamp(vA.z, tMin, tMax), clamp(vA.w, tMin, tMax));
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> clamp(const tvec<T, t_iDim>& vA, T tMin, T tMax)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = clamp(vA.v[i], tMin, tMax);
		}

		return vX;
	}

	template<class T>
	__HDINL__ tvec1<T> clamp(const tvec1<T>& vA, const tvec1<T>& vMin, const tvec1<T>& vMax)
	{
		return tvec1<T>(clamp(vA.x, vMin.x, vMax.x));
	}

	template<class T>
	__HDINL__ tvec2<T> clamp(const tvec2<T>& vA, const tvec2<T>& vMin, const tvec2<T>& vMax)
	{
		return tvec2<T>(clamp(vA.x, vMin.x, vMax.x), clamp(vA.y, vMin.y, vMax.y));
	}

	template<class T>
	__HDINL__ tvec3<T> clamp(const tvec3<T>& vA, const tvec3<T>& vMin, const tvec3<T>& vMax)
	{
		return tvec3<T>(clamp(vA.x, vMin.x, vMax.x), clamp(vA.y, vMin.y, vMax.y), clamp(vA.z, vMin.z, vMax.z));
	}

	template<class T>
	__HDINL__ tvec4<T> clamp(const tvec4<T>& vA, const tvec4<T>& vMin, const tvec4<T>& vMax)
	{
		return tvec4<T>(clamp(vA.x, vMin.x, vMax.x), clamp(vA.y, vMin.y, vMax.y), clamp(vA.z, vMin.z, vMax.z), clamp(vA.w, vMin.w, vMax.w));
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> clamp(const tvec<T, t_iDim>& vA, const tvec<T, t_iDim>& vMin, const tvec<T, t_iDim>& vMax)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = clamp(vA.v[i], vMin.v[i], vMax.v[i]);
		}

		return vX;
	}

	template<class T>
	__HDINL__ double point_to_line_distance(const tvec2<T>& vPnt, const tvec2<double>& vLinePnt1, const tvec2<double>& vLinePnt2)
	{
		tvec2<double> vVecToLine, vDirLine;

		// Vector from point to point 1 on line
		vVecToLine = vPnt - vLinePnt1;

		// Direction of line
		vDirLine  = vLinePnt2 - vLinePnt1;
		vDirLine /= length(vDirLine);

		// Vector from point to line in direction perpendicular to line
		vVecToLine -= dot(vVecToLine, vDirLine) * vDirLine;

		return length(vVecToLine);
	}

	/// @}
}	// namespace Tan
