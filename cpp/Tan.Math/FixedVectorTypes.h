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

#include "Tan.Core/Defines.h"


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// namespace: Tan
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
namespace Tan
{
	template<class T> struct tvec3;
	template<class T> struct tvec4;


	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	1D Vector class.
	/// </summary>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T>
	struct tvec1
	{
		typedef T TDataType;

		__HDINL__ tvec1()
		{
		}		//{ x = T(0); }

		__HDINL__ explicit tvec1(T _x)
		{
			x = _x;
		}

		__HDINL__ explicit tvec1(const tvec4<T>& vX)
		{
			x = vX.x;
		}

		//__HDINL__ tvec1( const tvec1<T>& vA ) { x = vA.x; }

		template<class T2>
		__HDINL__ explicit tvec1(const tvec1<T2>& vA)
		{
			x = T(vA.x);
		}

#if defined(__NVCC__)
		__HDINL__ explicit tvec1(const float1& fX)
		{
			x = T(fX.x);
		}

		__HDINL__ explicit tvec1(const float2& fX)
		{
			x = T(fX.x);
		}

		__HDINL__ explicit tvec1(const float3& fX)
		{
			x = T(fX.x);
		}

		__HDINL__ explicit tvec1(const float4& fX)
		{
			x = T(fX.x);
		}

		__HDINL__ explicit tvec1(const int1& fX)
		{
			x = T(fX.x);
		}

		__HDINL__ explicit tvec1(const int2& fX)
		{
			x = T(fX.x);
		}

		__HDINL__ explicit tvec1(const int3& fX)
		{
			x = T(fX.x);
		}

		__HDINL__ explicit tvec1(const int4& fX)
		{
			x = T(fX.x);
		}

		__HDINL__ tvec1<T>& operator=(const float1& fX)
		{
			x = T(fX.x);
			return *this;
		}
#endif
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Cast each element of this vector to the desired data type and returns the new vector.
		/// </summary>
		///
		/// <typeparam name="T2"> Generic type parameter. </typeparam>
		///
		/// <returns> The casted vector. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class T2>
		__HDINL__ tvec1<T2> Cast() const
		{
			tvec1<T2> vecCast;
			vecCast.x = T2(x);

			return vecCast;
		}

		__HDINL__ tvec1<T>& zero()
		{
			x = T(0);
			return *this;
		}

		__HDINL__ tvec1<T>& operator+=(const tvec1<T>& vA)
		{
			x += vA.x;
			return *this;
		}

		__HDINL__ tvec1<T>& operator-=(const tvec1<T>& vA)
		{
			x -= vA.x;
			return *this;
		}

		__HDINL__ tvec1<T>& operator*=(const tvec1<T>& vA)
		{
			x *= vA.x;
			return *this;
		}

		__HDINL__ tvec1<T>& operator/=(const tvec1<T>& vA)
		{
			x /= vA.x;
			return *this;
		}

		__HDINL__ tvec1<T>& operator*=(const T& tVal)
		{
			x *= tVal;
			return *this;
		}

		__HDINL__ tvec1<T>& operator/=(const T& tVal)
		{
			x /= tVal;
			return *this;
		}

		__HDINL__ tvec1<T>& operator+=(const T& tVal)
		{
			x += tVal;
			return *this;
		}

		__HDINL__ tvec1<T>& operator-=(const T& tVal)
		{
			x -= tVal;
			return *this;
		}

		T x;
	};

#if defined(__NVCC__)
	template<class T>
	__HDINL__ float1 make_float1(const tvec1<T>& vA)
	{
		return ::make_float1(vA.x);
	}
#endif

	template<class T>
	__HDINL__ tvec1<T> operator-(const tvec1<T>& vA)
	{
		return tvec1<T>(-vA.x);
	}

	template<class T>
	__HDINL__ tvec1<T> operator+(const tvec1<T>& vA, const tvec1<T>& vB)
	{
		return tvec1<T>(vA.x + vB.x);
	}

	template<class T>
	__HDINL__ tvec1<T> operator-(const tvec1<T>& vA, const tvec1<T>& vB)
	{
		return tvec1<T>(vA.x - vB.x);
	}

	template<class T>
	__HDINL__ tvec1<T> operator*(const tvec1<T>& vA, const tvec1<T>& vB)
	{
		return tvec1<T>(vA.x * vB.x);
	}

	template<class T>
	__HDINL__ tvec1<T> operator/(const tvec1<T>& vA, const tvec1<T>& vB)
	{
		return tvec1<T>(vA.x / vB.x);
	}

	template<class T>
	__HDINL__ tvec1<T> operator*(const tvec1<T>& vA, const T& tVal)
	{
		return tvec1<T>(vA.x * tVal);
	}

	template<class T>
	__HDINL__ tvec1<T> operator*(const T& tVal, const tvec1<T>& vA)
	{
		return tvec1<T>(tVal * vA.x);
	}

	template<class T>
	__HDINL__ tvec1<T> operator/(const tvec1<T>& vA, const T& tVal)
	{
		return tvec1<T>(vA.x / tVal);
	}

	template<class T>
	__HDINL__ tvec1<T> operator/(const T& tVal, const tvec1<T>& vA)
	{
		return tvec1<T>(tVal / vA.x);
	}

	template<class T>
	__HDINL__ tvec1<T> operator+(const tvec1<T>& vA, const T& tVal)
	{
		return tvec1<T>(vA.x + tVal);
	}

	template<class T>
	__HDINL__ tvec1<T> operator+(const T& tVal, const tvec1<T>& vA)
	{
		return tvec1<T>(tVal + vA.x);
	}

	template<class T>
	__HDINL__ tvec1<T> operator-(const tvec1<T>& vA, const T& tVal)
	{
		return tvec1<T>(vA.x - tVal);
	}

	template<class T>
	__HDINL__ tvec1<T> operator-(const T& tVal, const tvec1<T>& vA)
	{
		return tvec1<T>(tVal - vA.x);
	}

	template<class T>
	__HDINL__ T sum(const tvec1<T>& vA)
	{
		return vA.x;
	}

	template<class T>
	bool IsNumber(const tvec1<T>& vA)
	{
		return IsNumber(vA.x);
	}

	template<class T>
	bool IsFiniteNumber(const tvec1<T>& vA)
	{
		return IsFiniteNumber(vA.x);
	}

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	2D Vector class.
	/// </summary>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T>
	struct _tvec2
	{
		__HDINL__ _tvec2<T>& zero()
		{
			x = T(0);
			y = T(0);
			return *this;
		}

		__HDINL__ _tvec2<T>& operator+=(const _tvec2<T>& vA)
		{
			x += vA.x;
			y += vA.y;
			return *this;
		}

		__HDINL__ _tvec2<T>& operator-=(const _tvec2<T>& vA)
		{
			x -= vA.x;
			y -= vA.y;
			return *this;
		}

		__HDINL__ _tvec2<T>& operator*=(const _tvec2<T>& vA)
		{
			x *= vA.x;
			y *= vA.y;
			return *this;
		}

		__HDINL__ _tvec2<T>& operator/=(const _tvec2<T>& vA)
		{
			x /= vA.x;
			y /= vA.y;
			return *this;
		}

