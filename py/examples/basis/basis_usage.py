# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
basis_usage.py — Three ways to work with named basis blades.

Background
----------
A basis class such as ``BasisE3`` gives you a geometric algebra together with
all of its named basis blades (``e1``, ``e2``, ``e12``, ``I``, …) as
attributes of the object.  There are three common patterns for getting those
short names into your code, each with different trade-offs around readability,
type-checker support, and scope.

The three methods
-----------------
1. ``globals().update(b.blades())``
   The basis object has a helper ``blades()`` that returns a plain dict of
   all blade names → MV objects.  Calling ``globals().update(...)`` merges
   that dict into the module's global namespace, so you can write ``e1``
   instead of ``b.e1`` from that point on.
   Downside: the injection happens at *runtime*, so the linter and
   type-checker never see the names — they will flag every use of ``e1`` as
   an "undefined name" and auto-complete won't work.

2. Attribute access — ``b.e1``, ``b.e2``, …
   All blades are plain attributes declared in ``__init__``, so the
   type-checker already knows about them.  You always write the algebra
   prefix (``b.e1``), which is slightly more verbose but works everywhere:
   at module scope, inside functions, and in any editor with type-checking.

3. Explicit assignment block — ``e1: MV = b.e1``
   A short block at the top of your script (or function) copies each blade
   into a local variable with a full type annotation.  You get the natural
   ``e1`` notation *and* full linter/type-checker support, at the cost of
   writing the block once.  This is the recommended approach for scripts and
   notebooks.

Run with:
    uv run python py/examples/basis_usage.py
"""

from pytanga import MV
from pytanga.basis import BasisE3

# shared algebra instance used in all three sections
b = BasisE3()


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# Method 1 — globals().update()
#
# ``b.blades()`` returns a plain Python dict, e.g.
#   {'e1': <MV>, 'e2': <MV>, 'e12': <MV>, 'I': <MV>, …}
# Passing that dict to ``globals().update()`` merges every key into the
# module's global namespace, so you can write ``e1`` instead of ``b.e1``.
#
# This only works at *module* (script) scope — inside a function, ``globals()``
# refers to the module globals, not the local scope, so the names won't be
# available as local variables there.
#
# Pros  : fewest lines to write; reads like mathematical notation.
# Cons  : injection happens at runtime, so the linter reports every subsequent
#         use of ``e1`` as "undefined name" and auto-complete won't suggest
#         blade names.  Silence those warnings with ``# noqa: F821`` (flake8)
#         or ``# type: ignore[name-defined]`` (mypy / pyright).
# ─────────────────────────────────────────────────────────────────────────────
hr("Method 1 — globals().update()")

globals().update(b.blades())

# The linter will flag the three lines below as "undefined name".
# The code runs correctly at runtime; static analysis is blind.
(e1 * e2).show("e1 * e2")  # type: ignore[name-defined]  # noqa: F821
(e2 * e1).show("e2 * e1")  # type: ignore[name-defined]  # noqa: F821
(I * I).show("I  * I ")  # type: ignore[name-defined]  # noqa: F821


# ─────────────────────────────────────────────────────────────────────────────
# Method 2 — attribute access  (b.e1, b.e2, …)
#
# Every blade is a plain attribute set in ``BasisE3.__init__``, for example:
#   self.e1 = mv({1: 1})
# Because the assignment is inside ``__init__``, the type-checker sees
# ``b.e1`` as a known ``MV`` attribute and auto-complete works normally.
#
# This is the simplest option when you only use a few blades, or when you
# are writing library code where an algebra object is passed as a parameter.
#
# Pros  : no setup; fully type-checked; auto-complete works everywhere;
#         safe to use inside functions and class methods.
# Cons  : every expression must carry the ``b.`` prefix, which can feel
#         noisy in formula-heavy code.
# ─────────────────────────────────────────────────────────────────────────────
hr("Method 2 — attribute access (b.e1, b.e2, …)")

# All attributes are ordinary MV fields declared in __init__,
# so the type-checker knows they exist and have type MV.
(b.e1 * b.e2).show("b.e1 * b.e2")
(b.e2 * b.e1).show("b.e2 * b.e1")
(b.I * b.I).show("b.I  * b.I ")
b.e1.op(b.e2).show("b.e1.op(b.e2)")
b("e1 + 2 e2 + 3 e3").show("b(\"e1 + 2 e2 + 3 e3\")")


# Works identically inside a function — no algebra object needed.
def euclidean_dot(u: MV, v: MV) -> MV:
    """Scalar part of u * v  (= u · v for grade-1 vectors)."""
    return u.ip(v)


v1 = b("e1")
v2 = b("e2")
euclidean_dot(v1, v2).show("e1 · e2 (should be 0)")
euclidean_dot(v1, v1).show("e1 · e1 (should be 1)")


# ─────────────────────────────────────────────────────────────────────────────
# Method 3 — explicit assignment block
#
# Copy the blades you need into local (or module-level) variables with full
# type annotations.  The block is written once at the top of the script or
# function body and from that point on you get short unqualified names that
# the linter fully understands.
#
# Note: ``I`` is not a Python keyword, but it shadows nothing dangerous here;
# however some style guides flag single-letter uppercase names.  A safe
# alternative is to rename it (``I3``, ``ps``, etc.) as shown below.
#
# Pros  : short unqualified names (``e1``, not ``b.e1``); full type
#         information; works in function scope; the declaration block
#         also serves as self-documenting code (reader sees all blades used).
# Cons  : requires writing the declaration block; must be kept in sync if
#         you switch to a different algebra.
# ─────────────────────────────────────────────────────────────────────────────
hr("Method 3 — explicit assignment block")

# --- declaration block (paste once per algebra, adapt as needed) ---
e1: MV = b.e1
e2: MV = b.e2
e3: MV = b.e3
e12: MV = b.e12
e31: MV = b.e31
e23: MV = b.e23
I3: MV = b.I  # renamed to avoid shadowing Python's built-in
# ------------------------------------------------------------------

# From here the linter knows the type of every blade.
(e1 * e2).show("e1 * e2")
(e2 * e1).show("e2 * e1")
(e12 * e12).show("e12 * e12")
(I3 * I3).show("I  * I ")
e1.op(e2).show("e1 ∧ e2  (via .op)")
e1.op(e2.op(e3)).show("e1 ∧ e2 ∧ e3")


# Also works inside a function — just pass the multivectors you need.
def reflect_in_plane(v: MV, n: MV) -> MV:
    """Reflect vector v in the hyperplane with normal n."""
    return -(n * v * n)


reflect_in_plane(e1, e2).show("reflect(e1, n=e2)  → should be -e1: ")
reflect_in_plane(e2, e2).show("reflect(e2, n=e2)  → should be  e2: ")
