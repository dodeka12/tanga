# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The Expression class and the tensor-based product builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, cast, overload

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
    product_tensor_rc,
    product_tensor_rev,
)

from ._data_array import DataArray
from ._labels import OUT_LABEL, allocate_block, block_for_label
from ._variable import Variable

if TYPE_CHECKING:
    from pytanga.algebra import Algebra


@dataclass(frozen=True, slots=True)
class _CompiledPlan:
    """Precomputed evaluation plan for a fully-bound, MV/scalar ``Expression``.

    Captures everything that is invariant between repeated calls: the base
    tensor, the integer einsum layout, the variable→occurrence-axis map, the
    variable/output masks, the fixed binding order, and a precomputed greedy
    contraction path.
    """

    base: np.ndarray
    base_axes: list[int]
    var_axes: dict[str, list[int]]
    out_axes: list[int]
    masks: dict[str, BladeMask]
    out_mask: BladeMask
    order: tuple[str, ...]
    path: Any


def _run_compiled_plan(
    plan: _CompiledPlan, alg: "Algebra", values: dict[str, np.ndarray]
) -> np.ndarray:
    """Contract *plan* against pre-extracted per-variable coefficient arrays."""
    args: list[Any] = [plan.base, plan.base_axes]
    for name in plan.order:
        coeffs = values[name]
        for axis in plan.var_axes[name]:
            args.append(coeffs)
            args.append([axis])
    args.append(plan.out_axes)
    return np.einsum(*args, optimize=plan.path)


