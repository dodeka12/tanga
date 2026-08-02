# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binding fragments for floating-point product operations (GP, OP, IP, INV)."""


def gp_float_def() -> str:
    return """
    m.def("gp", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c;
        Tan::GA::GP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Geometric product: a * b");
"""


def op_float_def() -> str:
    return """
    m.def("op", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c;
        Tan::GA::OP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Outer (wedge) product: a ^ b");
"""


def ip_float_def() -> str:
    return """
    m.def("ip", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c;
        Tan::GA::IP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Inner product: a | b");
"""


def inv_float_def() -> str:
    return """
    m.def("inv", [](const TDynMV& a) {
        TDynMV c;
        TCong cong;
        auto res = Tan::GA::Inverse(c, a, cong);
        if (res != Tan::GA::EResult::Success)
            throw std::runtime_error("Multivector is not invertible");
        c.Prune();
        return c;
    }, py::arg("a"),
       "Multiplicative inverse");
"""
