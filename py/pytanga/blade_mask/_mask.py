# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.blade_mask._mask — BladeMask: an ordered, algebra-bound set of blade ids."""

from __future__ import annotations

from typing import Iterable

from pytanga.algebra._blade_names import blade_name
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
    the mask is the whole algebra.

    Examples::

        BladeMask(alg, [1, 2, 4])              # from int ids
        BladeMask(alg, "e1 + e2")              # from expression string
        BladeMask(alg, ["e12", "1 + e13"])     # from list of strings
        BladeMask(alg, grades=[0, 2])          # scalar + all bivectors
        BladeMask(alg, "e1", grades=[2])       # e1 plus all bivectors
        BladeMask(mv)                          # non-zero blades of mv
        BladeMask([mv1, mv2])                  # union of mv1 and mv2 blades
    """

    __slots__ = ("_ids", "_index", "_alg")

    def __init__(
        self,
        ctx: Algebra | MV | list[MV],
        ids: Iterable[int] | str | Iterable[str] = (),
        *,
        grades: list[int] | None = None,
    ) -> None:
        raw: set[int] = set()

        alg: Algebra
        if isinstance(ctx, Algebra):
            alg = ctx

            # --- resolve ids ---
            if isinstance(ids, str):
                # single expression string
                raw.update(_parse_mv_string(ids, alg.dim).keys())
            else:
                ids_list = list(ids)
                if ids_list and isinstance(ids_list[0], str):
                    # list of expression strings
                    for s in ids_list:
                        raw.update(_parse_mv_string(s, alg.dim).keys())
                else:
                    # iterable of int blade ids
                    raw.update(int(b) for b in ids_list)

            # --- resolve grades ---
            grade_set = set()
            if grades is not None:
                grade_set = set(grades)
            elif len(raw) == 0:
                grade_set = set(range(alg.dim + 1))

            if len(grade_set) > 0:
                for bid in range(alg.algebra_dim):
                    if _grade(bid) in grade_set:
                        raw.add(bid)

        elif isinstance(ctx, MV):
            raw = self._ids_from_mv(ctx, only_nonzero=True)
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
    def _ids_from_mv_list(cls, mvs: list[MV]) -> tuple[Algebra, list[int]]:
        """Build a mask that is the union of the non-zero blades of each MV in *mvs*.

        All MVs must belong to the same algebra.

        Parameters
        ----------
        mvs : list[MV]
            List of multivectors whose blade sets are unioned.

        Returns
        -------
        tuple[Algebra, list[int]]
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
        dim = self._alg.dim
        sorted_ids = sorted(self._ids, key=lambda b: (_grade(b), b))
        return [blade_name(bid, dim) for bid in sorted_ids]

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    def union(self, other: "BladeMask") -> "BladeMask":
        """Return a new mask containing the ids of both masks."""
        assert other._alg is self._alg, (
            "Cannot union BladeMasks from different algebras"
        )
        return BladeMask(self._alg, set(self._ids) | set(other._ids))

    def intersection(self, other: "BladeMask") -> "BladeMask":
        """Return a new mask containing only ids present in both masks."""
        assert other._alg is self._alg, (
            "Cannot intersect BladeMasks from different algebras"
        )
        return BladeMask(self._alg, set(self._ids) & set(other._ids))

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._ids)

    def __iter__(self):
        return iter(self._ids)

    def __contains__(self, item: int) -> bool:
        return item in self._index

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BladeMask):
            return NotImplemented
        return self._alg is other._alg and self._ids == other._ids

    def __repr__(self) -> str:
        return f"BladeMask({self.names()})"
