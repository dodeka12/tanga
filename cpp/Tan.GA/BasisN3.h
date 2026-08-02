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

#include "SubspaceMultivector.h"
#include "BladeMask.h"
#include "DynamicMultivector.h"
#include "MultivectorStyle.h"

#define TAN_GA_DECL_BASIS_N3(theType) \
	static const unsigned uSc = GA::CBasisN3<theType>::uSc; \
	static const unsigned uE1 = GA::CBasisN3<theType>::uE1; \
	static const unsigned uE2 = GA::CBasisN3<theType>::uE2; \
	static const unsigned uE3 = GA::CBasisN3<theType>::uE3; \
	static const unsigned uEp = GA::CBasisN3<theType>::uEp; \
	static const unsigned uEm = GA::CBasisN3<theType>::uEm; \
	static const unsigned uPs = GA::CBasisN3<theType>::uPs;

#define TAN_GA_DEF_MULTIV_BASIS_N3(theType, theBasis) \
	GA::CMultivector<theType, typename GA::_CBasisN3<theType>::TBlade> wSc; \
	GA::CMultivector<theType, typename GA::_CBasisN3<theType>::TBlade> wE1, wE2, wE3, wEi, wEo, wEinf; \
	GA::CMultivector<theType, typename GA::_CBasisN3<theType>::TBlade> wE23, wE31, wE12, wE1i, wE2i, wE3i, wE1o, wE2o, wE3o, wEio; \
	GA::CMultivector<theType, typename GA::_CBasisN3<theType>::TBlade> wE23i, wE31i, wE12i,      wE23o, wE31o, wE12o, wE1io, wE2io, wE3io, wE123; \
	GA::CMultivector<theType, typename GA::_CBasisN3<theType>::TBlade> wE23io, wE31io, wE12io, wE123i, wE123o; \
	GA::CMultivector<theType, typename GA::_CBasisN3<theType>::TBlade> wE123io, wI; \
	wSc   = (theBasis).Sc(); \
	wE1   = (theBasis).E1(); \
	wE2   = (theBasis).E2(); \
	wE3   = (theBasis).E3();  \
	wEi   = (theBasis).Einf();        \
	wEo   = (theBasis).Eo();  \
	wEinf = wEi; \
	GA::OP(wE23, wE2, wE3); \
	GA::OP(wE31, wE3, wE1); \
	GA::OP(wE12, wE1, wE2); \
	GA::OP(wE1i, wE1, wEi); \
	GA::OP(wE2i, wE2, wEi); \
	GA::OP(wE3i, wE3, wEi); \
	GA::OP(wE1o, wE1, wEo); \
	GA::OP(wE2o, wE2, wEo); \
	GA::OP(wE3o, wE3, wEo); \
	GA::OP(wEio, wEi, wEo); \
	GA::OP(wE23i, wE23, wEi); \
	GA::OP(wE31i, wE31, wEi); \
	GA::OP(wE12i, wE12, wEi); \
	GA::OP(wE23o, wE23, wEo); \
	GA::OP(wE31o, wE31, wEo); \
	GA::OP(wE12o, wE12, wEo); \
	GA::OP(wE1io, wE1i, wEo); \
	GA::OP(wE2io, wE2i, wEo); \
	GA::OP(wE3io, wE3i, wEo); \
	GA::OP(wE123, wE12, wE3); \
	GA::OP(wE23io, wE23i, wEo); \
	GA::OP(wE31io, wE31i, wEo); \
	GA::OP(wE12io, wE12i, wEo); \
	GA::OP(wE123i, wE123, wEi); \
	GA::OP(wE123o, wE123, wEo); \
	GA::OP(wE123io, wE123i, wEo); \
	wI = wE123io;

namespace Tan
{
	namespace GA
	{
		template<typename _TValue>
		class _CBasisN3 : public CValuePrecision<_TValue>
		{
		public:

			static const unsigned VectorSpaceDimension = 5;
			static const unsigned VectorSpaceSignature = (1 << 4);

			static const unsigned uSc = 0;
			static const unsigned uE1 = (1 << 0);
			static const unsigned uE2 = (1 << 1);
			static const unsigned uE3 = (1 << 2);
			static const unsigned uEp = (1 << 3);
			static const unsigned uEm = (1 << 4);

