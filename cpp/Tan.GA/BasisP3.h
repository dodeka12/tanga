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

#include "Tan.Core/Defines.h"

#include "Tan.Math/ValuePrecision.h"
#include "Tan.Math/FixedGeoTypes.h"

#include "SubspaceMultivector.h"
#include "BladeMask.h"
#include "DynamicMultivector.h"
#include "MultivectorStyle.h"

#define TAN_GA_DECL_BASIS_P3(theType)                        \
	static const unsigned uSc = GA::_CBasisP3<theType>::uSc; \
	static const unsigned uE1 = GA::_CBasisP3<theType>::uE1; \
	static const unsigned uE2 = GA::_CBasisP3<theType>::uE2; \
	static const unsigned uE3 = GA::_CBasisP3<theType>::uE3; \
	static const unsigned uE4 = GA::_CBasisP3<theType>::uE4; \
	static const unsigned uPs = GA::_CBasisP3<theType>::uPs;

#define TAN_GA_DEF_MULTIV_BASIS_P3(theType, theBasis)                                                      \
	GA::CMultivector<theType, typename GA::_CBasisP3<theType>::TBlade> wSc;                                \
	GA::CMultivector<theType, typename GA::_CBasisP3<theType>::TBlade> wE1, wE2, wE3, wE4;                 \
	GA::CMultivector<theType, typename GA::_CBasisP3<theType>::TBlade> wE23, wE31, wE12, wE41, wE42, wE43; \
	GA::CMultivector<theType, typename GA::_CBasisP3<theType>::TBlade> wE123, wE234, wE314, wE124;         \
	GA::CMultivector<theType, typename GA::_CBasisP3<theType>::TBlade> wE1234, wI;                         \
	wSc = (theBasis).Sc();                                                                                 \
	wE1 = (theBasis).E1();                                                                                 \
	wE2 = (theBasis).E2();                                                                                 \
	wE3 = (theBasis).E3();                                                                                 \
	wE4 = (theBasis).E4();                                                                                 \
	GA::OP(wE23, wE2, wE3);                                                                                \
	GA::OP(wE31, wE3, wE1);                                                                                \
	GA::OP(wE12, wE1, wE2);                                                                                \
	GA::OP(wE41, wE4, wE1);                                                                                \
	GA::OP(wE42, wE4, wE2);                                                                                \
	GA::OP(wE43, wE4, wE3);                                                                                \
	GA::OP(wE123, wE12, wE3);                                                                              \
	GA::OP(wE234, wE23, wE4);                                                                              \
	GA::OP(wE314, wE31, wE4);                                                                              \
	GA::OP(wE124, wE12, wE4);                                                                              \
	GA::OP(wE1234, wE123, wE4);                                                                            \
	wI = wE1234;

namespace Tan
{
	namespace GA
	{
		template <typename _TValue>
		class _CBasisP3 : public CValuePrecision<_TValue>
		{
		public:
			static const unsigned VectorSpaceDimension = 4;
			static const unsigned VectorSpaceSignature = 0;

			static const unsigned uSc = 0;
			static const unsigned uE1 = (1 << 0);
			static const unsigned uE2 = (1 << 1);
			static const unsigned uE3 = (1 << 2);
			static const unsigned uE4 = (1 << 3);

			static const unsigned uPs = (uE1 | uE2 | uE3 | uE4);

		public:
			typedef _TValue TValue;
			typedef CBlade<VectorSpaceDimension, VectorSpaceSignature> TBlade;
			typedef _CMultivector<TValue, TBlade> TMultivector;
			typedef CValuePrecision<_TValue> TValPrec;

			typedef _CSubspaceMultivector<TValue, TBlade, 1> TBaseVec1;
			typedef _CSubspaceMultivector<TValue, TBlade, 2> TBaseVec2;

		public:
			_CBasisP3()
			{
			}

			_CBasisP3(TValue fPrec)
			{
				SetValuePrecision(fPrec);
				_Init();
			}

