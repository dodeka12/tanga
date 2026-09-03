# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The Expression class and the tensor-based product builder."""

from __future__ import annotations

from types import NotImplementedType
from typing import TYPE_CHECKING, Any, NoReturn

import numpy as np

from pytanga.algebra import EInv, EProduct, MV
from pytanga.blade_mask import BladeMask
from pytanga.tensor import MVTensor, MVLabeledTensor
from pytanga.tensor._labeled import _axis_names
from pytanga.tensor.convert import from_tensor, to_tensor
from pytanga.tensor.ops import contract_labeled
from pytanga.tensor.product import (
    product_tensor,
    product_tensor_conj,
    product_tensor_rev,
)

from ._data_array import DataArray
from ._labels import OUT_LABEL, allocate_block, block_for_label
from ._variable import Variable

if TYPE_CHECKING:
    from pytanga.algebra import Algebra


class Expression:
    """A reduced tensor expression over named variables.

    Holds an ``MVLabeledTensor`` whose axes are:

    - axis 0: the output (result multivector) axis, labelled ``OUT_LABEL``;
    - one axis per variable occurrence, labelled by that occurrence's letter;
    - optional counting (``None``-mask) axes for batched partial evaluations.

    The result is a multilinear form in each variable: a variable may appear up
    to ``MAX_DEGREE`` times per term (e.g. ``v * v``).
    """

    __slots__ = ("_tensor", "_names", "_masks")

    def __init__(
        self,
        tensor: "MV | MVLabeledTensor",
        names: "dict[str, tuple[int, ...]] | BladeMask | None" = None,
        masks: "dict[str, BladeMask] | None" = None,
    ) -> None:
        if isinstance(tensor, MV):
            # Constant multivector expression.
            mask = names if isinstance(names, BladeMask) else BladeMask(tensor)
            self._tensor = MVLabeledTensor(to_tensor(tensor, mask=mask), OUT_LABEL)
            self._names = {}
            self._masks = {}
            return
        self._tensor = tensor  # MVLabeledTensor
        self._names = dict(names)  # name -> occurrence labels
        self._masks = dict(masks)  # name -> BladeMask

    @property
    def tensor(self) -> MVLabeledTensor:
        """The internal reduced ``MVLabeledTensor``."""
        return self._tensor

    @property
    def names(self) -> dict[str, tuple[int, ...]]:
        """A copy of the ``name -> occurrence labels`` mapping."""
        return dict(self._names)

    @property
    def masks(self) -> dict[str, BladeMask]:
        """A copy of the ``name -> BladeMask`` mapping."""
        return dict(self._masks)

    @property
    def out_mask(self) -> BladeMask:
        """The blade mask of the output axis."""
        return self._tensor.tensor.masks[0]

    @property
    def out_label(self) -> str:
        """The label of the output axis (always ``OUT_LABEL``)."""
        return OUT_LABEL

    @property
    def algebra(self) -> "Algebra":
        """The algebra this expression belongs to."""
        return self.out_mask.algebra

    @property
    def ndim(self) -> int:
        """Total number of axes (1 output + free variables + counting axes)."""
        return self._tensor.ndim

    def _has_counting_axes(self) -> bool:
        """True if the tensor carries batch (``None``-mask) axes beyond the output."""
        masks = self._tensor.tensor.masks
        return any(m is None for m in masks[1:])

    def _var_axes(self) -> tuple[list, list]:
        """Return ``(labels, masks)`` of the variable axes, in order."""
        raw = _axis_names(self._tensor.labels)
        masks = self._tensor.tensor.masks
        return list(raw[1:]), list(masks[1:])

    def __repr__(self) -> str:
        return f"Expression(names={sorted(self._names)}, out_mask={self.out_mask})"

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def __call__(self, **bindings: Any) -> "MV | Expression | list":
        """Evaluate the expression, binding some or all variables.

        A variable value may be:

        - a single ``MV`` (or scalar) — contract that variable;
        - a ``DataArray`` — contract its blade axis (matched to the variable
          mask) against every occurrence of the variable, keeping its counting
          axes element-wise.

        A binding key may also name a ``None``-mask counting axis already present
        in the expression, which reduces that axis:

        - ``expr(pnt_idx=scalars)`` — sum the axis away with a 1-D array;
        - ``expr(pnt_idx=data)`` — reduce with a ``DataArray``: a 1-D DataArray is
          the key (sum by default; ``"_"`` multiplies/keeps), while a multi-axis
          DataArray marks the key with ``"_"``/``"*"``/matching name and keeps the
          other axes as new named dimensions.

        If variables remain unbound, a new ``Expression`` over those variables is
        returned (it may carry counting axes).  Otherwise the result is an ``MV``
        (single values) or a nested ``list`` of ``MV`` (batched).
        """
        return self._evaluate(bindings, True)

    def _evaluate(
        self, bindings: dict[str, Any], check_blades: bool
    ) -> "MV | Expression | list":
        raw = _axis_names(self._tensor.labels)
        masks = self._tensor.tensor.masks

        counting = {}
        for i in range(1, len(raw)):
            if masks[i] is None:
                counting[raw[i]] = i

        unknown = set(bindings) - set(self._names) - set(counting)
        if unknown:
            raise ValueError(f"unknown variable(s): {sorted(unknown)}")

        if not bindings:
            if not self._names:
                return from_tensor(self._tensor.tensor)  # constant -> MV
            return self

        var_bindings = {k: v for k, v in bindings.items() if k in self._names}
        count_bindings = {k: v for k, v in bindings.items() if k in counting}

        base_tensor = self._tensor
        if count_bindings:
            base_labels = [(ax.name, ax.mode) for ax in self._tensor.labels]
            for name, value in count_bindings.items():
                mode = _count_binding_mode(name, value)
                base_labels[counting[name]] = (name, mode)
            base_tensor = MVLabeledTensor(self._tensor.tensor, base_labels)

        labeled = [base_tensor]
        alg = self.algebra
        used = set(_axis_names(base_tensor.labels))

        for name, value in count_bindings.items():
            length = self._tensor.tensor.shape[counting[name]]
            labeled.append(
                _count_binding_tensor(name, value, length, used, set(counting))
            )

        for name, value in var_bindings.items():
            labels = self._names[name]
            mask = self._masks[name]

            if isinstance(value, DataArray):
                labeled.extend(
                    _variable_dataarray_binding_tensors(value, mask, labels, used)
                )
                continue

            if isinstance(value, (int, float)):
                value = alg.multivector({0: float(value)})
            if not isinstance(value, MV):
                raise TypeError(
                    f"binding for {name!r} must be a single MV or DataArray, "
                    f"got {type(value).__name__}"
                )
            if check_blades:
                _check_blades(value, mask, name)
            for label in labels:
                labeled.append(MVLabeledTensor(to_tensor(value, mask=mask), label))

        result = contract_labeled(*labeled)

        remaining = set(self._names) - set(var_bindings)
        if remaining:
            new_names = {n: self._names[n] for n in remaining}
            new_masks = {n: self._masks[n] for n in remaining}
            return Expression(result, new_names, new_masks)

        return from_tensor(result.tensor)

    # ------------------------------------------------------------------
    # Products — chain into the tensor builder
    # ------------------------------------------------------------------

    def __mul__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | NotImplementedType":
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(self, other, EProduct.GP)

    def __rmul__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | NotImplementedType":
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(other, self, EProduct.GP)

    def __or__(
        self, other: "MV | Variable | Expression"
    ) -> "Expression | NotImplementedType":
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(self, other, EProduct.IP)

    def __ror__(
        self, other: "MV | Variable | Expression"
    ) -> "Expression | NotImplementedType":
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(other, self, EProduct.IP)

    def __xor__(
        self, other: "MV | Variable | Expression"
    ) -> "Expression | NotImplementedType":
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(self, other, EProduct.OP)

    def __rxor__(
        self, other: "MV | Variable | Expression"
    ) -> "Expression | NotImplementedType":
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(other, self, EProduct.OP)

    def __neg__(self) -> "Expression":
        return self._scale(-1.0)

    def __truediv__(self, other: Any) -> "Expression | NotImplementedType":
        if isinstance(other, (int, float)):
            return self._scale(1.0 / float(other))
        return NotImplemented

    def _scale(self, scalar: float) -> "Expression":
        return Expression(self._tensor.mul_scalar(scalar), self._names, self._masks)

    # ------------------------------------------------------------------
    # Addition / subtraction (broadcast with output-mask unification)
    # ------------------------------------------------------------------

    def __add__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression | NotImplementedType":
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _add(self, other)

    def __radd__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression | NotImplementedType":
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _add(other, self)

    def __sub__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression | NotImplementedType":
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _add(self, other, subtract=True)

    def __rsub__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression | NotImplementedType":
        if isinstance(other, (int, float)) and other == 0:
            return self._scale(-1.0)
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _add(other, self, subtract=True)

    # ------------------------------------------------------------------
    # Involutions
    # ------------------------------------------------------------------

    def __invert__(self) -> "Expression":
        return _apply_involution(self, EInv.REV)

    def conj(self) -> "Expression":
        return _apply_involution(self, EInv.CONJ)

    # ------------------------------------------------------------------
    # Inverse
    # ------------------------------------------------------------------

    def inv(self, var_name: str) -> "Expression":
        """Return the inverse linear map as a new expression.

        The expression must be a single-variable expression whose tensor is a
        square, invertible matrix over the output and variable axes.  The
        result maps the old output space back to the old variable space, keyed
        by *var_name*: ``self.inv(name)(**{name: y})`` recovers ``x`` from
        ``y = self(V1=x)``.
        """
        if self._has_counting_axes():
            raise ValueError("inv() requires a plain (non-stacked) expression")
        if len(self._names) != 1:
            raise ValueError(
                "inv() requires a single-variable expression "
                f"(got {sorted(self._names)})"
            )
        (name,) = self._names
        if len(self._names[name]) != 1:
            raise ValueError(
                f"inv() requires {name!r} to appear exactly once "
                f"(got {len(self._names[name])} occurrences)"
            )
        out_mask = self.out_mask
        var_mask = self._tensor.tensor.masks[1]
        if len(out_mask) != len(var_mask):
            raise ValueError(
                "inv() requires a square matrix "
                f"(output mask has {len(out_mask)} blades, "
                f"variable mask has {len(var_mask)})"
            )

        mat = np.asarray(self.tensor.data, dtype=np.float64)
        try:
            inv_mat = np.linalg.inv(mat)
        except np.linalg.LinAlgError as exc:
            raise ValueError("inv() failed: the expression matrix is singular") from exc

        new_label = allocate_block()[0]
        result = MVTensor(data=inv_mat, masks=(var_mask, out_mask))
        labeled = MVLabeledTensor(result, [(OUT_LABEL, "*"), (new_label, "*")])
        return Expression(labeled, {var_name: (new_label,)}, {var_name: out_mask})

    def _variable_matrix(self) -> tuple[BladeMask, np.ndarray]:
        """Return ``(var_mask, matrix)`` for the single remaining variable.

        Flattens every non-variable axis (the output axis and any counting
        axes) into the rows of a 2-D matrix whose columns are the blades of the
        variable's mask.  Raises ``ValueError`` unless the expression has
        exactly one variable occurring exactly once.
        """
        if len(self._names) != 1:
            raise ValueError(
                f"requires a single-variable expression (got {sorted(self._names)})"
            )
        (var_name,) = self._names
        labels = self._names[var_name]
        if len(labels) != 1:
            raise ValueError(
                f"requires {var_name!r} to appear exactly once "
                f"(got {len(labels)} occurrences)"
            )
        var_label = labels[0]
        var_mask = self._masks[var_name]

        raw = _axis_names(self._tensor.labels)
        var_axis = raw.index(var_label)
        data = np.asarray(self._tensor.tensor.data, dtype=np.float64)
        n_var = data.shape[var_axis]

        flat = np.moveaxis(data, var_axis, -1)
        matrix = flat.reshape(-1, n_var)
        return var_mask, matrix

    def lstsq(self, rhs: "MV | int | float | None" = None) -> "MV":
        """Solve this single-variable expression in the least-squares sense.

        The expression must have exactly one remaining variable, which must
        occur exactly once.  All non-variable axes (the output axis and any
        counting axes left by a partial evaluation) are flattened into the
        rows of a linear system whose columns are the blades of the variable's
        mask.

        - ``rhs=None`` (default): solve the homogeneous system
          ``M · vec(x) = 0``.  Returns the smallest-singular-vector solution
          (the right singular vector of the least singular value).
        - otherwise: solve ``M · vec(x) = rhs`` via ``numpy.linalg.lstsq``.
          This requires a non-stacked expression (no counting axes) and *rhs*
          must be an ``MV`` over the expression's output mask.

        Returns
        -------
        MV
            The variable value (coefficients over the variable mask).

        Raises
        ------
        ValueError
            If the expression has more than one variable, has no variable, or
            the sole variable occurs more than once, or *rhs* is given on a
            stacked expression.
        """
        from pytanga.tensor import MVTensor as _MVTensor

        var_mask, matrix = self._variable_matrix()

        if rhs is None:
            if matrix.shape[0] == 0:
                raise ValueError("lstsq(): empty linear system")
            _, _, vt = np.linalg.svd(matrix, full_matrices=False)
            x = vt[-1]
        else:
            if self._has_counting_axes():
                raise ValueError(
                    "lstsq() with rhs requires a non-stacked expression "
                    "(no counting axes); use a homogeneous fit or evaluate "
                    "batches separately"
                )
            if isinstance(rhs, (int, float)):
                rhs = self.algebra.multivector({0: float(rhs)})
            if not isinstance(rhs, MV):
                raise TypeError(f"lstsq() rhs must be an MV, got {type(rhs).__name__}")
            rhs_vec = to_tensor(rhs, mask=self.out_mask).data
            x, _, _, _ = np.linalg.lstsq(matrix, rhs_vec, rcond=None)

        result = _MVTensor(data=x.astype(np.float64), masks=(var_mask,))
        return from_tensor(result)

    def svd(self) -> tuple[list[float], list["MV"]]:
        """Return the singular values and right-singular multivectors.

        Treats this single-variable expression as a linear map and returns
        ``(values, mvs)`` where *values* is the list of singular values (in
        descending order) and *mvs* is the list of the corresponding
        right-singular vectors, each reconstructed as an ``MV`` over the
        variable's blade mask.

        Raises ``ValueError`` if the expression has no variable, more than one
        variable, or the sole variable occurs more than once.
        """
        from pytanga.tensor import MVTensor as _MVTensor

        var_mask, matrix = self._variable_matrix()
        if matrix.shape[0] == 0:
            raise ValueError("svd(): empty linear system")
        _u, s, vt = np.linalg.svd(matrix, full_matrices=False)
        mvs = [
            from_tensor(_MVTensor(data=vec.astype(np.float64), masks=(var_mask,)))
            for vec in vt
        ]
        return s.tolist(), mvs


