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
#include "Tan.Core/Array.h"
#include "ValuePrecision.h"

namespace Tan
{
    /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    /// \brief Rank-agnostic tensor container.
    ///
    /// Provides an N-dimensional container with the same storage and precision
    /// semantics as CMatrix<T> but without a fixed 2‑D shape.  Use when a
    /// function must return a 3‑D product tensor, a vector of matrices, etc.
    ///
    /// CTensor<T> inherits from CArray<T> and CValuePrecision<T> (same as CMatrix<T>).
    /// Unlike CMatrix<T>, CTensor<T> does NOT pin the first two axes as "row" / "col".
    ///
    /// \tparam _TValue  Numeric element type (float, double, int32_t, int64_t, etc.).
    ///
    /// \sa CArray, CMatrix
    /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    template <class _TValue>
    class CTensor : public CArray<_TValue>, public CValuePrecision<_TValue>
    {
    public:
        typedef _TValue TValue;
        typedef CTensor<TValue> TThis;
        typedef CArray<TValue> TArray;
        typedef typename TArray::TIterator TIterator;
        typedef typename TArray::TConstIterator TConstIterator;
        typedef typename TArray::TIdx TIdx;
        typedef typename TArray::TIdxVec TIdxVec;
        typedef typename TArray::TSizeVec TSizeVec;
        typedef CValuePrecision<_TValue> TValPrec;

    public:
        /// Default constructor — creates an empty tensor (zero dimensions).
        CTensor() = default;

        /// Construct with a given numeric precision threshold.
        CTensor(TValue fPrec) : CValuePrecision<TValue>(fPrec)
        {
            TValPrec::SetValuePrecision(fPrec);
        }

        CTensor(TThis &&xT) = default;
        TThis &operator=(TThis &&xT) = default;

        CTensor(const TThis &xT) = default;
        TThis &operator=(const TThis &xT) = default;

        // --------------------------------------------------------------------
        // Dimension introspection
        // --------------------------------------------------------------------

        /// Number of axes (rank).
        size_t GetDimension() const { return TArray::GetSize().size(); }

        /// Size along axis `uDim` (zero‑based).
        /// \pre `uDim < GetDimension()`
        size_t GetDimSize(size_t uDim) const
        {
            return TArray::GetSize()[uDim];
        }

        /// Full size vector (one entry per axis).
        const TSizeVec &GetSizes() const { return TArray::GetSize(); }

        /// Total number of elements (product of all axis sizes).
        size_t GetTotalSize() const { return TArray::GetTotalSize(); }

        /// Pointer to the beginning of the flat row‑major data buffer.
        TValue *GetData() { return TArray::GetDataPtr(); }

        /// Const pointer to the beginning of the flat row‑major data buffer.
        const TValue *GetData() const { return TArray::GetDataPtr(); }

        // --------------------------------------------------------------------
        // Resize
        // --------------------------------------------------------------------

        /// Assign a new shape, zeroing all elements.
        /// Existing data is NOT preserved — the tensor is treated as freshly allocated.
        void SetSize(const TSizeVec &vecSize)
        {
            TArray::SetSize(vecSize);
        }

        /// Convenience overload: SetSize({sizes...})
        template <typename... TDimSizes>
        void SetSize(TDimSizes... sizes)
        {
            TArray::SetSize(TSizeVec{static_cast<size_t>(sizes)...});
        }

        /// Resize the tensor, preserving elements that fit within the new shape.
        /// \pre The new shape must have the same number of dimensions.
        void Resize(const TSizeVec &vecSize)
        {
            if (TArray::GetTotalSize() == 0)
                TArray::SetSize(vecSize);
            else
                TArray::Resize(vecSize);
        }

        /// Convenience overload: Resize({sizes...})
        template <typename... TDimSizes>
        void Resize(TDimSizes... sizes)
        {
            Resize(TSizeVec{static_cast<size_t>(sizes)...});
        }

        // --------------------------------------------------------------------
        // Element access
        // --------------------------------------------------------------------

        /// N‑D element access via index vector.
        /// \pre `vecPos` must have exactly `GetDimension()` entries, each < the corresponding axis size.
        TValue &operator()(const TIdxVec &vecPos)
        {
            return *(TArray::GetDataPtr() + this->_GetPos(vecPos));
        }

        /// Const N‑D element access via index vector.
        const TValue &operator()(const TIdxVec &vecPos) const
        {
            return *(TArray::GetDataPtr() + this->_GetPos(vecPos));
        }

        // --------------------------------------------------------------------
        // Bulk operations
        // --------------------------------------------------------------------

        /// Fill all elements with zero.
        void Zero()
        {
            TValue *pData = GetData();
            size_t nTotal = GetTotalSize();
            for (size_t i = 0; i < nTotal; ++i)
                pData[i] = TValue(0);
        }
    };
} // namespace Tan