			const TBaseVec1 &Sc() const
			{
				return m_wSc;
			}

			const TBaseVec1 &Ps() const
			{
				return m_wPs;
			}

			const TBaseVec1 &E1() const
			{
				return m_wE1;
			}

			const TBaseVec1 &E2() const
			{
				return m_wE2;
			}

			const TBaseVec1 &E3() const
			{
				return m_wE3;
			}

			const TBaseVec1 &E4() const
			{
				return m_wE4;
			}

			const TBaseVec1 &E123() const
			{
				return m_wE123;
			}

			const TBaseVec1 &E321() const
			{
				return m_wE321;
			}

			const TBaseVec1 &E1234() const
			{
				return m_wE1234;
			}

			const TBaseVec1 &E4321() const
			{
				return m_wE4321;
			}

		protected:
			inline void _Init();

		protected:
			TBaseVec1 m_wSc;
			TBaseVec1 m_wPs;
			TBaseVec1 m_wE1;
			TBaseVec1 m_wE2;
			TBaseVec1 m_wE3;
			TBaseVec1 m_wE4;
			TBaseVec1 m_wE123;
			TBaseVec1 m_wE321;
			TBaseVec1 m_wE1234;
			TBaseVec1 m_wE4321;
		};

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 basis n 3.
		/// </summary>
		///
		/// <typeparam name="_TValue">	Type of the walue. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename _TValue>
		class CBasisP3 : public _CBasisP3<_TValue>
		{
		public:
			typedef _TValue TValue;
			typedef _CBasisP3<_TValue> TBase;
			typedef typename TBase::TBlade TBlade;
			typedef typename TBase::TMultivector TMultivector;
			typedef typename TBase::TValPrec TValPrec;

			typedef CMultivectorStyle<TValue, TBlade> TStyle;
			typedef typename TStyle::TBasis TBasis;
			typedef typename TStyle::SPairName TN;
			typedef typename TStyle::SBladePair TB;
			typedef CSubspaceMask<TBasis> TMask;

			typedef tvec3<TValue> TVec3;
			typedef tvec4<TValue> TVec4;
			typedef _CSubspaceMultivector<TValue, TBlade, 4> TPoint;
			typedef _CSubspaceMultivector<TValue, TBlade, 6> TLine;
			typedef _CSubspaceMultivector<TValue, TBlade, 4> TRotor;

			typedef tvec<TBlade, 4> TBladeListPoint;
			typedef tvec<TBlade, 6> TBladeListLine;
			typedef tvec<TBlade, 4> TBladeListRotor;

			typedef std::vector<TVec3> TVec3List;
			typedef std::vector<TVec4> TVec4List;
			typedef std::vector<TPoint> TPointList;
			typedef std::vector<TLine> TLineList;
			typedef std::vector<TRotor> TRotorList;

			typedef std::vector<TMultivector> TMultivectorList;

		public:
			static const unsigned uSc = TBase::uSc;
			static const unsigned uE1 = TBase::uE1;
			static const unsigned uE2 = TBase::uE2;
			static const unsigned uE3 = TBase::uE3;
			static const unsigned uE4 = TBase::uE4;
			static const unsigned uPs = TBase::uPs;

		public:
			CBasisP3()
			{
				try
				{
					TValPrec::Reset();
					_Init();
				}
				catch (std::exception &xEx)
				{
					TAN_RETHROW("Error creating basis", xEx);
				}
			}

			CBasisP3(TValue fPrec)
			{
				try
				{
					TValPrec::SetValuePrecision(fPrec);
					_Init();
				}
				catch (std::exception &xEx)
				{
					TAN_RETHROW("Error creating basis", xEx);
				}
			}

			std::string ToString()
			{
				return m_xStyle.ToString((CSubspaceBasis<TValue, TBlade>)m_xStyle);
			}

			template <typename TMultivectorA>
			std::string ToString(const TMultivectorA &wA)
			{
				return m_xStyle.ToString(wA);
			}