			static const unsigned uEpm = (uEp | uEm);
			static const unsigned uPs  = (uE1 | uE2 | uE3 | uEp | uEm);

		public:

			typedef _TValue TValue;
			typedef CBlade<VectorSpaceDimension, VectorSpaceSignature> TBlade;
			typedef _CMultivector<TValue, TBlade> TMultivector;
			typedef CValuePrecision<_TValue> TValPrec;

			typedef _CSubspaceMultivector<TValue, TBlade, 1> TBaseVec1;
			typedef _CSubspaceMultivector<TValue, TBlade, 2> TBaseVec2;

		public:

			_CBasisN3() { }

			_CBasisN3(TValue fPrec)
			{
				SetValuePrecision(fPrec);
				_Init();
			}

			const TBaseVec1& Sc()   const   { return m_wSc; }
			const TBaseVec1& Ps()   const   { return m_wPs; }

			const TBaseVec1& E1()   const   { return m_wE1; }
			const TBaseVec1& E2()   const   { return m_wE2; }
			const TBaseVec1& E3()   const   { return m_wE3; }
			const TBaseVec1& Ep()   const   { return m_wEp; }
			const TBaseVec1& Em()   const   { return m_wEm; }

			const TBaseVec1& Epm()  const   { return m_wEpm;        }

			const TBaseVec2& Einf() const   { return m_wEinf;       }
			const TBaseVec2& Eo()   const   { return m_wEo; }

			const TBaseVec1& E123() const   { return m_wE123;       }
			const TBaseVec1& E321() const   { return m_wE321;       }

			static const TBaseVec2& CreateEinf()
			{
				TBaseVec2 wEinf(tvec<TValue, 2>(TValue(1.0), TValue(1.0)), tvec<TBlade, 2>(TBlade(uEm), TBlade(uEp)));
				return wEinf;
			}

			static const TBaseVec2& CreateEo()
			{
				TBaseVec2 wEo(tvec<TValue, 2>(TValue(0.5), TValue(-0.5)), tvec<TBlade, 2>(TBlade(uEm), TBlade(uEp)));
				return wEo;
			}

		protected:

			inline void _Init();

		protected:

			TBaseVec1 m_wSc;
			TBaseVec1 m_wPs;
			TBaseVec1 m_wE1;
			TBaseVec1 m_wE2;
			TBaseVec1 m_wE3;
			TBaseVec1 m_wEp;
			TBaseVec1 m_wEm;
			TBaseVec1 m_wEpm;

			TBaseVec2 m_wEinf;
			TBaseVec2 m_wEo;

			TBaseVec1 m_wE123;
			TBaseVec1 m_wE321;
		};

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	 basis n 3.
		/// </summary>
		///
		/// <typeparam name="_TValue">	Type of the walue. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename _TValue>
		class CBasisN3 : public _CBasisN3<_TValue>
		{
		public:

			typedef _TValue TValue;
			typedef _CBasisN3<_TValue> TBase;
			typedef typename TBase::TBlade TBlade;
			typedef typename TBase::TMultivector TMultivector;
			typedef typename TBase::TValPrec TValPrec;

			typedef CMultivectorStyle<TValue, TBlade> TStyle;
			typedef typename TStyle::TBasis TBasis;
			typedef typename TStyle::SPairName TN;
			typedef typename TStyle::SBladePair TB;
			typedef CSubspaceMask<TBasis> TMask;

			typedef tvec3<TValue> TVec3;
			typedef _CSubspaceMultivector<TValue, TBlade,  5> TPoint;
			typedef _CSubspaceMultivector<TValue, TBlade,  4> TRotor;
			typedef _CSubspaceMultivector<TValue, TBlade,  7> TTranslator;
			typedef _CSubspaceMultivector<TValue, TBlade, 12> TMotor;

			typedef tvec<TBlade,  5> TBladeListPoint;
			typedef tvec<TBlade,  4> TBladeListRotor;
			typedef tvec<TBlade,  7> TBladeListTranslator;
			typedef tvec<TBlade, 12> TBladeListMotor;

			typedef std::vector<TVec3> TVec3List;
			typedef std::vector<TPoint> TPointList;
			typedef std::vector<TRotor> TRotorList;

