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

#include "Tan.Math/Tensor.h" // for CTensor<T>
#include "Enum.h"
#include "BladeMask.h"
#include "Blade_Operators.h" // for GPSign, IPSign, OPSign

namespace Tan
{
    namespace GA
    {
        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// \brief Build the 3D product tensor O^k_{ij} from three blade masks.
        ///
        /// For a binary GA product ∘, the coefficient of output blade k is
        ///   c^k = Σ_{i,j}  a^i · b^j · O^k_{ij}
        /// where O^k_{ij} is ±1 when blA ∘ blB produces blC, and 0 otherwise.
        ///
        /// The result is a CTensor of shape (|xMaskC|, |xMaskA|, |xMaskB|).
        /// Elements are ±1 when a valid product exists, 0 otherwise.
        ///
        /// \tparam TValue  Numeric type (float, double, int32_t, int64_t).
        /// \tparam TBlade  Blade type (must match the masks).
        /// \tparam FuncOp  Product sign function (GPSign, IPSign, or OPSign).
        ///
        /// \param[out] tenO         Result tensor, shape (|c_mask|, |a_mask|, |b_mask|).
        /// \param      xMaskA       Blade mask of the left operand A.
        /// \param      xMaskB       Blade mask of the right operand B.
        /// \param      xMaskC       Blade mask of the result C.
        /// \param      bLeftToRight true = A ∘ B, false = B ∘ A.
        /// \param      xFuncOp      Product sign/blade function.
        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        template <typename TValue, typename TBlade, typename FuncOp>
        void _EvalProductTensor(
            CTensor<TValue> &tenO,
            const CBladeMask<TBlade> &xMaskA,
            const CBladeMask<TBlade> &xMaskB,
            const CBladeMask<TBlade> &xMaskC,
            bool bLeftToRight,
            FuncOp xFuncOp,
            GA::EInv eInvLeft = GA::EInv::Id,
            GA::EInv eInvRight = GA::EInv::Id,
            GA::EInv eInvC = GA::EInv::Id)
        {
            const unsigned uDimA = xMaskA.Count();
            const unsigned uDimB = xMaskB.Count();
            const unsigned uDimC = xMaskC.Count();

            // Shape: (|c_mask|, |a_mask|, |b_mask|)
            tenO.SetSize(uDimC, uDimA, uDimB);
            tenO.Zero();

            unsigned uSign;
            TBlade blC;

            xMaskA.ForEachBlade([&](unsigned uIndexA, const TBlade &blA)
                                { xMaskB.ForEachBlade([&](unsigned uIndexB, const TBlade &blB)
                                                      {
                    bool bValid;
                    if (bLeftToRight)
                        bValid = xFuncOp(uSign, blC, blA, blB);
                    else
                        bValid = xFuncOp(uSign, blC, blB, blA);

                    unsigned uIndexC;
                    if (bValid && xMaskC.GetIndex(uIndexC, blC))
                    {
                        // Apply involution signs (stored tensor values are ±1 only, so XOR)
                        if (eInvLeft == GA::EInv::Rev)       uSign ^= (blA.GetReverseSign() & 1);
                        else if (eInvLeft == GA::EInv::Conj) uSign ^= (blA.GetConjugateSign() & 1);
                        if (eInvRight == GA::EInv::Rev)       uSign ^= (blB.GetReverseSign() & 1);
                        else if (eInvRight == GA::EInv::Conj) uSign ^= (blB.GetConjugateSign() & 1);
                        if (eInvC == GA::EInv::Rev)       uSign ^= (blC.GetReverseSign() & 1);
                        else if (eInvC == GA::EInv::Conj) uSign ^= (blC.GetConjugateSign() & 1);

                        typename CTensor<TValue>::TIdxVec pos = {uIndexC, uIndexA, uIndexB};
                        tenO(pos) = (uSign & 1) ? TValue(-1) : TValue(1);
                    } }); });
        }

        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// \brief Build the 3D geometric-product tensor O^k_{ij}.
        ///
        /// see _EvalProductTensor for the detailed contract.
        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        template <typename TValue, typename TBlade>
        void EvalProductTensor_GP(
            CTensor<TValue> &tenO,
            const CBladeMask<TBlade> &xMaskA,
            const CBladeMask<TBlade> &xMaskB,
            const CBladeMask<TBlade> &xMaskC,
            bool bLeftToRight = true,
            GA::EInv eInvLeft = GA::EInv::Id,
            GA::EInv eInvRight = GA::EInv::Id,
            GA::EInv eInvC = GA::EInv::Id)
        {
            _EvalProductTensor(tenO, xMaskA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
                               { return GPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight, eInvC);
        }

        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// \brief Build the 3D inner-product tensor O^k_{ij}.
        ///
        /// see _EvalProductTensor for the detailed contract.
        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        template <typename TValue, typename TBlade>
        void EvalProductTensor_IP(
            CTensor<TValue> &tenO,
            const CBladeMask<TBlade> &xMaskA,
            const CBladeMask<TBlade> &xMaskB,
            const CBladeMask<TBlade> &xMaskC,
            bool bLeftToRight = true,
            GA::EInv eInvLeft = GA::EInv::Id,
            GA::EInv eInvRight = GA::EInv::Id,
            GA::EInv eInvC = GA::EInv::Id)
        {
            _EvalProductTensor(tenO, xMaskA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
                               { return IPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight, eInvC);
        }

        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// \brief Build the 3D outer-product tensor O^k_{ij}.
        ///
        /// see _EvalProductTensor for the detailed contract.
        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        template <typename TValue, typename TBlade>
        void EvalProductTensor_OP(
            CTensor<TValue> &tenO,
            const CBladeMask<TBlade> &xMaskA,
            const CBladeMask<TBlade> &xMaskB,
            const CBladeMask<TBlade> &xMaskC,
            bool bLeftToRight = true,
            GA::EInv eInvLeft = GA::EInv::Id,
            GA::EInv eInvRight = GA::EInv::Id,
            GA::EInv eInvC = GA::EInv::Id)
        {
            _EvalProductTensor(tenO, xMaskA, xMaskB, xMaskC, bLeftToRight, [](unsigned &uSign, TBlade &blC, const TBlade &blA, const TBlade &blB) -> bool
                               { return OPSign(uSign, blC, blA, blB); }, eInvLeft, eInvRight, eInvC);
        }

    } // namespace GA
} // namespace Tan