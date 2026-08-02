# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binding fragments for product blade mask operations (mask-based, Phase 1 refactor)."""


def product_blade_mask_gp_a_def() -> str:
    return """
    m.def("product_blade_mask_gp_a", [](const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& col_ids,
            bool left_to_right, bool complete) {
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids)   xMaskA.Insert(TBlade(id));
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMask_GP(xMaskC, xMaskA, xMaskB, left_to_right, complete);
        std::vector<uint32_t> ids;
        xMaskC.ForEachBlade([&](unsigned, const TBlade& bl) {
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        });
        return ids;
    }, py::arg("a_ids"), py::arg("col_ids"),
        py::arg("left_to_right") = true, py::arg("complete") = false,
       "Predict output blade ids of GP from A-mask and B-mask.");
"""


def product_blade_mask_ip_a_def() -> str:
    return """
    m.def("product_blade_mask_ip_a", [](const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& col_ids,
            bool left_to_right, bool complete) {
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids)   xMaskA.Insert(TBlade(id));
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMask_IP(xMaskC, xMaskA, xMaskB, left_to_right, complete);
        std::vector<uint32_t> ids;
        xMaskC.ForEachBlade([&](unsigned, const TBlade& bl) {
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        });
        return ids;
    }, py::arg("a_ids"), py::arg("col_ids"),
        py::arg("left_to_right") = true, py::arg("complete") = false,
       "Predict output blade ids of IP from A-mask and B-mask.");
"""


def product_blade_mask_op_a_def() -> str:
    return """
    m.def("product_blade_mask_op_a", [](const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& col_ids,
            bool left_to_right, bool complete) {
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids)   xMaskA.Insert(TBlade(id));
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMask_OP(xMaskC, xMaskA, xMaskB, left_to_right, complete);
        std::vector<uint32_t> ids;
        xMaskC.ForEachBlade([&](unsigned, const TBlade& bl) {
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        });
        return ids;
    }, py::arg("a_ids"), py::arg("col_ids"),
        py::arg("left_to_right") = true, py::arg("complete") = false,
       "Predict output blade ids of OP from A-mask and B-mask.");
"""


# ---------------------------------------------------------------------------
# Inverse blade mask (predict B-mask from A-mask and C-mask, all dtypes)
# ---------------------------------------------------------------------------


def product_blade_mask_inv_gp_def() -> str:
    return """
    m.def("product_blade_mask_inv_gp", [](const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& c_ids,
            bool left_to_right) {
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids) xMaskA.Insert(TBlade(id));
        for (auto id : c_ids) xMaskC.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMaskInv_GP(xMaskB, xMaskA, xMaskC, left_to_right);
        std::vector<uint32_t> ids;
        xMaskB.ForEachBlade([&](unsigned, const TBlade& bl) {
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        });
        return ids;
    }, py::arg("a_ids"), py::arg("c_ids"),
        py::arg("left_to_right") = true,
       "Predict maximal B-mask blade ids for A*X=C from A-mask and C-mask.");
"""


def product_blade_mask_inv_ip_def() -> str:
    return """
    m.def("product_blade_mask_inv_ip", [](const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& c_ids,
            bool left_to_right) {
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids) xMaskA.Insert(TBlade(id));
        for (auto id : c_ids) xMaskC.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMaskInv_IP(xMaskB, xMaskA, xMaskC, left_to_right);
        std::vector<uint32_t> ids;
        xMaskB.ForEachBlade([&](unsigned, const TBlade& bl) {
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        });
        return ids;
    }, py::arg("a_ids"), py::arg("c_ids"),
        py::arg("left_to_right") = true,
       "Predict maximal B-mask blade ids for A|X=C from A-mask and C-mask.");
"""


def product_blade_mask_inv_op_def() -> str:
    return """
    m.def("product_blade_mask_inv_op", [](const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& c_ids,
            bool left_to_right) {
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids) xMaskA.Insert(TBlade(id));
        for (auto id : c_ids) xMaskC.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMaskInv_OP(xMaskB, xMaskA, xMaskC, left_to_right);
        std::vector<uint32_t> ids;
        xMaskB.ForEachBlade([&](unsigned, const TBlade& bl) {
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        });
        return ids;
    }, py::arg("a_ids"), py::arg("c_ids"),
        py::arg("left_to_right") = true,
       "Predict maximal B-mask blade ids for A^X=C from A-mask and C-mask.");
"""
