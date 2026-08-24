# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga._blade_names — bit-arithmetic blade name utilities (no C++)."""

__all__ = ["grade", "all_blades", "blade_name", "blade_id", "blade_id_signed"]


def grade(blade_id: int) -> int:
    """Return the number of set bits (popcount) of *blade_id*."""
    return bin(blade_id).count("1")


def all_blades(dim: int) -> list[int]:
    """Return every blade id for a *dim*-dimensional algebra.

    Sorted by grade then by id within each grade (canonical ordering).
    """
    if dim < 1 or dim > 32:
        raise ValueError(f"dim must be in [1, 32], got {dim}")
    return sorted(range(1 << dim), key=lambda b: (grade(b), b))


def blade_name(blade_id: int, dim: int) -> str:
    """Convert a bitmask *blade_id* to its canonical TanGA-style name.

    - ``0`` → ``"s"`` (scalar)
    - ``(1 << dim) - 1`` → ``"I"`` (pseudoscalar)
    - otherwise → ``"e"`` + 1-based indices of set bits in ascending order
    """
    if blade_id < 0 or blade_id >= (1 << dim):
        raise ValueError(f"blade_id {blade_id} out of range for dim={dim}")
    if blade_id == 0:
        return "s"
    if blade_id == (1 << dim) - 1:
        return "I"
    indices = [str(k + 1) for k in range(dim) if blade_id & (1 << k)]
    return "e" + "".join(indices)


def _permutation_sign(indices: list[int]) -> int:
    """Return ``+1`` for an even permutation, ``-1`` for an odd one.

    The permutation is the one that sorts *indices* into ascending order; its
    parity is computed as the parity of the number of inversions.
    """
    sign = 1
    n = len(indices)
    for i in range(n):
        for j in range(i + 1, n):
            if indices[i] > indices[j]:
                sign = -sign
    return sign


def blade_id_signed(name: str, dim: int) -> tuple[int, int]:
    """Parse a blade name to its ``(bitmask, sign)``.

    Returns the canonical bitmask together with the sign of the permutation
    needed to sort the given indices into ascending order, so reversed names
    resolve to the canonical blade with the correct sign:

    - ``"e13"``  → ``(5, 1)``
    - ``"e31"``  → ``(5, -1)``
    - ``"e321"`` → ``(7, -1)``

    Accepts the same inputs as :func:`blade_id`: ``"s"``/``"0"`` → scalar,
    ``"I"`` → pseudoscalar, or ``"e"`` + distinct 1-based indices in ``[1, dim]``
    (comma-separated for ``dim > 9``).
    """
    if name in ("s", "0"):
        return 0, 1
    if name == "I":
        return (1 << dim) - 1, 1
    if not name.startswith("e"):
        raise ValueError(f"Cannot parse blade name: {name!r}")
    tail = name[1:]
    if not tail:
        raise ValueError(f"Empty blade indices after 'e' in: {name!r}")

    if "," in tail:
        parts = tail.split(",")
        if not all(p.isdigit() for p in parts):
            raise ValueError(f"Non-numeric index in comma-separated name: {name!r}")
        indices = [int(p) for p in parts]
    else:
        if dim > 9:
            raise ValueError(
                f"Use comma-separated format (e.g. 'e1,2,10') for dim > 9; got {name!r}"
            )
        if not tail.isdigit():
            raise ValueError(f"Non-digit characters after 'e' in: {name!r}")
        indices = [int(c) for c in tail]

    if len(indices) != len(set(indices)):
        raise ValueError(f"Repeated basis-vector index in: {name!r}")
    if any(i < 1 or i > dim for i in indices):
        raise ValueError(f"Index out of range [1, {dim}] in: {name!r}")

    bitmask = 0
    for i in indices:
        bitmask |= 1 << (i - 1)
    return bitmask, _permutation_sign(indices)


def blade_id(name: str, dim: int) -> int:
    """Parse a blade name back to its canonical (unsigned) bitmask id.

    The returned bitmask is order-independent (``"e21"`` and ``"e12"`` give the
    same id).  Use :func:`blade_id_signed` when the permutation sign matters,
    e.g. string parsing of reversed names such as ``"e31"``.
    """
    return blade_id_signed(name, dim)[0]
