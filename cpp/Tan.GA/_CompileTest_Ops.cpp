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

#include "Tan.Math/Matrix.h"

#include "Blade.h"
#include "BladeMask.h"
#include "Multivector.h"
#include "SubspaceMultivector.h"

#include "BasisE3.h"
#include "BasisP3.h"
#include "BasisN3.h"
#include "MultivectorE3.h"
#include "MultivectorP3.h"
#include "MultivectorN3.h"
#include "SubspaceMultivectorE3.h"
#include "SubspaceMultivectorP3.h"
#include "SubspaceMultivectorN3.h"
#include "DynamicMultivector.h"

#include "SubspaceBasis.h"
#include "SubspaceMask.h"

#include "Matrix_MapToBladeMask.h"
#include "Matrix_MapToSubspace.h"

using namespace Tan;

// ///////////////////////////////////////////////////////////////////////////////////////////////////////
// Typedefs for functions
typedef double TValue;
typedef CMatrix<TValue> TMatrix;
typedef GA::CBasisE3<TValue> TBasis;
typedef GA::CBlade<3, 0> TBlade;
typedef GA::CBladeMask<TBlade> TBladeMask;
typedef GA::CMultivector<TValue, TBlade> TMultivector;
typedef GA::_CMultivector<TValue, TBlade> _TMultivector;
typedef GA::CSubspaceMultivector<TValue, TBlade, 3> TSubMultivector;
typedef GA::_CSubspaceMultivector<TValue, TBlade, 3> _TSubMultivector;
typedef GA::CDynamicMultivector<TValue, TBlade> TDynMultivector;

typedef GA::CSubspaceBasis<TValue, TBlade> TSubspaceBasis;
typedef GA::CSubspaceMask<TSubspaceBasis> TSubspaceMask;
typedef GA::CMultivectorStyle<TValue, TBlade> TStyle;

// ///////////////////////////////////////////////////////////////////////////////////////////////////////
// Functions Operators

template void GA::VersorProduct(TMultivector &wC, const TMultivector &wVersor, const TMultivector &wB);
template void GA::VersorProduct(TMultivector &wC, const TMultivector &wVersor, const TDynMultivector &wB);
template void GA::VersorProduct(TMultivector &wC, const TDynMultivector &wVersor, const TDynMultivector &wB);
template void GA::VersorProduct(TDynMultivector &wC, const TMultivector &wVersor, const TMultivector &wB);
template void GA::VersorProduct(TMultivector &wC, const TSubMultivector &wVersor, const TMultivector &wB);
template void GA::VersorProduct(TMultivector &wC, const TSubMultivector &wVersor, const TSubMultivector &wB);

template void GA::VersorProduct(std::vector<TMultivector> &vecwC, const TMultivector &wVersor, const std::vector<TMultivector> &vecwB);
template void GA::VersorProduct(std::vector<TMultivector> &vecwC, const TMultivector &wVersor, const std::vector<TDynMultivector> &vecwB);
template void GA::VersorProduct(std::vector<TMultivector> &vecwC, const TDynMultivector &wVersor, const std::vector<TDynMultivector> &vecwB);
template void GA::VersorProduct(std::vector<TDynMultivector> &vecwC, const TMultivector &wVersor, const std::vector<TMultivector> &vecwB);
template void GA::VersorProduct(std::vector<TMultivector> &vecwC, const TSubMultivector &wVersor, const std::vector<TMultivector> &vecwB);
template void GA::VersorProduct(std::vector<TMultivector> &vecwC, const TSubMultivector &wVersor, const std::vector<TSubMultivector> &vecwB);

template void GA::GP(TMultivector &wC, const TMultivector &wVersor, const TMultivector &wB);
template void GA::GP(TMultivector &wC, const TMultivector &wVersor, const TDynMultivector &wB);
template void GA::GP(TMultivector &wC, const TDynMultivector &wVersor, const TDynMultivector &wB);
template void GA::GP(TDynMultivector &wC, const TMultivector &wVersor, const TMultivector &wB);
template void GA::GP(TMultivector &wC, const TSubMultivector &wVersor, const TMultivector &wB);
template void GA::GP(TMultivector &wC, const TSubMultivector &wVersor, const TSubMultivector &wB);

template void GA::IP(TMultivector &wC, const TMultivector &wVersor, const TMultivector &wB);
template void GA::IP(TMultivector &wC, const TMultivector &wVersor, const TDynMultivector &wB);
template void GA::IP(TMultivector &wC, const TDynMultivector &wVersor, const TDynMultivector &wB);
template void GA::IP(TDynMultivector &wC, const TMultivector &wVersor, const TMultivector &wB);
template void GA::IP(TMultivector &wC, const TSubMultivector &wVersor, const TMultivector &wB);
template void GA::IP(TMultivector &wC, const TSubMultivector &wVersor, const TSubMultivector &wB);

template void GA::OP(TMultivector &wC, const TMultivector &wVersor, const TMultivector &wB);
template void GA::OP(TMultivector &wC, const TMultivector &wVersor, const TDynMultivector &wB);
template void GA::OP(TMultivector &wC, const TDynMultivector &wVersor, const TDynMultivector &wB);
template void GA::OP(TDynMultivector &wC, const TMultivector &wVersor, const TMultivector &wB);
template void GA::OP(TMultivector &wC, const TSubMultivector &wVersor, const TMultivector &wB);
template void GA::OP(TMultivector &wC, const TSubMultivector &wVersor, const TSubMultivector &wB);