class Expression:
    """A reduced tensor expression over named variables.

    Holds an ``MVLabeledTensor`` whose axes are:

    - axis 0: the output (result multivector) axis, labelled ``OUT_LABEL``;
    - one axis per variable occurrence, labelled by that occurrence's letter;
    - optional counting (``None``-mask) axes for batched partial evaluations.

    The result is a multilinear form in each variable: a variable may appear up
    to ``MAX_DEGREE`` times per term (e.g. ``v * v``).
    """

    __slots__ = ("_tensor", "_names", "_masks", "_compiled")

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
            self._compiled: _CompiledPlan | None = None
            return
        self._tensor = tensor  # MVLabeledTensor
        self._names = dict(cast("dict[str, tuple[int, ...]]", names))
        self._masks = dict(cast("dict[str, BladeMask]", masks))
        self._compiled = None

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
        return cast("BladeMask", self._tensor.tensor.masks[0])

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

    def _var_axes(self) -> tuple[list[Any], list[Any]]:
        """Return ``(labels, masks)`` of the variable axes, in order."""
        raw = _axis_names(self._tensor.labels)
        masks = self._tensor.tensor.masks
        return list(raw[1:]), list(masks[1:])

    def _counting_axes(self) -> dict[str | int, int]:
        """Return the counting-axis names → lengths (axes past the output whose
        mask is ``None``)."""
        raw = _axis_names(self._tensor.labels)
        masks = self._tensor.tensor.masks
        return {
            raw[i]: self._tensor.tensor.shape[i]
            for i in range(1, len(raw))
            if masks[i] is None
        }

    def __repr__(self) -> str:
        return f"Expression(names={sorted(self._names)}, out_mask={self.out_mask})"

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def __call__(self, **bindings: Any) -> "MV | Expression | list[Any]":
        """Evaluate the expression, binding some or all variables.

        A variable value may be:

        - a single ``MV`` (or scalar) — contract that variable;
        - a ``DataArray`` — contract its blade axis (matched to the variable
          mask) against every occurrence of the variable, keeping its counting
          axes element-wise;
        - an ``Expression`` — substitute that variable with the sub-expression
          (composition): its output mask must equal the variable's mask and it
          must not carry counting axes; its free variables become the result's
          new variables.

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

    def compile(self) -> Callable[..., MV]:
        """Return a fast compiled evaluator for fully-bound ``MV``/scalar values.

        ``compiled = expr.compile()``; then ``compiled(V1=x, V2=y) ==
        expr(V1=x, V2=y)`` for any concrete ``MV``/scalar binding, but the
        per-call cost is reduced to the numeric contraction only (the einsum
        layout, masks, and contraction path are computed once).

        The callable requires **every** free variable to be bound to an
        ``MV``/``int``/``float`` (a ``DataArray`` or ``Expression`` binding
        raises ``TypeError``), and validates that each value's blades lie within
        the variable's mask (raising ``ValueError`` otherwise, exactly like
        ``__call__``).  A constant expression returns a zero-argument callable.
        """
        if not self._names:
            const = from_tensor(self._tensor.tensor)

            def compiled() -> MV:
                return cast("MV", const)

            return compiled
        return self._compile(True)

    def _build_plan(self) -> _CompiledPlan:
        """Build the cached ``_CompiledPlan`` for this expression's structure."""
        raw = _axis_names(self._tensor.labels)
        name_to_int: dict[str | int, int] = {}
        for name in raw:
            if name not in name_to_int:
                name_to_int[name] = len(name_to_int)

        base_axes = [name_to_int[name] for name in raw]
        out_axes = [name_to_int[raw[0]]]
        var_axes = {
            name: [name_to_int[occ] for occ in occs]
            for name, occs in self._names.items()
        }
        order = tuple(self._names)
        out_mask = self.out_mask
        base = np.asarray(self._tensor.tensor.data, dtype=np.float64)

        # Precompute a greedy contraction path once, using placeholder arrays.
        path_args: list[Any] = [base, base_axes]
        for name in order:
            dummy = np.empty(len(self._masks[name]), dtype=np.float64)
            for axis in var_axes[name]:
                path_args.append(dummy)
                path_args.append([axis])
        path_args.append(out_axes)
        path = np.einsum_path(*path_args, optimize="greedy")[0]

        return _CompiledPlan(
            base=base,
            base_axes=base_axes,
            var_axes=var_axes,
            out_axes=out_axes,
            masks=dict(self._masks),
            out_mask=out_mask,
            order=order,
            path=path,
        )

    def _get_plan(self) -> _CompiledPlan:
        """Return the cached compiled plan, building it on first use."""
        if self._compiled is None:
            self._compiled = self._build_plan()
        return self._compiled

    def _compile(self, check_blades: bool) -> Callable[..., MV]:
        """Return the compiled evaluator closure over the cached plan."""
        plan = self._get_plan()
        alg = plan.out_mask.algebra

        def compiled(**bindings: Any) -> MV:
            missing = [name for name in plan.order if name not in bindings]
            extra = [name for name in bindings if name not in plan.masks]
            if missing or extra:
                raise ValueError(
                    "compiled evaluation requires exactly the free variable(s) "
                    f"{sorted(plan.order)}; got missing={sorted(missing)}, "
                    f"extra={sorted(extra)}"
                )

            values: dict[str, np.ndarray] = {}
            for name in plan.order:
                value = bindings[name]
                mask = plan.masks[name]
                if isinstance(value, (int, float)):
                    value = alg.multivector({0: float(value)})
                if not isinstance(value, MV):
                    raise TypeError(
                        f"binding for {name!r} must be a single MV or scalar, "
                        f"got {type(value).__name__}"
                    )
                if check_blades:
                    outside = mask.ids_outside(value)
                    if outside:
                        raise ValueError(
                            f"binding for {name!r} has blades outside its mask: "
                            f"{outside}"
                        )
                values[name] = np.asarray(
                    alg._mod.to_matrix(value._impl, mask.ids), dtype=np.float64
                ).ravel()

            result = _run_compiled_plan(plan, alg, values)
            impl = alg._mod.from_matrix(
                np.asarray(result, dtype=np.float64).reshape(-1, 1),
                plan.out_mask.ids,
            )
            return MV(impl, alg)

        return compiled

    def _evaluate(
        self,
        bindings: dict[str, Any],
        check_blades: bool,
        extra_counting: dict[str | int, int] | None = None,
    ) -> "MV | Expression | list[Any]":
        raw = _axis_names(self._tensor.labels)
        masks = self._tensor.tensor.masks

        counting = {}
        for i in range(1, len(raw)):
            if masks[i] is None:
                counting[raw[i]] = i

        extra = extra_counting or {}
        unknown = set(bindings) - set(self._names) - set(counting) - set(extra)
        if unknown:
            raise ValueError(f"unknown variable(s): {sorted(unknown)}")

        if not bindings:
            if not self._names:
                return from_tensor(self._tensor.tensor)  # constant -> MV
            return self

        var_bindings = {k: v for k, v in bindings.items() if k in self._names}
        count_bindings = {k: v for k, v in bindings.items() if k in counting}

        # Fast path: every variable bound to a concrete MV/scalar with no
        # counting-axis reduction — skip the general labelled contraction.
        if (
            not count_bindings
            and self._names
            and not self._has_counting_axes()
            and set(var_bindings) == set(self._names)
            and all(isinstance(v, (MV, int, float)) for v in var_bindings.values())
        ):
            return self._compile(check_blades)(**var_bindings)

        # Counting axes known to the surrounding reduction but absent from this
        # term are broadcast as constants (sum-reduction only).
        broadcast_scale = 1.0
        for name, value in bindings.items():
            if name not in extra or name in counting:
                continue
            if _count_binding_mode(name, value) != "*":
                raise ValueError(
                    f"broadcasting counting axis {name!r} on a term that does not "
                    "carry it is only supported for sum reduction ('*')"
                )
            if isinstance(value, DataArray):
                raise ValueError(
                    f"broadcasting counting axis {name!r} requires a raw 1-D "
                    "weight array, not a DataArray"
                )
            arr = np.asarray(value)
            if arr.ndim != 1:
                raise ValueError(
                    f"broadcasting counting axis {name!r} requires a raw 1-D "
                    "weight array"
                )
            broadcast_scale *= float(np.sum(arr))

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

        extra_names: dict[str, tuple[int, ...]] = {}
        extra_masks: dict[str, BladeMask] = {}

        for name, value in var_bindings.items():
            labels = self._names[name]
            mask = self._masks[name]

            if isinstance(value, DataArray):
                labeled.extend(
                    _variable_dataarray_binding_tensors(value, mask, labels, used)
                )
                continue

            if isinstance(value, Expression):
                tensors, fnames, fmasks = _expression_binding_tensors(
                    value, mask, labels, name
                )
                labeled.extend(tensors)
                for fname in fnames:
                    if fname in extra_names:
                        raise ValueError(
                            "multiple bound sub-expressions introduce the same "
                            f"free variable {fname!r}"
                        )
                extra_names.update(fnames)
                extra_masks.update(fmasks)
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
        collision = (remaining | set(var_bindings)) & set(extra_names)
        if collision:
            raise ValueError(
                "bound sub-expression(s) introduce variable name(s) "
                f"{sorted(collision)} that are already present in the host "
                "expression or being bound in the same call"
            )

        if remaining or extra_names:
            new_names = {n: self._names[n] for n in remaining}
            new_masks = {n: self._masks[n] for n in remaining}
            new_names.update(extra_names)
            new_masks.update(extra_masks)
            expr = Expression(result, new_names, new_masks)
            return (
                expr
                if broadcast_scale == 1.0
                else _scale_eval_result(expr, broadcast_scale)
            )

        out = from_tensor(result.tensor)
        return (
            out if broadcast_scale == 1.0 else _scale_eval_result(out, broadcast_scale)
        )

    def bind(self, **bindings: Any) -> "Expression":
        """Bind variables to values, or substitute them with other ``Variable``s.

        A binding value that is a :class:`Variable` substitutes that variable
        (relabeling it onto the new variable's block) instead of evaluating it;
        every other value binds as before.  A binding value that is an
        :class:`Expression` composes it into this expression: the bound variable
        is replaced by the sub-expression's tensor (its output mask must equal
        the variable's mask, and it must not carry counting axes), and the
        sub-expression's free variables join the result.

        Returns a new :class:`Expression` over the remaining variables.  Raises
        :class:`ValueError` if the binding would fully collapse the expression to
        a plain ``MV`` or a batched ``list`` (use :meth:`evaluate` or
        :meth:`__call__` for that instead), or if a bound sub-expression
        introduces a variable name that collides with the host expression.
        """
        subs = {k: v for k, v in bindings.items() if isinstance(v, Variable)}
        if subs:
            unknown = set(subs) - set(self._names)
            if unknown:
                raise ValueError(f"unknown variable(s): {sorted(unknown)}")
            expr = self._substitute(subs)
            values = {
                k: v for k, v in bindings.items() if not isinstance(v, Variable)
            }
            if not values:
                return expr
        else:
            expr = self
            values = bindings

        result = expr._evaluate(values, True)
        if not isinstance(result, Expression):
            raise ValueError(
                "bind() expected a partially-evaluated Expression, but the "
                "binding fully collapsed it. Use evaluate() or __call__()."
            )
        return result

    def evaluate(self, **bindings: Any) -> MV:
        """Evaluate all variables to a concrete :class:`MV`.

        Raises :class:`ValueError` if the result is still an ``Expression``
        (variables/axes unbound) or a batched ``list``.
        """
        result = self._evaluate(bindings, True)
        if not isinstance(result, MV):
            raise ValueError(
                "evaluate() expected a fully-bound MV, but the binding left "
                "variables/axes unbound (Expression) or produced a batched "
                "result (list)."
            )
        return result

    def _substitute(self, mapping: dict[str, Variable]) -> "Expression":
        """Re-key named variables onto target ``Variable``s (internal).

        ``mapping`` maps variable names to target ``Variable`` instances.  Names
        absent from this expression are skipped.  Each mapped variable's
        occurrence labels are moved onto the target's label block — merging
        several names that map to one target — so independently-created
        variables unify into one.  The tensor data is unchanged; the target mask
        must equal the source mask.
        """
        sources: list[tuple[str, Variable]] = []
        for name, target in mapping.items():
            if name not in self._names:
                continue
            if target.mask != self._masks[name]:
                raise ValueError(
                    f"cannot substitute variable {name!r} with "
                    f"{target.name!r}: blade masks differ"
                )
            sources.append((name, target))

        if not sources:
            return self

        source_names = {n for n, _ in sources}
        target_names = {t.name for _, t in sources}
        clash = target_names & {n for n in self._names if n not in source_names}
        if clash:
            raise ValueError(
                f"cannot substitute into {sorted(clash)[0]!r}: that name is "
                "already a distinct variable in the expression (map it too, or "
                "rename it first)"
            )

        rename: dict[int, int] = {}
        final_names: dict[str, tuple[int, ...]] = {
            n: lbls for n, lbls in self._names.items() if n not in source_names
        }
        final_masks: dict[str, BladeMask] = {
            n: m for n, m in self._masks.items() if n not in source_names
        }

        by_target: dict[int, tuple[Variable, list[str]]] = {}
        for name, target in sources:
            by_target.setdefault(id(target), (target, []))[1].append(name)

        for target, names in by_target.values():
            block = target.labels
            merged: list[int] = []
            for name in names:
                old_labels = self._names[name]
                if len(merged) + len(old_labels) > len(block):
                    raise ValueError(
                        f"variable {target.name!r} would appear more than "
                        f"{len(block)} times in a product term"
                    )
                new_labels = block[len(merged) : len(merged) + len(old_labels)]
                for old, new in zip(old_labels, new_labels):
                    rename[old] = new
                merged.extend(new_labels)
            final_names[target.name] = tuple(merged)
            final_masks[target.name] = target.mask

        new_labels = []
        for ax in self._tensor.labels:
            name = ax.name
            if isinstance(name, int):
                name = rename.get(name, name)
            new_labels.append((name, ax.mode))
        labeled = MVLabeledTensor(self._tensor.tensor, new_labels)
        return Expression(labeled, final_names, final_masks)

    def rename_var(self, old: "str | Variable", new_name: str) -> "Expression":
        """Rename a variable, keeping its label block (name-only).

        ``old`` is the variable's current name (or a ``Variable`` whose ``.name``
        is used).  ``new_name`` must not collide with a different existing name.
        The label block is unchanged, so the result still merges with
        expressions built from the same original ``Variable``.
        """
        name = old.name if isinstance(old, Variable) else str(old)
        if name not in self._names:
            raise ValueError(f"cannot rename unknown variable {name!r}")
        new_name = str(new_name)
        if new_name != name and new_name in self._names:
            raise ValueError(
                f"cannot rename {name!r} to {new_name!r}: name already in use"
            )
        new_names = dict(self._names)
        new_masks = dict(self._masks)
        new_names[new_name] = new_names.pop(name)
        new_masks[new_name] = new_masks.pop(name)
        return Expression(self._tensor, new_names, new_masks)

    # ------------------------------------------------------------------
    # Products — chain into the tensor builder
    # ------------------------------------------------------------------

    def __mul__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression":
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _product(self, other, EProduct.GP)

    def __rmul__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression":
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _product(other, self, EProduct.GP)

    def __or__(self, other: "MV | Variable | Expression") -> "Expression":
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _product(self, other, EProduct.IP)

    def __ror__(self, other: "MV | Variable | Expression") -> "Expression":
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _product(other, self, EProduct.IP)

    def __xor__(self, other: "MV | Variable | Expression") -> "Expression":
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _product(self, other, EProduct.OP)

    def __rxor__(self, other: "MV | Variable | Expression") -> "Expression":
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _product(other, self, EProduct.OP)

    def __neg__(self) -> "Expression":
        return self._scale(-1.0)

    def __truediv__(self, other: Any) -> "Expression":
        if isinstance(other, (int, float)):
            return self._scale(1.0 / float(other))
        return NotImplemented  # type: ignore[return-value]

    def _scale(self, scalar: float) -> "Expression":
        return Expression(self._tensor.mul_scalar(scalar), self._names, self._masks)

    # ------------------------------------------------------------------
    # Addition / subtraction (broadcast with output-mask unification)
    # ------------------------------------------------------------------

    def __add__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression":
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _add(self, other)

    def __radd__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression":
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _add(other, self)

    def __sub__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression":
        if isinstance(other, (int, float)) and other == 0:
            return self
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _add(self, other, subtract=True)

    def __rsub__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression":
        if isinstance(other, (int, float)) and other == 0:
            return self._scale(-1.0)
        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        if not isinstance(other, (MV, Variable, Expression)):
            return NotImplemented  # type: ignore[return-value]
        return _add(other, self, subtract=True)

    # ------------------------------------------------------------------
    # Involutions
    # ------------------------------------------------------------------

    def __invert__(self) -> "Expression":
        return _apply_involution(self, EInv.REV)

    def conj(self) -> "Expression":
        return _apply_involution(self, EInv.CONJ)

    def project_onto(self, other: "MV | BladeMask") -> "Expression":
        """Restrict self to a blade set, keeping only self's components.

        - ``MV`` — retain self's output blades that are non-zero in *other*.
        - ``BladeMask`` — retain self's output blades whose id is exactly in
          ``other.ids``.

        The result's output mask is the corresponding subspace; variable axes
        and occurrences are unchanged.  A disjoint projection collapses to a
        zero constant expression.
        """
        if isinstance(other, MV):
            target = BladeMask(other)
        elif isinstance(other, BladeMask):
            target = other
        else:
            raise TypeError(
                f"project_onto expects MV or BladeMask, got {type(other).__name__}"
            )
        if target.algebra is not self.algebra:
            raise ValueError("project_onto: blade set belongs to a different algebra")
        return _restrict_output(self, target)

    # ------------------------------------------------------------------
    # Named GA product methods
    # ------------------------------------------------------------------

    def gp(self, other: Any) -> "Expression | AffineExpression":
        """Geometric product ``self * other``."""
        return cast("Expression | AffineExpression", gp(self, other))

    def ip(self, other: Any) -> "Expression | AffineExpression":
        """Inner product ``self | other``."""
        return cast("Expression | AffineExpression", ip(self, other))

    def op(self, other: Any) -> "Expression | AffineExpression":
        """Outer (wedge) product ``self ^ other``."""
        return cast("Expression | AffineExpression", op(self, other))

    def vp(self, b: Any) -> "Expression | AffineExpression":
        """Versor product ``self * b * ~self``."""
        return cast("Expression | AffineExpression", vp(self, b))

    def nvp(self, b: Any) -> "Expression | AffineExpression":
        """Normalized versor product ``self * b * inverse(self)``."""
        return cast("Expression | AffineExpression", nvp(self, b))

    def sp(self, other: Any) -> "ScalarExpression":
        """Scalar product: the scalar part of ``self * other``."""
        return cast("ScalarExpression", sp(self, other))

    def cp(self, other: Any) -> "Expression | AffineExpression":
        """Commutator: ``(self * other - other * self) / 2``."""
        return cast("Expression | AffineExpression", cp(self, other))

    def acp(self, other: Any) -> "Expression | AffineExpression":
        """Anti-commutator: ``(self * other + other * self) / 2``."""
        return cast("Expression | AffineExpression", acp(self, other))

    def rc(self, other: Any) -> "Expression | AffineExpression":
        """Right contraction ``self ⌊ other``."""
        return cast("Expression | AffineExpression", rc(self, other))

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
        var_mask = cast("BladeMask", self._tensor.tensor.masks[1])
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

    def get_tensor(self) -> MVTensor:
        """Return the raw expression tensor as an ``MVTensor``.

        Axes are labelled by the raw ``BladeMask``s (the output axis, one axis
        per variable occurrence, plus optional ``None`` counting axes).  To
        recombine the axes into named bases, call :meth:`MVTensor.get_array`.
        """
        return self._tensor.tensor

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
        return cast("MV", from_tensor(result))

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
            cast(
                "MV",
                from_tensor(_MVTensor(data=vec.astype(np.float64), masks=(var_mask,))),
            )
            for vec in vt
        ]
        return cast("list[float]", s.tolist()), mvs


