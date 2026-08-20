# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The Expression class and the tensor-based product builder."""

from __future__ import annotations

import numpy as np

from pytanga.algebra import EInv, EProduct, MV
from pytanga.blade_mask import BladeMask
from pytanga.tensor import MVTensor, MVLabeledTensor
from pytanga.tensor._labeled import _raw_names
from pytanga.tensor.convert import from_tensor, to_tensor
from pytanga.tensor.ops import contract_labeled
from pytanga.tensor.product import (
    product_tensor,
    product_tensor_conj,
    product_tensor_rev,
)

from ._labels import OUT_LABEL, allocate_block, block_for_label
from ._variable import Variable


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

    def __init__(self, tensor, names, masks) -> None:
        self._tensor = tensor  # MVLabeledTensor
        self._names = dict(names)  # name -> occurrence labels
        self._masks = dict(masks)  # name -> BladeMask

    @property
    def tensor(self) -> MVLabeledTensor:
        """The internal reduced ``MVLabeledTensor``."""
        return self._tensor

    @property
    def names(self) -> dict:
        """A copy of the ``name -> occurrence labels`` mapping."""
        return dict(self._names)

    @property
    def masks(self) -> dict:
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
    def algebra(self):
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

    def _var_axes(self):
        """Return ``(labels, masks)`` of the variable axes, in order."""
        raw = _raw_names(self._tensor.labels)
        masks = self._tensor.tensor.masks
        return list(raw[1:]), list(masks[1:])

    def __repr__(self) -> str:
        return f"Expression(names={sorted(self._names)}, out_mask={self.out_mask})"

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def __call__(self, **bindings):
        """Evaluate the expression, binding some or all variables.

        A value may be:

        - an ``MV`` (or scalar) — contract that variable;
        - a ``list``/``tuple`` of MVs — bind a batch, adding an auto-labelled
          counting axis;
        - a ``(label, [mvs...])`` tuple — bind a batch with an explicit
          single-letter label for the counting axis.

        If variables remain unbound, a new ``Expression`` over those variables
        is returned (it may carry counting axes).  Otherwise the result is an
        ``MV`` (single values) or a nested ``list`` of ``MV`` (batched).
        """
        return self._evaluate(bindings, True)

    def _evaluate(self, bindings, check_blades: bool):
        unknown = set(bindings) - set(self._names)
        if unknown:
            raise ValueError(f"unknown variable(s): {sorted(unknown)}")

        if not bindings:
            if not self._names:
                return from_tensor(self._tensor.tensor)  # constant -> MV
            return self

        labeled = [self._tensor]
        alg = self.algebra
        used = set(_raw_names(self._tensor.labels))

        for name, value in bindings.items():
            labels = self._names[name]
            mask = self._masks[name]

            if (
                isinstance(value, tuple)
                and len(value) == 2
                and isinstance(value[0], str)
            ):
                batch = value[0]
                if not (len(batch) == 1 and batch.isascii() and batch.isalpha()):
                    raise ValueError(
                        f"counting label must be a single letter, got {batch!r}"
                    )
                if batch in used:
                    raise ValueError(f"counting label {batch!r} is already in use")
                used.add(batch)
                items = list(value[1])
                _validate_items(items, name)
                for label in labels:
                    labeled.append(
                        MVLabeledTensor(
                            to_tensor(items, mask=mask), label + batch + "_"
                        )
                    )
                continue

            if isinstance(value, (list, tuple)):
                batch = _next_batch_label(used)
                used.add(batch)
                items = list(value)
                _validate_items(items, name)
                for label in labels:
                    labeled.append(
                        MVLabeledTensor(
                            to_tensor(items, mask=mask), label + batch + "_"
                        )
                    )
                continue

            if isinstance(value, (int, float)):
                value = alg.multivector({0: float(value)})
            if not isinstance(value, MV):
                raise TypeError(
                    f"binding for {name!r} must be an MV, got {type(value).__name__}"
                )
            if check_blades:
                _check_blades(value, mask, name)
            for label in labels:
                labeled.append(MVLabeledTensor(to_tensor(value, mask=mask), label))

        result = contract_labeled(*labeled)

        remaining = set(self._names) - set(bindings)
        if remaining:
            new_names = {n: self._names[n] for n in remaining}
            new_masks = {n: self._masks[n] for n in remaining}
            return Expression(result, new_names, new_masks)

        return from_tensor(result.tensor)

    # ------------------------------------------------------------------
    # Products — chain into the tensor builder
    # ------------------------------------------------------------------

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(self, other, EProduct.GP)

    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(other, self, EProduct.GP)

    def __or__(self, other):
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(self, other, EProduct.IP)

    def __ror__(self, other):
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(other, self, EProduct.IP)

    def __xor__(self, other):
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(self, other, EProduct.OP)

    def __rxor__(self, other):
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _product(other, self, EProduct.OP)

    def __neg__(self):
        return self._scale(-1.0)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self._scale(1.0 / float(other))
        return NotImplemented

    def _scale(self, scalar: float) -> "Expression":
        return Expression(self._tensor.mul_scalar(scalar), self._names, self._masks)

    # ------------------------------------------------------------------
    # Addition / subtraction (broadcast with output-mask unification)
    # ------------------------------------------------------------------

    def __add__(self, other):
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _add(self, other)

    def __radd__(self, other):
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _add(other, self)

    def __sub__(self, other):
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented
        return _add(self, other, subtract=True)

    def __rsub__(self, other):
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

    def __invert__(self):
        return _apply_involution(self, EInv.REV)

    def conj(self):
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
        labeled = MVLabeledTensor(result, OUT_LABEL + new_label)
        return Expression(labeled, {var_name: (new_label,)}, {var_name: out_mask})