		__HDINL__ _tvec2<T>& operator*=(const T& tVal)
		{
			x *= tVal;
			y *= tVal;
			return *this;
		}

		__HDINL__ _tvec2<T>& operator/=(const T& tVal)
		{
			x /= tVal;
			y /= tVal;
			return *this;
		}

		__HDINL__ _tvec2<T>& operator+=(const T& tVal)
		{
			x += tVal;
			y += tVal;
			return *this;
		}

		__HDINL__ _tvec2<T>& operator-=(const T& tVal)
		{
			x -= tVal;
			y -= tVal;
			return *this;
		}

		__HDINL__ T& operator[](int iIdx)
		{
			if (iIdx == 1)
			{
				return y;
			}

			return x;
		}

		//second major full order...
		__HDINL__ bool operator<(const _tvec2<T>& vA) const
		{
			return (y < vA.y) || ((y == vA.y) && (x < vA.x));
		}

		__HDINL__ bool operator==(const _tvec2<T>& vA) const
		{
			return (x == vA.x) && (y == vA.y);
		}

		__HDINL__ bool operator!=(const _tvec2<T>& vA) const
		{
			return (x != vA.x) || (y != vA.y);
		}

		T x, y;
	};

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	2D Vector class.
	/// </summary>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T>
	struct tvec2 : _tvec2<T>
	{
		typedef T TDataType;

		__HDINL__ tvec2()
		{
		}

		__HDINL__ tvec2(const _tvec2<T>& _v2)
		{
			this->x = _v2.x;
			this->y = _v2.y;
		}

		__HDINL__ explicit tvec2(T _x, T _y)
		{
			this->x = _x;
			this->y = _y;
		}

		template<class T2>
		__HDINL__ explicit tvec2(const tvec2<T2>& vA)
		{
			this->x = T(vA.x);
			this->y = T(vA.y);
		}

		template<class T2>
		__HDINL__ explicit tvec2(const tvec3<T2>& vX)
		{
			this->x = T(vX.x);
			this->y = T(vX.y);
		}

		template<class T2>
		__HDINL__ explicit tvec2(const tvec4<T2>& vX)
		{
			this->x = T(vX.x);
			this->y = T(vX.y);
		}

#if defined(__NVCC__)
		__HDINL__ explicit tvec2(const float1& fX)
		{
			this->x = T(fX.x);
			this->y = T(0);
		}

		__HDINL__ explicit tvec2(const float2& fX)
		{
			this->x = T(fX.x);
			this->y = T(fX.y);
		}

		__HDINL__ explicit tvec2(const float3& fX)
		{
			this->x = T(fX.x);
			this->y = T(fX.y);
		}

		__HDINL__ explicit tvec2(const float4& fX)
		{
			this->x = T(fX.x);
			this->y = T(fX.y);
		}

		__HDINL__ explicit tvec2(const int1& fX)
		{
			this->x = T(fX.x);
			this->y = T(0);
		}

		__HDINL__ explicit tvec2(const int2& fX)
		{
			this->x = T(fX.x);
			this->y = T(fX.y);
		}

		__HDINL__ explicit tvec2(const int3& fX)
		{
			this->x = T(fX.x);
			this->y = T(fX.y);
		}

		__HDINL__ explicit tvec2(const int4& fX)
		{
			this->x = T(fX.x);
			this->y = T(fX.y);
		}

		__HDINL__ tvec2<T>& operator=(const float2& fX)
		{
			this->x = T(fX.x);
			this->y = T(fX.y);
			return *this;
		}

#endif

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Cast each element of this vector to the desired data type and returns the new vector.
		/// </summary>
		///
		/// <typeparam name="T2"> Generic type parameter. </typeparam>
		///
		/// <returns> The casted vector. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class T2>
		__HDINL__ tvec2<T2> Cast() const
		{
			tvec2<T2> vecCast;
			vecCast.x = T2(this->x);
			vecCast.y = T2(this->y);

			return vecCast;
		}
	};

#if defined(__NVCC__)
	template<class T>
	__HDINL__ float2 make_float2(const tvec2<T>& vA)
	{
		return ::make_float2(vA.x, vA.y);
	}
#endif

	template<class T>
	__HDINL__ tvec2<T> operator-(const tvec2<T>& vA)
	{
		return tvec2<T>(-vA.x, -vA.y);
	}

	template<class T>
	__HDINL__ tvec2<T> operator+(const tvec2<T>& vA, const tvec2<T>& vB)
	{
		return tvec2<T>(vA.x + vB.x, vA.y + vB.y);
	}

	template<class T1, class T2>
	__HDINL__ tvec2<T1> operator+(const tvec2<T1>& vA, const tvec2<T2>& vB)
	{
		return tvec2<T1>(vA.x + T2(vB.x), vA.y + T2(vB.y));
	}

	template<class T>
	__HDINL__ tvec2<T> operator-(const tvec2<T>& vA, const tvec2<T>& vB)
	{
		return tvec2<T>(vA.x - vB.x, vA.y - vB.y);
	}

	template<class T>
	__HDINL__ tvec2<T> operator*(const tvec2<T>& vA, const tvec2<T>& vB)
	{
		return tvec2<T>(vA.x * vB.x, vA.y * vB.y);
	}

	template<class T>
	__HDINL__ tvec2<T> operator/(const tvec2<T>& vA, const tvec2<T>& vB)
	{
		return tvec2<T>(vA.x / vB.x, vA.y / vB.y);
	}

	template<class T>
	__HDINL__ tvec2<T> operator*(const tvec2<T>& vA, const T& tVal)
	{
		return tvec2<T>(vA.x * tVal, vA.y * tVal);
	}

	template<class T>
	__HDINL__ tvec2<T> operator*(const T& tVal, const tvec2<T>& vA)
	{
		return tvec2<T>(tVal * vA.x, tVal * vA.y);
	}

	template<class T>
	__HDINL__ tvec2<T> operator*(const tvec2<T>& vA, bool bVal)
	{
		return tvec2<T>(vA.x * bVal, vA.y * bVal);
	}

	template<class T>
	__HDINL__ tvec2<T> operator*(bool bVal, const tvec2<T>& vA)
	{
		return tvec2<T>(bVal * vA.x, bVal * vA.y);
	}

	template<class T>
	__HDINL__ tvec2<T> operator/(const tvec2<T>& vA, const T& tVal)
	{
		return tvec2<T>(vA.x / tVal, vA.y / tVal);
	}

	template<class T>
	__HDINL__ tvec2<T> operator/(const T& tVal, const tvec2<T>& vA)
	{
		return tvec2<T>(tVal / vA.x, tVal / vA.y);
	}

	template<class T>
	__HDINL__ tvec2<T> operator+(const tvec2<T>& vA, const T& tVal)
	{
		return tvec2<T>(vA.x + tVal, vA.y + tVal);
	}

	template<class T>
	__HDINL__ tvec2<T> operator+(const T& tVal, const tvec2<T>& vA)
	{
		return tvec2<T>(tVal + vA.x, tVal + vA.y);
	}

	template<class T>
	__HDINL__ tvec2<T> operator-(const tvec2<T>& vA, const T& tVal)
	{
		return tvec2<T>(vA.x - tVal, vA.y - tVal);
	}

