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
// Functions MapToBladeMask
template void GA::EvalBladeMask(TBladeMask &xBladeMask, const TMultivector &wA, bool bOnlyNonZeroComps);

template void GA::EvalProductBladeMask_GP(TBladeMask &xMaskC, const TMultivector &wA, const TBladeMask &xMaskB, bool bLeftToRight, bool bComplete);

template void GA::EvalProductBladeMask_IP(TBladeMask &xMaskC, const TMultivector &wA, const TBladeMask &xMaskB, bool bLeftToRight, bool bComplete);

template void GA::EvalProductBladeMask_OP(TBladeMask &xMaskC, const TMultivector &wA, const TBladeMask &xMaskB, bool bLeftToRight, bool bComplete);

template void GA::ToMatrix(TMatrix &matA, const TMultivector &wA, const TBladeMask &xMask);
template void GA::ToMultivector(TMultivector &wA, const TMatrix &matA, const TBladeMask &xMask);

template void GA::EvalProductMatrix_GP(TMatrix &matA, const TMultivector &wA, const TBladeMask &xMaskB, const TBladeMask &xMaskC, bool bLeftToRight, GA::EInv, GA::EInv);
template void GA::EvalProductMatrixArray_GP(TMatrix &matA, const std::vector<TMultivector> &wListA, const TBladeMask &xMaskB, const TBladeMask &xMaskC, bool bLeftToRight, GA::EInv, GA::EInv);
template void GA::EvalProductMatrix_GP(TMatrix &matA, const TMultivector &wA, const TBladeMask &xMaskA, const TBladeMask &xMaskB, const TBladeMask &xMaskC, bool bLeftToRight, GA::EInv, GA::EInv);

template void GA::EvalProductMatrix_IP(TMatrix &matA, const TMultivector &wA, const TBladeMask &xMaskB, const TBladeMask &xMaskC, bool bLeftToRight, GA::EInv, GA::EInv);
template void GA::EvalProductMatrixArray_IP(TMatrix &matA, const std::vector<TMultivector> &wListA, const TBladeMask &xMaskB, const TBladeMask &xMaskC, bool bLeftToRight, GA::EInv, GA::EInv);
template void GA::EvalProductMatrix_IP(TMatrix &matA, const TMultivector &wA, const TBladeMask &xMaskA, const TBladeMask &xMaskB, const TBladeMask &xMaskC, bool bLeftToRight, GA::EInv, GA::EInv);

template void GA::EvalProductMatrix_OP(TMatrix &matA, const TMultivector &wA, const TBladeMask &xMaskB, const TBladeMask &xMaskC, bool bLeftToRight, GA::EInv, GA::EInv);
template void GA::EvalProductMatrixArray_OP(TMatrix &matA, const std::vector<TMultivector> &wListA, const TBladeMask &xMaskB, const TBladeMask &xMaskC, bool bLeftToRight, GA::EInv, GA::EInv);
template void GA::EvalProductMatrix_OP(TMatrix &matA, const TMultivector &wA, const TBladeMask &xMaskA, const TBladeMask &xMaskB, const TBladeMask &xMaskC, bool bLeftToRight, GA::EInv, GA::EInv);

// ///////////////////////////////////////////////////////////////////////////////////////////////////////
// Functions MapToSubspace
template void GA::EvalBladeMask(TBladeMask &xBladeMask, const TSubspaceBasis &xSubspace);
// template void GA::EvalBladeList(tvec<TBlade, TBlade::VectorSpaceDimension>& vBladeList, const TSubspaceBasis& xSubspace);

template void GA::EvalProductSubspaceMask_GP(TSubspaceMask &xMaskC, const TSubspaceMask &xMaskA, const TSubspaceMask &xMaskB, const TStyle &xAlgebraBasis);
template void GA::EvalProductSubspaceMask_IP(TSubspaceMask &xMaskC, const TSubspaceMask &xMaskA, const TSubspaceMask &xMaskB, const TStyle &xAlgebraBasis);
template void GA::EvalProductSubspaceMask_OP(TSubspaceMask &xMaskC, const TSubspaceMask &xMaskA, const TSubspaceMask &xMaskB, const TStyle &xAlgebraBasis);

template void GA::ToMatrix(TMatrix &matA, const TMultivector &wA, const TSubspaceMask &xMask, const TSubspaceBasis &xAlgebraBasis);
template void GA::ToMatrix(TMatrix &matA, const std::vector<TMultivector> &vecwListA, const TSubspaceMask &xMask, const TSubspaceBasis &xAlgebraBasis);

template void GA::ToMultivector(TMultivector &wA, const TMatrix &matA, const TSubspaceMask &xMask, const TSubspaceBasis &xAlgebraBasis);
template void GA::ToMultivector(std::vector<TMultivector> &vecwListA, const TMatrix &matA, const TSubspaceMask &xMask, const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_GP_Reverse(TMatrix &matA,
											   const TMultivector &wA,
											   const bool bReverseA,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_GP_Reverse(TMatrix &matA,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const TMultivector &wB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_GP_Reverse(TMatrix &matA,
											   const std::vector<TMultivector> &wListA,
											   const bool bReverseA,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_GP_Reverse(TMatrix &matA,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const std::vector<TMultivector> &wListB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_GP_Reverse(TMatrix &matProduct,
											   const TMatrix &matA,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TStyle &xAlgebraBasis);

template void GA::EvalProductMatrix_GP_Reverse(TMatrix &matProduct,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const TMatrix &matB,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TStyle &xAlgebraBasis);

template void GA::EvalProductMatrix_OP_Reverse(TMatrix &matA,
											   const TMultivector &wA,
											   const bool bReverseA,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_OP_Reverse(TMatrix &matA,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const TMultivector &wB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_OP_Reverse(TMatrix &matA,
											   const std::vector<TMultivector> &wListA,
											   const bool bReverseA,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_OP_Reverse(TMatrix &matA,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const std::vector<TMultivector> &wListB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_OP_Reverse(TMatrix &matProduct,
											   const TMatrix &matA,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TStyle &xAlgebraBasis);

template void GA::EvalProductMatrix_OP_Reverse(TMatrix &matProduct,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const TMatrix &matB,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TStyle &xAlgebraBasis);

template void GA::EvalProductMatrix_IP_Reverse(TMatrix &matA,
											   const TMultivector &wA,
											   const bool bReverseA,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_IP_Reverse(TMatrix &matA,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const TMultivector &wB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

template void GA::EvalProductMatrix_IP_Reverse(TMatrix &matA,
											   const std::vector<TMultivector> &wListA,
											   const bool bReverseA,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TSubspaceBasis &xAlgebraBasis);

// template void GA::EvalProductMatrix_GP_Reverse(TMatrix& matA,
// 		const TSubspaceMask& xMaskA,
// 		const bool bReverseA,
// 		const std::vector<TMultivector>& wListB,
// 		const bool bReverseB,
// 		const TSubspaceMask& xMaskC,
// 		const TSubspaceBasis& xAlgebraBasis);

template void GA::EvalProductMatrix_IP_Reverse(TMatrix &matProduct,
											   const TMatrix &matA,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TStyle &xAlgebraBasis);

template void GA::EvalProductMatrix_IP_Reverse(TMatrix &matProduct,
											   const TSubspaceMask &xMaskA,
											   const bool bReverseA,
											   const TMatrix &matB,
											   const TSubspaceMask &xMaskB,
											   const bool bReverseB,
											   const TSubspaceMask &xMaskC,
											   const TStyle &xAlgebraBasis);
