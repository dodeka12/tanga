# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for scale and tick computation (``pytanga.viz._scale``)."""

import pytest

from pytanga.viz._scale import (
    LinearScale,
    LogScale,
    log_ticks,
    make_scale,
    nice_linear_ticks,
)


class TestLinearScale:
    def test_identity_mapping(self):
        s = LinearScale()
        assert s.to_world(3.5) == 3.5
        assert s.from_world(3.5) == 3.5
        assert s.is_log is False

    def test_ticks_cover_range_ascending(self):
        ticks = LinearScale().ticks(0.0, 10.0)
        values = [v for v, _ in ticks]
        assert values == sorted(values)
        assert values[0] <= 0.0
        assert values[-1] >= 10.0
        assert all(isinstance(label, str) for _, label in ticks)

    def test_nice_step_is_1_2_or_5(self):
        values = [v for v, _ in nice_linear_ticks(0.0, 10.0, max_ticks=8)]
        steps = {round(values[i + 1] - values[i], 9) for i in range(len(values) - 1)}
        assert len(steps) == 1
        assert steps.pop() in (1.0, 2.0, 5.0)

    def test_single_point_range(self):
        ticks = LinearScale().ticks(5.0, 5.0)
        assert ticks == [(5.0, "5")]

    def test_reversed_range_is_sorted(self):
        ticks = LinearScale().ticks(10.0, 0.0)
        values = [v for v, _ in ticks]
        assert values == sorted(values)


class TestLogScale:
    def test_to_world(self):
        s = LogScale(10.0)
        assert s.to_world(100.0) == pytest.approx(2.0)
        assert s.from_world(2.0) == pytest.approx(100.0)
        assert s.is_log is True

    def test_ticks_powers_of_ten(self):
        s = LogScale(10.0)
        ticks = s.ticks(0.1, 100.0)
        assert [v for v, _ in ticks] == pytest.approx([0.1, 1.0, 10.0, 100.0])
        assert [label for _, label in ticks] == ["0.1", "1", "10", "100"]

    def test_ticks_any_base(self):
        s = LogScale(2.0)
        ticks = s.ticks(1.0, 8.0)
        assert [v for v, _ in ticks] == pytest.approx([1.0, 2.0, 4.0, 8.0])

    def test_exact_power_upper_bound(self):
        # Guards against floating-point log10 error at exact powers.
        ticks = LogScale(10.0).ticks(1.0, 1000.0)
        assert [v for v, _ in ticks] == pytest.approx([1.0, 10.0, 100.0, 1000.0])

    def test_negative_range_raises(self):
        with pytest.raises(ValueError):
            LogScale(10.0).ticks(-1.0, 10.0)

    def test_zero_lower_bound_raises(self):
        with pytest.raises(ValueError):
            LogScale(10.0).ticks(0.0, 10.0)

    def test_non_positive_value_raises(self):
        with pytest.raises(ValueError):
            LogScale(10.0).to_world(0.0)

    def test_invalid_base_raises(self):
        with pytest.raises(ValueError):
            LogScale(1.0)


class TestMakeScale:
    def test_linear_string(self):
        assert isinstance(make_scale("linear"), LinearScale)

    def test_log_string_with_base(self):
        s = make_scale("log", base=2.0)
        assert isinstance(s, LogScale)
        assert s.base == 2.0

    def test_instance_passthrough(self):
        s = LinearScale()
        assert make_scale(s) is s

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            make_scale("sqrt")


class TestLogTicks:
    def test_log_ticks_helper(self):
        assert [v for v, _ in log_ticks(1.0, 100.0, 10.0)] == pytest.approx(
            [1.0, 10.0, 100.0]
        )