class AffineExpression:
    """A sum of :class:`Expression` terms that could not be merged into one tensor.

    Holds a flat ``list`` of ``Expression`` terms (each a multilinear form in its
    own variables).  ``+``/``-`` concatenate term lists, ``*`` distributes over
    the terms, and ``__call__`` evaluates each term and sums the results.
    """

    __slots__ = ("_terms", "_union_cache", "_out_mask_cache", "_counting_cache")

    def __init__(self, terms: "list[Expression]") -> None:
        self._terms = list(terms)
        self._union_cache: dict[str, BladeMask] | None = None
        self._out_mask_cache: BladeMask | None = None
        self._counting_cache: dict[str | int, int] | None = None

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
        """Union of each variable's masks across all terms (cached)."""
        if self._union_cache is not None:
            return self._union_cache
        result: dict[str, BladeMask] = {}
        for term in self._terms:
            for name, mask in term.masks.items():
                if name in result:
                    result[name] = result[name].union(mask)
                else:
                    result[name] = mask
        self._union_cache = result
        return result

    def _counting_axes_union(self) -> dict[str | int, int]:
        """Union of each term's counting axes, with a length-consistency check."""
        if self._counting_cache is not None:
            return self._counting_cache
        result: dict[str | int, int] = {}
        for term in self._terms:
            for name, length in term._counting_axes().items():
                if name in result and result[name] != length:
                    raise ValueError(
                        f"counting axis {name!r} has inconsistent lengths across terms"
                    )
                result[name] = length
        self._counting_cache = result
        return result

    def _has_counting_axes(self) -> bool:
        """True if any term carries a batch (``None``-mask) axis."""
        return any(t._has_counting_axes() for t in self._terms)

    @property
    def out_mask(self) -> BladeMask:
        """The union of the terms' output blade masks (cached)."""
        if self._out_mask_cache is not None:
            return self._out_mask_cache
        result = self._terms[0].out_mask
        for term in self._terms[1:]:
            result = result.union(term.out_mask)
        self._out_mask_cache = result
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

    def __call__(self, **bindings: Any) -> "MV | AffineExpression | list[Any]":
        """Evaluate the sum, binding some or all variables.

        Values are a single ``MV``/scalar, a ``DataArray``, or an ``Expression``
        (composition — see :meth:`Expression.__call__`).  Fully bound single
        values yield an ``MV``; fully bound ``DataArray`` bindings yield a
        (nested) ``list``; a remaining variable yields an ``AffineExpression``
        (or a list of them).
        """
        counting = self._counting_axes_union()
        unknown = set(bindings) - self.names - set(counting)
        if unknown:
            raise ValueError(f"unknown variable(s): {sorted(unknown)}")

        if not bindings:
            return self

        union = self._union_masks()
        var_bindings = {k: v for k, v in bindings.items() if k in self.names}
        count_bindings = {k: v for k, v in bindings.items() if k in counting}
        for name, value in var_bindings.items():
            if isinstance(value, (int, float)):
                var_bindings[name] = self.algebra.multivector({0: float(value)})
            if isinstance(value, MV):
                _check_blades(value, union[name], name)

        results = []
        for term in self._terms:
            sub = {k: v for k, v in var_bindings.items() if k in term.names}
            sub.update(count_bindings)
            results.append(term._evaluate(sub, False, extra_counting=counting))

        return _combine_terms(results)

    def compile(self) -> Callable[..., MV]:
        """Return a fast compiled evaluator summing each term's compiled plan.

        ``compiled = aff.compile()``; then ``compiled(V1=x, V2=y) ==
        aff(V1=x, V2=y)`` for concrete ``MV``/scalar bindings.  Every free
        variable must be bound (a ``DataArray``/``Expression`` binding raises
        ``TypeError``).  Values are validated against the union mask once, then
        each term contracts over its own mask and the coefficient vectors are
        summed into the union output mask.
        """
        names = set(self.names)
        union = self._union_masks()
        out_union = self.out_mask
        alg = out_union.algebra
        term_plans = [(term._get_plan(), term.out_mask) for term in self._terms]

        def compiled(**bindings: Any) -> MV:
            missing = [name for name in names if name not in bindings]
            extra = [name for name in bindings if name not in names]
            if missing or extra:
                raise ValueError(
                    "compiled evaluation requires exactly the free variable(s) "
                    f"{sorted(names)}; got missing={sorted(missing)}, "
                    f"extra={sorted(extra)}"
                )

            coerced: dict[str, MV] = {}
            for name, value in bindings.items():
                if isinstance(value, (int, float)):
                    value = alg.multivector({0: float(value)})
                if not isinstance(value, MV):
                    raise TypeError(
                        f"binding for {name!r} must be a single MV or scalar, "
                        f"got {type(value).__name__}"
                    )
                outside = union[name].ids_outside(value)
                if outside:
                    raise ValueError(
                        f"binding for {name!r} has blades outside its mask: "
                        f"{outside}"
                    )
                coerced[name] = value

            acc = np.zeros(len(out_union), dtype=np.float64)
            for plan, term_out in term_plans:
                values: dict[str, np.ndarray] = {}
                for name in plan.order:
                    mask = plan.masks[name]
                    values[name] = np.asarray(
                        alg._mod.to_matrix(coerced[name]._impl, mask.ids),
                        dtype=np.float64,
                    ).ravel()
                term_res = _run_compiled_plan(plan, alg, values)
                out_pos = [out_union.index(oid) for oid in term_out.ids]
                acc[out_pos] += term_res

            impl = alg._mod.from_matrix(acc.reshape(-1, 1), out_union.ids)
            return MV(impl, alg)

        return compiled

    def bind(self, **bindings: Any) -> "AffineExpression":
        """Bind variables to values, or substitute them with other ``Variable``s.

        A binding value that is a :class:`Variable` substitutes that variable in
        every term (see :meth:`Expression._substitute`) instead of evaluating it;
        every other value binds as before (an :class:`Expression` value composes
        the sub-expression into each term).  Raises :class:`ValueError` if the
        sum fully collapses to an ``MV`` or a batched ``list`` (use
        :meth:`evaluate` or :meth:`__call__` instead).
        """
        subs = {k: v for k, v in bindings.items() if isinstance(v, Variable)}
        if subs:
            unknown = set(subs) - self.names
            if unknown:
                raise ValueError(f"unknown variable(s): {sorted(unknown)}")
            expr = self._substitute(subs)
            values = {
                k: v for k, v in bindings.items() if not isinstance(v, Variable)
            }
            if not values:
                return expr
        else:
            expr = self
            values = bindings

        result = expr(**values)
        if not isinstance(result, AffineExpression):
            raise ValueError(
                "bind() expected a partially-evaluated AffineExpression, but "
                "the binding fully collapsed it. Use evaluate() or __call__()."
            )
        return result

    def evaluate(self, **bindings: Any) -> MV:
        """Evaluate all variables to a concrete :class:`MV`.

        Raises :class:`ValueError` if the result is still an
        ``AffineExpression`` (variables unbound) or a batched ``list``.
        """
        result = self(**bindings)
        if not isinstance(result, MV):
            raise ValueError(
                "evaluate() expected a fully-bound MV, but the binding left "
                "variables unbound (AffineExpression) or produced a batched "
                "result (list)."
            )
        return result

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

    def __truediv__(self, other: Any) -> "AffineExpression":
        if isinstance(other, (int, float)):
            return self._scale(1.0 / float(other))
        return NotImplemented  # type: ignore[return-value]

    def _scale(self, scalar: float) -> "AffineExpression":
        return AffineExpression([t._scale(scalar) for t in self._terms])

    # ------------------------------------------------------------------
    # Involutions / inverse
    # ------------------------------------------------------------------

    def __invert__(self) -> "AffineExpression":
        return AffineExpression([~t for t in self._terms])

    def conj(self) -> "AffineExpression":
        return AffineExpression([t.conj() for t in self._terms])

    # ------------------------------------------------------------------
    # Variable substitution / renaming
    # ------------------------------------------------------------------

    def _substitute(self, mapping: dict[str, Variable]) -> "AffineExpression":
        """Re-key named variables across every term.

        See :meth:`Expression._substitute` for the per-term semantics.
        """
        return AffineExpression([t._substitute(mapping) for t in self._terms])

    def rename_var(self, old: "str | Variable", new_name: str) -> "AffineExpression":
        """Rename a variable in every term that contains it (name-only).

        Terms that do not contain ``old`` are passed through unchanged, mirroring
        the leniency of :meth:`_substitute`.  Raises ``ValueError`` if ``old`` is
        absent from every term, or if ``new_name`` already denotes a different
        variable in any term.
        """
        name = old.name if isinstance(old, Variable) else str(old)
        if name not in self.names:
            raise ValueError(f"cannot rename unknown variable {name!r}")
        new_name = str(new_name)
        if new_name != name and new_name in self.names:
            raise ValueError(
                f"cannot rename {name!r} to {new_name!r}: name already in use"
            )
        return AffineExpression([
            t.rename_var(old, new_name) if name in t.names else t
            for t in self._terms
        ])

    def project_onto(self, other: "MV | BladeMask") -> "AffineExpression":
        """Restrict every term to a blade set (see :meth:`Expression.project_onto`).

        Terms whose entire output is dropped collapse to zero and are removed;
        if every term is dropped the result is a single zero constant term.
        """
        terms = [t.project_onto(other) for t in self._terms]
        kept = [t for t in terms if len(t.out_mask)]
        return AffineExpression(kept or [Expression(self.algebra.multivector({}))])

    # ------------------------------------------------------------------
    # Named GA product methods — distribute over the terms
    # ------------------------------------------------------------------

    def _distribute(self, fn: Any, other: Any) -> "AffineExpression":
        """Apply a binary product ``fn`` over every term pair."""
        if isinstance(other, AffineExpression):
            return AffineExpression(
                [fn(a, b) for a in self._terms for b in other._terms]
            )
        return AffineExpression([fn(t, other) for t in self._terms])

    def gp(self, other: Any) -> "AffineExpression":
        """Geometric product ``self * other``."""
        if isinstance(other, (int, float)):
            return self._scale(float(other))
        return self._distribute(lambda a, b: _product(a, b, EProduct.GP), other)

    def ip(self, other: Any) -> "AffineExpression":
        """Inner product ``self | other``."""
        return self._distribute(lambda a, b: _product(a, b, EProduct.IP), other)

    def op(self, other: Any) -> "AffineExpression":
        """Outer (wedge) product ``self ^ other``."""
        return self._distribute(lambda a, b: _product(a, b, EProduct.OP), other)

    def vp(self, b: Any) -> "AffineExpression":
        """Versor product ``self * b * ~self``."""
        return self._distribute(vp, b)

    def nvp(self, b: Any) -> "AffineExpression":
        """Normalized versor product ``self * b * inverse(self)``."""
        return self._distribute(nvp, b)

    def sp(self, other: Any) -> "AffineExpression":
        """Scalar product: the scalar part of ``self * other``."""
        return self._distribute(sp, other)

    def cp(self, other: Any) -> "AffineExpression":
        """Commutator: ``(self * other - other * self) / 2``."""
        return self._distribute(cp, other)

    def acp(self, other: Any) -> "AffineExpression":
        """Anti-commutator: ``(self * other + other * self) / 2``."""
        return self._distribute(acp, other)

    def rc(self, other: Any) -> "AffineExpression":
        """Right contraction ``self ⌊ other``."""
        return self._distribute(rc, other)

    def _variable_matrix(self) -> tuple[str, BladeMask, np.ndarray]:
        """Return ``(var_name, var_mask, matrix)`` for a single-linear-map sum.

        Requires exactly one variable name, appearing exactly once in every term
        (each term linear in it; no constant or repeated-variable terms).  Builds
        ``matrix`` by evaluating the sum at each canonical basis blade of the
        variable mask and flattening the results over ``out_mask`` (counting axes
        contribute extra rows).
        """
        names = self.names
        if len(names) != 1:
            raise ValueError(
                f"requires a single-variable expression (got {sorted(names)})"
            )
        (var_name,) = names
        for term in self._terms:
            if var_name not in term.names or len(term.names[var_name]) != 1:
                raise ValueError(
                    f"requires {var_name!r} to appear exactly once in every term"
                )

        var_mask = self._union_masks()[var_name]
        out_mask = self.out_mask

        cols = []
        for blade_id in var_mask.ids:
            basis = self.algebra.multivector({blade_id: 1.0})
            res = self(**{var_name: basis})
            col = np.concatenate(
                [
                    np.asarray(to_tensor(leaf, mask=out_mask).data, dtype=np.float64)
                    for leaf in _flatten_mvs(res)
                ]
            )
            cols.append(col)

        matrix = (
            np.column_stack(cols).astype(np.float64)
            if cols
            else np.empty((len(out_mask), 0), dtype=np.float64)
        )
        return var_name, var_mask, matrix

    def get_tensor(self) -> MVTensor:
        """Return the raw affine tensor as an ``MVTensor``.

        Supports a single variable appearing ``k >= 1`` times in every term (no
        counting axes).  Returns a rank-``(1 + k)`` tensor whose axis 0 is the
        union output mask and axes ``1..k`` are the union variable mask.  For
        ``k == 1`` this is the single-linear-map matrix.  Recombine the axes
        into named bases with :meth:`MVTensor.get_array`.
        """
        names = self.names
        if len(names) != 1:
            raise ValueError(
                f"get_tensor() requires a single-variable expression (got {sorted(names)})"
            )
        (var_name,) = names

        k: int | None = None
        for term in self._terms:
            if var_name not in term.names:
                raise ValueError(f"requires {var_name!r} to appear in every term")
            occ = len(term.names[var_name])
            if k is None:
                k = occ
            elif occ != k:
                raise ValueError(
                    f"requires {var_name!r} to appear the same number of times "
                    f"in every term (got {k} and {occ})"
                )
            if term._has_counting_axes():
                raise ValueError("get_tensor() does not support counting axes on terms yet")

        assert k is not None
        var_union = self._union_masks()[var_name]
        out_union = self.out_mask

        raw = np.zeros((len(out_union),) + (len(var_union),) * k, dtype=np.float64)
        for term in self._terms:
            t = term.tensor.tensor
            out_t = term.out_mask
            var_t = term.masks[var_name]
            out_pos = [out_union.index(oid) for oid in out_t.ids]
            var_pos = [var_union.index(vid) for vid in var_t.ids]
            raw[np.ix_(out_pos, *([var_pos] * k))] += np.asarray(
                t.data, dtype=np.float64
            )

        return MVTensor(data=raw, masks=(out_union,) + (var_union,) * k)

    def lstsq(self, rhs: "MV | int | float | None" = None) -> "MV":
        """Solve this single-linear-map affine expression in the least-squares sense.

        Requires exactly one variable appearing once per term.  All output blades
        (and any counting axes) are flattened into the rows of a linear system
        whose columns are the blades of the variable mask.

        - ``rhs=None`` (default): solve the homogeneous system via the smallest
          singular vector.
        - otherwise: solve ``M · vec(x) = rhs`` via ``numpy.linalg.lstsq``,
          requiring a non-stacked expression and *rhs* over ``out_mask``.
        """
        from pytanga.tensor import MVTensor as _MVTensor

        _name, var_mask, matrix = self._variable_matrix()

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
        return cast("MV", from_tensor(result))

    def svd(self) -> tuple[list[float], list["MV"]]:
        """Return the singular values and right-singular multivectors.

        Treats this single-linear-map affine expression as a linear map and
        returns ``(values, mvs)`` — the descending singular values and the
        corresponding right-singular vectors, each reconstructed as an ``MV``
        over the variable's blade mask.
        """
        from pytanga.tensor import MVTensor as _MVTensor

        _name, var_mask, matrix = self._variable_matrix()
        if matrix.shape[0] == 0:
            raise ValueError("svd(): empty linear system")
        _u, s, vt = np.linalg.svd(matrix, full_matrices=False)
        mvs = [
            cast(
                "MV",
                from_tensor(_MVTensor(data=vec.astype(np.float64), masks=(var_mask,))),
            )
            for vec in vt
        ]
        return cast("list[float]", s.tolist()), mvs

    def inv(self, var_name: str) -> "Expression":
        """Return the inverse linear map as a new expression.

        The affine expression must reduce to a single linear map: exactly one
        variable appearing once per term, non-stacked, and square
        (``len(out_mask) == len(var_mask)``).  The result maps the old output
        space back to the old variable space, keyed by *var_name*.
        """
        if self._has_counting_axes():
            raise ValueError("inv() requires a plain (non-stacked) expression")
        _name, var_mask, matrix = self._variable_matrix()
        out_mask = self.out_mask
        if len(out_mask) != len(var_mask):
            raise ValueError(
                "inv() requires a square matrix "
                f"(output mask has {len(out_mask)} blades, "
                f"variable mask has {len(var_mask)})"
            )

        try:
            inv_mat = np.linalg.inv(matrix)
        except np.linalg.LinAlgError as exc:
            raise ValueError("inv() failed: the expression matrix is singular") from exc

        new_label = allocate_block()[0]
        result = MVTensor(data=inv_mat, masks=(var_mask, out_mask))
        labeled = MVLabeledTensor(result, [(OUT_LABEL, "*"), (new_label, "*")])
        return Expression(labeled, {var_name: (new_label,)}, {var_name: out_mask})