class AffineExpression:
    """A sum of :class:`Expression` terms that could not be merged into one tensor.

    Holds a flat ``list`` of ``Expression`` terms (each a multilinear form in its
    own variables).  ``+``/``-`` concatenate term lists, ``*`` distributes over
    the terms, and ``__call__`` evaluates each term and sums the results.
    """

    __slots__ = ("_terms",)

    def __init__(self, terms: "list[Expression]") -> None:
        self._terms = list(terms)

    @property
    def terms(self) -> list["Expression"]:
        """A copy of the term list (each an ``Expression``)."""
        return list(self._terms)

    @property
    def names(self) -> set[str]:
        """The set of variable names appearing in any term."""
        result: set[str] = set()
        for term in self._terms:
            result.update(term.names)
        return result

    @property
    def masks(self) -> dict[str, BladeMask]:
        """Union of the per-variable masks (``name -> BladeMask``)."""
        result: dict[str, BladeMask] = {}
        for term in self._terms:
            result.update(term.masks)
        return result

    def _union_masks(self) -> dict[str, BladeMask]:
        """Union of each variable's masks across all terms."""
        result: dict[str, BladeMask] = {}
        for term in self._terms:
            for name, mask in term.masks.items():
                if name in result:
                    result[name] = result[name].union(mask)
                else:
                    result[name] = mask
        return result

    @property
    def out_mask(self) -> BladeMask:
        """The union of the terms' output blade masks."""
        result = self._terms[0].out_mask
        for term in self._terms[1:]:
            result = result.union(term.out_mask)
        return result

    @property
    def algebra(self) -> "Algebra":
        """The algebra this affine expression belongs to."""
        return self.out_mask.algebra

    def __repr__(self) -> str:
        return f"AffineExpression(terms={len(self._terms)})"

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def __call__(self, **bindings: Any) -> "MV | AffineExpression | list":
        """Evaluate the sum, binding some or all variables.

        Values are a single ``MV``/scalar or a ``DataArray``, exactly as for
        :meth:`Expression.__call__`.  Fully bound single values yield an ``MV``;
        fully bound ``DataArray`` bindings yield a (nested) ``list``; a remaining
        variable yields an ``AffineExpression`` (or a list of them).
        """
        unknown = set(bindings) - self.names
        if unknown:
            raise ValueError(f"unknown variable(s): {sorted(unknown)}")

        if not bindings:
            return self

        union = self._union_masks()
        for name, value in bindings.items():
            if isinstance(value, (int, float)):
                bindings[name] = self.algebra.multivector({0: float(value)})
            if isinstance(value, MV):
                _check_blades(value, union[name], name)

        results = []
        for term in self._terms:
            sub = {k: v for k, v in bindings.items() if k in term.names}
            results.append(term._evaluate(sub, False))

        return _combine_terms(results)

    # ------------------------------------------------------------------
    # Addition / subtraction — concatenate term lists
    # ------------------------------------------------------------------

    def __add__(self, other: Any) -> "AffineExpression":
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _affine_add(self, other, subtract=False)

    def __radd__(self, other: Any) -> "AffineExpression":
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _affine_add(other, self, subtract=False)

    def __sub__(self, other: Any) -> "AffineExpression":
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _affine_add(self, other, subtract=True)

    def __rsub__(self, other: Any) -> "AffineExpression":
        if isinstance(other, (int, float)) and other == 0:
            return -self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _affine_add(other, self, subtract=True)

    def __neg__(self) -> "AffineExpression":
        return AffineExpression([-t for t in self._terms])

    # ------------------------------------------------------------------
    # Products — distribute over the terms
    # ------------------------------------------------------------------

    def __mul__(self, other: Any) -> "AffineExpression":
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        if isinstance(other, AffineExpression):
            return AffineExpression(
                [_product(a, b, EProduct.GP) for a in self._terms for b in other._terms]
            )
        return AffineExpression([_product(t, other, EProduct.GP) for t in self._terms])

    def __rmul__(self, other: Any) -> "AffineExpression":
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        return AffineExpression([_product(other, t, EProduct.GP) for t in self._terms])

    def __or__(self, other: Any) -> "AffineExpression":
        if isinstance(other, AffineExpression):
            return AffineExpression(
                [_product(a, b, EProduct.IP) for a in self._terms for b in other._terms]
            )
        return AffineExpression([_product(t, other, EProduct.IP) for t in self._terms])

    def __ror__(self, other: Any) -> "AffineExpression":
        return AffineExpression([_product(other, t, EProduct.IP) for t in self._terms])

    def __xor__(self, other: Any) -> "AffineExpression":
        if isinstance(other, AffineExpression):
            return AffineExpression(
                [_product(a, b, EProduct.OP) for a in self._terms for b in other._terms]
            )
        return AffineExpression([_product(t, other, EProduct.OP) for t in self._terms])

    def __rxor__(self, other: Any) -> "AffineExpression":
        return AffineExpression([_product(other, t, EProduct.OP) for t in self._terms])

    def __truediv__(self, other: Any) -> "AffineExpression | NotImplementedType":
        if isinstance(other, (int, float)):
            return self._scale(1.0 / float(other))
        return NotImplemented

    def _scale(self, scalar: float) -> "AffineExpression":
        return AffineExpression([t._scale(scalar) for t in self._terms])

    # ------------------------------------------------------------------
    # Involutions / inverse
    # ------------------------------------------------------------------

    def __invert__(self) -> "AffineExpression":
        return AffineExpression([~t for t in self._terms])

    def conj(self) -> "AffineExpression":
        return AffineExpression([t.conj() for t in self._terms])

    def inv(self, var_name: str) -> "NoReturn":
        raise ValueError(
            "inv() requires a single linear Expression, not an AffineExpression"
        )


