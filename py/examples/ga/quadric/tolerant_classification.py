# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""tolerant_classification.py — classify a noisy quadric within a tolerance.

Shows how a quadric that is *almost* a cone (a tiny perturbation of the
homogeneous constant) is classified as a hyperboloid by the exact ``.kind``, but
as a cone once a tolerance is set on the ``Geometry`` instance (or passed to
``Geometry.refine``).

Run with:  uv run python py/examples/ga/quadric/tolerant_classification.py

Keywords: quadric, classification, tolerance, cone, refine, Geometry
"""

import numpy as np

from pytanga.geometry import Geometry
from pytanga.quadric import BasisQ3, Quadric3D


def _main() -> None:
    # x^2 + y^2 - z^2 = 0 is a cone; a tiny constant turns it into a hyperboloid.
    q = Quadric3D(np.diag([1.0, 1.0, -1.0, 1e-6]))

    geo = Geometry(BasisQ3())
    print("exact classification:")
    print("  kind:", q.kind.value, " rank:", q.rank)

    geo.tol = 1e-4
    refined = geo.refine(q)
    print("with tolerance 1e-4:")
    print("  refined to:", type(refined).__name__)


if __name__ == "__main__":
    _main()