			typedef std::vector<TMultivector> TMultivectorList;

		public:
			static const unsigned uSc = TBase::uSc;
			static const unsigned uE1 = TBase::uE1;
			static const unsigned uE2 = TBase::uE2;
			static const unsigned uE3 = TBase::uE3;
			static const unsigned uEp = TBase::uEp;
			static const unsigned uEm = TBase::uEm;

			static const unsigned uEpm = TBase::uEpm;
			static const unsigned uPs  = TBase::uPs;

		public:

			CBasisN3()
			{
				TValPrec::Reset();
				_Init();
			}

			CBasisN3(TValue fPrec)
			{
				TValPrec::SetValuePrecision(fPrec);
				_Init();
			}

			std::string ToString()
			{
				return m_xStyle.ToString((CSubspaceBasis<TValue, TBlade>)m_xStyle);
			}

			template<typename TMultivectorA>
			std::string ToString(const TMultivectorA& wA)
			{
				return m_xStyle.ToString(wA);
			}

			template<typename TMultivectorA>
			std::string ToString(const std::vector<TMultivectorA>& wListA) const
			{
				return m_xStyle.ToString(wListA);
			}

			std::string ToString(const TBasis& xSubBasis) const
			{
				return m_xStyle.ToString(xSubBasis);
			}

			std::string ToString(const TMask& xMask, bool bSimple = false) const
			{
				return m_xStyle.ToString(xMask, bSimple);
			}

			const TBasis& Basis() const                { return m_xStyle; }
			const TStyle& Style() const                { return m_xStyle; }

			const TBasis& BasisScalar() const                { return m_xBasisScalar; }
			const TBasis& BasisPoint() const                { return m_xBasisPoint; }
			const TBasis& BasisPointPair() const                { return m_xBasisPointPair; }
			const TBasis& BasisLine() const                { return m_xBasisLine; }
			const TBasis& BasisCircle() const                { return m_xBasisCircle; }
			const TBasis& BasisPlane() const                { return m_xBasisPlane; }
			const TBasis& BasisSphere() const                { return m_xBasisSphere; }
			const TBasis& BasisSpace() const                { return m_xBasisSpace; }

			const TBasis& BasisReflection() const                { return m_xBasisReflection; }
			const TBasis& BasisInversion() const                { return m_xBasisInversion; }
			const TBasis& BasisRotor() const                { return m_xBasisRotor; }
			const TBasis& BasisTranslator() const                { return m_xBasisTranslator; }
			const TBasis& BasisDilator() const                { return m_xBasisDilator; }
			const TBasis& BasisGeneralDilator() const                { return m_xBasisGeneralDilator; }
			const TBasis& BasisMotor() const                { return m_xBasisMotor; }
			const TBasis& BasisGeneralRotor() const                { return m_xBasisGeneralRotor; }

			const TMask& MaskScalar() const                { return m_xMaskScalar; }
			const TMask& MaskPoint() const                { return m_xMaskPoint; }
			const TMask& MaskPointPair() const                { return m_xMaskPointPair; }
			const TMask& MaskLine() const                { return m_xMaskLine; }
			const TMask& MaskCircle() const                { return m_xMaskCircle; }
			const TMask& MaskPlane() const                { return m_xMaskPlane; }
			const TMask& MaskSphere() const                { return m_xMaskSphere; }
			const TMask& MaskSpace() const                { return m_xMaskSpace; }

			const TMask& MaskReflection() const                { return m_xMaskReflection; }
			const TMask& MaskInversion() const                { return m_xMaskInversion; }
			const TMask& MaskRotor() const                { return m_xMaskRotor; }
			const TMask& MaskTranslator() const                { return m_xMaskTranslator; }
			const TMask& MaskDilator() const                { return m_xMaskDilator; }
			const TMask& MaskGeneralDilator() const                { return m_xMaskGeneralDilator; }
			const TMask& MaskMotor() const                { return m_xMaskMotor; }
			const TMask& MaskGeneralRotor() const                { return m_xMaskGeneralRotor; }

