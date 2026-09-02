# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Template-based C++ binding code generator for TANGA geometric algebra.

Reads ``_template.cpp`` and substitutes concrete values for every placeholder.
"""

from pathlib import Path

from ._blade_masks import (
    product_blade_mask_gp_a_def,
    product_blade_mask_inv_gp_def,
    product_blade_mask_inv_ip_def,
    product_blade_mask_inv_op_def,
    product_blade_mask_ip_a_def,
    product_blade_mask_op_a_def,
)
from ._blade_ops import (
    blade_factorize_def,
    blade_factorize_versor_def,
    blade_inverse_def,
    blade_project_def,
    blade_project_vec_def,
    blade_pseudo_inverse_def,
    blade_reject_def,
    blade_reject_vec_def,
    join_def,
    meet_def,
)
from ._float_products import gp_float_def, inv_float_def, ip_float_def, op_float_def
from ._int_products import (
    gp_int_mod_def,
    inv_int_mod_def,
    ip_int_mod_def,
    op_int_mod_def,
    reduce_int_def,
)
from ._matrix import matrix_common_def, matrix_int_def
from ._mv_operators import (
    dual_def,
    gp_conj_def,
    gp_rev_def,
    grade_proj_def,
    grades_def,
    ip_conj_def,
    ip_rev_def,
    is_grade_def,
    is_scalar_def,
    is_zero_def,
    magnitude_def,
    magnitude_sq_def,
    op_conj_def,
    op_rev_def,
    project_onto_def,
    project_onto_mask_def,
    scalar_def,
    sp_def,
)
from ._tensor import product_tensor_def
from ._utils import sub_bare, sub_braced

_TEMPLATE_PATH = Path(__file__).parent.parent / "_template.cpp"


def module_name(dim: int, sig: int, dtype: str) -> str:
    return f"binding_dim{dim}_sig{sig}_{dtype}"


def generate(dim: int, sig: int, dtype: str, output: Path) -> None:
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")

    ctype_map = {
        "float32": "float",
        "float64": "double",
        "int32": "int32_t",
        "int64": "int64_t",
    }
    ctype = ctype_map[dtype]
    cong = (
        f"Tan::CCongruence_Float<{ctype}>"
        if dtype.startswith("float")
        else f"Tan::CCongruence_HMod<{ctype}>"
    )
    mod_name = module_name(dim, sig, dtype)

    # basic braced placeholders
    template = sub_braced(template, "DIM", str(dim))
    template = sub_braced(template, "SIG", str(sig))
    template = sub_braced(template, "CTYPE", ctype)
    template = sub_braced(template, "CONG_TYPE", cong)
    template = sub_braced(template, "MODULE_NAME", mod_name)

    # Product / inv definitions — bare words
    if dtype.startswith("float"):
        template = sub_bare(template, "GP_MOD_DEF", gp_float_def())
        template = sub_bare(template, "OP_MOD_DEF", op_float_def())
        template = sub_bare(template, "IP_MOD_DEF", ip_float_def())
        template = sub_braced(template, "INV_DEF", inv_float_def())
        template = sub_bare(template, "REDUCE_DEF", "")
        template = sub_bare(template, "MATRIX_DEF", matrix_common_def(ctype))
    else:
        template = sub_bare(template, "GP_MOD_DEF", gp_int_mod_def(ctype))
        template = sub_bare(template, "OP_MOD_DEF", op_int_mod_def(ctype))
        template = sub_bare(template, "IP_MOD_DEF", ip_int_mod_def(ctype))
        template = sub_braced(template, "INV_DEF", inv_int_mod_def(ctype))
        template = sub_bare(template, "REDUCE_DEF", reduce_int_def(ctype))
        template = sub_bare(
            template, "MATRIX_DEF", matrix_common_def(ctype) + matrix_int_def(ctype)
        )

    # Extended MV operators (Phases A-D, all dtypes)
    template = sub_bare(template, "GRADE_PROJ_DEF", grade_proj_def())
    template = sub_bare(template, "SCALAR_DEF", scalar_def(ctype))
    template = sub_bare(template, "DUAL_DEF", dual_def())
    template = sub_bare(template, "MAGNITUDE_SQ_DEF", magnitude_sq_def(ctype))
    template = sub_bare(template, "MAGNITUDE_DEF", magnitude_def())
    template = sub_bare(template, "IS_ZERO_DEF", is_zero_def())
    template = sub_bare(template, "IS_SCALAR_DEF", is_scalar_def())
    template = sub_bare(template, "SP_DEF", sp_def(ctype))
    template = sub_bare(template, "PROJECT_ONTO_DEF", project_onto_def())
    template = sub_bare(template, "PROJECT_ONTO_MASK_DEF", project_onto_mask_def())
    template = sub_bare(template, "GP_REV_DEF", gp_rev_def())
    template = sub_bare(template, "GP_CONJ_DEF", gp_conj_def())
    template = sub_bare(template, "IP_REV_DEF", ip_rev_def())
    template = sub_bare(template, "IP_CONJ_DEF", ip_conj_def())
    template = sub_bare(template, "OP_REV_DEF", op_rev_def())
    template = sub_bare(template, "OP_CONJ_DEF", op_conj_def())
    template = sub_bare(template, "GRADES_DEF", grades_def())
    template = sub_bare(template, "IS_GRADE_DEF", is_grade_def())

    # Blade operations (Phase E) — dtype-independent
    template = sub_bare(template, "BLADE_INVERSE_DEF", blade_inverse_def())
    template = sub_bare(
        template, "BLADE_PSEUDO_INVERSE_DEF", blade_pseudo_inverse_def()
    )
    template = sub_bare(template, "BLADE_FACTORIZE_DEF", blade_factorize_def())
    template = sub_bare(template, "JOIN_DEF", join_def())
    template = sub_bare(template, "MEET_DEF", meet_def())
    template = sub_bare(
        template, "BLADE_FACTORIZE_VERSOR_DEF", blade_factorize_versor_def()
    )
    template = sub_bare(template, "BLADE_PROJECT_DEF", blade_project_def())
    template = sub_bare(template, "BLADE_PROJECT_VEC_DEF", blade_project_vec_def())
    template = sub_bare(template, "BLADE_REJECT_DEF", blade_reject_def())
    template = sub_bare(template, "BLADE_REJECT_VEC_DEF", blade_reject_vec_def())

    # Product blade mask from A-mask (mask-based, Phase 1 refactor)
    template = sub_bare(
        template, "PRODUCT_BLADE_MASK_GP_A_DEF", product_blade_mask_gp_a_def()
    )
    template = sub_bare(
        template, "PRODUCT_BLADE_MASK_IP_A_DEF", product_blade_mask_ip_a_def()
    )
    template = sub_bare(
        template, "PRODUCT_BLADE_MASK_OP_A_DEF", product_blade_mask_op_a_def()
    )

    # Product tensor (3D Cayley table for GP/IP/OP)
    template = sub_bare(template, "PRODUCT_TENSOR_DEF", product_tensor_def(ctype))

    # Inverse blade mask (predict B-mask from A-mask and C-mask)
    template = sub_bare(
        template, "PRODUCT_BLADE_MASK_INV_GP_DEF", product_blade_mask_inv_gp_def()
    )
    template = sub_bare(
        template, "PRODUCT_BLADE_MASK_INV_IP_DEF", product_blade_mask_inv_ip_def()
    )
    template = sub_bare(
        template, "PRODUCT_BLADE_MASK_INV_OP_DEF", product_blade_mask_inv_op_def()
    )

    output.write_text(template, encoding="utf-8")
