# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binding fragment for product tensor construction (GP/IP/OP, all dtypes)."""


def product_tensor_def(ctype: str) -> str:
    """Build GP/IP/OP tensor bindings using the CTensor<T> return type from Phase 0.

    Returns a single string containing all three python-def bindings
    (product_tensor_gp, product_tensor_ip, product_tensor_op).
    """
    return f"""
    // -----------------------------------------------------------------------
    // Product-tensor construction (3D Cayley table for GP/IP/OP)
    // -----------------------------------------------------------------------

    // Helper: copy N‑D CTensor to numpy array (both row-major)
    auto _tensor_to_arr = [](const Tan::CTensor<{ctype}>& ten) -> py::array_t<{ctype}> {{
        size_t ndim = ten.GetDimension();
        const auto& sizes = ten.GetSizes();
        std::vector<py::ssize_t> py_sizes(ndim);
        for (size_t d = 0; d < ndim; ++d)
            py_sizes[d] = static_cast<py::ssize_t>(sizes[d]);
        py::array_t<{ctype}> arr(py_sizes);
        auto buf = arr.mutable_data();
        const {ctype}* src = ten.GetData();     // row-major flat storage from CArray
        std::copy(src, src + ten.GetTotalSize(), buf);
        return arr;
    }};

    // Helper: convert involution string to GA::EInv enum
    auto _parse_inv = [](const std::string& s) -> Tan::GA::EInv {{
        if (s == "id")   return Tan::GA::EInv::Id;
        if (s == "rev")  return Tan::GA::EInv::Rev;
        if (s == "conj") return Tan::GA::EInv::Conj;
        throw std::runtime_error("Unknown involution: " + s);
    }};

    auto _build_tensor = [_tensor_to_arr, _parse_inv](
                              const std::vector<uint32_t>& a_ids,
                              const std::vector<uint32_t>& b_ids,
                              const std::vector<uint32_t>& c_ids,
                              bool left_to_right,
                              const std::string& left_inv,
                              const std::string& right_inv,
                              const std::string& c_inv,
                              const std::string& product_name) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids) xMaskA.Insert(TBlade(id));
        for (auto id : b_ids) xMaskB.Insert(TBlade(id));
        for (auto id : c_ids) xMaskC.Insert(TBlade(id));

        Tan::GA::EInv eInvLeft  = _parse_inv(left_inv);
        Tan::GA::EInv eInvRight = _parse_inv(right_inv);
        Tan::GA::EInv eInvC     = _parse_inv(c_inv);

        Tan::CTensor<{ctype}> ten;
        if (product_name == "gp")
            Tan::GA::EvalProductTensor_GP<{ctype}, TBlade>(ten, xMaskA, xMaskB, xMaskC, left_to_right, eInvLeft, eInvRight, eInvC);
        else if (product_name == "ip")
            Tan::GA::EvalProductTensor_IP<{ctype}, TBlade>(ten, xMaskA, xMaskB, xMaskC, left_to_right, eInvLeft, eInvRight, eInvC);
        else if (product_name == "op")
            Tan::GA::EvalProductTensor_OP<{ctype}, TBlade>(ten, xMaskA, xMaskB, xMaskC, left_to_right, eInvLeft, eInvRight, eInvC);
        else
            throw std::runtime_error("Unknown product: " + product_name);
        return _tensor_to_arr(ten);
    }};

    m.def("product_tensor_gp", _build_tensor,
        py::arg("a_ids"), py::arg("b_ids"), py::arg("c_ids"),
        py::arg("left_to_right") = true,
        py::arg("left_inv") = "id",
        py::arg("right_inv") = "id",
        py::arg("c_inv") = "id",
        py::arg("_product") = "gp",
        "Build the 3D geometric-product tensor O[k,i,j] from blade masks.");

    m.def("product_tensor_ip", _build_tensor,
        py::arg("a_ids"), py::arg("b_ids"), py::arg("c_ids"),
        py::arg("left_to_right") = true,
        py::arg("left_inv") = "id",
        py::arg("right_inv") = "id",
        py::arg("c_inv") = "id",
        py::arg("_product") = "ip",
        "Build the 3D inner-product tensor O[k,i,j] from blade masks.");

    m.def("product_tensor_op", _build_tensor,
        py::arg("a_ids"), py::arg("b_ids"), py::arg("c_ids"),
        py::arg("left_to_right") = true,
        py::arg("left_inv") = "id",
        py::arg("right_inv") = "id",
        py::arg("c_inv") = "id",
        py::arg("_product") = "op",
        "Build the 3D outer-product tensor O[k,i,j] from blade masks.");
"""