template void GA::GP_Reverse(TMultivector &wC, const TMultivector &wA, const bool bReverseA, const TMultivector &wB, const bool bReverseB);
template void GA::GP_Reverse(TMultivector &wC, const TSubMultivector &wA, const bool bReverseA, const TMultivector &wB, const bool bReverseB);
template void GA::GP_Reverse(TMultivector &wC, const TDynMultivector &wA, const bool bReverseA, const TMultivector &wB, const bool bReverseB);
template void GA::GP_Reverse(TDynMultivector &wC, const TMultivector &wA, const bool bReverseA, const TMultivector &wB, const bool bReverseB);
template void GA::GP_Reverse(TDynMultivector &wC, const TSubMultivector &wA, const bool bReverseA, const TMultivector &wB, const bool bReverseB);
template void GA::GP_Reverse(TDynMultivector &wC, const TDynMultivector &wA, const bool bReverseA, const TMultivector &wB, const bool bReverseB);

template void GA::GP_Conjugate(TMultivector &wC, const TMultivector &wA, const bool bConjugateA, const TMultivector &wB, const bool bConjugateB);
template void GA::GP_Conjugate(TMultivector &wC, const TSubMultivector &wA, const bool bConjugateA, const TMultivector &wB, const bool bConjugateB);
template void GA::GP_Conjugate(TMultivector &wC, const TDynMultivector &wA, const bool bConjugateA, const TMultivector &wB, const bool bConjugateB);
template void GA::GP_Conjugate(TDynMultivector &wC, const TMultivector &wA, const bool bConjugateA, const TMultivector &wB, const bool bConjugateB);
template void GA::GP_Conjugate(TDynMultivector &wC, const TSubMultivector &wA, const bool bConjugateA, const TMultivector &wB, const bool bConjugateB);
template void GA::GP_Conjugate(TDynMultivector &wC, const TDynMultivector &wA, const bool bConjugateA, const TMultivector &wB, const bool bConjugateB);

template void GA::SP(TValue &fValue, const TMultivector &wA, const TMultivector &wB);
template void GA::SP(TValue &fValue, const TSubMultivector &wA, const TMultivector &wB);
template void GA::SP(TValue &fValue, const TDynMultivector &wA, const TMultivector &wB);

template void GA::ScalarProductOperator(TValue &fValue, const TValue &fValA, const TBlade &blA, const TMultivector &wB);
template void GA::ScalarProductOperator(TValue &fValue, const TValue &fValA, const TBlade &blA, const TSubMultivector &wB);
template void GA::ScalarProductOperator(TValue &fValue, const TValue &fValA, const TBlade &blA, const TDynMultivector &wB);

template TMultivector GA::GetReverse(const TMultivector &wB);
template TSubMultivector GA::GetReverse(const TSubMultivector &wB);
template TDynMultivector GA::GetReverse(const TDynMultivector &wB);

template void GA::Reverse(TMultivector &wA);
template void GA::Reverse(TSubMultivector &wA);
template void GA::Reverse(TDynMultivector &wA);

template TMultivector GA::GetConjugate(const TMultivector &wB);
template TSubMultivector GA::GetConjugate(const TSubMultivector &wB);
template TDynMultivector GA::GetConjugate(const TDynMultivector &wB);

template void GA::Conjugate(TMultivector &wA);
template void GA::Conjugate(TSubMultivector &wA);
template void GA::Conjugate(TDynMultivector &wA);

template TMultivector &GA::Complement(TMultivector &wB, const TMultivector &wA);
template TMultivector &GA::Complement(TMultivector &wB, const TSubMultivector &wA);
template TMultivector &GA::Complement(TMultivector &wB, const TDynMultivector &wA);

template TMultivector &GA::Dual(TMultivector &wB, const TMultivector &wA);
template TMultivector &GA::Dual(TMultivector &wB, const TSubMultivector &wA);
template TMultivector &GA::Dual(TMultivector &wB, const TDynMultivector &wA);

template TMultivector &GA::LDual(TMultivector &wB, const TMultivector &wA);
template TMultivector &GA::LDual(TMultivector &wB, const TSubMultivector &wA);
template TMultivector &GA::LDual(TMultivector &wB, const TDynMultivector &wA);

template TMultivector GA::GetGradeProjection(const TMultivector &wB, unsigned uGrade);
template TSubMultivector GA::GetGradeProjection(const TSubMultivector &wB, unsigned uGrade);
template TDynMultivector GA::GetGradeProjection(const TDynMultivector &wB, unsigned uGrade);

template void GA::GradeProjection(TMultivector &wA, unsigned uGrade);
template void GA::GradeProjection(TSubMultivector &wA, unsigned uGrade);
template void GA::GradeProjection(TDynMultivector &wA, unsigned uGrade);

template TValue GA::MagnitudeSquared(const TMultivector &wA);
template TValue GA::MagnitudeSquared(const TSubMultivector &wA);
template TValue GA::MagnitudeSquared(const TDynMultivector &wA);

template TValue GA::Magnitude(const TMultivector &wA);
template TValue GA::Magnitude(const TSubMultivector &wA);
template TValue GA::Magnitude(const TDynMultivector &wA);

template TValue GA::Scalar(const TMultivector &wA);
template TValue GA::Scalar(const TSubMultivector &wA);
template TValue GA::Scalar(const TDynMultivector &wA);

template bool GA::IsScalar(const TMultivector &wA);
template bool GA::IsZero(const TMultivector &wA);
template void GA::ProjectTo(TMultivector &wA, const TMultivector &wB);
template void GA::ProjectToBlade(TValue &fValA, const TBlade &blA, const TMultivector &wB);
template void GA::ConvertMultivectorType(TMultivector &wA, const TMultivector &wB);

template TMultivector &GA::Add(TMultivector &wC, const TMultivector &wA, const TMultivector &wB);
template TMultivector &GA::Sub(TMultivector &wC, const TMultivector &wA, const TMultivector &wB);