def _variable_dataarray_binding_tensors(
    data: DataArray, mask: BladeMask, labels: tuple[int, ...], used: set
) -> list[MVLabeledTensor]:
    """Build one labeled tensor per occurrence for a ``DataArray`` binding."""
    array = data.array
    specs = data.masks

    blade_axis = None
    masks = []
    for i, spec in enumerate(specs):
        if isinstance(spec, BladeMask):
            if blade_axis is not None:
                raise ValueError("binding specs may contain only one BladeMask")
            if spec != mask:
                raise ValueError("binding BladeMask does not match the variable mask")
            blade_axis = i
            masks.append(spec)
        else:
            masks.append(None)

    if blade_axis is None:
        raise ValueError("binding DataArray must contain one BladeMask")

    for i, spec in enumerate(specs):
        if i == blade_axis:
            continue
        if spec in used:
            raise ValueError(f"counting name {spec!r} is already in use")
        used.add(spec)

    tensor = MVTensor(data=array, masks=tuple(masks))

    out = []
    for lab in labels:
        lab_list = []
        for i, spec in enumerate(specs):
            if i == blade_axis:
                lab_list.append((lab, "*"))
            else:
                lab_list.append((spec, "_"))
        out.append(MVLabeledTensor(tensor, lab_list))
    return out