	template<class T>
	__HDINL__ tvec2<T> operator-(const T& tVal, const tvec2<T>& vA)
	{
		return tvec2<T>(tVal - vA.x, tVal - vA.y);
	}

	template<class T>
	__HDINL__ T sum(const tvec2<T>& vA)
	{
		return vA.x + vA.y;
	}

	template<class T>
	bool IsNumber(const tvec2<T>& vA)
	{
		return IsNumber(vA.x) && IsNumber(vA.y);
	}

	template<class T>
	bool IsFiniteNumber(const tvec2<T>& vA)
	{
		return IsFiniteNumber(vA.x) && IsFiniteNumber(vA.y);
	}

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	3D Vector class.
	/// </summary>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class T>
	struct tvec3
	{
		typedef T TDataType;

		__HDINL__ tvec3()
		{
		}		//{ x = T(0); y = T(0); z = T(0); }

		__HDINL__ explicit tvec3(T _x, T _y, T _z)
		{
			x = _x;
			y = _y;
			z = _z;
		}

		__HDINL__ explicit tvec3(const tvec4<T>& vX)
		{
			x = vX.x;
			y = vX.y;
			z = vX.z;
		}

#if defined(__NVCC__)

		__HDINL__ explicit tvec3(const float1& fX)
		{
			x = T(fX.x);
			y = T(0);
			z = T(0);
		}

		__HDINL__ explicit tvec3(const float2& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(0);
		}

		__HDINL__ explicit tvec3(const float3& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
		}

		__HDINL__ explicit tvec3(const float4& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
		}

		__HDINL__ explicit tvec3(const int1& fX)
		{
			x = T(fX.x);
			y = T(0);
			z = T(0);
		}

		__HDINL__ explicit tvec3(const int2& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(0);
		}

		__HDINL__ explicit tvec3(const int3& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
		}

		__HDINL__ explicit tvec3(const int4& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
		}
#endif