def _variable_dataarray_binding_tensors(
    data: DataArray, mask: BladeMask, labels: tuple[int, ...], used: set[str | int]
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
        if not isinstance(spec, str):
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


def _expression_binding_tensors(
    inner: "Expression",
    mask: BladeMask,
    labels: tuple[int, ...],
    name: str,
) -> tuple[list[MVLabeledTensor], dict[str, tuple[int, ...]], dict[str, BladeMask]]:
    """Build labelled tensors for binding *name* to a sub-expression *inner*.

    The inner expression's output axis (``"k"``) is relabelled onto each of the
    host variable's occurrence *labels*; the inner expression's free variables
    are re-keyed onto fresh blocks of size ``len(inner.names[v]) * len(labels)``
    so a repeated host variable substitutes the sub-expression consistently (its
    free variables stay one shared variable, not independent copies).
    """
    if inner.out_mask != mask:
        raise ValueError(
            f"cannot bind variable {name!r} to an expression whose output mask "
            f"{inner.out_mask.names()} differs from the variable mask {mask.names()}"
        )
    if inner._has_counting_axes():
        raise ValueError(
            f"cannot bind variable {name!r} to an expression that carries "
            "counting/batch axes"
        )

    k = len(labels)

    # Map each inner free-variable occurrence label -> (var, occurrence index).
    label_index: dict[int, tuple[str, int]] = {}
    for vname, vlbls in inner.names.items():
        for occ, lab in enumerate(vlbls):
            label_index[lab] = (vname, occ)

    # One fresh, contiguous block per inner free variable (size m_v * k).
    free_names: dict[str, tuple[int, ...]] = {}
    for vname, vlbls in inner.names.items():
        free_names[vname] = allocate_block(len(vlbls) * k)

    inner_axes = inner.tensor.labels
    out: list[MVLabeledTensor] = []
    for j, label in enumerate(labels):
        new_labels: list[tuple[int, str]] = []
        for ax_i, ax in enumerate(inner_axes):
            if ax_i == 0:
                new_labels.append((label, "*"))
            else:
                vname, occ = label_index[cast(int, ax.name)]
                new_labels.append(
                    (free_names[vname][j * len(inner.names[vname]) + occ], "*")
                )
        out.append(MVLabeledTensor(inner.tensor.tensor, new_labels))

    free_masks = {vname: inner.masks[vname] for vname in free_names}
    return out, free_names, free_masks


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
    specs: "tuple[BladeMask | str, ...]",
    length: int,
    used: set[str | int],
    counting_names: set[str | int],
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
    used: set[str | int],
    counting_names: set[str | int],
) -> MVLabeledTensor:
    """Build the labeled tensor for a ``DataArray`` counting-axis reduction."""
    array = data.array
    specs = data.masks
    if array.ndim == 1:
        spec0 = specs[0]
        if not isinstance(spec0, str):
            raise TypeError(
                f"counting-axis reduction spec must be a str, "
                f"got {type(spec0).__name__}"
            )
        n, m = _parse_count_spec(spec0, name)
        if array.shape[0] != length:
            raise ValueError(
                f"counting-axis binding for {name!r} has length "
                f"{array.shape[0]}, expected {length}"
            )
        return MVLabeledTensor(MVTensor(array, (None,)), [(name, m)])
    return _count_array_binding_tensor(name, array, specs, length, used, counting_names)