def _parse_count_spec(spec: str, key: str) -> tuple[str, str]:
    """Return ``(name, mode)`` for one counting-axis reduction spec.

    ``"_"`` resolves to the binding key in element-wise mode; ``"*"`` resolves to
    the binding key in contract mode; a trailing ``_`` means element-wise
    (kept/multiplied); otherwise the axis is contracted.
    """
    if spec == "_":
        return key, "_"
    if spec == "*":
        return key, "*"
    if spec.endswith("_"):
        return spec[:-1], "_"
    return spec, "*"


def _count_binding_mode(name: str, value: Any) -> str:
    """Return the reduction mode (``"*"`` or ``"_"``) for a counting-axis binding."""
    if isinstance(value, DataArray):
        for spec in value.masks:
            n, m = _parse_count_spec(spec, name)
            if n == name:
                return m
    return "*"


def _count_array_binding_tensor(
    name: str,
    array: np.ndarray,
    specs: tuple,
    length: int,
    used: set,
    counting_names: set,
) -> MVLabeledTensor:
    """Build the labeled tensor for a multi-axis counting-axis reduction."""
    if len(specs) != array.ndim:
        raise ValueError(
            f"binding specs have {len(specs)} axes but the array has {array.ndim}"
        )

    resolved = []
    key_hits = []
    for spec in specs:
        if not isinstance(spec, str):
            raise TypeError(
                f"counting-axis reduction spec must be a str, got {type(spec).__name__}"
            )
        n, m = _parse_count_spec(spec, name)
        resolved.append((n, m))
        if n == name:
            key_hits.append((n, m))

    if len(key_hits) != 1:
        raise ValueError(
            f"counting-axis reduction for {name!r} must name it exactly once "
            f"(got {len(key_hits)})"
        )
    key_mode = key_hits[0][1]

    labels = []
    for n, m in resolved:
        if n == name:
            labels.append((n, key_mode))
        elif n in counting_names:
            labels.append((n, "_"))
        elif n in used:
            raise ValueError(f"counting name {n!r} collides with an existing axis")
        else:
            used.add(n)
            labels.append((n, "_"))

    key_axis = next(i for i, (n, _m) in enumerate(resolved) if n == name)
    if array.shape[key_axis] != length:
        raise ValueError(
            f"counting-axis binding for {name!r} has length "
            f"{array.shape[key_axis]}, expected {length}"
        )

    return MVLabeledTensor(MVTensor(array, (None,) * array.ndim), labels)