class AffineExpression:
    """A sum of :class:`Expression` terms that could not be merged into one tensor.

    Holds a flat ``list`` of ``Expression`` terms (each a multilinear form in its
    own variables).  ``+``/``-`` concatenate term lists, ``*`` distributes over
    the terms, and ``__call__`` evaluates each term and sums the results.
    """

    __slots__ = ("_terms",)

    def __init__(self, terms) -> None:
        self._terms = list(terms)

    @property
    def terms(self) -> list:
        """A copy of the term list (each an ``Expression``)."""
        return list(self._terms)

    @property
    def names(self) -> set:
        """The set of variable names appearing in any term."""
        result: set = set()
        for term in self._terms:
            result.update(term.names)
        return result

    @property
    def masks(self) -> dict:
        """Union of the per-variable masks (``name -> BladeMask``)."""
        result: dict = {}
        for term in self._terms:
            result.update(term.masks)
        return result

    def _union_masks(self) -> dict:
        """Union of each variable's masks across all terms."""
        result: dict = {}
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
    def algebra(self):
        """The algebra this affine expression belongs to."""
        return self.out_mask.algebra

    def __repr__(self) -> str:
        return f"AffineExpression(terms={len(self._terms)})"

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def __call__(self, **bindings):
        """Evaluate the sum, binding some or all variables.

        A value may be an ``MV`` (or scalar) or a ``list``/``tuple`` of MVs
        (batch), exactly as for :meth:`Expression.__call__`.  Fully bound single
        values yield an ``MV``; fully bound batches yield a ``list`` of ``MV``; a
        remaining variable yields an ``AffineExpression`` (or, for partial
        batches, a ``list`` of ``AffineExpression``).
        """
        unknown = set(bindings) - self.names
        if unknown:
            raise ValueError(f"unknown variable(s): {sorted(unknown)}")

        if not bindings:
            return self

        singles, batches = _split_bindings(bindings)
        union = self._union_masks()
        for name, value in singles.items():
            if isinstance(value, (int, float)):
                value = self.algebra.multivector({0: float(value)})
            _check_blades(value, union[name], name)

        if not batches:
            return self._call_singles(singles)

        if self.names <= set(singles) | set(batches) and len(batches) == 1:
            return self._call_full_batch(singles, batches)
        return self._call_batch_loop(singles, batches)

    def _call_singles(self, singles):
        results = []
        for term in self._terms:
            sub = {k: v for k, v in singles.items() if k in term.names}
            results.append(term._evaluate(sub, False))

        if all(isinstance(r, MV) for r in results):
            total = results[0]
            for r in results[1:]:
                total = total + r
            return total

        terms = [_to_expression(r) if isinstance(r, MV) else r for r in results]
        return AffineExpression(terms)

    def _call_full_batch(self, singles, batches):
        bname = next(iter(batches))
        items = _items_of(batches[bname])
        n = len(items)
        per_term = []
        for term in self._terms:
            sub = {k: v for k, v in singles.items() if k in term.names}
            if bname in term.names:
                sub[bname] = items
            per_term.append(term._evaluate(sub, False))

        out = []
        for i in range(n):
            total = None
            for r in per_term:
                val = r[i] if isinstance(r, list) else r
                total = val if total is None else total + val
            out.append(total)
        return out

    def _call_batch_loop(self, singles, batches):
        bname = next(iter(batches))
        items = _items_of(batches[bname])
        rest = {k: v for k, v in batches.items() if k != bname}
        out = []
        for item in items:
            new_singles = dict(singles)
            new_singles[bname] = item
            out.append(self.__call__(**new_singles, **rest))
        return out

    # ------------------------------------------------------------------
    # Addition / subtraction — concatenate term lists
    # ------------------------------------------------------------------

    def __add__(self, other):
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _affine_add(self, other, subtract=False)

    def __radd__(self, other):
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _affine_add(other, self, subtract=False)

    def __sub__(self, other):
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _affine_add(self, other, subtract=True)

    def __rsub__(self, other):
        if isinstance(other, (int, float)) and other == 0:
            return -self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _affine_add(other, self, subtract=True)

    def __neg__(self):
        return AffineExpression([-t for t in self._terms])

    # ------------------------------------------------------------------
    # Products — distribute over the terms
    # ------------------------------------------------------------------

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        if isinstance(other, AffineExpression):
            return AffineExpression(
                [_product(a, b, EProduct.GP) for a in self._terms for b in other._terms]
            )
        return AffineExpression([_product(t, other, EProduct.GP) for t in self._terms])

    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        return AffineExpression([_product(other, t, EProduct.GP) for t in self._terms])

    def __or__(self, other):
        if isinstance(other, AffineExpression):
            return AffineExpression(
                [_product(a, b, EProduct.IP) for a in self._terms for b in other._terms]
            )
        return AffineExpression([_product(t, other, EProduct.IP) for t in self._terms])

    def __ror__(self, other):
        return AffineExpression([_product(other, t, EProduct.IP) for t in self._terms])

    def __xor__(self, other):
        if isinstance(other, AffineExpression):
            return AffineExpression(
                [_product(a, b, EProduct.OP) for a in self._terms for b in other._terms]
            )
        return AffineExpression([_product(t, other, EProduct.OP) for t in self._terms])

    def __rxor__(self, other):
        return AffineExpression([_product(other, t, EProduct.OP) for t in self._terms])

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self._scale(1.0 / float(other))
        return NotImplemented

    def _scale(self, scalar: float):
        return AffineExpression([t._scale(scalar) for t in self._terms])

    # ------------------------------------------------------------------
    # Involutions / inverse
    # ------------------------------------------------------------------

    def __invert__(self):
        return AffineExpression([~t for t in self._terms])

    def conj(self):
        return AffineExpression([t.conj() for t in self._terms])

    def inv(self, var_name: str):
        raise ValueError(
            "inv() requires a single linear Expression, not an AffineExpression"
        )


