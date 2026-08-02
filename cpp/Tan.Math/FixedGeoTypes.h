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

#include "FixedVectorTypes.h"

namespace Tan
{
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	TanG rectangle.
	/// </summary>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<typename TValue>
	struct SRectangle
	{
		SRectangle() { };
		SRectangle(TValue fMinX, TValue fMinY, TValue fMaxX, TValue fMaxY)
		{
			Set(fMinX, fMinY, fMaxX, fMaxY);
		}

		void Set(TValue fMinX, TValue fMinY, TValue fMaxX, TValue fMaxY)
		{
			vMinPos.x = (fMinX < fMaxX ? fMinX : fMaxX);
			vMaxPos.x = (fMinX > fMaxX ? fMinX : fMaxX);

			vMinPos.y = (fMinY < fMaxY ? fMinY : fMaxY);
			vMaxPos.y = (fMinY > fMaxY ? fMinY : fMaxY);
		}

		tvec2<TValue> Size() const { return vMaxPos - vMinPos;  }
		tvec2<TValue> Center() const { return vMinPos + Size() / TValue(2); }

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Test whether this rectangle is inside of the given rectangle xRect.
		/// </summary>
		///
		/// <typeparam name="typename T">	Type of the typename t. </typeparam>
		/// <param name="xRect">	The rectangle. </param>
		///
		/// <returns>	True if inside of xRect, false if not. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename T>
		bool IsInsideOf(const SRectangle<T>& xRect) const
		{
			return vMinPos.x >= TValue(xRect.vMinPos.x)
			       &&      vMinPos.y >= TValue(xRect.vMinPos.y)
			       &&      vMaxPos.x <= TValue(xRect.vMaxPos.x)
			       &&      vMaxPos.y <= TValue(xRect.vMaxPos.y);
		}

		tvec2<TValue> vMinPos;
		tvec2<TValue> vMaxPos;
	};

	////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>	Receive circle 2 d. </summary>
	///
	/// <remarks>	Perwass, . </remarks>
	////////////////////////////////////////////////////////////////////////////////////////////////////

	template<typename TValue>
	struct SCircle2D
	{
		SCircle2D() { }

		template<typename T2>
		explicit SCircle2D(const SCircle2D<T2>& xCircle)
		{
			vCenter = tvec2<TValue>(xCircle.vCenter);
			tRadius = TValue(xCircle.tRadius);
		}

		tvec2<TValue> vCenter;
		TValue tRadius;
	};

	////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>	Represents an ellipse in 2D space.
	/// 			 </summary>
	///
	/// <remarks>	Perwass, . </remarks>
	////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	struct SEllipse2D
	{
		SEllipse2D() { }

		template<typename T2>
		explicit SEllipse2D(const SEllipse2D<T2>& xEllipse)
		{
			vCenter = tvec2<TValue>(xEllipse.vCenter);
			vDir1   = tvec2<TValue>(xEllipse.vDir1);
			vDir2   = tvec2<TValue>(xEllipse.vDir2);

			tRadius1 = TValue(xEllipse.tRadius1);
			tRadius2 = TValue(xEllipse.tRadius2);
		}

		void Zero()
		{
			vCenter.zero();
			vDir1.zero();
			vDir2.zero();
			tRadius1 = TValue(0);
			tRadius2 = TValue(0);
		}

		TValue FocusRadius() const { return ::sqrt(::abs(tRadius2 * tRadius2 - tRadius1 * tRadius1)); }
		TValue MinRadius() const { return tRadius1 < tRadius2 ? tRadius1 : tRadius2;  }
		TValue MaxRadius() const { return tRadius1 > tRadius2 ? tRadius1 : tRadius2;  }
		TValue Eccentricity() const { return FocusRadius() / MaxRadius(); }
		tvec2<TValue> Axis1() const { return tRadius1 * vDir1; }
		tvec2<TValue> Axis2() const { return tRadius2 * vDir2; }
		tvec2<TValue> MinDir() const { return tRadius1 < tRadius2 ? vDir1 : vDir2;  }
		tvec2<TValue> MaxDir() const { return tRadius1 > tRadius2 ? vDir1 : vDir2;  }
		tvec2<TValue> FocusPoint() const { return FocusRadius() * MaxDir(); }

		void ScaleBy(TValue dScale)
		{
			vCenter  *= dScale;
			tRadius1 *= dScale;
			tRadius2 *= dScale;
		}

		tvec2<TValue> vCenter;
		tvec2<TValue> vDir1;
		tvec2<TValue> vDir2;

		TValue tRadius1;
		TValue tRadius2;
	};

	////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>	Data that described a projective conic. </summary>
	///
	/// <remarks>	Perwass, . </remarks>
	////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	struct SConic2D
	{
		SConic2D() { }

		template<typename T2>
		explicit SConic2D(const SConic2D<T2>& xConic)
		{
			vCenter = tvec2<TValue>(xConic.vCenter);
			vDir1   = tvec2<TValue>(xConic.vDir1);
			vDir2   = tvec2<TValue>(xConic.vDir2);

			tLambda1 = TValue(xConic.tLambda1);
			tLambda2 = TValue(xConic.tLambda2);
			tRho     = TValue(xConic.tRho);
		}

		tvec2<TValue> vCenter;
		tvec2<TValue> vDir1;
		tvec2<TValue> vDir2;

		TValue tLambda1;
		TValue tLambda2;
		TValue tRho;
	};