def _count_dataarray_binding_tensor(
    name: str,
    data: DataArray,
    length: int,
    used: set,
    counting_names: set,
) -> MVLabeledTensor:
    """Build the labeled tensor for a ``DataArray`` counting-axis reduction."""
    array = data.array
    specs = data.masks
    if array.ndim == 1:
        n, m = _parse_count_spec(specs[0], name)
        if array.shape[0] != length:
            raise ValueError(
                f"counting-axis binding for {name!r} has length "
                f"{array.shape[0]}, expected {length}"
            )
        return MVLabeledTensor(MVTensor(array, (None,)), [(name, m)])
    return _count_array_binding_tensor(name, array, specs, length, used, counting_names)


def _count_binding_tensor(
    name: str, value: Any, length: int, used: set, counting_names: set
) -> MVLabeledTensor:
    """Build the labeled tensor for a counting-axis reduction binding."""
    if isinstance(value, DataArray):
        return _count_dataarray_binding_tensor(
            name, value, length, used, counting_names
        )

    if isinstance(value, np.ndarray):
        arr = value
    elif isinstance(value, (list, tuple)):
        arr = np.asarray(value)
    else:
        raise TypeError(
            f"counting-axis binding for {name!r} must be a 1-D array or "
            f"DataArray, got {type(value).__name__}"
        )
    if arr.ndim != 1:
        raise ValueError(
            f"counting-axis binding for {name!r} must be 1-D; use a DataArray "
            f"to keep other dimensions"
        )
    if arr.shape[0] != length:
        raise ValueError(
            f"counting-axis binding for {name!r} has length {arr.shape[0]}, "
            f"expected {length}"
        )
    return MVLabeledTensor(MVTensor(arr, (None,)), [(name, "*")])