def _items_of(value):
    """Return the list of MVs/scalars for a (possibly named) batch binding."""
    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
        return list(value[1])
    return list(value)


def _split_bindings(bindings):
    """Partition bindings into single-value and batch (list/tuple) bindings."""
    singles = {}
    batches = {}
    for name, value in bindings.items():
        if isinstance(value, (list, tuple)):
            batches[name] = value
        else:
            singles[name] = value
    return singles, batches


def _coerce_addend(x):
    """Return the term list for an addend."""
    if isinstance(x, AffineExpression):
        return list(x.terms)
    if isinstance(x, (MV, Expression)):
        return [_to_expression(x)]
    raise TypeError(f"unsupported operand type {type(x).__name__}")


def _affine_add(left, right, subtract: bool = False):
    """Concatenate two addends into an ``AffineExpression``."""
    lterms = _coerce_addend(left)
    rterms = _coerce_addend(right)
    if subtract:
        rterms = [-t for t in rterms]
    return AffineExpression(lterms + rterms)


# ---------------------------------------------------------------------------
# Operand resolution
# ---------------------------------------------------------------------------


def _operand(x):
    """Classify an operand as ``('var'|'const'|'expr', value)``."""
    if isinstance(x, Variable):
        return "var", x
    if isinstance(x, Expression):
        return "expr", x
    if isinstance(x, MV):
        return "const", x
    raise TypeError(f"unsupported operand type {type(x).__name__}")