		template<class T2>
		__HDINL__ explicit tvec3(const tvec2<T2>& vA)
		{
			x = T(vA.x);
			y = T(vA.y);
			z = T(0);
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Constructor. X and Y are taken from given tvec2 vA and Z from second parameter tZ.
		/// </summary>
		///
		/// <typeparam name="T2">	Generic type parameter. </typeparam>
		/// <param name="vA">	The tvec2. </param>
		/// <param name="tZ">	The z coordinate. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class T2>
		__HDINL__ explicit tvec3(const tvec2<T2>& vA, T2 tZ)
		{
			x = T(vA.x);
			y = T(vA.y);
			z = T(tZ);
		}

		template<class T2>
		__HDINL__ explicit tvec3(const tvec3<T2>& vA)
		{
			x = T(vA.x);
			y = T(vA.y);
			z = T(vA.z);
		}

#if defined(__NVCC__)

		__HDINL__ tvec3<T>& operator=(const float3& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
			return *this;
		}
#endif

		__HDINL__ tvec3<T>& operator=(const tvec4<T>& vX)
		{
			x = vX.x;
			y = vX.y;
			z = vX.z;
			return *this;
		}

		__HDINL__ bool operator==(const tvec3<T>& vX) const
		{
			return (x == vX.x) && (y == vX.y) && (z == vX.z);
		}

		__HDINL__ bool operator!=(const tvec3<T>& vX) const
		{
			return (x != vX.x) || (y != vX.y) || (z != vX.z);
		}

		__HDINL__ bool operator<(T tValue) const
		{
			return (x < tValue) && (y < tValue) && (z < tValue);
		}

		__HDINL__ bool operator<=(T tValue) const
		{
			return (x <= tValue) && (y <= tValue) && (z <= tValue);
		}

		__HDINL__ bool operator>(T tValue) const
		{
			return (x > tValue) && (y > tValue) && (z > tValue);
		}

		__HDINL__ bool operator>=(T tValue) const
		{
			return (x >= tValue) && (y >= tValue) && (z >= tValue);
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Cast each element of this vector to the desired data type and returns the new vector.
		/// </summary>
		///
		/// <typeparam name="T2"> Generic type parameter. </typeparam>
		///
		/// <returns> The casted vector. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class T2>
		__HDINL__ tvec3<T2> Cast() const
		{
			tvec3<T2> vecCast;
			vecCast.x = T2(x);
			vecCast.y = T2(y);
			vecCast.z = T2(z);

			return vecCast;
		}

		__HDINL__ tvec3<T>& zero()
		{
			x = T(0);
			y = T(0);
			z = T(0);
			return *this;
		}

		__HDINL__ tvec3<T>& operator+=(const tvec3<T>& vA)
		{
			x += vA.x;
			y += vA.y;
			z += vA.z;
			return *this;
		}

		__HDINL__ tvec3<T>& operator-=(const tvec3<T>& vA)
		{
			x -= vA.x;
			y -= vA.y;
			z -= vA.z;
			return *this;
		}

		__HDINL__ tvec3<T>& operator*=(const tvec3<T>& vA)
		{
			x *= vA.x;
			y *= vA.y;
			z *= vA.z;
			return *this;
		}

		__HDINL__ tvec3<T>& operator/=(const tvec3<T>& vA)
		{
			x /= vA.x;
			y /= vA.y;
			z /= vA.z;
			return *this;
		}

		__HDINL__ tvec3<T>& operator*=(const T& tVal)
		{
			x *= tVal;
			y *= tVal;
			z *= tVal;
			return *this;
		}

		__HDINL__ tvec3<T>& operator/=(const T& tVal)
		{
			x /= tVal;
			y /= tVal;
			z /= tVal;
			return *this;
		}

		__HDINL__ tvec3<T>& operator+=(const T& tVal)
		{
			x += tVal;
			y += tVal;
			z += tVal;
			return *this;
		}

		__HDINL__ tvec3<T>& operator-=(const T& tVal)
		{
			x -= tVal;
			y -= tVal;
			z -= tVal;
			return *this;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Vector cross product.
		/// </summary>
		///
		/// <param name="vA"> The input vector. </param>
		///
		/// <returns> The result of the operation. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		__HDINL__ tvec3<T>& operator^=(const tvec3<T>& vA)
		{
			T _x = y * vA.z - z * vA.y;
			T _y = z * vA.x - x * vA.z;
			T _z = x * vA.y - y * vA.x;

			x = _x;
			y = _y;
			z = _z;

			return *this;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Array indexer operator.
		/// </summary>
		///
		/// <param name="nIdx"> The index. </param>
		///
		/// <returns> The indexed value. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		__HDINL__ T& operator[](size_t nIdx)
		{
			return (nIdx == 0) ? x : (nIdx == 1) ? y : z;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Array indexer operator.
		/// </summary>
		///
		/// <param name="nIdx"> The index. </param>
		///
		/// <returns> The indexed value. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		__HDINL__ const T& operator[](size_t nIdx) const
		{
			return (nIdx == 0) ? x : (nIdx == 1) ? y : z;
		}

		/// <summary> The X component. </summary>
		T x;
		/// <summary> The Y component. </summary>
		T y;
		/// <summary> The Z component. </summary>
		T z;
	};

#if defined(__NVCC__)

	template<class T>
	__HDINL__ float3 make_float3(const tvec3<T>& vA)
	{
		return ::make_float3(vA.x, vA.y, vA.z);
	}
#endif

	template<class T>
	__HDINL__ tvec3<T> operator-(const tvec3<T>& vA)
	{
		return tvec3<T>(-vA.x, -vA.y, -vA.z);
	}

	template<class T>
	__HDINL__ tvec3<T> operator+(const tvec3<T>& vA, const tvec3<T>& vB)
	{
		return tvec3<T>(vA.x + vB.x, vA.y + vB.y, vA.z + vB.z);
	}

	template<class T>
	__HDINL__ tvec3<T> operator-(const tvec3<T>& vA, const tvec3<T>& vB)
	{
		return tvec3<T>(vA.x - vB.x, vA.y - vB.y, vA.z - vB.z);
	}

	template<class T>
	__HDINL__ tvec3<T> operator*(const tvec3<T>& vA, const tvec3<T>& vB)
	{
		return tvec3<T>(vA.x * vB.x, vA.y * vB.y, vA.z * vB.z);
	}

	template<class T>
	__HDINL__ tvec3<T> operator/(const tvec3<T>& vA, const tvec3<T>& vB)
	{
		return tvec3<T>(vA.x / vB.x, vA.y / vB.y, vA.z / vB.z);
	}

/// Vector cross product
	template<class T>
	__HDINL__ tvec3<T> operator^(const tvec3<T>& vA, const tvec3<T>& vB)
	{
		return tvec3<T>(vA.y * vB.z - vA.z * vB.y
				, vA.z * vB.x - vA.x * vB.z
				, vA.x * vB.y - vA.y * vB.x
				);
	}

	template<class T>
	__HDINL__ tvec3<T> operator*(const tvec3<T>& vA, const T& tVal)
	{
		return tvec3<T>(vA.x * tVal, vA.y * tVal, vA.z * tVal);
	}

	template<class T>
	__HDINL__ tvec3<T> operator*(const T& tVal, const tvec3<T>& vA)
	{
		return tvec3<T>(tVal * vA.x, tVal * vA.y, tVal * vA.z);
	}

	template<class T>
	__HDINL__ tvec3<T> operator/(const tvec3<T>& vA, const T& tVal)
	{
		return tvec3<T>(vA.x / tVal, vA.y / tVal, vA.z / tVal);
	}

	template<class T>
	__HDINL__ tvec3<T> operator/(const T& tVal, const tvec3<T>& vA)
	{
		return tvec3<T>(tVal / vA.x, tVal / vA.y, tVal / vA.z);
	}

	template<class T>
	__HDINL__ tvec3<T> operator+(const tvec3<T>& vA, const T& tVal)
	{
		return tvec3<T>(vA.x + tVal, vA.y + tVal, vA.z + tVal);
	}

	template<class T>
	__HDINL__ tvec3<T> operator+(const T& tVal, const tvec3<T>& vA)
	{
		return tvec3<T>(tVal + vA.x, tVal + vA.y, tVal + vA.z);
	}

	template<class T>
	__HDINL__ tvec3<T> operator-(const tvec3<T>& vA, const T& tVal)
	{
		return tvec3<T>(vA.x - tVal, vA.y - tVal, vA.z - tVal);
	}

	template<class T>
	__HDINL__ tvec3<T> operator-(const T& tVal, const tvec3<T>& vA)
	{
		return tvec3<T>(tVal - vA.x, tVal - vA.y, tVal - vA.z);
	}

	template<class T>
	__HDINL__ T sum(const tvec3<T>& vA)
	{
		return vA.x + vA.y + vA.z;
	}

	template<class T>
	bool IsNumber(const tvec3<T>& vA)
	{
		return IsNumber(vA.x) && IsNumber(vA.y) && IsNumber(vA.z);
	}

	template<class T>
	bool IsFiniteNumber(const tvec3<T>& vA)
	{
		return IsFiniteNumber(vA.x) && IsFiniteNumber(vA.y) && IsFiniteNumber(vA.z);
	}

////////////////////////////////////////////////////////////////////////////////////////////
//// Vector 4

/**
		\brief 4D Vector class.
**/
	template<class T>
	struct tvec4
	{
		typedef T TDataType;

		__HDINL__ tvec4()
		{
		}		//{ x = T(0); y = T(0); z = T(0); w = T(0); }

		__HDINL__ explicit tvec4(T _x, T _y, T _z, T _w)
		{
			x = _x;
			y = _y;
			z = _z;
			w = _w;
		}

#if defined(__NVCC__)

		__HDINL__ explicit tvec4(const float1& fX)
		{
			x = T(fX.x);
			y = T(0);
			z = T(0);
			w = T(0);
		}

		__HDINL__ explicit tvec4(const float2& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(0);
			w = T(0);
		}

		__HDINL__ explicit tvec4(const float3& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
			w = T(0);
		}

		__HDINL__ explicit tvec4(const float4& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
			w = T(fX.w);
		}

		__HDINL__ explicit tvec4(const int1& fX)
		{
			x = T(fX.x);
			y = T(0);
			z = T(0);
			w = T(0);
		}

		__HDINL__ explicit tvec4(const int2& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(0);
			w = T(0);
		}

		__HDINL__ explicit tvec4(const int3& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
			w = T(0);
		}

		__HDINL__ explicit tvec4(const int4& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
			w = T(fX.w);
		}

		__HDINL__ explicit tvec4(const uchar1& fX)
		{
			x = T(fX.x);
			y = T(0);
			z = T(0);
			w = T(0);
		}

		__HDINL__ explicit tvec4(const uchar2& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(0);
			w = T(0);
		}

		__HDINL__ explicit tvec4(const uchar3& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
			w = T(0);
		}

		__HDINL__ explicit tvec4(const uchar4& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
			w = T(fX.w);
		}
#endif

		//__HDINL__ tvec4( const tvec4<T>& vA ) { x = vA.x; y = vA.y; z = vA.z; w = vA.w; }

		template<class T2>
		__HDINL__ explicit tvec4(const tvec4<T2>& vA)
		{
			x = T(vA.x);
			y = T(vA.y);
			z = T(vA.z);
			w = T(vA.w);
		}

		template<class T2>
		__HDINL__ explicit tvec4(const tvec3<T2>& vA, const T2& fW)
		{
			x = T(vA.x);
			y = T(vA.y);
			z = T(vA.z);
			w = T(fW);
		}

#if defined(__NVCC__)

		__HDINL__ tvec4<T>& operator=(const float4& fX)
		{
			x = T(fX.x);
			y = T(fX.y);
			z = T(fX.z);
			w = T(fX.w);
			return *this;
		}
#endif

		__HDINL__ tvec4<T>& operator=(const tvec3<T>& vX)
		{
			x = vX.x;
			y = vX.y;
			z = vX.z;
			w = T(0);
			return *this;
		}

		__HDINL__ bool operator==(const tvec4<T>& vX) const
		{
			return (x == vX.x) && (y == vX.y) && (z == vX.z) && (w == vX.w);
		}

		__HDINL__ bool operator!=(const tvec4<T>& vX) const
		{
			return (x != vX.x) || (y != vX.y) || (z != vX.z) || (w != vX.w);
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Cast each element of this vector to the desired data type and returns the new vector.
		/// </summary>
		///
		/// <typeparam name="T2"> Generic type parameter. </typeparam>
		///
		/// <returns> The casted vector. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class T2>
		__HDINL__ tvec4<T2> Cast() const
		{
			tvec4<T2> vecCast;
			vecCast.x = T2(x);
			vecCast.y = T2(y);
			vecCast.z = T2(z);
			vecCast.w = T2(w);

			return vecCast;
		}

		__HDINL__ tvec4<T>& zero()
		{
			x = T(0);
			y = T(0);
			z = T(0);
			w = T(0);
			return *this;
		}

		__HDINL__ tvec4<T>& operator+=(const tvec4<T>& vA)
		{
			x += vA.x;
			y += vA.y;
			z += vA.z;
			w += vA.w;
			return *this;
		}

		__HDINL__ tvec4<T>& operator-=(const tvec4<T>& vA)
		{
			x -= vA.x;
			y -= vA.y;
			z -= vA.z;
			w -= vA.w;
			return *this;
		}

		__HDINL__ tvec4<T>& operator*=(const tvec4<T>& vA)
		{
			x *= vA.x;
			y *= vA.y;
			z *= vA.z;
			w *= vA.w;
			return *this;
		}

		__HDINL__ tvec4<T>& operator/=(const tvec4<T>& vA)
		{
			x /= vA.x;
			y /= vA.y;
			z /= vA.z;
			w /= vA.w;
			return *this;
		}

		__HDINL__ tvec4<T>& operator*=(const T& tVal)
		{
			x *= tVal;
			y *= tVal;
			z *= tVal;
			w *= tVal;
			return *this;
		}

		__HDINL__ tvec4<T>& operator/=(const T& tVal)
		{
			x /= tVal;
			y /= tVal;
			z /= tVal;
			w /= tVal;
			return *this;
		}

		__HDINL__ tvec4<T>& operator+=(const T& tVal)
		{
			x += tVal;
			y += tVal;
			z += tVal;
			w += tVal;
			return *this;
		}

		__HDINL__ tvec4<T>& operator-=(const T& tVal)
		{
			x -= tVal;
			y -= tVal;
			z -= tVal;
			w -= tVal;
			return *this;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Array indexer operator.
		/// </summary>
		///
		/// <param name="nIdx"> The index. </param>
		///
		/// <returns> The indexed value. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		__HDINL__ T& operator[](size_t nIdx)
		{
			return (nIdx == 0) ? x : (nIdx == 1) ? y : (nIdx == 2) ? z : w;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Array indexer operator.
		/// </summary>
		///
		/// <param name="nIdx"> The index. </param>
		///
		/// <returns> The indexed value. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		__HDINL__ const T& operator[](size_t nIdx) const
		{
			return (nIdx == 0) ? x : (nIdx == 1) ? y : (nIdx == 2) ? z : w;
		}

		/// <summary> The X component. </summary>
		T x;
		/// <summary> The Y component. </summary>
		T y;
		/// <summary> The Z component. </summary>
		T z;
		/// <summary> The W component. </summary>
		T w;
	};

#if defined(__NVCC__)

	template<class T>
	__HDINL__ float4 make_float4(const tvec4<T>& vA)
	{
		return ::make_float4(vA.x, vA.y, vA.z, vA.w);
	}
#endif

	template<class T>
	__HDINL__ tvec4<T> operator-(const tvec4<T>& vA)
	{
		return tvec4<T>(-vA.x, -vA.y, -vA.z, -vA.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator+(const tvec4<T>& vA, const tvec4<T>& vB)
	{
		return tvec4<T>(vA.x + vB.x, vA.y + vB.y, vA.z + vB.z, vA.w + vB.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator-(const tvec4<T>& vA, const tvec4<T>& vB)
	{
		return tvec4<T>(vA.x - vB.x, vA.y - vB.y, vA.z - vB.z, vA.w - vB.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator+(const tvec4<T>& vA, const tvec3<T>& vB)
	{
		return tvec4<T>(vA.x + vB.x, vA.y + vB.y, vA.z + vB.z, vA.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator-(const tvec4<T>& vA, const tvec3<T>& vB)
	{
		return tvec4<T>(vA.x - vB.x, vA.y - vB.y, vA.z - vB.z, vA.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator+(const tvec3<T>& vA, const tvec4<T>& vB)
	{
		return tvec4<T>(vA.x + vB.x, vA.y + vB.y, vA.z + vB.z, vB.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator-(const tvec3<T>& vA, const tvec4<T>& vB)
	{
		return tvec4<T>(vA.x - vB.x, vA.y - vB.y, vA.z - vB.z, vB.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator*(const tvec4<T>& vA, const tvec4<T>& vB)
	{
		return tvec4<T>(vA.x * vB.x, vA.y * vB.y, vA.z * vB.z, vA.w * vB.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator/(const tvec4<T>& vA, const tvec4<T>& vB)
	{
		return tvec4<T>(vA.x / vB.x, vA.y / vB.y, vA.z / vB.z, vA.w / vB.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator*(const tvec4<T>& vA, const T& tVal)
	{
		return tvec4<T>(vA.x * tVal, vA.y * tVal, vA.z * tVal, vA.w * tVal);
	}

	template<class T>
	__HDINL__ tvec4<T> operator*(const T& tVal, const tvec4<T>& vA)
	{
		return tvec4<T>(tVal * vA.x, tVal * vA.y, tVal * vA.z, tVal * vA.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator*(const tvec4<T>& vA, bool bVal)
	{
		return tvec4<T>(vA.x * bVal, vA.y * bVal, vA.z * bVal, vA.w * bVal);
	}

	template<class T>
	__HDINL__ tvec4<T> operator*(bool bVal, const tvec4<T>& vA)
	{
		return tvec4<T>(bVal * vA.x, bVal * vA.y, bVal * vA.z, bVal * vA.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator/(const tvec4<T>& vA, const T& tVal)
	{
		return tvec4<T>(vA.x / tVal, vA.y / tVal, vA.z / tVal, vA.w / tVal);
	}

	template<class T>
	__HDINL__ tvec4<T> operator/(const T& tVal, const tvec4<T>& vA)
	{
		return tvec4<T>(tVal / vA.x, tVal / vA.y, tVal / vA.z, tVal / vA.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator+(const tvec4<T>& vA, const T& tVal)
	{
		return tvec4<T>(vA.x + tVal, vA.y + tVal, vA.z + tVal, vA.w + tVal);
	}

	template<class T>
	__HDINL__ tvec4<T> operator+(const T& tVal, const tvec4<T>& vA)
	{
		return tvec4<T>(tVal + vA.x, tVal + vA.y, tVal + vA.z, tVal + vA.w);
	}

	template<class T>
	__HDINL__ tvec4<T> operator-(const tvec4<T>& vA, const T& tVal)
	{
		return tvec4<T>(vA.x - tVal, vA.y - tVal, vA.z - tVal, vA.w - tVal);
	}

	template<class T>
	__HDINL__ tvec4<T> operator-(const T& tVal, const tvec4<T>& vA)
	{
		return tvec4<T>(tVal - vA.x, tVal - vA.y, tVal - vA.z, tVal - vA.w);
	}

	template<class T>
	__HDINL__ T sum(const tvec4<T>& vA)
	{
		return vA.x + vA.y + vA.z + vA.w;
	}

	template<class T>
	bool IsNumber(const tvec4<T>& vA)
	{
		return IsNumber(vA.x) && IsNumber(vA.y) && IsNumber(vA.z) && IsNumber(vA.w);
	}

	template<class T>
	bool IsFiniteNumber(const tvec4<T>& vA)
	{
		return IsFiniteNumber(vA.x) && IsFiniteNumber(vA.y) && IsFiniteNumber(vA.z) && IsFiniteNumber(vA.w);
	}

////////////////////////////////////////////////////////////////////////////////////////////
//// Vector N
/**
		\brief N-D Vector class.

		While the types tvec1<T>, tvec2<T>, tvec3<T> and tvec4<T> can also be replaced by this
		vector type, it is not possible to access the components of a tvec<T,iDim> via
		\c x, \c y, \c z and \c w.
**/
	template<class T, const int t_iDim>
	struct tvec
	{
		typedef T TDataType;

		static const int c_iCnt = t_iDim;

		__HDINL__ tvec()
		{
		}

		__HDINL__ tvec(T(&_v)[t_iDim])
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] = _v[i];
			}
		}

		__HDINL__ tvec(T tVal0)
		{
			v[0] = tVal0;
		}

		__HDINL__ tvec(T tVal0, T tVal1)
		{
			TAN_STATIC_ASSERT(t_iDim == 2);
			v[0] = tVal0;
			v[1] = tVal1;
		}

		__HDINL__ tvec(T tVal0, T tVal1, T tVal2)
		{
			TAN_STATIC_ASSERT(t_iDim == 3);
			v[0] = tVal0;
			v[1] = tVal1;
			v[2] = tVal2;
		}

		__HDINL__ tvec(T tVal0, T tVal1, T tVal2, T tVal3)
		{
			TAN_STATIC_ASSERT(t_iDim == 4);
			v[0] = tVal0;
			v[1] = tVal1;
			v[2] = tVal2;
			v[3] = tVal3;
		}

		__HDINL__ tvec(T tVal0, T tVal1, T tVal2, T tVal3, T tVal4)
		{
			TAN_STATIC_ASSERT(t_iDim == 5);
			v[0] = tVal0;
			v[1] = tVal1;
			v[2] = tVal2;
			v[3] = tVal3;
			v[4] = tVal4;
		}

		__HDINL__ tvec(T tVal0, T tVal1, T tVal2, T tVal3, T tVal4, T tVal5)
		{
			TAN_STATIC_ASSERT(t_iDim == 6);
			v[0] = tVal0;
			v[1] = tVal1;
			v[2] = tVal2;
			v[3] = tVal3;
			v[4] = tVal4;
			v[5] = tVal5;
		}

		__HDINL__ tvec(T tVal0, T tVal1, T tVal2, T tVal3, T tVal4, T tVal5, T tVal6)
		{
			TAN_STATIC_ASSERT(t_iDim == 7);
			v[0] = tVal0;
			v[1] = tVal1;
			v[2] = tVal2;
			v[3] = tVal3;
			v[4] = tVal4;
			v[5] = tVal5;
			v[6] = tVal6;
		}

		__HDINL__ tvec(T tVal0, T tVal1, T tVal2, T tVal3, T tVal4, T tVal5, T tVal6, T tVal7)
		{
			TAN_STATIC_ASSERT(t_iDim == 8);
			v[0] = tVal0;
			v[1] = tVal1;
			v[2] = tVal2;
			v[3] = tVal3;
			v[4] = tVal4;
			v[5] = tVal5;
			v[6] = tVal6;
			v[7] = tVal7;
		}

		template<class T2>
		__HDINL__ tvec(const tvec<T2, t_iDim>& vA)
		{
			*this = vA;
		}

#if defined(__NVCC__)

		__HDINL__ tvec(const float1& vX)
		{
			*this = vA;
		}

		__HDINL__ tvec(const float2& vX)
		{
			*this = vA;
		}

		__HDINL__ tvec(const float3& vX)
		{
			*this = vA;
		}

		__HDINL__ tvec(const float4& vX)
		{
			*this = vA;
		}

		__HDINL__ tvec(const int1& vX)
		{
			*this = vA;
		}

		__HDINL__ tvec(const int2& vX)
		{
			*this = vA;
		}

		__HDINL__ tvec(const int3& vX)
		{
			*this = vA;
		}

		__HDINL__ tvec(const int4& vX)
		{
			*this = vA;
		}

#endif

		///////////////////////////////////////////////////////////////////
		// operator = tvec<T,iDim>

		template<class T2>
		__HDINL__ tvec<T, t_iDim>& operator=(const tvec<T2, t_iDim>& vX)
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] = T(vX.v[i]);
			}

			return *this;
		}

#if defined(__NVCC__)

		///////////////////////////////////////////////////////////////////
		// operator = floatN
		__HDINL__ tvec<T, t_iDim>& operator=(const float1& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			for (int i = 1; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator=(const float2& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			if (t_iDim >= 2)
			{
				v[1] = T(vX.y);
			}

			for (int i = 2; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator=(const float3& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			if (t_iDim >= 2)
			{
				v[1] = T(vX.y);
			}

			if (t_iDim >= 3)
			{
				v[2] = T(vX.z);
			}

			for (int i = 3; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator=(const float4& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			if (t_iDim >= 2)
			{
				v[1] = T(vX.y);
			}

			if (t_iDim >= 3)
			{
				v[2] = T(vX.z);
			}

			if (t_iDim >= 4)
			{
				v[3] = T(vX.w);
			}

			for (int i = 4; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		///////////////////////////////////////////////////////////////////
		// operator = intN
		__HDINL__ tvec<T, t_iDim>& operator=(const int1& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			for (int i = 1; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator=(const int2& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			if (t_iDim >= 2)
			{
				v[1] = T(vX.y);
			}

			for (int i = 2; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator=(const int3& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			if (t_iDim >= 2)
			{
				v[1] = T(vX.y);
			}

			if (t_iDim >= 3)
			{
				v[2] = T(vX.z);
			}

			for (int i = 3; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator=(const int4& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			if (t_iDim >= 2)
			{
				v[1] = T(vX.y);
			}

			if (t_iDim >= 3)
			{
				v[2] = T(vX.z);
			}

			if (t_iDim >= 4)
			{
				v[3] = T(vX.w);
			}

			for (int i = 4; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}
#endif

		///////////////////////////////////////////////////////////////////
		// operator = tvecN<T>

		template<class T2>
		__HDINL__ tvec<T, t_iDim>& operator=(const tvec1<T2>& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			for (int i = 1; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		template<class T2>
		__HDINL__ tvec<T, t_iDim>& operator=(const tvec2<T2>& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			if (t_iDim >= 2)
			{
				v[1] = T(vX.y);
			}

			for (int i = 2; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		template<class T2>
		__HDINL__ tvec<T, t_iDim>& operator=(const tvec3<T2>& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			if (t_iDim >= 2)
			{
				v[1] = T(vX.y);
			}

			if (t_iDim >= 3)
			{
				v[2] = T(vX.z);
			}

			for (int i = 3; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		template<class T2>
		__HDINL__ tvec<T, t_iDim>& operator=(const tvec4<T2>& vX)
		{
			if (t_iDim >= 1)
			{
				v[0] = T(vX.x);
			}

			if (t_iDim >= 2)
			{
				v[1] = T(vX.y);
			}

			if (t_iDim >= 3)
			{
				v[2] = T(vX.z);
			}

			if (t_iDim >= 4)
			{
				v[3] = T(vX.w);
			}

			for (int i = 4; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		///////////////////////////////////////////////////////////////////

		__HDINL__ tvec<T, t_iDim>& zero()
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] = T(0);
			}

			return *this;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Cast each element of this vector to the desired data type and returns the new vector.
		/// </summary>
		///
		/// <typeparam name="T2"> Generic type parameter. </typeparam>
		///
		/// <returns> The casted vector. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<class T2>
		__HDINL__ tvec<T2, t_iDim> Cast() const
		{
			tvec<T2, t_iDim> vecCast;
			for (int i = 0; i < t_iDim; ++i)
			{
				vecCast[i] = T2(v[i]);
			}

			return vecCast;
		}

		__HDINL__ T& operator[](size_t nIdx)
		{
			return v[nIdx];
			//return (T&) GetElement<0>(iIdx);
		}

		__HDINL__ const T& operator[](size_t nIdx) const
		{
			return v[nIdx];
			//return GetElement<0>(iIdx);
		}

		template<int t_iIdx> __HDINL__ const T& GetElement(size_t nIdx) const
		{
			if (t_iIdx == nIdx)
			{
				return v[t_iIdx];
			}
			else
			{
				if (t_iIdx == t_iDim - 1)
				{
					return v[t_iDim - 1];
				}
				else
				{
					return GetElement<t_iIdx + 1>(nIdx);
				}
			}
		}

		__HDINL__ bool operator==(const tvec<T, t_iDim>& vA)        const
		{
			bool res = true;
			for (int i = 0; (i < t_iDim) && res; i++)
			{
				res = res && (v[i] == vA.v[i]);
			}

			return res;
		}

		__HDINL__ bool operator!=(const tvec<T, t_iDim>& vA)        const
		{
			return !(tvec<T, t_iDim>::operator==(vA));
		}

		__HDINL__ tvec<T, t_iDim>& operator+=(const tvec<T, t_iDim>& vA)
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] += vA.v[i];
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator-=(const tvec<T, t_iDim>& vA)
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] -= vA.v[i];
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator*=(const tvec<T, t_iDim>& vA)
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] *= vA.v[i];
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator/=(const tvec<T, t_iDim>& vA)
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] /= vA.v[i];
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator*=(const T& tVal)
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] *= tVal;
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator/=(const T& tVal)
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] /= tVal;
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator+=(const T& tVal)
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] += tVal;
			}

			return *this;
		}

		__HDINL__ tvec<T, t_iDim>& operator-=(const T& tVal)
		{
			for (int i = 0; i < t_iDim; ++i)
			{
				v[i] -= tVal;
			}

			return *this;
		}

		template<typename FuncOp>
		bool ForEach(FuncOp xFuncOp) const
		{
			const T* pData = v;

			for (int iIdx = 0; iIdx < t_iDim; ++iIdx, ++pData)
			{
				if (!xFuncOp(*pData))
				{
					return false;
				}
			}

			return true;
		}

		template<typename FuncOp>
		bool ForEachIndex(FuncOp xFuncOp) const
		{
			const T* pData = v;
			for (int iIdx = 0; iIdx < t_iDim; ++iIdx, ++pData)
			{
				if (!xFuncOp(*pData, iIdx))
				{
					return false;
				}
			}

			return true;
		}

		T v[t_iDim];
	};

//////////////////////////////////////////////////////////////////////////////
//// Make Float

#if defined(__NVCC__)

	template<class T, const int t_iDim>
	__HDINL__ float1 make_float1(const tvec<T, t_iDim>& vA)
	{
		if (t_iDim >= 1)
		{
			return ::make_float1(float(vA.v[0]));
		}

		return ::make_float1(0.0f);
	}

	template<class T, const int t_iDim>
	__HDINL__ float2 make_float2(const tvec<T, t_iDim>& vA)
	{
		if (t_iDim == 1)
		{
			return ::make_float2(float(vA.v[0]), 0.0f);
		}
		else if (t_iDim >= 2)
		{
			return ::make_float2(float(vA.v[0]), float(vA.v[1]));
		}

		return ::make_float2(0.0f, 0.0f);
	}

	template<class T, const int t_iDim>
	__HDINL__ float3 make_float3(const tvec<T, t_iDim>& vA)
	{
		if (t_iDim == 1)
		{
			return ::make_float3(float(vA.v[0]), 0.0f, 0.0f);
		}
		else if (t_iDim == 2)
		{
			return ::make_float3(float(vA.v[0]), float(vA.v[1]), 0.0f);
		}
		else if (t_iDim >= 3)
		{
			return ::make_float3(float(vA.v[0]), float(vA.v[1]), float(vA.v[2]));
		}

		return ::make_float3(0.0f, 0.0f, 0.0f);
	}

	template<class T, const int t_iDim>
	__HDINL__ float4 make_float4(const tvec<T, t_iDim>& vA)
	{
		if (t_iDim == 1)
		{
			return ::make_float4(float(vA.v[0]), 0.0f, 0.0f, 0.0f);
		}
		else if (t_iDim == 2)
		{
			return ::make_float4(float(vA.v[0]), float(vA.v[1]), 0.0f, 0.0f);
		}
		else if (t_iDim == 3)
		{
			return ::make_float4(float(vA.v[0]), float(vA.v[1]), float(vA.v[2]), 0.0f);
		}
		else if (t_iDim >= 4)
		{
			return ::make_float4(float(vA.v[0]), float(vA.v[1]), float(vA.v[2]), float(vA.v[3]));
		}

		return ::make_float4(0.0f, 0.0f, 0.0f, 0.0f);
	}

//////////////////////////////////////////////////////////////////////////////
//// Make Int

	template<class T, const int t_iDim>
	__HDINL__ int1 make_int1(const tvec<T, t_iDim>& vA)
	{
		if (t_iDim >= 1)
		{
			return ::make_int1(int(vA.v[0]));
		}

		return ::make_int1(0);
	}

	template<class T, const int t_iDim>
	__HDINL__ int2 make_int2(const tvec<T, t_iDim>& vA)
	{
		if (t_iDim == 1)
		{
			return ::make_int2(int(vA.v[0]), 0);
		}
		else if (t_iDim >= 2)
		{
			return ::make_int2(int(vA.v[0]), int(vA.v[1]));
		}

		return ::make_int2(0, 0);
	}

	template<class T, const int t_iDim>
	__HDINL__ int3 make_int3(const tvec<T, t_iDim>& vA)
	{
		if (t_iDim == 1)
		{
			return ::make_int3(int(vA.v[0]), 0, 0);
		}
		else if (t_iDim == 2)
		{
			return ::make_int3(int(vA.v[0]), int(vA.v[1]), 0);
		}
		else if (t_iDim >= 3)
		{
			return ::make_int3(int(vA.v[0]), int(vA.v[1]), int(vA.v[2]));
		}

		return ::make_int3(0, 0, 0);
	}

	template<class T, const int t_iDim>
	__HDINL__ int4 make_int4(const tvec<T, t_iDim>& vA)
	{
		if (t_iDim == 1)
		{
			return ::make_int4(int(vA.v[0]), 0, 0, 0);
		}
		else if (t_iDim == 2)
		{
			return ::make_int4(int(vA.v[0]), int(vA.v[1]), 0, 0);
		}
		else if (t_iDim == 3)
		{
			return ::make_int4(int(vA.v[0]), int(vA.v[1]), int(vA.v[2]), 0);
		}
		else if (t_iDim >= 4)
		{
			return ::make_int4(int(vA.v[0]), int(vA.v[1]), int(vA.v[2]), int(vA.v[3]));
		}

		return ::make_int4(0, 0, 0, 0);
	}

#endif

//////////////////////////////////////////////////////////////////////////////
/// Arithmetic

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator-(const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;
		const T* pA = vA.v;

		vX.ForEach([&](T& tValue) -> bool
				{
					tValue = -*pA;
					++pA;
					return true;
				});

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator+(const tvec<T, t_iDim>& vA, const tvec<T, t_iDim>& vB)
	{
		tvec<T, t_iDim> vX;
		const T* pA = vA.v;
		const T* pB = vB.v;

		vX.ForEach([&](T& tValue) -> bool
				{
					tValue = (*pA) + (*pB);
					++pA;
					++pB;
					return true;
				});

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator-(const tvec<T, t_iDim>& vA, const tvec<T, t_iDim>& vB)
	{
		tvec<T, t_iDim> vX;
		const T* pA = vA.v;
		const T* pB = vB.v;

		vX.ForEach([&](T& tValue) -> bool
				{
					tValue = (*pA) - (*pB);
					++pA;
					++pB;
					return true;
				});

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator*(const tvec<T, t_iDim>& vA, const tvec<T, t_iDim>& vB)
	{
		tvec<T, t_iDim> vX;
		const T* pA = vA.v;
		const T* pB = vB.v;

		vX.ForEach([&](T& tValue) -> bool
				{
					tValue = (*pA) * (*pB);
					++pA;
					++pB;
					return true;
				});

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator/(const tvec<T, t_iDim>& vA, const tvec<T, t_iDim>& vB)
	{
		tvec<T, t_iDim> vX;
		const T* pA = vA.v;
		const T* pB = vB.v;

		vX.ForEach([&](T& tValue) -> bool
				{
					tValue = (*pA) / (*pB);
					++pA;
					++pB;
					return true;
				});

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator*(const tvec<T, t_iDim>& vA, const T& tVal)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = vA.v[i] * tVal;
		}

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator*(const T& tVal, const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = tVal * vA.v[i];
		}

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator/(const tvec<T, t_iDim>& vA, const T& tVal)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = vA.v[i] / tVal;
		}

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator/(const T& tVal, const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = tVal / vA.v[i];
		}

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator+(const tvec<T, t_iDim>& vA, const T& tVal)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = vA.v[i] + tVal;
		}

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator+(const T& tVal, const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = tVal + vA.v[i];
		}

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator-(const tvec<T, t_iDim>& vA, const T& tVal)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = vA.v[i] - tVal;
		}

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ tvec<T, t_iDim> operator-(const T& tVal, const tvec<T, t_iDim>& vA)
	{
		tvec<T, t_iDim> vX;

		for (int i = 0; i < t_iDim; ++i)
		{
			vX.v[i] = tVal - vA.v[i];
		}

		return vX;
	}

	template<class T, const int t_iDim>
	__HDINL__ T sum(const tvec<T, t_iDim>& vA)
	{
		T tVal = T(0);

		for (int i = 0; i < t_iDim; ++i)
		{
			tVal += vA.v[i];
		}

		return tVal;
	}

	template<class T, const int t_iDim>
	__HDINL__ T prod(const tvec<T, t_iDim>& vA)
	{
		T tVal = T(1);

		for (int i = 0; i < t_iDim; ++i)
		{
			tVal *= vA.v[i];
		}

		return tVal;
	}

	template<class T, const int t_iDim>
	bool IsNumber(const tvec<T, t_iDim>& vA)
	{
		return vA.ForEach([](const T& tValue) -> bool
				{
					return IsNumber(tValue);
				});
	}

	template<class T, const int t_iDim>
	bool IsFiniteNumber(const tvec<T, t_iDim>& vA)
	{
		return vA.ForEach([](const T& tValue) -> bool
				{
					return IsFiniteNumber(tValue);
				});
	}

/// Vector cross product for 3D
	template<class T>
	__HDINL__ tvec<T, 3> operator^(const tvec<T, 3>& vA, const tvec<T, 3>& vB)
	{
		return tvec<T, 3>(vA.v[1] * vB.v[2] - vA.v[2] * vB.v[1]
				, vA.v[2] * vB.v[0] - vA.v[0] * vB.v[2]
				, vA.v[0] * vB.v[1] - vA.v[1] * vB.v[0]
				);
	}

} // namespace Tan

/************************************************************************/
/* Type definitions                                                     */
/************************************************************************/
#pragma region "TYPEDEF"

typedef Tan::tvec1<float> fvec1;
typedef Tan::tvec2<float> fvec2;
typedef Tan::tvec3<float> fvec3;
typedef Tan::tvec4<float> fvec4;
typedef Tan::tvec<float, 10> fvec10;
typedef Tan::tvec<float, 12> fvec12;

typedef Tan::tvec1<double> dvec1;
typedef Tan::tvec2<double> dvec2;
typedef Tan::tvec3<double> dvec3;
typedef Tan::tvec4<double> dvec4;
typedef Tan::tvec<double, 10> dvec10;
typedef Tan::tvec<double, 12> dvec12;

typedef Tan::tvec1<int> ivec1;
typedef Tan::tvec2<int> ivec2;
typedef Tan::tvec3<int> ivec3;
typedef Tan::tvec4<int> ivec4;

typedef Tan::tvec1<unsigned> uvec1;
typedef Tan::tvec2<unsigned> uvec2;
typedef Tan::tvec3<unsigned> uvec3;
typedef Tan::tvec4<unsigned> uvec4;

typedef Tan::tvec1<short> svec1;
typedef Tan::tvec2<short> svec2;
typedef Tan::tvec3<short> svec3;
typedef Tan::tvec4<short> svec4;

typedef Tan::tvec1<unsigned short> usvec1;
typedef Tan::tvec2<unsigned short> usvec2;
typedef Tan::tvec3<unsigned short> usvec3;
typedef Tan::tvec4<unsigned short> usvec4;

#pragma endregion "TYPEDEF"
