# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binding fragments for matrix / blade-mask operations (all dtypes)."""


def matrix_common_def(ctype: str) -> str:
    """Blade-mask, matrix-conversion, and product-matrix bindings for all dtypes."""
    return f"""
    // -----------------------------------------------------------------------
    // Helper: convert CMatrix<{ctype}> to a 2-D numpy array
    // -----------------------------------------------------------------------
    auto _mat_to_arr = [](const Tan::CMatrix<{ctype}>& mat) -> py::array_t<{ctype}> {{
        py::ssize_t nr = static_cast<py::ssize_t>(mat.GetRowCount());
        py::ssize_t nc = static_cast<py::ssize_t>(mat.GetColCount());
        py::array_t<{ctype}> arr(std::vector<py::ssize_t>{{nr, nc}});
        auto buf = arr.mutable_unchecked<2>();
        for (py::ssize_t r = 0; r < nr; ++r)
            for (py::ssize_t c = 0; c < nc; ++c)
                buf(r, c) = mat(static_cast<size_t>(r), static_cast<size_t>(c));
        return arr;
    }};

    auto _parse_inv = [](const std::string& s) -> Tan::GA::EInv {{
        if (s == "rev")  return Tan::GA::EInv::Rev;
        if (s == "conj") return Tan::GA::EInv::Conj;
        return Tan::GA::EInv::Id;
    }};

    // -----------------------------------------------------------------------
    // Blade-mask utilities
    // -----------------------------------------------------------------------
    m.def("blade_mask", [](const TDynMV& a, bool only_nonzero) {{
        Tan::GA::CBladeMask<TBlade> mask;
        Tan::GA::EvalBladeMask(mask, a, only_nonzero);
        std::vector<uint32_t> ids;
        mask.ForEachBlade([&](unsigned, const TBlade& bl) {{
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        }});
        return ids;
    }}, py::arg("a"), py::arg("only_nonzero") = true,
       "Return sorted list of blade ids present in a.");

    m.def("product_blade_mask_gp", [](const TDynMV& a,
            const std::vector<uint32_t>& col_ids,
            bool left_to_right, bool complete) {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMask_GP(xMaskC, a, xMaskB, left_to_right, complete);
        std::vector<uint32_t> ids;
        xMaskC.ForEachBlade([&](unsigned, const TBlade& bl) {{
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        }});
        return ids;
    }}, py::arg("a"), py::arg("col_ids"),
        py::arg("left_to_right") = true, py::arg("complete") = false,
       "Predict output blade ids of geometric product A*X (or X*A).");

    m.def("product_blade_mask_ip", [](const TDynMV& a,
            const std::vector<uint32_t>& col_ids,
            bool left_to_right, bool complete) {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMask_IP(xMaskC, a, xMaskB, left_to_right, complete);
        std::vector<uint32_t> ids;
        xMaskC.ForEachBlade([&](unsigned, const TBlade& bl) {{
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        }});
        return ids;
    }}, py::arg("a"), py::arg("col_ids"),
        py::arg("left_to_right") = true, py::arg("complete") = false,
       "Predict output blade ids of inner product A|X (or X|A).");

    m.def("product_blade_mask_op", [](const TDynMV& a,
            const std::vector<uint32_t>& col_ids,
            bool left_to_right, bool complete) {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMask_OP(xMaskC, a, xMaskB, left_to_right, complete);
        std::vector<uint32_t> ids;
        xMaskC.ForEachBlade([&](unsigned, const TBlade& bl) {{
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        }});
        return ids;
    }}, py::arg("a"), py::arg("col_ids"),
        py::arg("left_to_right") = true, py::arg("complete") = false,
       "Predict output blade ids of outer product A^X (or X^A).");

    // -----------------------------------------------------------------------
    // Matrix ↔ MV conversion
    // -----------------------------------------------------------------------
    m.def("to_matrix", [_mat_to_arr](const TDynMV& a,
            const std::vector<uint32_t>& blade_ids) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> mask;
        for (auto id : blade_ids) mask.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::ToMatrix(mat, a, mask);
        return _mat_to_arr(mat);
    }}, py::arg("a"), py::arg("blade_ids"),
       "Extract coefficient column of a as a (n,1) numpy array.");

    m.def("to_matrix_batch", [_mat_to_arr](const std::vector<TDynMV>& mvs,
            const std::vector<uint32_t>& blade_ids) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> mask;
        for (auto id : blade_ids) mask.Insert(TBlade(id));

        Tan::CMatrix<{ctype}> mat;
        mat.SetSize(blade_ids.size(), mvs.size());
        mat.Zero();

        size_t col = 0;
        for (const auto& mv : mvs) {{
            mask.ForEachBlade([&](unsigned uRow, const TBlade& bl) {{
                {ctype} val{{}};
                if (mv.GetValueBlade(val, bl))
                    mat(uRow, col) = val;
            }});
            ++col;
        }}
        return _mat_to_arr(mat);
    }}, py::arg("mvs"), py::arg("blade_ids"),
       "Extract coefficients of a list of MVs into an (n_blades, n_mvs) array.");

    m.def("from_matrix", [](py::array_t<{ctype}> arr,
            const std::vector<uint32_t>& blade_ids) {{
        auto buf = arr.unchecked<2>();
        size_t n = static_cast<size_t>(buf.shape(0));
        if (n != blade_ids.size())
            throw std::runtime_error("from_matrix: array rows != len(blade_ids)");
        Tan::GA::CBladeMask<TBlade> mask;
        for (auto id : blade_ids) mask.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        mat.SetSize(n, 1);
        for (size_t i = 0; i < n; ++i) mat(i, 0) = buf(i, 0);
        TDynMV c;
        Tan::GA::ToMultivector(c, mat, mask);
        c.Prune();
        return c;
    }}, py::arg("arr"), py::arg("blade_ids"),
       "Reconstruct a DynMV from a (n,1) numpy array and blade_ids.");

    m.def("from_matrix_batch", [](py::array_t<{ctype}> arr,
            const std::vector<uint32_t>& blade_ids) -> std::vector<TDynMV> {{
        auto buf = arr.unchecked<2>();
        size_t n_rows = static_cast<size_t>(buf.shape(0));
        size_t n_cols = static_cast<size_t>(buf.shape(1));
        if (n_rows != blade_ids.size())
            throw std::runtime_error(
                "from_matrix_batch: array rows != len(blade_ids)");
        Tan::GA::CBladeMask<TBlade> mask;
        for (auto id : blade_ids) mask.Insert(TBlade(id));

        std::vector<TDynMV> out;
        out.reserve(n_cols);
        for (size_t c = 0; c < n_cols; ++c) {{
            TDynMV mv;
            mask.ForEachBlade([&](unsigned uRow, const TBlade& bl) {{
                {ctype} val = buf(uRow, c);
                if (val != {ctype}(0))
                    mv.SetValueBlade(val, bl);
            }});
            out.push_back(std::move(mv));
        }}
        return out;
    }}, py::arg("arr"), py::arg("blade_ids"),
       "Reconstruct a list of DynMV from an (n_blades, n_mvs) array.");

    // -----------------------------------------------------------------------
    // Product-matrix construction
    // -----------------------------------------------------------------------
    m.def("product_matrix_gp", [_mat_to_arr, _parse_inv](const TDynMV& a,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            bool left_to_right,
            const std::string& left_inv,
            const std::string& right_inv) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrix_GP(mat, a, xMaskB, xMaskC, left_to_right,
            _parse_inv(left_inv), _parse_inv(right_inv));
        return _mat_to_arr(mat);
    }}, py::arg("a"), py::arg("col_ids"), py::arg("row_ids"),
        py::arg("left_to_right") = true,
        py::arg("left_inv") = "id", py::arg("right_inv") = "id",
       "Build geometric product matrix M: M*vec(X)=vec(A*X) (or X*A).");

    m.def("product_matrix_ip", [_mat_to_arr, _parse_inv](const TDynMV& a,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            bool left_to_right,
            const std::string& left_inv,
            const std::string& right_inv) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrix_IP(mat, a, xMaskB, xMaskC, left_to_right,
            _parse_inv(left_inv), _parse_inv(right_inv));
        return _mat_to_arr(mat);
    }}, py::arg("a"), py::arg("col_ids"), py::arg("row_ids"),
        py::arg("left_to_right") = true,
        py::arg("left_inv") = "id", py::arg("right_inv") = "id",
       "Build inner product matrix M: M*vec(X)=vec(A|X) (or X|A).");

    m.def("product_matrix_op", [_mat_to_arr, _parse_inv](const TDynMV& a,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            bool left_to_right,
            const std::string& left_inv,
            const std::string& right_inv) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrix_OP(mat, a, xMaskB, xMaskC, left_to_right,
            _parse_inv(left_inv), _parse_inv(right_inv));
        return _mat_to_arr(mat);
    }}, py::arg("a"), py::arg("col_ids"), py::arg("row_ids"),
        py::arg("left_to_right") = true,
        py::arg("left_inv") = "id", py::arg("right_inv") = "id",
       "Build outer product matrix M: M*vec(X)=vec(A^X) (or X^A).");

    m.def("product_matrix_gp_masked", [_mat_to_arr, _parse_inv](const TDynMV& a,
            const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            bool left_to_right,
            const std::string& left_inv,
            const std::string& right_inv) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids)   xMaskA.Insert(TBlade(id));
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrix_GP(mat, a, xMaskA, xMaskB, xMaskC, left_to_right,
            _parse_inv(left_inv), _parse_inv(right_inv));
        return _mat_to_arr(mat);
    }}, py::arg("a"), py::arg("a_ids"), py::arg("col_ids"), py::arg("row_ids"),
        py::arg("left_to_right") = true,
        py::arg("left_inv") = "id", py::arg("right_inv") = "id",
       "Build geometric product matrix restricting which blades of A participate.");

    m.def("product_matrix_ip_masked", [_mat_to_arr, _parse_inv](const TDynMV& a,
            const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            bool left_to_right,
            const std::string& left_inv,
            const std::string& right_inv) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids)   xMaskA.Insert(TBlade(id));
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrix_IP(mat, a, xMaskA, xMaskB, xMaskC, left_to_right,
            _parse_inv(left_inv), _parse_inv(right_inv));
        return _mat_to_arr(mat);
    }}, py::arg("a"), py::arg("a_ids"), py::arg("col_ids"), py::arg("row_ids"),
        py::arg("left_to_right") = true,
        py::arg("left_inv") = "id", py::arg("right_inv") = "id",
       "Build inner product matrix restricting which blades of A participate.");

    m.def("product_matrix_op_masked", [_mat_to_arr, _parse_inv](const TDynMV& a,
            const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            bool left_to_right,
            const std::string& left_inv,
            const std::string& right_inv) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids)   xMaskA.Insert(TBlade(id));
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrix_OP(mat, a, xMaskA, xMaskB, xMaskC, left_to_right,
            _parse_inv(left_inv), _parse_inv(right_inv));
        return _mat_to_arr(mat);
    }}, py::arg("a"), py::arg("a_ids"), py::arg("col_ids"), py::arg("row_ids"),
        py::arg("left_to_right") = true,
        py::arg("left_inv") = "id", py::arg("right_inv") = "id",
       "Build outer product matrix restricting which blades of A participate.");

    m.def("product_matrix_array_gp", [_mat_to_arr](const std::vector<TDynMV>& mvs,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            bool left_to_right) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrixArray_GP(mat, mvs, xMaskB, xMaskC, left_to_right);
        return _mat_to_arr(mat);
    }}, py::arg("mvs"), py::arg("col_ids"), py::arg("row_ids"),
        py::arg("left_to_right") = true,
       "Build stacked geometric product matrix from list of MVs.");

    m.def("product_matrix_array_ip", [_mat_to_arr](const std::vector<TDynMV>& mvs,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            bool left_to_right) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrixArray_IP(mat, mvs, xMaskB, xMaskC, left_to_right);
        return _mat_to_arr(mat);
    }}, py::arg("mvs"), py::arg("col_ids"), py::arg("row_ids"),
        py::arg("left_to_right") = true,
       "Build stacked inner product matrix from list of MVs.");

    m.def("product_matrix_array_op", [_mat_to_arr](const std::vector<TDynMV>& mvs,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            bool left_to_right) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrixArray_OP(mat, mvs, xMaskB, xMaskC, left_to_right);
        return _mat_to_arr(mat);
    }}, py::arg("mvs"), py::arg("col_ids"), py::arg("row_ids"),
        py::arg("left_to_right") = true,
       "Build stacked outer product matrix from list of MVs.");

    // -----------------------------------------------------------------------
    // Reverse / Conjugate product matrix (diagonal sign matrix from blade mask)
    // -----------------------------------------------------------------------
    m.def("product_matrix_rev", [_mat_to_arr](const std::vector<uint32_t>& mask_ids) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMask;
        for (auto id : mask_ids) xMask.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrix_Reverse(mat, xMask);
        return _mat_to_arr(mat);
    }}, py::arg("mask_ids"),
       "Build diagonal reverse product matrix: M[i,i] = +-1 by grade.");

    m.def("product_matrix_conj", [_mat_to_arr](const std::vector<uint32_t>& mask_ids) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMask;
        for (auto id : mask_ids) xMask.Insert(TBlade(id));
        Tan::CMatrix<{ctype}> mat;
        Tan::GA::EvalProductMatrix_Conjugate(mat, xMask);
        return _mat_to_arr(mat);
    }}, py::arg("mask_ids"),
       "Build diagonal conjugate product matrix: M[i,i] = +-1 by grade and signature.");
"""