			const TBladeListPoint&       BladeListPoint() const { return m_vBladeListPoint; }
			const TBladeListRotor&       BladeListRotor() const { return m_vBladeListRotor; }
			const TBladeListTranslator&       BladeListTranslator() const { return m_vBladeListTranslator; }
			const TBladeListMotor&       BladeListMotor() const { return m_vBladeListMotor; }

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
			TPoint& CreatePoint(TPoint& wPnt, const TVec3& vPnt3d)
			{
				TValue fLen = length_square(vPnt3d);

				wPnt.Create(
						tvec<TValue, 5>(vPnt3d.x, vPnt3d.y, vPnt3d.z, TValue(0.5) * (fLen - TValue(1)), TValue(0.5) * (fLen + TValue(1))),
						m_vBladeListPoint);

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
			TPointList& CreatePoint(TPointList& vecwPnt, const TVec3List& vecvPnt3d)
			{
				// Declare blade type
				typedef CBasisN3<TValue>::TBlade TBlade;

				// Declare blade ids for N3 basis
				TAN_GA_DECL_BASIS_N3(TValue);

				vecwPnt.resize(vecvPnt3d.size());
				Transform(vecwPnt, vecvPnt3d, [&](TPoint& wPnt, const TVec3& vPnt3d)
						{
							CreatePoint(wPnt, vPnt3d);
						});

				return vecwPnt;
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
			template<typename TMultivectorX>
			bool IsPoint(const TMultivectorX& wPnt)
			{
				bool bHasGrade1 = false;
				TMultivectorX wA(wPnt.GetValuePrecision());

				// Test whether all elements are of grade 1
				if (!wPnt.ForEachBladeTest([&](const TValue& fValA, const TBlade& blA) -> bool
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

							    return true;
						    }))
				{
					return false;
				}

				if (!bHasGrade1)
				{
					return false;
				}

				// Calculate geometric product of point with itself.
				GP(wA, wPnt, wPnt);

				// The result must be zero if wA is a point.
				return GA::IsZero(wA);
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
			template<typename TMultivectorX>
			bool TryPointToVec3(TVec3& vPnt3d, const TMultivectorX& wPnt)
			{
				typedef typename TMultivectorX::TBlade TBlade;
				TValue fValueEo;
				typename TMultivectorX::TValue fValue;

				GA::SP(fValueEo, wPnt, TBase::m_wEinf);
				fValueEo = -fValueEo;

				if (wPnt.IsZero(fValueEo))
				{
					return false;
				}

				wPnt.GetValueBlade(fValue, TBlade(CBasisN3<TValue>::uE1));
				vPnt3d.x = TValue(fValue) / fValueEo;

				wPnt.GetValueBlade(fValue, TBlade(CBasisN3<TValue>::uE2));
				vPnt3d.y = TValue(fValue) / fValueEo;

				wPnt.GetValueBlade(fValue, TBlade(CBasisN3<TValue>::uE3));
				vPnt3d.z = TValue(fValue) / fValueEo;

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
			template<typename TMultivectorX>
			void PointToVec3(TVec3& vPnt3d, const TMultivectorX& wPnt)
			{
				if (!TryPointToVec3(vPnt3d, wPnt))
				{
					TAN_THROW_RT("Cannot convert conformal multivector to Euclidean point");
				}
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
			template<typename TMultivectorX>
			TVec3List& PointToVec3(TVec3List& vecvPnt3d, const std::vector<TMultivectorX>& vecwPnt)
			{
				try
				{
					vecvPnt3d.resize(vecwPnt.size());
					Transform(vecvPnt3d, vecwPnt, [&](TVec3& vPnt3d, const TMultivectorX& wPnt)
							{
								vPnt3d.zero();
								TryPointToVec3(vPnt3d, wPnt);
							});

					return vecvPnt3d;
				}
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error converting point list to list of vector 3", xEx);
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
			TRotor& CreateRotor(TRotor& wRotor, const TVec3& vRotationAxis, const TValue& dRotationAngleRad)
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
				catch (std::exception& xEx)
				{
					TAN_RETHROW("Error creating rotor", xEx);
				}
			}

			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			/// <summary>
			/// 	Translators.
			/// </summary>
			///
			/// <param name="wTranslator"> 	[in,out] The translator. </param>
			/// <param name="vTranslation">	The translation. </param>
			///
			/// <returns>	. </returns>
			/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
			TTranslator& CreateTranslator(TTranslator& wTranslator, const TVec3& vTranslation)
			{
				TValue fNegHalf = -TValue(0.5);

				// REVIEW which create is called here
				wTranslator.Create(
						tvec<TValue, 7>(TValue(1),
								fNegHalf * vTranslation.x, fNegHalf * vTranslation.y, fNegHalf * vTranslation.z,
								fNegHalf * vTranslation.x, fNegHalf * vTranslation.y, fNegHalf * vTranslation.z),
						tvec<TBlade, 7>(uSc, uE1 | uEp, uE2 | uEp, uE3 | uEp, uE1 | uEm, uE2 | uEm, uE3 | uEm));

				wTranslator.SetValuePrecision(TValPrec::GetValuePrecision());

				return wTranslator;
			}

		protected:

			inline void _Init();

		protected:

			TStyle m_xStyle;

			TBasis m_xBasisScalar;
			TBasis m_xBasisPoint;
			TBasis m_xBasisPointPair;
			TBasis m_xBasisLine;
			TBasis m_xBasisCircle;
			TBasis m_xBasisPlane;
			TBasis m_xBasisSphere;
			TBasis m_xBasisSpace;

			TBasis m_xBasisReflection;
			TBasis m_xBasisInversion;
			TBasis m_xBasisRotor;
			TBasis m_xBasisTranslator;
			TBasis m_xBasisDilator;
			TBasis m_xBasisGeneralDilator;
			TBasis m_xBasisMotor;
			TBasis m_xBasisGeneralRotor;

			TMask m_xMaskScalar;
			TMask m_xMaskPoint;
			TMask m_xMaskPointPair;
			TMask m_xMaskLine;
			TMask m_xMaskCircle;
			TMask m_xMaskPlane;
			TMask m_xMaskSphere;
			TMask m_xMaskSpace;

			TMask m_xMaskReflection;
			TMask m_xMaskInversion;
			TMask m_xMaskRotor;
			TMask m_xMaskTranslator;
			TMask m_xMaskDilator;
			TMask m_xMaskGeneralDilator;
			TMask m_xMaskMotor;
			TMask m_xMaskGeneralRotor;

			TBladeListPoint                 m_vBladeListPoint;
			TBladeListRotor                 m_vBladeListRotor;
			TBladeListTranslator    m_vBladeListTranslator;
			TBladeListMotor                 m_vBladeListMotor;
		};

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Initialises this _CBasisN3&lt;_TValue&gt;
		/// </summary>
		///
		/// <typeparam name="_TValue">	Type of the walue. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename _TValue>
		void _CBasisN3<_TValue>::_Init()
		{
			try
			{
				TValue fPrec = TValPrec::GetValuePrecision();
				m_wSc.SetValuePrecision(fPrec);
				m_wPs.SetValuePrecision(fPrec);
				m_wE1.SetValuePrecision(fPrec);
				m_wE2.SetValuePrecision(fPrec);
				m_wE3.SetValuePrecision(fPrec);
				m_wEp.SetValuePrecision(fPrec);
				m_wEm.SetValuePrecision(fPrec);
				m_wEpm.SetValuePrecision(fPrec);

				m_wEinf.SetValuePrecision(fPrec);
				m_wEo.SetValuePrecision(fPrec);

				m_wSc.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uSc)));
				m_wPs.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uPs)));