			template <typename TMultivectorA>
			std::string ToString(const std::vector<TMultivectorA> &wListA) const
			{
				return m_xStyle.ToString(wListA);
			}

			std::string ToString(const TBasis &xSubBasis) const
			{
				return m_xStyle.ToString(xSubBasis);
			}

			std::string ToString(const TMask &xMask, bool bSimple = false) const
			{
				return m_xStyle.ToString(xMask, bSimple);
			}

			const TBasis &Basis() const
			{
				return m_xStyle;
			}

			const TStyle &Style() const
			{
				return m_xStyle;
			}

			const TBasis &BasisScalar() const
			{
				return m_xBasisScalar;
			}

			const TBasis &BasisPoint() const
			{
				return m_xBasisPoint;
			}

			const TBasis &BasisLine() const
			{
				return m_xBasisLine;
			}

			const TBasis &BasisPlane() const
			{
				return m_xBasisPlane;
			}

			const TBasis &BasisSpace() const
			{
				return m_xBasisSpace;
			}

			const TBasis &BasisReflection() const
			{
				return m_xBasisReflection;
			}

			const TBasis &BasisRotor() const
			{
				return m_xBasisRotor;
			}

			const TMask &MaskScalar() const
			{
				return m_xMaskScalar;
			}

			const TMask &MaskPoint() const
			{
				return m_xMaskPoint;
			}

			const TMask &MaskLine() const
			{
				return m_xMaskLine;
			}

			const TMask &MaskPlane() const
			{
				return m_xMaskPlane;
			}

			const TMask &MaskSpace() const
			{
				return m_xMaskSpace;
			}

			const TMask &MaskReflection() const
			{
				return m_xMaskReflection;
			}

			const TMask &MaskRotor() const
			{
				return m_xMaskRotor;
			}

			const TBladeListPoint &BladeListPoint() const
			{
				return m_vBladeListPoint;
			}