def _count_binding_tensor(
    name: str,
    value: Any,
    length: int,
    used: set[str | int],
    counting_names: set[str | int],
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


def _scale_eval_result(result: Any, scale: float) -> Any:
    """Scale an evaluation result (``MV``/``Expression``/nested list) by a scalar."""
    if isinstance(result, list):
        return [_scale_eval_result(x, scale) for x in result]
    return result * scale


def _flatten_mvs(result: Any) -> list["MV"]:
    """Flatten an evaluation result (``MV`` or nested list) into a list of ``MV``."""
    if isinstance(result, list):
        out: list["MV"] = []
        for x in result:
            out.extend(_flatten_mvs(x))
        return out
    return [result]


def _combine_terms(results: list[Any]) -> "MV | AffineExpression | list[Any]":
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
        return cast("BladeMask", val.mask)
    if kind == "expr":
        return cast("BladeMask", val.out_mask)
    if kind == "const":
        return BladeMask(val)
    raise AssertionError(f"unknown operand kind {kind!r}")


# ---------------------------------------------------------------------------
# Product builder
# ---------------------------------------------------------------------------


def _resolve_product_operands(
    left: Any, right: Any
) -> tuple[str, Any, str, Any, BladeMask, BladeMask]:
    """Classify two product operands and return ``(Lkind, Lval, Rkind, Rval, m_L, m_R)``.

    Rejects the case where both operands are stacked (batched) expressions, and
    verifies both operands belong to the same algebra.
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

    return Lkind, Lval, Rkind, Rval, m_L, m_R


def _contract_product(
    info: tuple[str, Any, str, Any, BladeMask, BladeMask],
    prod: MVTensor,
) -> Expression:
    """Contract a pre-built 3-D product tensor against two operands.

    *prod* must carry masks ``(c_mask, a_mask, b_mask)`` and data shape
    ``(c, a, b)``.  Operands are classified by :func:`_resolve_product_operands`.
    """
    Lkind, Lval, Rkind, Rval, m_L, m_R = info
    m_C = prod.masks[0]

    operands = [prod.data]
    axes = [[0, 1, 2]]  # C, L, R
    out_axes = [0]
    next_ax = 3

    var_specs: list[tuple[str | int, str]] = []
    var_masks: list[BladeMask] = []
    names: dict[str, tuple[int, ...]] = {}
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
            rename: dict[int, int] = {}
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


def _product(
    left: Any,
    right: Any,
    product: EProduct,
    a_inv: EInv = EInv.ID,
    b_inv: EInv = EInv.ID,
    c_mask: BladeMask | None = None,
) -> Expression:
    """Build the reduced expression for ``left ∘ right``.

    Builds the 3-D product tensor and contracts every constant/expression
    operand, leaving one axis per remaining variable plus the output axis.
    """
    info = _resolve_product_operands(left, right)
    _, _, _, _, m_L, m_R = info
    prod = product_tensor(m_L, m_R, c_mask, product=product, a_inv=a_inv, b_inv=b_inv)
    return _contract_product(info, prod)


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


def _restrict_output(expr: Expression, keep: BladeMask) -> Expression:
    """Restrict an expression's output axis to the blades in *keep*.

    Returns a new :class:`Expression` whose output mask is the intersection of
    ``expr.out_mask`` and *keep*; a disjoint intersection collapses to a zero
    constant expression.
    """
    old_mask = expr.out_mask
    keep_ids = [bid for bid in old_mask.ids if bid in keep]
    if not keep_ids:
        return Expression(expr.algebra.multivector({}))
    new_mask = BladeMask(expr.algebra, keep_ids)
    data = expr.tensor.data
    new_data = np.zeros((len(new_mask), *data.shape[1:]), dtype=data.dtype)
    for k, bid in enumerate(new_mask.ids):
        new_data[k] = data[old_mask.index(bid)]
    new_masks = (new_mask, *expr.tensor.tensor.masks[1:])
    return Expression(
        MVLabeledTensor(MVTensor(data=new_data, masks=new_masks), expr.tensor.labels),
        expr.names,
        expr.masks,
    )


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
    outside = mask.ids_outside(value)
    if outside:
        raise ValueError(f"binding for {name!r} has blades outside its mask: {outside}")


def _validate_items(items: list[Any], name: str) -> None:
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


def _next_batch_label(used: set[str]) -> str:
    """Return an unused single-letter label for a batched binding."""
    for ch in _BATCH_POOL:
        if ch not in used:
            return ch
    raise RuntimeError("too many batched variables in one evaluation")


class ScalarExpression(Expression):
    """An :class:`Expression` whose fully-bound value is a scalar.

    Produced by :func:`sp`.  Identical to a plain ``Expression`` with a
    scalar-only output mask, except that a full evaluation unwraps to a Python
    ``float``/``int`` (the scalar coefficient) instead of a scalar-grade ``MV``.
    """

    __slots__ = ()

    def __call__(self, **bindings: Any) -> Any:
        return _unwrap_scalar(super().__call__(**bindings))

    def evaluate(self, **bindings: Any) -> Any:
        result = super().evaluate(**bindings)
        if not isinstance(result, MV):
            raise ValueError(
                "evaluate() expected a fully-bound scalar, but the binding left "
                "variables unbound or produced a batched result"
            )
        return result.scalar

    def bind(self, **bindings: Any) -> Any:
        return _unwrap_scalar(super().bind(**bindings))

    def _scale(self, scalar: float) -> "ScalarExpression":
        return ScalarExpression(
            self._tensor.mul_scalar(scalar), self._names, self._masks
        )


def _unwrap_scalar(result: Any) -> Any:
    """Recursively unwrap scalar-expression results to ``float``/``int``."""
    if isinstance(result, MV):
        return result.scalar
    if isinstance(result, list):
        return [_unwrap_scalar(x) for x in result]
    if isinstance(result, Expression) and not isinstance(result, ScalarExpression):
        # A partial evaluation dropped the ScalarExpression wrapper; restore it.
        return ScalarExpression(result.tensor, result.names, result.masks)
    return result


def _scalar_mask(left: Any, right: Any) -> BladeMask:
    """Return the scalar blade mask for the algebra of *left* or *right*."""
    for value in (left, right):
        if isinstance(value, (MV, Variable, Expression)):
            return BladeMask(value.algebra, [0])
    raise TypeError("sp() requires at least one multivector-valued operand")


# ---------------------------------------------------------------------------
# Named GA product functions
# ---------------------------------------------------------------------------


@overload
def project_onto(x: MV, other: "MV | BladeMask") -> MV: ...
@overload
def project_onto(x: Expression, other: "MV | BladeMask") -> Expression: ...
@overload
def project_onto(x: AffineExpression, other: "MV | BladeMask") -> AffineExpression: ...
def project_onto(
    x: "MV | Expression | AffineExpression", other: "MV | BladeMask"
) -> "MV | Expression | AffineExpression":
    """Restrict *x* (MV / Expression / AffineExpression) to a blade set.

    ``other`` is an ``MV`` (its non-zero blades) or a ``BladeMask`` (exact id
    membership).  The return type matches *x*.
    """
    return x.project_onto(other)


def gp(left: Any, right: Any) -> "MV | Expression | AffineExpression":
    """Geometric product ``left * right``.

    Operands may be constant multivectors, variables, or expressions.
    """
    return cast("MV | Expression | AffineExpression", left * right)


def ip(left: Any, right: Any) -> "MV | Expression | AffineExpression":
    """Inner product ``left | right``."""
    return cast("MV | Expression | AffineExpression", left | right)


def op(left: Any, right: Any) -> "MV | Expression | AffineExpression":
    """Outer (wedge) product ``left ^ right``."""
    return cast("MV | Expression | AffineExpression", left ^ right)


def vp(versor: Any, b: Any) -> "MV | Expression | AffineExpression":
    """Versor product ``versor * b * ~versor``."""
    return cast("MV | Expression | AffineExpression", versor * b * ~versor)


def nvp(versor: Any, b: Any) -> "MV | Expression | AffineExpression":
    """Normalized versor product ``versor * b * inverse(versor)``.

    The versor must be a concrete multivector (or a constant expression); a
    symbolic versor's inverse is not representable in the expression system.
    """
    if isinstance(versor, MV):
        inv = versor.inv()
    elif (
        isinstance(versor, Expression)
        and not versor.names
        and not versor._has_counting_axes()
    ):
        inv = versor().inv()
    else:
        raise ValueError(
            "nvp() requires a constant versor; a symbolic versor's inverse is "
            "not representable in the expression system"
        )
    return cast("MV | Expression | AffineExpression", versor * b * inv)


def sp(left: Any, right: Any) -> "float | int | ScalarExpression":
    """Scalar product: the scalar part of ``left * right``.

    Fully concrete operands produce a ``float``/``int`` directly; symbolic
    operands produce a :class:`ScalarExpression` that unwraps to a scalar when
    fully evaluated.
    """
    if isinstance(left, MV) and isinstance(right, MV):
        return cast("float | int", left.sp(right))
    expr = _product(left, right, EProduct.GP, c_mask=_scalar_mask(left, right))
    return ScalarExpression(expr.tensor, expr.names, expr.masks)


def cp(left: Any, right: Any) -> "MV | Expression | AffineExpression":
    """Commutator: ``(left * right - right * left) / 2``."""
    return cast("MV | Expression | AffineExpression", 0.5 * (left * right - right * left))


def acp(left: Any, right: Any) -> "MV | Expression | AffineExpression":
    """Anti-commutator: ``(left * right + right * left) / 2``."""
    return cast("MV | Expression | AffineExpression", 0.5 * (left * right + right * left))


def rc(left: Any, right: Any) -> "MV | Expression | AffineExpression":
    """Right contraction ``left ⌊ right``."""
    if isinstance(left, MV) and isinstance(right, MV):
        return cast("MV", left.rc(right))
    info = _resolve_product_operands(left, right)
    _, _, _, _, m_L, m_R = info
    prod = product_tensor_rc(m_L, m_R)
    return _contract_product(info, prod)


def unify(
    expressions: "list[Expression | AffineExpression]",
    **mapping: Variable,
) -> "list[Expression | AffineExpression]":
    """Re-key variables across a list of expressions onto canonical ``Variable``s.

    ``mapping`` maps variable names to target ``Variable`` instances (the same
    form as :meth:`Expression.bind`).  Each expression is re-keyed via
    :meth:`Expression._substitute`, which is lenient — names absent from a given
    expression are skipped, so one mapping can unify a heterogeneous list, e.g.
    ``unify([e1, e2], X=X, Y=X)``.

    Returns a new list of re-keyed expressions (same order); combine them with
    ``+`` / ``sum`` afterwards.
    """
    if not mapping:
        raise ValueError("unify() requires at least one name=Variable mapping")
    for name, target in mapping.items():
        if not isinstance(target, Variable):
            raise TypeError(
                f"unify() mapping value for {name!r} must be a Variable, "
                f"got {type(target).__name__}"
            )

    out: list[Expression | AffineExpression] = []
    for expr in expressions:
        if isinstance(expr, AffineExpression):
            out.append(expr._substitute(mapping))
        elif isinstance(expr, Expression):
            out.append(expr._substitute(mapping))
        else:
            raise TypeError(
                f"unify() expects Expression or AffineExpression, got "
                f"{type(expr).__name__}"
            )
    return out