				m_wE1.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE1)));
				m_wE2.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE2)));
				m_wE3.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE3)));
				m_wEp.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uEp)));
				m_wEm.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uEm)));
				m_wEpm.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uEpm)));

				m_wEinf.Create(tvec<TValue, 2>(TValue(1.0), TValue(1.0)), tvec<TBlade, 2>(TBlade(uEm), TBlade(uEp)));
				m_wEo.Create(tvec<TValue, 2>(TValue(0.5), TValue(-0.5)), tvec<TBlade, 2>(TBlade(uEm), TBlade(uEp)));

				m_wE123.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE1 | uE2 | uE3)));
				m_wE321.Create(tvec<TValue, 1>(-TValue(1)), tvec<TBlade, 1>(TBlade(uE1 | uE2 | uE3)));
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error initializing N3 Basis", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Initialises this CBasisN3&lt;_TValue&gt;
		/// </summary>
		///
		/// <typeparam name="_TValue">	Type of the walue. </typeparam>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename _TValue>
		void CBasisN3<_TValue>::_Init()
		{
			try
			{
				_CBasisN3<TValue>::_Init();

				TValue fP = TValPrec::GetValuePrecision();

				TAN_GA_DEF_MULTIV_BASIS_N3(TValue, *this);

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis N3
				m_xStyle.SetValuePrecision(fP);
				m_xStyle
				// Grade 0
					<< TN(wSc, "")

					// Grade 1
					<< TN(wE1, "e1") << TN(wE2, "e2") << TN(wE3, "e3") << TN(wEi, "ei") << TN(wEo, "eo")

					// Grade 2
					<< TN(wE23, "e23")      << TN(wE31, "e31")      << TN(wE12, "e12")
					<< TN(wE1i, "e1i")      << TN(wE2i, "e2i")      << TN(wE3i, "e3i")
					<< TN(wE1o, "e1o")  << TN(wE2o, "e2o")  << TN(wE3o, "e3o")
					<< TN(wEio, "E")

					// Grade 3
					<< TN(wE1io, "e1E")             << TN(wE2io, "e2E")             << TN(wE3io, "e3E")
					<< TN(wE23i, "e23i")    << TN(wE31i, "e31i")    << TN(wE12i, "e12i")
					<< TN(wE23o, "e23o")    << TN(wE31o, "e31o")    << TN(wE12o, "e12o")
					<< TN(wE123, "e123")

					// Grade 4
					<< TN(wE23io, "e23E")   << TN(wE31io, "e31E")   << TN(wE12io, "e12E")
					<< TN(wE123i, "e123i")  << TN(wE123o, "e123o")

					// Grade 5
					<< TN(wE123io, "I");

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
					<< TB(wE1) << TB(wE2) << TB(wE3) << TB(wEi) << TB(wEo);
				m_xBasisPoint.EvalReciprocalBasis();

				m_xMaskPoint.Reset();
				m_xMaskPoint.Insert(m_xBasisPoint, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Point Pair
				m_xBasisPointPair.SetValuePrecision(fP);
				m_xBasisPointPair
					<< TB(wE23)     << TB(wE31)     << TB(wE12)
					<< TB(wE1i)     << TB(wE2i)     << TB(wE3i)
					<< TB(wE1o)     << TB(wE2o)     << TB(wE3o)
					<< TB(wEio);
				m_xBasisPointPair.EvalReciprocalBasis();

				m_xMaskPointPair.Reset();
				m_xMaskPointPair.Insert(m_xBasisPointPair, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Line
				m_xBasisLine.SetValuePrecision(fP);
				m_xBasisLine
					<< TB(wE23i) << TB(wE31i)       << TB(wE12i)
					<< TB(wE1io) << TB(wE2io)       << TB(wE3io);
				m_xBasisLine.EvalReciprocalBasis();

				m_xMaskLine.Reset();
				m_xMaskLine.Insert(m_xBasisLine, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Circle
				m_xBasisCircle.SetValuePrecision(fP);
				m_xBasisCircle
					<< TB(wE23i) << TB(wE31i) << TB(wE12i)
					<< TB(wE23o) << TB(wE31o) << TB(wE12o)
					<< TB(wE1io) << TB(wE2io) << TB(wE3io)
					<< TB(wE123);
				m_xBasisCircle.EvalReciprocalBasis();

				m_xMaskCircle.Reset();
				m_xMaskCircle.Insert(m_xBasisCircle, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Plane
				m_xBasisPlane.SetValuePrecision(fP);
				m_xBasisPlane
					<< TB(wE23io) << TB(wE31io) << TB(wE12io)
					<< TB(wE123i);
				m_xBasisPlane.EvalReciprocalBasis();

				m_xMaskPlane.Reset();
				m_xMaskPlane.Insert(m_xBasisPlane, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Sphere
				m_xBasisSphere.SetValuePrecision(fP);
				m_xBasisSphere
					<< TB(wE23io) << TB(wE31io) << TB(wE12io)
					<< TB(wE123i) << TB(wE123o);
				m_xBasisSphere.EvalReciprocalBasis();

				m_xMaskSphere.Reset();
				m_xMaskSphere.Insert(m_xBasisSphere, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Space
				m_xBasisSpace.SetValuePrecision(fP);
				m_xBasisSpace
					<< TB(wE123io);
				m_xBasisSpace.EvalReciprocalBasis();

				m_xMaskSpace.Reset();
				m_xMaskSpace.Insert(m_xBasisSpace, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Reflection
				m_xBasisReflection.SetValuePrecision(fP);
				m_xBasisReflection
					<< TB(wE1) << TB(wE2) << TB(wE3) << TB(wEi);
				m_xBasisReflection.EvalReciprocalBasis();

				m_xMaskReflection.Reset();
				m_xMaskReflection.Insert(m_xBasisReflection, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Inversion
				m_xBasisInversion.SetValuePrecision(fP);
				m_xBasisInversion
					<< TB(wE1) << TB(wE2) << TB(wE3) << TB(wEi) << TB(wEo);
				m_xBasisInversion.EvalReciprocalBasis();

				m_xMaskInversion.Reset();
				m_xMaskInversion.Insert(m_xBasisInversion, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Rotor
				m_xBasisRotor.SetValuePrecision(fP);
				m_xBasisRotor
					<< TB(wSc)
					<< TB(wE23)     << TB(wE31)     << TB(wE12);
				m_xBasisRotor.EvalReciprocalBasis();

				m_xMaskRotor.Reset();
				m_xMaskRotor.Insert(m_xBasisRotor, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Translator
				m_xBasisTranslator.SetValuePrecision(fP);
				m_xBasisTranslator
					<< TB(wSc)
					<< TB(wE1i)     << TB(wE2i)     << TB(wE3i);
				m_xBasisTranslator.EvalReciprocalBasis();

				m_xMaskTranslator.Reset();
				m_xMaskTranslator.Insert(m_xBasisTranslator, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Dilator
				m_xBasisDilator.SetValuePrecision(fP);
				m_xBasisDilator
					<< TB(wSc)
					<< TB(wEio);
				m_xBasisDilator.EvalReciprocalBasis();

				m_xMaskDilator.Reset();
				m_xMaskDilator.Insert(m_xBasisDilator, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis General Dilator
				m_xBasisGeneralDilator.SetValuePrecision(fP);
				m_xBasisGeneralDilator
					<< TB(wSc)
					<< TB(wE1i)     << TB(wE2i)     << TB(wE3i)
					<< TB(wEio);
				m_xBasisGeneralDilator.EvalReciprocalBasis();

				m_xMaskGeneralDilator.Reset();
				m_xMaskGeneralDilator.Insert(m_xBasisGeneralDilator, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis Motor
				m_xBasisMotor.SetValuePrecision(fP);
				m_xBasisMotor
					<< TB(wSc)
					<< TB(wE23)     << TB(wE31)     << TB(wE12)
					<< TB(wE1i)     << TB(wE2i)     << TB(wE3i)
					<< TB(wE123i);
				m_xBasisMotor.EvalReciprocalBasis();

				m_xMaskMotor.Reset();
				m_xMaskMotor.Insert(m_xBasisMotor, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// Basis General Rotor
				m_xBasisGeneralRotor.SetValuePrecision(fP);
				m_xBasisGeneralRotor
					<< TB(wSc)
					<< TB(wE23)     << TB(wE31)     << TB(wE12)
					<< TB(wE1i)     << TB(wE2i)     << TB(wE3i);
				m_xBasisGeneralRotor.EvalReciprocalBasis();

				m_xMaskGeneralRotor.Reset();
				m_xMaskGeneralRotor.Insert(m_xBasisGeneralRotor, Basis());

				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

				EvalBladeList(m_vBladeListPoint, m_xBasisPoint);
				EvalBladeList(m_vBladeListRotor, m_xBasisRotor);
				EvalBladeList(m_vBladeListTranslator, m_xBasisTranslator);
				EvalBladeList(m_vBladeListMotor, m_xBasisMotor);
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error initializing N3 Basis", xEx);
			}
		}
	}
}	// .GA