	////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>	Receive line 3 d. </summary>
	///
	/// <remarks>	Perwass, . </remarks>
	////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	struct SLine3D
	{
		SLine3D() { }

		template<typename T2>
		explicit SLine3D(const SLine3D<T2>& xLine)
		{
			vOrigin = tvec3<TValue>(xLine.vOrigin);
			vDir    = tvec3<TValue>(xLine.vDir);
		}

		/// <summary>	Origin of the line. </summary>
		tvec3<TValue> vOrigin;

		/// <summary>	The direction of the line. </summary>
		tvec3<TValue> vDir;
	};

	template<class TValue> struct SPlaneSegment3D;

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	 conic 2 d.
	/// </summary>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

	template<class TValue>
	struct SPlane3D
	{
		SPlane3D() { }

		template<typename T2>
		explicit SPlane3D(const SPlane3D<T2>& xPlane)
		{
			tDistance = (TValue) (xPlane.tDistance);
			vNormal   = tvec3<TValue>(xPlane.vNormal);
		}

		template<typename T2>
		explicit SPlane3D(const SPlaneSegment3D<T2>& xPlaneSeg)
		{
			vNormal   = tvec3<TValue>(xPlaneSeg.Normal());
			tDistance = dot(vNormal, tvec3<TValue>(xPlaneSeg.vCenter));
		}

		bool IsValid()
		{
			return IsFiniteNumber(tDistance) && IsFiniteNumber(vNormal) && (length(vNormal) > TValue(0));
		}

		/// <summary>	The distance from the origin along the normal vector. </summary>
		TValue tDistance;

		/// <summary>	The plane normal. </summary>
		tvec3<TValue> vNormal;
	};

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	 plane segment 3 d.
	/// </summary>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<class TValue>
	struct SPlaneSegment3D
	{
		SPlaneSegment3D() { }

		template<typename T2>
		explicit SPlaneSegment3D(const SPlaneSegment3D<T2>& xPlaneSeg)
		{
			vCenter = tvec3<TValue>(xPlaneSeg.vCenter);
			vDir1   = tvec3<TValue>(xPlaneSeg.vDir1);
			vDir2   = tvec3<TValue>(xPlaneSeg.vDir2);

			tLen1 = (TValue) (xPlaneSeg.tLen1);
			tLen2 = (TValue) (xPlaneSeg.tLen2);
		}

		template<typename T2>
		explicit SPlaneSegment3D(const SPlane3D<T2>& xPlane, const T2& tSize = T2(1))
		{
			tvec3<TValue> vNormal = tvec3<TValue>(xPlane.vNormal);

			tvec3<TValue> vA1 = vNormal ^ tvec3<TValue>(1, 0, 0);
			tvec3<TValue> vA2 = vNormal ^ tvec3<TValue>(0, 1, 0);
			tvec3<TValue> vA3 = vNormal ^ tvec3<TValue>(0, 0, 1);

			TValue dL1 = length(vA1);
			TValue dL2 = length(vA2);
			TValue dL3 = length(vA3);

			if (dL1 > dL2)
			{
				if (dL1 > dL3) { vDir1 = vA1; }
				else{ vDir1 = vA3; }
			}
			else
			{
				if (dL2 > dL3) { vDir1 = vA2; }
				else{ vDir1 = vA3; }
			}

			vDir1 = normalize(vDir1);
			vDir2 = vNormal ^ vDir1;

			vCenter = (TValue) (xPlane.tDistance) * vNormal;

			tLen1 = tSize;
			tLen2 = tSize;
		}

		tvec3<TValue> Axis1() const { return tLen1 * vDir1;  }
		tvec3<TValue> Axis2() const { return tLen2 * vDir2;  }

		tvec3<TValue> Normal() const { return normalize(vDir1 ^ vDir2); }
		TValue Area() const { return tLen1 * tLen2;  }

		void GetCorner(tvec3<TValue>& vC1, tvec3<TValue>& vC2, tvec3<TValue>& vC3, tvec3<TValue>& vC4) const
		{
			tvec3<TValue> vHalfAxis1 = TValue(0.5) * tLen1 * vDir1;
			tvec3<TValue> vHalfAxis2 = TValue(0.5) * tLen2 * vDir2;

			vC1 = vCenter - vHalfAxis1 - vHalfAxis2;
			vC2 = vCenter - vHalfAxis1 + vHalfAxis2;
			vC3 = vCenter + vHalfAxis1 + vHalfAxis2;
			vC4 = vCenter + vHalfAxis1 - vHalfAxis2;
		}

		void GetCorner(tvec3<TValue> pvC[4]) const
		{
			tvec3<TValue> vHalfAxis1 = TValue(0.5) * tLen1 * vDir1;
			tvec3<TValue> vHalfAxis2 = TValue(0.5) * tLen2 * vDir2;

			pvC[0] = vCenter - vHalfAxis1 - vHalfAxis2;
			pvC[1] = vCenter - vHalfAxis1 + vHalfAxis2;
			pvC[2] = vCenter + vHalfAxis1 + vHalfAxis2;
			pvC[3] = vCenter + vHalfAxis1 - vHalfAxis2;
		}

		tvec3<TValue> vCenter;
		tvec3<TValue> vDir1;
		tvec3<TValue> vDir2;

		TValue tLen1;
		TValue tLen2;
	};
}	// Tan
