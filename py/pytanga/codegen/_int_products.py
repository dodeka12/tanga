# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binding fragments for integer (modular arithmetic) product operations."""


def gp_int_mod_def(ctype: str) -> str:
    return f"""
    m.def("gp", [](const TDynMV& a, const TDynMV& b) {{
        TDynMV c;
        Tan::GA::GP(c, a, b);
        c.Prune();
        return c;
    }}, py::arg("a"), py::arg("b"),
       "Geometric product: a * b (integer arithmetic)");

    m.def("gp_mod", [](const TDynMV& a, const TDynMV& b, unsigned mod) {{
        TDynMV c;
        TCong cong(static_cast<{ctype}>(mod));
        Tan::GA::GP_Congruence(c, a, b, cong);
        c.Prune();
        return c;
    }}, py::arg("a"), py::arg("b"), py::arg("mod"),
       "Geometric product modulo mod");
"""


def op_int_mod_def(ctype: str) -> str:
    return """
    m.def("op", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c;
        Tan::GA::OP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Outer (wedge) product: a ^ b (integer arithmetic)");

    m.def("op_mod", [](const TDynMV& a, const TDynMV& b, unsigned mod) {
        TDynMV c;
        Tan::GA::OP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"), py::arg("mod"),
       "Outer product (mod applied post-hoc via Python)");
"""


def ip_int_mod_def(ctype: str) -> str:
    return """
    m.def("ip", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c;
        Tan::GA::IP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Inner product: a | b (integer arithmetic)");

    m.def("ip_mod", [](const TDynMV& a, const TDynMV& b, unsigned mod) {
        TDynMV c;
        Tan::GA::IP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"), py::arg("mod"),
       "Inner product (mod applied post-hoc via Python)");
"""


def inv_int_mod_def(ctype: str) -> str:
    return f"""
    m.def("inv", [](const TDynMV& a, unsigned mod) {{
        TDynMV c;
        TCong cong(static_cast<{ctype}>(mod));
        auto res = Tan::GA::Inverse(c, a, cong);
        if (res != Tan::GA::EResult::Success)
            throw std::runtime_error("Multivector is not invertible modulo " + std::to_string(mod));
        c.Prune();
        return c;
    }}, py::arg("a"), py::arg("mod"),
       "Multiplicative inverse modulo mod");
"""


def reduce_int_def(ctype: str) -> str:
    return f"""
    m.def("reduce", [](const TDynMV& a, unsigned mod) {{
        TDynMV c = a;
        TCong cong(static_cast<{ctype}>(mod));
        Tan::GA::Congruence(c, cong);
        c.Prune();
        return c;
    }}, py::arg("a"), py::arg("mod"),
       "Apply half-space modular reduction: map all coefficients into [-mod/2, mod/2].");
"""