def _add_values(a: Any, b: Any) -> Any:
    """Add two evaluation results, broadcasting a single MV over nested lists."""
    if isinstance(a, list) and isinstance(b, list):
        return [_add_values(x, y) for x, y in zip(a, b)]
    if isinstance(a, list):
        return [_add_values(x, b) for x in a]
    if isinstance(b, list):
        return [_add_values(a, y) for y in b]
    return a + b


def _combine_terms(results: list) -> "MV | AffineExpression | list":
    """Combine per-term evaluation results, broadcasting single values.

    Each result is an ``MV``, a (nested) ``list`` of ``MV``, or a partial
    ``Expression``.
    """
    if any(isinstance(r, Expression) for r in results):
        if any(isinstance(r, list) for r in results):
            n = len(next(r for r in results if isinstance(r, list)))
            return [
                _combine_terms([r[i] if isinstance(r, list) else r for r in results])
                for i in range(n)
            ]
        terms = [_to_expression(r) if isinstance(r, MV) else r for r in results]
        return AffineExpression(terms)

    total = results[0]
    for r in results[1:]:
        total = _add_values(total, r)
    return total


def _coerce_addend(x: Any) -> list["Expression"]:
    """Return the term list for an addend."""
    if isinstance(x, AffineExpression):
        return list(x.terms)
    if isinstance(x, (MV, Expression)):
        return [_to_expression(x)]
    raise TypeError(f"unsupported operand type {type(x).__name__}")


def _affine_add(left: Any, right: Any, subtract: bool = False) -> AffineExpression:
    """Concatenate two addends into an ``AffineExpression``."""
    lterms = _coerce_addend(left)
    rterms = _coerce_addend(right)
    if subtract:
        rterms = [-t for t in rterms]
    return AffineExpression(lterms + rterms)


# ---------------------------------------------------------------------------
# Operand resolution
# ---------------------------------------------------------------------------


def _operand(x: Any) -> tuple[str, Any]:
    """Classify an operand as ``('var'|'const'|'expr', value)``."""
    if isinstance(x, Variable):
        return "var", x
    if isinstance(x, Expression):
        return "expr", x
    if isinstance(x, MV):
        return "const", x
    raise TypeError(f"unsupported operand type {type(x).__name__}")


