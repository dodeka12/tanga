# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.blade_mask._mask — BladeMask: an ordered, algebra-bound set of blade ids."""

from __future__ import annotations

from typing import Iterable, Iterator, Sequence

import numpy as np

from pytanga.algebra._blade_names import grade as _grade
from pytanga.algebra._parse import _parse_mv_string
from pytanga.algebra import Algebra
from pytanga.algebra import MV


class BladeMask:
    """An ordered, deduplicated set of blade ids belonging to a specific algebra.

    Blade ids are stored internally as a sorted tuple (canonical order) with a
    companion dict for O(1) position lookup.  The algebra reference ensures that
    two masks from different algebras are never silently combined.

    Construction
    ------------
    The first positional argument ``ctx`` determines how the mask is built:

    - **``Algebra``** — the ``ids`` and ``grades`` parameters are used
      (see below).  This is the most general form.
    - **``MV``** — builds a mask from the non‑zero blades of that
      multivector (equivalent to ``BladeMask.from_mv(mv)``).  The ``ids``
      and ``grades`` parameters are ignored.
    - **``list[MV]``** — builds a mask from the **union** of the non‑zero
      blades of all multivectors in the list (equivalent to
      ``BladeMask.from_array(mvs)``).  The ``ids`` and ``grades``
      parameters are ignored.

    When ``ctx`` is an ``Algebra``, ``ids`` and ``grades`` are resolved:

    ``ids`` accepts:
        - ``Iterable[int]`` — blade ids collected directly.
        - ``str`` — parsed with the MV string parser; signs and
          coefficients are discarded, only the blade ids are kept.
        - ``Iterable[str]`` — each string parsed independently; ids are
          unioned.

    ``grades`` (keyword, optional) — adds every blade id whose popcount
    equals any value in the list.  Applied after ``ids``; the two are
    unioned.

    If ``ctx`` is an Algebra instance, but neither ids, nor grades are given,
    the mask is the whole algebra.  Passing an explicit empty ``ids`` iterable
    (``[]`` / ``set()``) yields an **empty** mask instead.

    Examples::

        BladeMask(alg, [1, 2, 4])              # from int ids
        BladeMask(alg, "e1 + e2")              # from expression string
        BladeMask(alg, ["e12", "1 + e13"])     # from list of strings
        BladeMask(alg, grades=[0, 2])          # scalar + all bivectors
        BladeMask(alg, "e1", grades=[2])       # e1 plus all bivectors
        BladeMask(mv)                          # non-zero blades of mv
        BladeMask([mv1, mv2])                  # union of mv1 and mv2 blades
    """

    __slots__ = ("_ids", "_index", "_alg", "_basis")

    def __init__(
        self,
        ctx: Algebra | MV | list[MV],
        ids: Iterable[int] | str | Iterable[str] | None = None,
        *,
        grades: list[int] | None = None,
    ) -> None:
        raw: set[int] = set()

        alg: Algebra
        if isinstance(ctx, Algebra):
            alg = ctx

            # --- resolve ids ---
            if ids is None:
                # No ids supplied; the full-mask default is applied below when
                # grades is also omitted.  An explicit empty iterable is kept
                # empty.
                pass
            elif isinstance(ids, str):
                # single expression string
                raw.update(_parse_mv_string(ids, alg.dim, alg._composite_basis()).keys())
            else:
                ids_list = list(ids)
                if ids_list and isinstance(ids_list[0], str):
                    # list of expression strings
                    for s in ids_list:
                        if isinstance(s, str):
                            raw.update(_parse_mv_string(s, alg.dim, alg._composite_basis()).keys())
                else:
                    # iterable of int blade ids
                    raw.update(int(b) for b in ids_list)

            # --- resolve grades ---
            grade_set = set()
            if grades is not None:
                grade_set = set(grades)
            elif ids is None:
                grade_set = set(range(alg.dim + 1))

            if len(grade_set) > 0:
                for bid in range(alg.algebra_dim):
                    if _grade(bid) in grade_set:
                        raw.add(bid)

        elif isinstance(ctx, MV):
            raw = set(self._ids_from_mv(ctx, only_nonzero=True))
            alg = ctx.algebra

        elif isinstance(ctx, list) and ctx and isinstance(ctx[0], MV):
            alg, raw = self._ids_from_mv_list(ctx)

        else:
            raise ValueError(
                "BladeMask constructor requires Algebra, MV, or list[MV] as first argument"
            )

        self._ids: tuple[int, ...] = tuple(sorted(raw))
        self._index: dict[int, int] = {bid: i for i, bid in enumerate(self._ids)}
        self._alg = alg
        self._basis: tuple[tuple[str, MV], ...] | None = None
        self._attach_display_basis(raw)

    # ------------------------------------------------------------------
    # Classmethods
    # ------------------------------------------------------------------

    @classmethod
    def _ids_from_mv(cls, a: MV, only_nonzero: bool = True) -> list[int]:
        """Build a mask from the blades present in multivector *a*.

        Delegates to ``alg._mod.blade_mask`` (Phase 2 C++ binding).
        Falls back to iterating ``a.to_dict()`` if the binding is not yet available.
        """
        alg = a.algebra
        try:
            raw_ids = alg._mod.blade_mask(a._impl, only_nonzero)
        except AttributeError:
            # Phase 2 not yet compiled — use Python fallback
            d = a._impl.to_dict()
            raw_ids = [k for k, v in d.items() if (not only_nonzero or v != 0)]
        return raw_ids

    @classmethod
    def from_mv(cls, a: MV, only_nonzero: bool = True) -> "BladeMask":
        raw_ids = cls._ids_from_mv(a, only_nonzero=only_nonzero)
        return cls(a.algebra, raw_ids)

    @classmethod
    def _ids_from_mv_list(cls, mvs: list[MV]) -> tuple[Algebra, set[int]]:
        """Build a mask that is the union of the non-zero blades of each MV in *mvs*.

        All MVs must belong to the same algebra.

        Parameters
        ----------
        mvs : list[MV]
            List of multivectors whose blade sets are unioned.

        Returns
        -------
        tuple[Algebra, set[int]]
            The algebra and the union of the individual blade masks.
        """
        from pytanga.algebra import MV as _MV

        if not mvs:
            raise ValueError("from_array requires at least one MV")
        alg = None
        raw: set[int] = set()
        for mv in mvs:
            if not isinstance(mv, _MV):
                raise ValueError("All elements in list must be multivectors")

            if alg is None:
                alg = mv.algebra
            elif mv.algebra is not alg:
                raise ValueError(
                    "All MVs in from_array must belong to the same algebra"
                )
            try:
                raw_ids = alg._mod.blade_mask(mv._impl, True)
            except AttributeError:
                d = mv._impl.to_dict()
                raw_ids = [k for k, v in d.items() if v != 0]
            raw.update(raw_ids)
        if alg is None:
            raise ValueError("from_array requires at least one MV")
        return alg, raw

    @classmethod
    def from_array(cls, mvs: list[MV]) -> "BladeMask":
        alg, raw = cls._ids_from_mv_list(mvs)
        return cls(alg, raw)

    @classmethod
    def from_str(cls, alg: Algebra, s: str) -> "BladeMask":
        """Convenience alias for ``BladeMask(alg, s)``."""
        return cls(alg, s)

    @classmethod
    def full(cls, alg: Algebra) -> "BladeMask":
        """Return a mask containing all 2^dim blades of the algebra."""
        return cls(alg, grades=list(range(alg.dim + 1)))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def algebra(self) -> Algebra:
        """The algebra this mask belongs to."""
        return self._alg

    @property
    def ids(self) -> list[int]:
        """Sorted list of blade ids (copy)."""
        return list(self._ids)

    @property
    def basis_vectors(self) -> list[MV]:
        """The basis direction multivectors, in order.

        The named directions when a basis is attached, otherwise one primitive
        blade per id (in ``ids`` order).
        """
        if self._basis is not None:
            return [mv for _, mv in self._basis]
        return [self._alg.multivector({bid: 1.0}) for bid in self._ids]

    @property
    def basis_names(self) -> list[str]:
        """The basis direction names, in order (see :attr:`basis_vectors`)."""
        if self._basis is not None:
            return [name for name, _ in self._basis]
        return [self._alg.blade_name(bid) for bid in self._ids]

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def index(self, blade_id: int) -> int:
        """Return the 0-based position of *blade_id* in this mask.

        Raises ``KeyError`` if *blade_id* is not in the mask.
        """
        return self._index[blade_id]

    def names(self) -> list[str]:
        """Return the blade name for each id in this mask, sorted by grade."""
        sorted_ids = sorted(self._ids, key=lambda b: (_grade(b), b))
        return [self._alg.blade_name(bid) for bid in sorted_ids]

    # ------------------------------------------------------------------
    # Named basis
    # ------------------------------------------------------------------

    def with_basis(
        self,
        directions: Sequence[MV | tuple[str, MV]],
        *,
        names: Sequence[str] | None = None,
    ) -> "BladeMask":
        """Return a new mask over the same raw ids, labelled by *directions*.

        *directions* is either a sequence of ``MV`` (with optional parallel
        *names*) or a sequence of ``(name, MV)`` pairs.  Each direction must lie
        within this mask's span (its non-zero raw blades ⊆ ``ids``); a reduced
        set is allowed.
        """
        if names is not None and len(names) != len(directions):
            raise ValueError("names must have one entry per basis direction")

        entries: list[tuple[str, MV]] = []
        for i, item in enumerate(directions):
            if isinstance(item, MV):
                mv = item
                name = names[i] if names is not None else f"d{i}"
            else:
                name, mv = item
            support = set(self._ids_from_mv(mv, only_nonzero=True))
            extra = sorted(support - set(self._ids))
            if extra:
                raise ValueError(
                    f"basis direction {name!r} contains blades outside the mask: {extra}"
                )
            entries.append((str(name), mv))

        result = BladeMask(self._alg, list(self._ids))
        result._basis = tuple(entries)
        return result

    def basis_matrix(self, directions: Sequence[MV] | None = None) -> np.ndarray:
        """Return the raw→named change-of-basis matrix (shape ``(len(self), n)``).

        Column ``k`` holds the raw-blade coefficients of direction ``k`` over
        ``self.ids`` order.  Defaults to :attr:`basis_vectors`.
        """
        from pytanga.matrix.convert import to_matrix

        vecs: Sequence[MV] = self.basis_vectors if directions is None else directions
        return to_matrix(list(vecs), mask=self).data

    def _attach_display_basis(self, raw: set[int]) -> None:
        """Attach the algebra display basis to *raw* iff it fully covers it."""
        display = self._alg._get_display_basis()
        if display is None:
            return
        entries: list[tuple[str, MV]] = []
        covered: set[int] = set()
        for name, blade, _pinv, _blade_id in display:
            support = set(self._ids_from_mv(blade, only_nonzero=True))
            if support and support <= raw:
                entries.append((name, blade))
                covered |= support
        if covered == raw:
            self._basis = tuple(entries)

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    def union(self, other: "BladeMask") -> "BladeMask":
        """Return a new mask containing the ids of both masks.

        When both masks carry a named basis, the returned mask's basis is the
        deduplicated union of the two direction sets (by name).  Otherwise the
        result is a plain raw-id union with the default display basis (if any).
        """
        assert other._alg is self._alg, (
            "Cannot union BladeMasks from different algebras"
        )
        if self._basis is not None and other._basis is not None:
            merged: list[tuple[str, MV]] = []
            seen: set[str] = set()
            for entry in list(self._basis) + list(other._basis):
                if entry[0] not in seen:
                    seen.add(entry[0])
                    merged.append(entry)
            result = BladeMask(self._alg, set(self._ids) | set(other._ids))
            result._basis = tuple(merged)
            return result
        return BladeMask(self._alg, set(self._ids) | set(other._ids))

    def intersection(
        self, other: "BladeMask", *, discard_basis: bool = False
    ) -> "BladeMask":
        """Return a new mask containing only ids present in both masks.

        When both masks carry a named basis, the intersection is computed at the
        named-direction level: only directions present (by name) in both are
        kept, and the raw ids are the union of those directions' supports.  When
        both masks are raw-only, the raw-id intersection is returned unchanged.
        When only one mask carries a named basis the intersection cannot be
        aligned: ``discard_basis=True`` falls back to the raw-id intersection,
        otherwise a ``ValueError`` is raised.
        """
        assert other._alg is self._alg, (
            "Cannot intersect BladeMasks from different algebras"
        )
        if self._basis is not None and other._basis is not None:
            other_names = {name for name, _ in other._basis}
            shared = [entry for entry in self._basis if entry[0] in other_names]
            support: set[int] = set()
            for _, mv in shared:
                support.update(self._ids_from_mv(mv, only_nonzero=True))
            result = BladeMask(self._alg, support)
            result._basis = tuple(shared)
            return result
        if self._basis is None and other._basis is None:
            return BladeMask(self._alg, set(self._ids) & set(other._ids))
        if discard_basis:
            return BladeMask(self._alg, set(self._ids) & set(other._ids))
        raise ValueError(
            "cannot align the named basis of the two masks for intersection; "
            "pass discard_basis=True to fall back to the raw-id intersection"
        )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._ids)

    def __iter__(self) -> "Iterator[int]":
        return iter(self._ids)

    def __contains__(self, item: int) -> bool:
        return item in self._index

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BladeMask):
            return NotImplemented
        return self._alg is other._alg and self._ids == other._ids

    def __repr__(self) -> str:
        return f"BladeMask({self.names()})"
