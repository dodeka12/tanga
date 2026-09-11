# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binding fragments for extended multivector operators (all dtypes)."""


def grade_proj_def() -> str:
    return """
    m.def("grade_proj", [](const TDynMV& a, unsigned grade) {
        TDynMV c = Tan::GA::GetGradeProjection(a, grade);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("grade"),
       "Extract grade-k part <A>_k.");
"""


def scalar_def(ctype: str) -> str:
    return f"""
    m.def("scalar", [](const TDynMV& a) -> {ctype} {{
        return Tan::GA::Scalar(a);
    }}, py::arg("a"),
       "Return the scalar coefficient of a.");
"""


def dual_def() -> str:
    return """
    m.def("complement", [](const TDynMV& a) {
        TDynMV c;
        Tan::GA::Complement(c, a);
        c.Prune();
        return c;
    }, py::arg("a"),
       "Compute the unsigned complement: blade mask is bitwise XOR with "
       "pseudoscalar; complement(complement(A))=A for all dimensions and "
       "signatures.  This is a purely combinatorial operation, NOT the "
       "Clifford dual.  Use dual() for the geometrically correct dual.");

    m.def("dual", [](const TDynMV& a) {
        TDynMV c;
        Tan::GA::Dual(c, a);
        c.Prune();
        return c;
    }, py::arg("a"),
       "Compute the signed dual *A = A . I^{-1}. "
       "The dual-of-dual may introduce a sign depending on dimension "
       "and signature.  In G(3,0): *(a^b) = a x b (cross product).");

    m.def("ldual", [](const TDynMV& a) {
        TDynMV c;
        Tan::GA::LDual(c, a);
        c.Prune();
        return c;
    }, py::arg("a"),
       "Compute the left dual I . A (left multiplication by the "
       "pseudoscalar, no inverse needed).  In G(3,0): I.(a^b) = -(a x b).");
"""


def magnitude_sq_def(ctype: str) -> str:
    return f"""
    m.def("magnitude_sq", [](const TDynMV& a) -> {ctype} {{
        return Tan::GA::MagnitudeSquared(a);
    }}, py::arg("a"),
       "Return sum of squared coefficients.");
"""


def magnitude_def() -> str:
    return """
    m.def("magnitude", [](const TDynMV& a) -> double {
        return Tan::GA::Magnitude(a);
    }, py::arg("a"),
       "Return sqrt(sum of squared coefficients).");
"""


def is_zero_def() -> str:
    return """
    m.def("is_zero", [](const TDynMV& a) -> bool {
        return Tan::GA::IsZero(a);
    }, py::arg("a"),
       "Return True if all blades are zero.");
"""


def is_scalar_def() -> str:
    return """
    m.def("is_scalar", [](const TDynMV& a) -> bool {
        return Tan::GA::IsScalar(a);
    }, py::arg("a"),
       "Return True if only the scalar blade is non-zero.");
"""


def sp_def(ctype: str) -> str:
    return f"""
    m.def("sp", [](const TDynMV& a, const TDynMV& b) -> {ctype} {{
        {ctype} val{{}};
        Tan::GA::SP(val, a, b);
        return val;
    }}, py::arg("a"), py::arg("b"),
       "Scalar product (scalar part of geometric product).");
"""


def project_onto_def() -> str:
    return """
    m.def("project_onto", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c = a;
        Tan::GA::ProjectOnto(c, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Restrict a to the blade set of b (retain a's blades that are non-zero in b).");
"""


def project_onto_mask_def() -> str:
    return """
    m.def("project_onto_mask", [](const TDynMV& a, std::vector<unsigned> ids) {
        TDynMV c = a;
        Tan::GA::CBladeMask<TBlade> xMask;
        for (unsigned id : ids) {
            xMask << id;
        }
        Tan::GA::ProjectOnto(c, xMask);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("ids"),
       "Restrict a to the given blade ids (exact membership).");
"""


def gp_rev_def() -> str:
    return """
    m.def("gp_rev", [](const TDynMV& a, bool revA, const TDynMV& b, bool revB) {
        TDynMV c;
        Tan::GA::GP_Reverse(c, a, revA, b, revB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("rev_a"), py::arg("b"), py::arg("rev_b"),
       "Geometric product with optional reverse on operands.");
"""


def gp_conj_def() -> str:
    return """
    m.def("gp_conj", [](const TDynMV& a, bool conjA, const TDynMV& b, bool conjB) {
        TDynMV c;
        Tan::GA::GP_Conjugate(c, a, conjA, b, conjB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("conj_a"), py::arg("b"), py::arg("conj_b"),
       "Geometric product with optional conjugate on operands.");
"""


def ip_rev_def() -> str:
    return """
    m.def("ip_rev", [](const TDynMV& a, bool revA, const TDynMV& b, bool revB) {
        TDynMV c;
        Tan::GA::IP_Reverse(c, a, revA, b, revB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("rev_a"), py::arg("b"), py::arg("rev_b"),
       "Inner product with optional reverse on operands.");
"""


def ip_conj_def() -> str:
    return """
    m.def("ip_conj", [](const TDynMV& a, bool conjA, const TDynMV& b, bool conjB) {
        TDynMV c;
        Tan::GA::IP_Conjugate(c, a, conjA, b, conjB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("conj_a"), py::arg("b"), py::arg("conj_b"),
       "Inner product with optional conjugate on operands.");
"""


def op_rev_def() -> str:
    return """
    m.def("op_rev", [](const TDynMV& a, bool revA, const TDynMV& b, bool revB) {
        TDynMV c;
        Tan::GA::OP_Reverse(c, a, revA, b, revB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("rev_a"), py::arg("b"), py::arg("rev_b"),
       "Outer product with optional reverse on operands.");
"""


def op_conj_def() -> str:
    return """
    m.def("op_conj", [](const TDynMV& a, bool conjA, const TDynMV& b, bool conjB) {
        TDynMV c;
        Tan::GA::OP_Conjugate(c, a, conjA, b, conjB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("conj_a"), py::arg("b"), py::arg("conj_b"),
       "Outer product with optional conjugate on operands.");
"""


def grades_def() -> str:
    return """
    m.def("grades", [](const TDynMV& a) -> std::vector<unsigned> {
        return Tan::GA::Grades(a);
    }, py::arg("a"),
       "Return the list of grades present in this multivector (0..dim), sorted ascending.");
"""


def is_grade_def() -> str:
    return """
    m.def("is_grade", [](const TDynMV& a, unsigned grade) -> bool {
        return Tan::GA::IsGrade(a, grade);
    }, py::arg("a"), py::arg("grade"),
       "Return True if all non-zero blades of the multivector are of the given grade.");
"""