def _value_mask(kind: str, val: Any) -> BladeMask:
    """Return the blade mask of an operand's value axis."""
    if kind == "var":
        return val.mask
    if kind == "expr":
        return val.out_mask
    if kind == "const":
        return BladeMask(val)
    raise AssertionError(f"unknown operand kind {kind!r}")


# ---------------------------------------------------------------------------
# Product builder
# ---------------------------------------------------------------------------


def _product(
    left: Any,
    right: Any,
    product: EProduct,
    a_inv: EInv = EInv.ID,
    b_inv: EInv = EInv.ID,
) -> Expression:
    """Build the reduced expression for ``left ∘ right``.

    Builds the 3-D product tensor and contracts every constant/expression
    operand, leaving one axis per remaining variable plus the output axis.
    """
    Lkind, Lval = _operand(left)
    Rkind, Rval = _operand(right)

    stacked = [
        kind
        for kind, val in ((Lkind, Lval), (Rkind, Rval))
        if kind == "expr" and val._has_counting_axes()
    ]
    if len(stacked) == 2:
        raise ValueError(
            "cannot compose two stacked (batched) expressions; "
            "fully evaluate one of them before the product"
        )

    m_L = _value_mask(Lkind, Lval)
    m_R = _value_mask(Rkind, Rval)

    if m_L.algebra is not m_R.algebra:
        raise ValueError("expression operands belong to different algebras")

    prod = product_tensor(m_L, m_R, None, product=product, a_inv=a_inv, b_inv=b_inv)
    m_C = prod.masks[0]

    operands = [prod.data]
    axes = [[0, 1, 2]]  # C, L, R
    out_axes = [0]
    next_ax = 3

    var_specs: list[tuple[str, str]] = []
    var_masks: list[BladeMask] = []
    names: dict[str, tuple[str, ...]] = {}
    masks: dict[str, BladeMask] = {}

    def add(kind: str, val: Any, value_axis: int) -> None:
        nonlocal next_ax
        if kind == "var":
            block = val.labels
            occ = len(names.get(val.name, ()))
            if occ >= len(block):
                raise ValueError(
                    f"variable {val.name!r} appears more than {len(block)} times "
                    "in a product term"
                )
            lab = block[occ]
            var_specs.append((lab, "*"))
            var_masks.append(val.mask)
            names[val.name] = names.get(val.name, ()) + (lab,)
            masks[val.name] = val.mask
            out_axes.append(value_axis)
            return
        if kind == "const":
            vec_mask = m_L if value_axis == 1 else m_R
            operands.append(to_tensor(val, mask=vec_mask).data)
            axes.append([value_axis])
            return
        if kind == "expr":
            # A variable already present in the product must shift its
            # occurrences onto the next free slots of its (shared) label block.
            rename: dict[str, str] = {}
            for nm, lbls in val.names.items():
                if nm in names:
                    block = block_for_label(lbls[0])
                    base = len(names[nm])
                    if base + len(lbls) > len(block):
                        raise ValueError(
                            f"variable {nm!r} appears more than {len(block)} times "
                            "in a product term"
                        )
                    for i, old in enumerate(lbls):
                        rename[old] = block[base + i]
                    names[nm] = names[nm] + block[base : base + len(lbls)]
                    masks[nm] = val.masks[nm]
                else:
                    names[nm] = lbls
                    masks[nm] = val.masks[nm]
            raw = _axis_names(val.tensor.labels)
            e_masks = val.tensor.tensor.masks
            sub = [value_axis]
            for i in range(1, val.ndim):
                lab = raw[i]
                mode = "_" if e_masks[i] is None else "*"
                var_specs.append((rename.get(lab, lab), mode))
                var_masks.append(e_masks[i])
                sub.append(next_ax)
                out_axes.append(next_ax)
                next_ax += 1
            operands.append(val.tensor.data)
            axes.append(sub)
            return

    add(Lkind, Lval, 1)
    add(Rkind, Rval, 2)

    args = []
    for op, sub in zip(operands, axes):
        args.append(op)
        args.append(sub)
    args.append(out_axes)
    result_data = np.einsum(*args)

    labels = [(OUT_LABEL, "*"), *var_specs]
    result = MVTensor(data=result_data, masks=(m_C, *var_masks))
    labeled = MVLabeledTensor(result, labels)
    return Expression(labeled, names, masks)


def _to_expression(x: Any) -> Expression:
    """Coerce an ``MV``/``Variable`` into an ``Expression``.

    An ``MV`` becomes a zero-variable (constant) expression; a ``Variable``
    becomes the identity map over its mask.
    """
    if isinstance(x, Expression):
        return x
    if isinstance(x, Variable):
        return _involution(x, EInv.ID)
    if isinstance(x, MV):
        labeled = MVLabeledTensor(to_tensor(x, mask=BladeMask(x)), OUT_LABEL)
        return Expression(labeled, {}, {})
    raise TypeError(f"unsupported operand type {type(x).__name__}")


