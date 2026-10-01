"""Half-split PSI must split by row order and report per-feature missing drops."""
from __future__ import annotations

import numpy as np
import pandas as pd

from run_experiments import half_split_psi_results


def _frame(rows: int = 4000) -> pd.DataFrame:
    """Large halves: with 10 bins, PSI noise is ~k(k-1)/(2n), so small samples
    cannot distinguish a stable feature from a shifted one."""
    rng = np.random.default_rng(3)
    half = rows // 2
    frame = pd.DataFrame(
        {
            "amount": np.concatenate([rng.normal(100, 10, half), rng.normal(100, 10, half)]),
            "geo_distance": np.concatenate([rng.normal(50, 5, half), rng.normal(50, 5, half)]),
            "drifting": np.concatenate([rng.normal(0, 1, half), rng.normal(20, 1, half)]),
            "timestamp": np.arange(rows),
            "isFraud": np.zeros(rows, dtype=int),
        }
    )
    frame.loc[5:9, "amount"] = np.nan
    frame.loc[half + 20 : half + 24, "amount"] = np.nan
    return frame


def test_split_is_by_row_order():
    result = half_split_psi_results(_frame())
    assert result["split"].startswith("row order")
    amount = result["features"]["amount"]
    assert amount["referenceRows"] == 2000
    assert amount["currentRows"] == 2000


def test_timestamp_is_excluded():
    result = half_split_psi_results(_frame())
    assert "timestamp" in result["excludedFeatures"]
    assert "timestamp" not in result["features"]
    assert "isFraud" not in result["features"]


def test_missing_values_are_dropped_per_feature():
    amount = half_split_psi_results(_frame())["features"]["amount"]
    assert amount["referenceNonMissing"] == 1995
    assert amount["currentNonMissing"] == 1995
    assert amount["referenceRows"] == 2000


def test_a_feature_with_missing_values_does_not_shrink_others():
    features = half_split_psi_results(_frame())["features"]
    assert features["geo_distance"]["referenceNonMissing"] == 2000
    assert features["drifting"]["currentNonMissing"] == 2000


def test_a_real_shift_is_detected():
    features = half_split_psi_results(_frame())["features"]
    assert features["drifting"]["psi"] >= 0.2
    assert features["drifting"]["drifted"] is True
    assert "drifting" in half_split_psi_results(_frame())["driftedFeatures"]


def test_a_stable_feature_is_not_flagged():
    features = half_split_psi_results(_frame())["features"]
    assert features["geo_distance"]["psi"] < 0.1
    assert features["geo_distance"]["drifted"] is False


def test_overall_psi_is_the_mean_of_the_features():
    result = half_split_psi_results(_frame())
    expected = float(np.mean([item["psi"] for item in result["features"].values()]))
    assert result["overallPsi"] == round(expected, 6)


def test_is_reproducible():
    frame = _frame()
    assert half_split_psi_results(frame) == half_split_psi_results(frame)


def test_non_numeric_column_is_skipped():
    frame = _frame()
    frame["country"] = ["US"] * (len(frame) // 2) + ["NG"] * (len(frame) - len(frame) // 2)
    features = half_split_psi_results(frame)["features"]
    assert "country" not in features


def test_empty_half_returns_zero_not_a_crash():
    frame = pd.DataFrame({"amount": [1.0, 2.0, np.nan, np.nan], "isFraud": [0, 0, 0, 0]})
    amount = half_split_psi_results(frame)["features"]["amount"]
    assert amount["psi"] == 0.0
    assert amount["referenceNonMissing"] == 2
    assert amount["currentNonMissing"] == 0


def test_all_missing_column_is_skipped():
    frame = pd.DataFrame({"amount": [np.nan, np.nan, np.nan, np.nan], "isFraud": [0, 0, 0, 0]})
    assert "amount" not in half_split_psi_results(frame)["features"]


def test_values_beyond_the_reference_maximum_are_not_discarded():
    """Current values above the reference maximum must count in the top bin."""
    from backend.detection.statistical_drift import StatisticalDriftDetector

    reference = np.linspace(0.0, 1.0, 2000)
    current = np.concatenate([reference, np.full(2000, 50.0)])
    detector = StatisticalDriftDetector()
    assert detector._psi(reference, current) > 0.2