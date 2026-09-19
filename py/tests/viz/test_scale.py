# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for scale and tick computation (``pytanga.viz._scale``)."""

import pytest

from pytanga.viz._scale import (
    LinearScale,
    LogScale,
    generate_linear_intervals,
    log_ticks,
    make_scale,
    nice_linear_ticks,
    normalize_intervals,
)


class TestLinearScale:
    def test_identity_mapping(self):  # noqa: ANN201
        s = LinearScale()
        assert s.to_world(3.5) == 3.5
        assert s.from_world(3.5) == 3.5
        assert s.is_log is False

    def test_ticks_cover_range_ascending(self):  # noqa: ANN201
        ticks = LinearScale().ticks(0.0, 10.0)
        values = [v for v, _ in ticks]
        assert values == sorted(values)
        assert values[0] <= 0.0
        assert values[-1] >= 10.0
        assert all(isinstance(label, str) for _, label in ticks)

    def test_nice_step_is_1_2_or_5(self):  # noqa: ANN201
        values = [v for v, _ in nice_linear_ticks(0.0, 10.0, max_ticks=8)]
        steps = {round(values[i + 1] - values[i], 9) for i in range(len(values) - 1)}
        assert len(steps) == 1
        assert steps.pop() in (1.0, 2.0, 5.0)

    def test_single_point_range(self):  # noqa: ANN201
        ticks = LinearScale().ticks(5.0, 5.0)
        assert ticks == [(5.0, "5")]

    def test_reversed_range_is_sorted(self):  # noqa: ANN201
        ticks = LinearScale().ticks(10.0, 0.0)
        values = [v for v, _ in ticks]
        assert values == sorted(values)


class TestLogScale:
    def test_to_world(self):  # noqa: ANN201
        s = LogScale(10.0)
        assert s.to_world(100.0) == pytest.approx(2.0)
        assert s.from_world(2.0) == pytest.approx(100.0)
        assert s.is_log is True

    def test_ticks_powers_of_ten(self):  # noqa: ANN201
        s = LogScale(10.0)
        ticks = s.ticks(0.1, 100.0)
        assert [v for v, _ in ticks] == pytest.approx([0.1, 1.0, 10.0, 100.0])
        assert [label for _, label in ticks] == ["0.1", "1", "10", "100"]

    def test_ticks_any_base(self):  # noqa: ANN201
        s = LogScale(2.0)
        ticks = s.ticks(1.0, 8.0)
        assert [v for v, _ in ticks] == pytest.approx([1.0, 2.0, 4.0, 8.0])

    def test_exact_power_upper_bound(self):  # noqa: ANN201
        # Guards against floating-point log10 error at exact powers.
        ticks = LogScale(10.0).ticks(1.0, 1000.0)
        assert [v for v, _ in ticks] == pytest.approx([1.0, 10.0, 100.0, 1000.0])

    def test_negative_range_raises(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            LogScale(10.0).ticks(-1.0, 10.0)

    def test_zero_lower_bound_raises(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            LogScale(10.0).ticks(0.0, 10.0)

    def test_non_positive_value_raises(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            LogScale(10.0).to_world(0.0)

    def test_invalid_base_raises(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            LogScale(1.0)


class TestMakeScale:
    def test_linear_string(self):  # noqa: ANN201
        assert isinstance(make_scale("linear"), LinearScale)

    def test_log_string_with_base(self):  # noqa: ANN201
        s = make_scale("log", base=2.0)
        assert isinstance(s, LogScale)
        assert s.base == 2.0

    def test_instance_passthrough(self):  # noqa: ANN201
        s = LinearScale()
        assert make_scale(s) is s

    def test_invalid_raises(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            make_scale("sqrt")


class TestLogTicks:
    def test_log_ticks_helper(self):  # noqa: ANN201
        assert [v for v, _ in log_ticks(1.0, 100.0, 10.0)] == pytest.approx(
            [1.0, 10.0, 100.0]
        )


class TestIntervals:
    def test_normalize_dedupes_sorts_positives(self):  # noqa: ANN201
        assert normalize_intervals([10, 2, 5, 2, 0, -1]) == [2.0, 5.0, 10.0]

    def test_normalize_none_and_empty(self):  # noqa: ANN201
        assert normalize_intervals(None) is None
        assert normalize_intervals([]) is None
        assert normalize_intervals([0, -1]) is None

    def test_generate_spans_range_with_finest_step(self):  # noqa: ANN201
        steps = generate_linear_intervals(0.0, 10.0)
        # 1/2/5 mantissas from span/100 (0.1) up to the span decade (10).
        assert steps[0] == pytest.approx(0.1)
        assert 1.0 in steps
        assert 2.0 in steps
        assert 5.0 in steps
        assert 10.0 in steps

    def test_nice_ticks_uses_explicit_intervals(self):  # noqa: ANN201
        # A range where the default 1/2/5 step would be 100 (0,100,...,1000),
        # but the explicit list restricts steps to {50, 200, 500}.
        ticks = [v for v, _ in nice_linear_ticks(0.0, 1000.0, max_ticks=8, intervals=[50, 200, 500])]
        steps = {round(ticks[i + 1] - ticks[i], 9) for i in range(len(ticks) - 1)}
        assert steps == {200.0}

    def test_nice_ticks_auto_generates_same_as_default(self):  # noqa: ANN201
        assert nice_linear_ticks(0.0, 10.0, max_ticks=8) == nice_linear_ticks(
            0.0, 10.0, max_ticks=8, intervals=generate_linear_intervals(0.0, 10.0)
        )

    def test_intervals_ignored_for_log_scale(self):  # noqa: ANN201
        ticks = LogScale(10.0).ticks(0.1, 100.0, intervals=[0.05, 0.25, 0.75])
        assert [v for v, _ in ticks] == pytest.approx([0.1, 1.0, 10.0, 100.0])

    def test_zero_tick_is_exactly_zero(self):  # noqa: ANN201
        # Accumulating `t += step` used to leave a 3.4e-18 residue at the zero
        # crossing; the integer-index multiplication must yield exactly 0.0.
        ticks = nice_linear_ticks(-0.05, 0.05, max_ticks=11, intervals=[0.01, 0.02, 0.05])
        zero = next(v for v, _ in ticks if abs(v) < 1e-9)
        assert zero == 0.0