def _reindex_output(expr: Expression, union: BladeMask) -> MVLabeledTensor:
    """Pad an expression's output axis to *union*, zero-filling missing blades."""
    old_mask = expr.out_mask
    data = expr.tensor.data
    new_data = np.zeros((len(union), *data.shape[1:]), dtype=data.dtype)
    for j, bid in enumerate(old_mask.ids):
        new_data[union.index(bid)] = data[j]
    new_masks = (union, *expr.tensor.tensor.masks[1:])
    return MVLabeledTensor(MVTensor(data=new_data, masks=new_masks), expr.tensor.labels)


def _add(
    left: Any, right: Any, subtract: bool = False
) -> "Expression | AffineExpression":
    """Add/subtract two operands, merging when they share the same axis layout.

    Two tensor expressions merge into a single ``Expression`` only when they
    carry the exact same variable occurrences in the same order; otherwise the
    result is an :class:`AffineExpression` (a sum of terms).  Constants and
    differently-shaped expressions are therefore legal affine addends.
    """
    L = _to_expression(left)
    R = _to_expression(right)
    same_axes = _axis_names(L.tensor.labels) == _axis_names(R.tensor.labels)
    if (L._has_counting_axes() or R._has_counting_axes()) and not same_axes:
        raise ValueError(
            "cannot add stacked (batched) expressions with different axis "
            "layouts; fully evaluate them before addition"
        )
    if same_axes:
        union = L.out_mask.union(R.out_mask)
        Lt = _reindex_output(L, union)
        Rt = _reindex_output(R, union)
        result = Lt - Rt if subtract else Lt + Rt
        return Expression(result, dict(L.names), dict(L.masks))
    return AffineExpression([L, R._scale(-1.0) if subtract else R])


def _involution_tensor(mask: BladeMask, inv: EInv) -> MVTensor:
    """Return the diagonal sign tensor for an involution."""
    if inv == EInv.REV:
        return product_tensor_rev(mask)
    if inv == EInv.CONJ:
        return product_tensor_conj(mask)
    if inv == EInv.ID:
        return MVTensor(data=np.eye(len(mask)), masks=(mask, mask))
    raise ValueError(f"unknown involution {inv!r}")


def _apply_involution(expr: Expression, inv: EInv) -> Expression:
    """Apply an involution to an expression's output axis (axis 0)."""
    diag = np.diag(_involution_tensor(expr.out_mask, inv).data)
    shape = (-1,) + (1,) * (expr.ndim - 1)
    data = expr.tensor.data * diag.reshape(shape)
    tensor = MVTensor(data=data, masks=expr.tensor.tensor.masks)
    return Expression(
        MVLabeledTensor(tensor, expr.tensor.labels), expr.names, expr.masks
    )


def _involution(x: Any, inv: EInv) -> Expression:
    """Involution of a ``Variable`` or ``Expression``.

    ``~v`` wraps the sign tensor as a two-axis expression (output × variable);
    ``~E`` applies the sign to the expression's output axis.
    """
    if isinstance(x, Variable):
        labeled = MVLabeledTensor(
            _involution_tensor(x.mask, inv), [(OUT_LABEL, "*"), (x.label, "*")]
        )
        return Expression(labeled, {x.name: (x.label,)}, {x.name: x.mask})
    if isinstance(x, Expression):
        return _apply_involution(x, inv)
    raise TypeError(f"unsupported operand type {type(x).__name__}")


def _check_blades(value: Any, mask: BladeMask, name: str) -> None:
    """Raise if *value* has non-zero blades outside *mask*."""
    outside = [bid for bid in BladeMask(value).ids if bid not in mask]
    if outside:
        raise ValueError(f"binding for {name!r} has blades outside its mask: {outside}")


def _validate_items(items: list, name: str) -> None:
    """Type-check every item in a batched binding.

    Blade-membership is deliberately *not* checked per item: ``to_tensor(list,
    mask)`` extracts only the mask's coefficients (out-of-mask blades are
    ignored), so a per-item check would add an O(n) C++ call without changing
    the result.
    """
    for item in items:
        if not isinstance(item, (MV, int, float)):
            raise TypeError(
                f"binding for {name!r}: list item must be an MV, "
                f"got {type(item).__name__}"
            )


_BATCH_POOL = "nopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _next_batch_label(used: set) -> str:
    """Return an unused single-letter label for a batched binding."""
    for ch in _BATCH_POOL:
        if ch not in used:
            return ch
    raise RuntimeError("too many batched variables in one evaluation")