			const TBladeListRotor &BladeListRotor() const
			{
				return m_vBladeListRotor;
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	/
			/// 	 Entities.
			/// </summary>
			///
			/// <param name="wPnt">  	[in,out] The point. </param>
			/// <param name="vPnt3d">	The point 3D. </param>
			///
			/// <returns>	. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			TPoint &CreatePoint(TPoint &wPnt, const TVec3 &vPnt3d)
			{
				wPnt.Create(tvec<TValue, 4>(vPnt3d.x, vPnt3d.y, vPnt3d.z, TValue(1)), m_vBladeListPoint);
				wPnt.SetValuePrecision(TValPrec::GetValuePrecision());
				return wPnt;
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Point n 3.
			/// </summary>
			///
			/// <param name="wListPnt">  	[in,out] The list point. </param>
			/// <param name="wListPnt3d">	The list point 3D. </param>
			///
			/// <returns>	. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			TPointList &CreatePoint(TPointList &vecwPnt, const TVec3List &vecvPnt3d)
			{
				try
				{
					// Declare blade type
					typedef CBasisP3<TValue>::TBlade TBlade;

					vecwPnt.resize(vecvPnt3d.size());

					Transform(vecwPnt, vecvPnt3d, [&](TPoint &wPnt, const tvec3<TValue> &vPnt3d)
							  { CreatePoint(wPnt, vPnt3d); });

					return vecwPnt;
				}
				catch (std::exception &xEx)
				{
					TAN_RETHROW("Error getting 3D point list", xEx);
				}
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Creates a direction.
			/// </summary>
			///
			/// <param name="wPnt">  	[in,out] The point. </param>
			/// <param name="vPnt3d">	The point 3D. </param>
			///
			/// <returns>	The new direction. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			TPoint &CreateDirection(TPoint &wPnt, const TVec3 &vPnt3d)
			{
				wPnt.Create(tvec<TValue, 4>(vPnt3d.x, vPnt3d.y, vPnt3d.z, TValue(0)), m_vBladeListPoint);
				wPnt.SetValuePrecision(TValPrec::GetValuePrecision());
				return wPnt;
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Creates a line.
			/// </summary>
			///
			/// <param name="xLine">  	[in,out] The line. </param>
			/// <param name="vOrigin">	The origin. </param>
			/// <param name="vDir">   	The dir. </param>
			///
			/// <returns>	The new line. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			TLine &CreateLine(TLine &wLine, const TVec3 &vOrigin, const TVec3 &vDir)
			{
				wLine.Create(m_vBladeListLine);
				TPoint wOrigin, wDir;
				CreatePoint(wOrigin, vOrigin);
				CreateDirection(wDir, vDir);
				GA::OP(wLine, wOrigin, wDir);

				return wLine;
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Creates a line.
			/// </summary>
			///
			/// <param name="wLine">	[in,out] The line. </param>
			/// <param name="xLine">	The line. </param>
			///
			/// <returns>	The new line. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			TLine &CreateLine(TLine &wLine, const SLine3D<TValue> &xLine)
			{
				return CreateLine(wLine, xLine.vOrigin, xLine.vDir);
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Query if 'wPnt' is point.
			/// </summary>
			///
			/// <param name="wPnt">	The point. </param>
			///
			/// <returns>	True if point, false if not. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			template <typename TMultivectorX>
			bool IsPoint(const TMultivectorX &wPnt)
			{
				bool bHasGrade1 = false;

				// Test whether all elements are of grade 1
				if (!wPnt.ForEachBlade([&](const TValue &fValA, const TBlade &blA) -> bool
									   {
							    if (!wPnt.IsZero(fValA))
							    {
								    if (blA.GetGrade() != 1)
								    {
									    return false;
								    }
								    else
								    {
									    bHasGrade1 = true;
								    }
							    }

							    return true; }))
				{
					return false;
				}

				if (!bHasGrade1)
				{
					return false;
				}

				return true;
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Try point to vector 3.
			/// </summary>
			///
			/// <typeparam name="typename TMultivectorX">	Type of the typename t multivector x coordinate. </typeparam>
			/// <param name="vPnt3d">	[in,out] The point 3D. </param>
			/// <param name="wPnt">  	The point. </param>
			///
			/// <returns>	True if it succeeds, false if it fails. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			template <typename TMultivectorX>
			bool TryPointToVec3(TVec3 &vPnt3d, bool &bIsAtInfinity, const TMultivectorX &wPnt)
			{
				typedef typename TMultivectorX::TBlade TBlade;
				typename TMultivectorX::TValue fValue;

				wPnt.GetValueBlade(fValue, TBlade(CBasisP3<TValue>::uE1));
				vPnt3d.x = TValue(fValue);

				wPnt.GetValueBlade(fValue, TBlade(CBasisP3<TValue>::uE2));
				vPnt3d.y = TValue(fValue);

				wPnt.GetValueBlade(fValue, TBlade(CBasisP3<TValue>::uE3));
				vPnt3d.z = TValue(fValue);

				wPnt.GetValueBlade(fValue, TBlade(CBasisP3<TValue>::uE4));
				if (!TValPrec::IsZero(fValue))
				{
					bIsAtInfinity = false;
					vPnt3d /= TValue(fValue);
				}
				else
				{
					bIsAtInfinity = true;
				}

				return true;
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Point to vector 3.
			/// </summary>
			///
			/// <typeparam name="typename TMultivectorX">	Type of the typename t multivector x coordinate. </typeparam>
			/// <param name="vPnt3d">	[in,out] The point 3D. </param>
			/// <param name="wPnt">  	The point. </param>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			template <typename TMultivectorX>
			void PointToVec3(TVec3 &vPnt3d, bool &bIsAtInfinity, const TMultivectorX &wPnt)
			{
				if (!TryPointToVec3(vPnt3d, bIsAtInfinity, wPnt))
				{
					TAN_THROW_RT("Cannot convert conformal multivector to Euclidean point");
				}
			}

			template <typename TMultivectorX>
			void PointToVec3(TVec3 &vPnt3d, const TMultivectorX &wPnt)
			{
				bool bIsAtInfinity;
				PointToVec3(vPnt3d, bIsAtInfinity, wPnt);
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Point to vector 3.
			/// </summary>
			///
			/// <typeparam name="TMultivectorX">	Type of the typename t multivector x coordinate. </typeparam>
			/// <param name="vecvPnt3d">	[in,out] The mv point 3D. </param>
			/// <param name="vecwPnt">  	The mw point. </param>
			///
			/// <returns>	A list of. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			template <typename TMultivectorX>
			TVec3List &PointToVec3(TVec3List &vecvPnt3d, const std::vector<TMultivectorX> &vecwPnt)
			{
				try
				{
					bool bIsAtInfinity;
					vecvPnt3d.resize(vecwPnt.size());
					Transform(vecvPnt3d, vecwPnt, [&](TVec3 &vPnt3d, const TMultivectorX &wPnt)
							  {
								vPnt3d.zero();
								TryPointToVec3(vPnt3d, bIsAtInfinity, wPnt); });

					return vecvPnt3d;
				}
				catch (std::exception &xEx)
				{
					TAN_RETHROW("Error converting points to three dimensional vector", xEx);
				}
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Rotors.
			/// </summary>
			///
			/// <param name="wRotor">				[in,out] The rotor. </param>
			/// <param name="vRotationAxis">		The rotation axis. </param>
			/// <param name="dRotationAngleRad">	The rotation angle radians. </param>
			///
			/// <returns>	. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			TRotor &CreateRotor(TRotor &wRotor, const TVec3 &vRotationAxis, const TValue &dRotationAngleRad)
			{
				try
				{
					TValue fCos = TValue(cos(double(dRotationAngleRad) / 2.0));
					TValue fSin = -TValue(sin(double(dRotationAngleRad) / 2.0));

					TVec3 vAxis = normalize(vRotationAxis);

					wRotor.Create(
						tvec<TValue, 4>(fCos, fSin * vAxis.x, fSin * vAxis.y, fSin * vAxis.z),
						tvec<TBlade, 4>(uSc, uE2 | uE3, uE1 | uE3, uE1 | uE2));

					wRotor.SetValuePrecision(TValPrec::GetValuePrecision());

					return wRotor;
				}
				catch (std::exception &xEx)
				{
					TAN_RETHROW("Error creating rotor", xEx);
				}
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Generate a rotor that rotates vector vA into vector vB without scaling.
			/// </summary>
			///
			/// <param name="wRotor">	[in,out] The rotor. </param>
			/// <param name="vA">	 	The v a. </param>
			/// <param name="vB">	 	The v b. </param>
			///
			/// <returns>	The rotor. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			TRotor &CreateRotor(TRotor &wRotor, const TVec3 &vA, const TVec3 &vB)
			{
				try
				{
					TVec3 vDirA, vDirB, vAxis;
					vDirA = normalize(vA);
					vDirB = normalize(vB);

					vAxis = vDirA ^ vDirB;

					return CreateRotor(wRotor, vAxis, ::acos(dot(vDirA, vDirB)));
				}
				catch (std::exception &xEx)
				{
					TAN_RETHROW("Error generating rotor", xEx);
				}
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Try to get line components from multivector. Assumes that multivector represents a line. If the mutlivector represents
			/// 	a line at infinity, then the function return a zero vector as vDir and the normal vector of two parallel planes whose
			/// 	intersection is this line in vOrig.
			/// </summary>
			///
			/// <param name="vOrig">			[out] The line origin. </param>
			/// <param name="vDir">				[out] The line direction. </param>
			/// <param name="bIsAtInfinity">	[out] Set to true on return, if the line lies at infinity. </param>
			/// <param name="wLine">			A multivector representing a line. </param>
			/// <param name="bTestOPNS">		(optional) If true assumes multivector represents a line in outer product null space
			/// 								(OPNS). If false assumes the multivector represents a line in the inner product null space
			/// 								(IPNS). </param>
			///
			/// <returns>	True if it succeeds, false if it fails. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			bool TryGetLineComponents(TVec3 &vOrig, TVec3 &vDir, bool &bIsAtInfinity, const TMultivector &wLine, bool bTestOPNS = true)
			{
				TMultivector wL;

				wL = GA::GetGradeProjection(wLine, 2);

				if (GA::IsZero(wL))
				{
					return false;
				}

				// If the multivector represents the line in the IPNS, then
				// take the dual of wLine for analysis.
				if (!bTestOPNS)
				{
					TMultivector wL2(wL);
					GA::Dual(wL, wL2);
				}

				TMultivector wDir;
				GA::IP(wDir, TBase::m_wE4, wL);
				TValue dDirLen2 = MagnitudeSquared(wDir);

				// If the direction component of the line is zero,
				// then multivector does not represent a line.
				if (this->IsZero(dDirLen2))
				{
					// Line at infinity
					bIsAtInfinity = true;

					// Set direction to zero
					vDir.zero();

					// Calculate the dual of wL w.r.t. the subspace e1^e2^e3.
					TMultivector wNormal;
					GA::IP(wNormal, wL, TBase::m_wE321);

					// Set vOrig to this normal
					PointToVec3(vOrig, wNormal);
				}
				else
				{
					bIsAtInfinity = false;

					// Remove the direction part from the line
					TMultivector wMoment;
					GA::OP(wMoment, TBase::m_wE4, wDir);
					wMoment = wL - wMoment;

					// Calculate the line origin
					TMultivector wOrig;
					GA::IP(wOrig, wMoment, wDir / dDirLen2);

					PointToVec3(vOrig, wOrig);
					PointToVec3(vDir, wDir / ::sqrt(dDirLen2));
				}

				return true;
			}

		protected:
			inline void _Init();

		protected:
			TStyle m_xStyle;

			TBasis m_xBasisScalar;
			TBasis m_xBasisPoint;
			TBasis m_xBasisLine;
			TBasis m_xBasisPlane;
			TBasis m_xBasisSpace;

			TBasis m_xBasisReflection;
			TBasis m_xBasisRotor;

			TMask m_xMaskScalar;
			TMask m_xMaskPoint;
			TMask m_xMaskLine;
			TMask m_xMaskPlane;
			TMask m_xMaskSpace;

			TMask m_xMaskReflection;
			TMask m_xMaskRotor;

			TBladeListPoint m_vBladeListPoint;
			TBladeListLine m_vBladeListLine;
			TBladeListRotor m_vBladeListRotor;
		};

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Initialises this _CBasisP3&lt;_TValue&gt;
		/// </summary>
		///
		/// <typeparam name="_TValue">	Type of the value. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename _TValue>
		void _CBasisP3<_TValue>::_Init()
		{
			// TODO catch exceptions here
			TValue fPrec = TValPrec::GetValuePrecision();
			m_wSc.SetValuePrecision(fPrec);
			m_wPs.SetValuePrecision(fPrec);
			m_wE1.SetValuePrecision(fPrec);
			m_wE2.SetValuePrecision(fPrec);
			m_wE3.SetValuePrecision(fPrec);
			m_wE4.SetValuePrecision(fPrec);

			m_wSc.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uSc)));
			m_wPs.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uPs)));

			m_wE1.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE1)));
			m_wE2.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE2)));
			m_wE3.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE3)));
			m_wE4.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE4)));

			m_wE123.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE1 | uE2 | uE3)));
			m_wE321.Create(tvec<TValue, 1>(-TValue(1)), tvec<TBlade, 1>(TBlade(uE1 | uE2 | uE3)));

			m_wE1234.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE1 | uE2 | uE3 | uE4)));
			m_wE4321.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE1 | uE2 | uE3 | uE4)));
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Initialises this CBasisP3&lt;_TValue&gt;
		/// </summary>
		///
		/// <typeparam name="_TValue">	Type of the value. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename _TValue>
		void CBasisP3<_TValue>::_Init()
		{
			try
			{
				_CBasisP3<TValue>::_Init();

				TValue fP = TValPrec::GetValuePrecision();
				// const TValue fZ	= TValue(0);
				// const TValue fU	= TValue(1);
				// const TValue fN	= TValue(-1);

				TAN_GA_DEF_MULTIV_BASIS_P3(TValue, *this);

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis N3
				m_xStyle.SetValuePrecision(fP);
				m_xStyle
					// Grade 0
					<< TN(wSc, "")

					// Grade 1
					<< TN(wE1, "e1") << TN(wE2, "e2") << TN(wE3, "e3") << TN(wE4, "e4")

					// Grade 2
					<< TN(wE23, "e23") << TN(wE31, "e31") << TN(wE12, "e12") << TN(wE41, "e41") << TN(wE42, "e42") << TN(wE43, "e43")

					// Grade 3
					<< TN(wE234, "e234") << TN(wE314, "e314") << TN(wE124, "e124") << TN(wE123, "e123")

					// Grade 4
					<< TN(wE1234, "I");

				m_xStyle.EvalReciprocalBasis();
				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Scalar
				m_xBasisScalar.SetValuePrecision(fP);
				m_xBasisScalar
					<< TB(wSc);
				m_xBasisScalar.EvalReciprocalBasis();

				m_xMaskScalar.Reset();
				m_xMaskScalar.Insert(m_xBasisScalar, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Point
				m_xBasisPoint.SetValuePrecision(fP);
				m_xBasisPoint
					<< TB(wE1) << TB(wE2) << TB(wE3) << TB(wE4);
				m_xBasisPoint.EvalReciprocalBasis();

				m_xMaskPoint.Reset();
				m_xMaskPoint.Insert(m_xBasisPoint, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Line
				m_xBasisLine.SetValuePrecision(fP);
				m_xBasisLine
					<< TB(wE23) << TB(wE31) << TB(wE12) << TB(wE41) << TB(wE42) << TB(wE43);
				m_xBasisLine.EvalReciprocalBasis();

				m_xMaskLine.Reset();
				m_xMaskLine.Insert(m_xBasisLine, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Plane
				m_xBasisPlane.SetValuePrecision(fP);
				m_xBasisPlane
					<< TB(wE234) << TB(wE314) << TB(wE124) << TB(wE123);
				m_xBasisPlane.EvalReciprocalBasis();

				m_xMaskPlane.Reset();
				m_xMaskPlane.Insert(m_xBasisPlane, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Space
				m_xBasisSpace.SetValuePrecision(fP);
				m_xBasisSpace
					<< TB(wE1234);
				m_xBasisSpace.EvalReciprocalBasis();

				m_xMaskSpace.Reset();
				m_xMaskSpace.Insert(m_xBasisSpace, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Reflection
				m_xBasisReflection.SetValuePrecision(fP);
				m_xBasisReflection
					<< TB(wE1) << TB(wE2) << TB(wE3) << TB(wE4);
				m_xBasisReflection.EvalReciprocalBasis();

				m_xMaskReflection.Reset();
				m_xMaskReflection.Insert(m_xBasisReflection, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Rotor
				m_xBasisRotor.SetValuePrecision(fP);
				m_xBasisRotor
					<< TB(wSc)
					<< TB(wE23) << TB(wE31) << TB(wE12);
				m_xBasisRotor.EvalReciprocalBasis();

				m_xMaskRotor.Reset();
				m_xMaskRotor.Insert(m_xBasisRotor, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

				EvalBladeList(m_vBladeListPoint, m_xBasisPoint);
				EvalBladeList(m_vBladeListLine, m_xBasisLine);
				EvalBladeList(m_vBladeListRotor, m_xBasisRotor);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error initializing basis", xEx);
			}
		}
	}
} // .GA
