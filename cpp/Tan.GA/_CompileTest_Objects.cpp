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
template class CMatrix<float>;
template class CMatrix<double>;

typedef GA::CBlade<3, 0> TBlade;

template class GA::CBlade<3, 0>;
template class GA::CBladeMask<TBlade>;
template class GA::CSubspaceBasis<float, TBlade>;
template class GA::CSubspaceMask < GA::CSubspaceBasis < float, TBlade >>;

template class GA::CMultivector<int, TBlade>;
template class GA::CMultivector<double, TBlade>;
template class GA::CSubspaceMultivector<int, TBlade, 5>;
template class GA::CSubspaceMultivector<double, TBlade, 5>;
template class GA::CDynamicMultivector<float, TBlade>;
template class GA::CDynamicMultivector<double, TBlade>;

template class GA::CBasisE3<float>;
template class GA::CMultivectorE3<float>;
template class GA::CSubspaceMultivectorE3<float, 5>;

template class GA::CBasisE3<double>;
template class GA::CMultivectorE3<double>;
template class GA::CSubspaceMultivectorE3<double, 5>;

template class GA::CBasisP3<float>;
template class GA::CMultivectorP3<float>;
template class GA::CSubspaceMultivectorP3<float, 5>;

template class GA::CBasisP3<double>;
template class GA::CMultivectorP3<double>;
template class GA::CSubspaceMultivectorP3<double, 5>;

template class GA::CBasisN3<float>;
template class GA::CMultivectorN3<float>;
template class GA::CSubspaceMultivectorN3<float, 5>;

template class GA::CBasisN3<double>;
template class GA::CMultivectorN3<double>;
template class GA::CSubspaceMultivectorN3<double, 5>;

