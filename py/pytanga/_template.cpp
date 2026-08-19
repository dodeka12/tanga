// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass

// @@AUTO-GENERATED — do not edit; see pytanga/_codegen.py@@
// Algebra: G({DIM}, {SIG})  dtype: {CTYPE}
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <map>
#include <stdexcept>
#include <string>
#include <cstdint>
#include <vector>

#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/MV_Operators.h"
#include "Tan.GA/MV_Blade_Ops.h"
#include "Tan.GA/Algo.h"
#include "Tan.GA/Matrix_MapToBladeMask.h"
#include "Tan.GA/Tensor_Product.h"
#include "Tan.Math/Congruence.h"
#include "Tan.Math/Matrix.Algo.GE.h"
#include "Tan.Math/Tensor.h"

namespace py = pybind11;

using TBlade = Tan::GA::CBlade<{DIM}, {SIG}>;
using TDynMV = Tan::GA::CDynamicMultivector<{CTYPE}, TBlade>;
using TCong = {CONG_TYPE};

PYBIND11_MODULE({MODULE_NAME}, m)
{
    // -----------------------------------------------------------------------
    // Module-level constants
    // -----------------------------------------------------------------------
    m.attr("VECTOR_SPACE_DIM") = static_cast<unsigned>(TBlade::VectorSpaceDimension);
    m.attr("ALGEBRA_DIM") = static_cast<unsigned>(TBlade::AlgebraDimension);
    m.attr("SIGNATURE") = static_cast<unsigned>(TBlade::VectorSpaceSignature);
    m.attr("PSEUDOSCALAR_ID") = static_cast<unsigned>(TBlade::PseudoScalarId);

    // -----------------------------------------------------------------------
    // DynMV class
    // -----------------------------------------------------------------------
    py::class_<TDynMV>(m, "DynMV")
        .def(py::init<>())

        // set / get a single blade coefficient by its uint32 blade-id
        .def("set", [](TDynMV &mv, uint32_t id, {CTYPE} val)
             { mv.SetValueBlade(val, TBlade(id)); }, py::arg("blade_id"), py::arg("value"))

        .def("get", [](const TDynMV &mv, uint32_t id) ->
             { CTYPE } {
            {CTYPE} val{};
            mv.GetValueBlade(val, TBlade(id));
            return val; }, py::arg("blade_id"))

        // export all non-zero entries as dict[int, <value>]
        .def("to_dict", [](const TDynMV &mv)
             {
            std::map<uint32_t, {CTYPE}> d;
            mv.ForEachBlade([&](const {CTYPE}& v, const TBlade& bl) {
                d[bl.GetId()] = v;
            });
            return d; })

        // overwrite from dict[int, <value>]; clears existing entries first
        .def("from_dict", [](TDynMV &mv, const std::map<uint32_t, {CTYPE}> &d)
             {
            mv.Reset();
            for (const auto& kv : d) {
                mv.SetValueBlade(kv.second, TBlade(kv.first));
            } }, py::arg("coeffs"))

        .def("blade_count", [](const TDynMV &mv)
             { return mv.GetBladeCount(); })

        .def("reset", [](TDynMV &mv)
             { mv.Reset(); })
        .def("prune", [](TDynMV &mv)
             { mv.Prune(); });

    // -----------------------------------------------------------------------
    // Algebra products
    // -----------------------------------------------------------------------
    {
        {
            GP_MOD_DEF
        }
    }
    {
        {
            OP_MOD_DEF
        }
    }
    {
        {
            IP_MOD_DEF
        }
    }

    {INV_DEF}

    // -----------------------------------------------------------------------
    // Linear operations: add, sub, neg, scale
    // -----------------------------------------------------------------------
    m.def("add", [](const TDynMV &a, const TDynMV &b)
          {
        TDynMV c = a;
        c += b;
        c.Prune();
        return c; }, py::arg("a"), py::arg("b"), "Component-wise addition: a + b.");

    m.def("sub", [](const TDynMV &a, const TDynMV &b)
          {
        TDynMV c = a;
        c -= b;
        c.Prune();
        return c; }, py::arg("a"), py::arg("b"), "Component-wise subtraction: a - b.");

    m.def("neg", [](const TDynMV &a)
          {
        TDynMV c = -a;
        return c; }, py::arg("a"), "Unary negation: -a.");

    m.def("scale", [](const TDynMV &a, {CTYPE} s)
          {
        TDynMV c;
        a.ForEachBlade([&](const {CTYPE}& v, const TBlade& bl) {
            c.SetValueBlade(v * s, bl);
        });
        c.Prune();
        return c; }, py::arg("a"), py::arg("s"), "Scalar scaling: s * a.");

    // -----------------------------------------------------------------------
    // Reverse and versor product
    // -----------------------------------------------------------------------
    m.def("rev", [](const TDynMV &a)
          {
        TDynMV c = Tan::GA::GetReverse(a);
        c.Prune();
        return c; }, py::arg("a"), "Reverse of a: reverses the order of basis vectors in each blade "
                             "(negates grades 2, 3 mod 4).");

    m.def("vp", [](const TDynMV &versor, const TDynMV &b)
          {
        TDynMV c;
        Tan::GA::VersorProduct(c, versor, b);
        c.Prune();
        return c; }, py::arg("versor"), py::arg("b"), "Versor product: versor * b * reverse(versor).");

    m.def("conj", [](const TDynMV &a)
          {
        TDynMV c = Tan::GA::GetConjugate(a);
        c.Prune();
        return c; }, py::arg("a"), "Clifford conjugate: rev(a) * (-1)^r, where r is the number of "
                             "negative-metric basis vectors in each blade.");

    // -----------------------------------------------------------------------
    // Grade projection, scalar extraction, dual
    // -----------------------------------------------------------------------
    {
        {
            GRADE_PROJ_DEF
        }
    }
    {
        {
            SCALAR_DEF
        }
    }
    {
        {
            DUAL_DEF
        }
    }

    // -----------------------------------------------------------------------
    // Magnitude
    // -----------------------------------------------------------------------
    {
        {
            MAGNITUDE_SQ_DEF
        }
    }
    {
        {
            MAGNITUDE_DEF
        }
    }

    // -----------------------------------------------------------------------
    // Boolean queries
    // -----------------------------------------------------------------------
    {
        {
            IS_ZERO_DEF
        }
    }
    {
        {
            IS_SCALAR_DEF
        }
    }
    {
        {
            GRADES_DEF
        }
    }
    {
        {
            IS_GRADE_DEF
        }
    }

    // -----------------------------------------------------------------------
    // Scalar product & projection
    // -----------------------------------------------------------------------
    {
        {
            SP_DEF
        }
    }
    {
        {
            PROJECT_TO_DEF
        }
    }

    // -----------------------------------------------------------------------
    // GP/IP/OP with reverse/conjugate flags (Phase D)
    // -----------------------------------------------------------------------
    {
        {
            GP_REV_DEF
        }
    }
    {
        {
            GP_CONJ_DEF
        }
    }
    {
        {
            IP_REV_DEF
        }
    }
    {
        {
            IP_CONJ_DEF
        }
    }
    {
        {
            OP_REV_DEF
        }
    }
    {
        {
            OP_CONJ_DEF
        }
    }

    // -----------------------------------------------------------------------
    // Blade operations (Phase E)
    // -----------------------------------------------------------------------
    {
        {
            BLADE_INVERSE_DEF
        }
    }
    {
        {
            BLADE_PSEUDO_INVERSE_DEF
        }
    }
    {
        {
            BLADE_FACTORIZE_DEF
        }
    }
    {
        {
            JOIN_DEF
        }
    }
    {
        {
            MEET_DEF
        }
    }
    {
        {
            BLADE_FACTORIZE_VERSOR_DEF
        }
    }
    {
        {
            BLADE_PROJECT_DEF
        }
    }
    {
        {
            BLADE_PROJECT_VEC_DEF
        }
    }
    {
        {
            BLADE_REJECT_DEF
        }
    }
    {
        {
            BLADE_REJECT_VEC_DEF
        }
    }

    // -----------------------------------------------------------------------
    // Product blade mask from A-mask (mask-based, Phase 1 refactor)
    // -----------------------------------------------------------------------
    {
        {
            PRODUCT_BLADE_MASK_GP_A_DEF
        }
    }
    {
        {
            PRODUCT_BLADE_MASK_IP_A_DEF
        }
    }
    {
        {
            PRODUCT_BLADE_MASK_OP_A_DEF
        }
    }

    // -----------------------------------------------------------------------
    // Inverse blade mask (predict B-mask from A-mask and C-mask)
    // -----------------------------------------------------------------------
    {
        {
            PRODUCT_BLADE_MASK_INV_GP_DEF
        }
    }
    {
        {
            PRODUCT_BLADE_MASK_INV_IP_DEF
        }
    }
    {
        {
            PRODUCT_BLADE_MASK_INV_OP_DEF
        }
    }

    {
        {
            REDUCE_DEF
        }
    }
    {
        {
            MATRIX_DEF
        }
    }

    // -----------------------------------------------------------------------
    // Product-tensor construction (3D Cayley table for GP/IP/OP)
    // -----------------------------------------------------------------------
    {
        {
            PRODUCT_TENSOR_DEF
        }
    }
}
