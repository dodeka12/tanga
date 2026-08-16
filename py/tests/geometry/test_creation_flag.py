# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 6a — creation path reads ``basis.opns``.

Verifies that ``create_entity`` respects the algebra's ``opns`` flag
(rather than a per-call keyword) for every algebra, by asserting the
produced blade grade under OPNS vs IPNS.
"""

from __future__ import annotations

import pytest

from pytanga.basis import (
    BasisE2,
    BasisE3,
    BasisN2,
    BasisN3,
    BasisP2,
    BasisP3,
    BasisPGA2,
    BasisPGA3,
)
from pytanga.geometry.create import create_entity
from pytanga.geometry.entities import Direction, Line, Plane, Point, Space, Sphere


@pytest.mark.parametrize(
    "alg_cls,entity,opns_grade,ipns_grade",
    [
        # E2: point is flag-independent (grade-1); use Direction for a dual pair
        (BasisE2, Direction(1, 0, 0), 1, 1),
        (BasisE2, Space(scale=2.0), 2, 0),
        (BasisE3, Direction(1, 0, 0), 1, 2),
        (BasisE3, Space(scale=2.0), 3, 0),
        (BasisP2, Point(1, 2, 0), 1, 2),
        (BasisP2, Space(scale=2.0), 3, 0),
        (BasisP3, Point(1, 2, 3), 1, 3),
        (BasisP3, Space(scale=2.0), 4, 0),
        (BasisN2, Point(1, 2, 0), 1, 3),
        (BasisN3, Point(1, 2, 3), 1, 4),
        (BasisN3, Sphere(Point(0, 0, 0), 2.0), 4, 1),
        (BasisPGA2, Point(1, 2, 0), 2, 1),
        (BasisPGA3, Point(1, 2, 3), 3, 1),
    ],
)
def test_create_entity_respects_algebra_opns(
    alg_cls, entity, opns_grade, ipns_grade
):
    opns_alg = alg_cls(opns=True)
    ipns_alg = alg_cls(opns=False)

    opns_mv = create_entity(opns_alg, entity)
    ipns_mv = create_entity(ipns_alg, entity)

    assert set(opns_mv.grades) == {opns_grade}
    assert set(ipns_mv.grades) == {ipns_grade}


def test_create_entity_no_opns_kwarg():
    """create_entity must not accept an ``opns`` keyword anymore."""
    alg = BasisN3()
    with pytest.raises(TypeError):
        create_entity(alg, Point(1, 2, 3), opns=True)  # type: ignore[call-arg]


def test_line_respects_opns():
    alg = BasisN3(opns=True)
    line = Line(Point(0, 0, 0), Direction(1, 0, 0))
    opns_mv = create_entity(alg, line)
    alg.opns = False
    ipns_mv = create_entity(alg, line)
    # N3 line: OPNS grade-3, IPNS grade-2
    assert set(opns_mv.grades) == {3}
    assert set(ipns_mv.grades) == {2}