def matrix_int_def(ctype: str) -> str:
    """Modular-integer solve binding (integer dtypes only)."""
    return f"""
    // -----------------------------------------------------------------------
    // Modular-integer solve  (integer dtypes only)
    // -----------------------------------------------------------------------
    m.def("solve_mod", [](const TDynMV& wA, const TDynMV& wY,
            const std::vector<uint32_t>& col_ids,
            const std::vector<uint32_t>& row_ids,
            unsigned modulus) {{
        Tan::GA::CBladeMask<TBlade> xMaskB, xMaskC;
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        for (auto id : row_ids) xMaskC.Insert(TBlade(id));

        // Build product matrix for A
        Tan::CMatrix<{ctype}> matA;
        Tan::GA::EvalProductMatrix_GP(matA, wA, xMaskB, xMaskC, true);

        // Build RHS from Y
        Tan::CMatrix<{ctype}> matY;
        Tan::GA::ToMatrix(matY, wY, xMaskC);

        // Gauss elimination + back substitution in the modular ring
        TCong cong(static_cast<{ctype}>(modulus));
        std::vector<size_t> vecRowIdx;
        auto eRes = Tan::CMatrixAlgoGE<{ctype}>::GaussElimination(
                vecRowIdx, matA, matY, cong);

        if (eRes != Tan::EMatrixResult::Success)
            throw std::runtime_error("solve_mod: system has no unique solution");

        eRes = Tan::CMatrixAlgoGE<{ctype}>::TriangularBackSub(
                vecRowIdx, matA, matY, cong);

        if (eRes != Tan::EMatrixResult::Success)
            throw std::runtime_error("solve_mod: back-substitution failed");

        // Sort rows to undo pivot permutation
        Tan::CMatrix<{ctype}> matSorted;
        Tan::CMatrixAlgoGE<{ctype}>::SortRows(matSorted, vecRowIdx, matY);

        TDynMV wX;
        Tan::GA::ToMultivector(wX, matSorted, xMaskB);
        wX.Prune();
        return wX;
    }}, py::arg("wA"), py::arg("wY"),
        py::arg("col_ids"), py::arg("row_ids"), py::arg("modulus"),
       "Solve A*X = Y modulo modulus using Gaussian elimination.");
"""
