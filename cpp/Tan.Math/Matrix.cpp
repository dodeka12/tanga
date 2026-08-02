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

#include <cstdint>

#include "Matrix.h"
#include "Matrix.Algo.SVD.h"
#include "Matrix.Algo.GE.h"

#ifdef _DEBUG
// ///////////////////////////////////////////////////////////////////
// Compile matrix class and matrix algos for specific types
// to find compile errors.
using namespace Tan;

template class CMatrix<float>;
template class CMatrix<double>;

template class CMatrix<int32_t>;
template class CMatrix<int64_t>;

// Compile matrix algos
 
template Tan::CMatrixAlgoSVD<double>;
template Tan::CMatrixAlgoGE<double>;
template Tan::CMatrixAlgoGE<int32_t>;
template Tan::CMatrixAlgoGE<int64_t>;
// ///////////////////////////////////////////////////////////////////
#endif
