# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binding fragments for blade operations (Phase E, all dtypes)."""


def blade_inverse_def() -> str:
    return """
    m.def("blade_inverse", [](const TDynMV& a) {
        TDynMV c = Tan::GA::InverseBlade(a);
        c.Prune();
        return c;
    }, py::arg("a"),
       "Compute the inverse of a blade: A^{-1} = reverse(A) / IP(A, reverse(A)).");
"""


def blade_pseudo_inverse_def() -> str:
    return """
    m.def("blade_pseudo_inverse", [](const TDynMV& a) {
        TDynMV c = Tan::GA::PseudoInverseBlade(a);
        c.Prune();
        return c;
    }, py::arg("a"),
       "Compute the pseudo-inverse of a blade: A^{-1} = conjugate(A) / IP(A, conjugate(A)).");
"""


def blade_factorize_def() -> str:
    return """
    m.def("blade_factorize", [](const TDynMV& a) {
        return Tan::GA::FactorizeBlade(a);
    }, py::arg("a"),
       "Factorize a blade into k normalized grade-1 vectors. Returns a list of DynMV.");
"""


def join_def() -> str:
    return """
    m.def("join", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c = Tan::GA::Join(a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Compute the join of two blades: the smallest-grade blade that contains both A and B.");
"""


def meet_def() -> str:
    return """
    m.def("meet", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c = Tan::GA::Meet(a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Compute the meet of two blades: the largest-grade blade contained in both A and B.");
"""


def blade_factorize_versor_def() -> str:
    return """
    m.def("blade_factorize_versor", [](const TDynMV& a) {
        auto [wScale, vecFactors] = Tan::GA::FactorizeVersor(a);
        return py::make_tuple(wScale, vecFactors);
    }, py::arg("a"),
       "Factorize a versor into (scale, [factor_vectors]).");
"""


def blade_project_def() -> str:
    return """
    m.def("blade_project", [](const TDynMV& a, const TDynMV& n) {
        TDynMV c = Tan::GA::Project(a, n);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("n"),
       "Project a multivector onto a blade N_l: proj_N(A) = (A . N) N^-1, where N^-1 = conj(N) / IP(N, conj(N)).");
"""


def blade_project_vec_def() -> str:
    return """
    m.def("blade_project_vec", [](const std::vector<TDynMV>& vecA, const TDynMV& n) {
        std::vector<TDynMV> vecC;
        Tan::GA::Project(vecC, n, vecA);
        return vecC;
    }, py::arg("vec_a"), py::arg("n"),
       "Project each multivector in vec_a onto blade n.");
"""


def blade_reject_def() -> str:
    return """
    m.def("blade_reject", [](const TDynMV& a, const TDynMV& n) {
        TDynMV c = Tan::GA::Reject(a, n);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("n"),
       "Compute the rejection from a blade N_l: rej_N(A) = A - proj_N(A).");
"""


def blade_reject_vec_def() -> str:
    return """
    m.def("blade_reject_vec", [](const std::vector<TDynMV>& vecA, const TDynMV& n) {
        std::vector<TDynMV> vecC;
        Tan::GA::Reject(vecC, n, vecA);
        return vecC;
    }, py::arg("vec_a"), py::arg("n"),
       "Compute the rejection of each multivector in vec_a from blade n.");
"""