def _value_mask(kind, val) -> BladeMask:
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


def _product(left, right, product, a_inv=EInv.ID, b_inv=EInv.ID) -> Expression:
    """Build the reduced expression for ``left ∘ right``.

    Builds the 3-D product tensor and contracts every constant/expression
    operand, leaving one axis per remaining variable plus the output axis.
    """
    Lkind, Lval = _operand(left)
    Rkind, Rval = _operand(right)

    for kind, val in ((Lkind, Lval), (Rkind, Rval)):
        if kind == "expr" and val._has_counting_axes():
            raise ValueError(
                "cannot compose a stacked (batched) expression; "
                "fully evaluate it before further products"
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

    var_labels: list[str] = []
    var_masks: list[BladeMask] = []
    names: dict[str, tuple[str, ...]] = {}
    masks: dict[str, BladeMask] = {}

    def add(kind, val, value_axis) -> None:
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
            var_labels.append(lab)
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
            raw = _raw_names(val.tensor.labels)
            e_masks = val.tensor.tensor.masks
            sub = [value_axis]
            for i in range(1, val.ndim):
                lab = raw[i]
                var_labels.append(rename.get(lab, lab))
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

    raw_labels = OUT_LABEL + "".join(var_labels)
    labels = "".join(ch + "*" for ch in raw_labels)
    result = MVTensor(data=result_data, masks=(m_C, *var_masks))
    labeled = MVLabeledTensor(result, labels)
    return Expression(labeled, names, masks)


def _to_expression(x) -> Expression:
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


def _add(left, right, subtract: bool = False):
    """Add/subtract two operands, merging when they share the same axis layout.

    Two tensor expressions merge into a single ``Expression`` only when they
    carry the exact same variable occurrences in the same order; otherwise the
    result is an :class:`AffineExpression` (a sum of terms).  Constants and
    differently-shaped expressions are therefore legal affine addends.
    """
    L = _to_expression(left)
    R = _to_expression(right)
    if L._has_counting_axes() or R._has_counting_axes():
        raise ValueError(
            "cannot add a stacked (batched) expression; "
            "fully evaluate it before addition"
        )
    if _raw_names(L.tensor.labels) == _raw_names(R.tensor.labels):
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


def _involution(x, inv: EInv) -> Expression:
    """Involution of a ``Variable`` or ``Expression``.

    ``~v`` wraps the sign tensor as a two-axis expression (output × variable);
    ``~E`` applies the sign to the expression's output axis.
    """
    if isinstance(x, Variable):
        labeled = MVLabeledTensor(_involution_tensor(x.mask, inv), OUT_LABEL + x.label)
        return Expression(labeled, {x.name: (x.label,)}, {x.name: x.mask})
    if isinstance(x, Expression):
        return _apply_involution(x, inv)
    raise TypeError(f"unsupported operand type {type(x).__name__}")


def _check_blades(value, mask: BladeMask, name: str) -> None:
    """Raise if *value* has non-zero blades outside *mask*."""
    outside = [bid for bid in BladeMask(value).ids if bid not in mask]
    if outside:
        raise ValueError(f"binding for {name!r} has blades outside its mask: {outside}")


def _validate_items(items, name: str) -> None:
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
