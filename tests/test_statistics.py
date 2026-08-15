import math

import pytest

from performance_lab.performance import summarize_distribution


def test_tiny_sample_percentiles_are_qualified_as_unavailable() -> None:
    summary = summarize_distribution([10.0, 20.0, 30.0])
    assert summary.sample_count == 3
    assert summary.median == 20.0
    assert summary.p90.qualified is False
    assert summary.p90.value is None
    assert "at least 10" in (summary.p90.qualification or "")
    assert summary.p95.qualified is False


def test_percentiles_are_reported_when_sample_size_justifies_them() -> None:
    values = [float(value) for value in range(1, 21)]
    summary = summarize_distribution(values)
    assert summary.p90.qualified
    assert summary.p90.value == pytest.approx(18.1)
    assert summary.p95.qualified
    assert summary.p95.value == pytest.approx(19.05)
    assert summary.raw_values == tuple(values)


def test_dispersion_and_coefficient_of_variation_are_preserved() -> None:
    summary = summarize_distribution([1.0, 2.0, 3.0, 4.0])
    assert summary.mean == 2.5
    assert summary.stddev > 0
    assert summary.coefficient_of_variation is not None
    assert summary.minimum == 1.0
    assert summary.maximum == 4.0


def test_zero_mean_has_no_coefficient_of_variation() -> None:
    summary = summarize_distribution([-1.0, 1.0])
    assert summary.mean == 0.0
    assert summary.coefficient_of_variation is None


def test_non_finite_or_empty_samples_are_rejected() -> None:
    with pytest.raises(ValueError):
        summarize_distribution([])
    with pytest.raises(ValueError):
        summarize_distribution([1.0, math.inf])
