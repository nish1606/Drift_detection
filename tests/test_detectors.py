from __future__ import annotations

import numpy as np

from backend.detection.concept_drift import ConceptDriftDetector
from backend.detection.data_quality import DataQualityChecker
from backend.detection.semantic_drift import detect_semantic_drift
from backend.detection.statistical_drift import StatisticalDriftDetector


def test_paper_psi_fixture_is_drifted():
    detector = StatisticalDriftDetector()
    score = detector._psi([1, 1, 1, 2, 2, 2], [100, 120, 150, 160, 170, 180])
    # The current window lies entirely above the reference maximum, so all six
    # values fall in the top bin: (1 - 1e-6) * ln(1 / 1e-6) with the remaining
    # bins contributing their small reverse terms, i.e. 6.9077. The previous
    # 13.1223 came from the top edge being left at the reference maximum, which
    # discarded every current value and scored unnormalised shares.
    assert round(score, 4) == 6.9077
    assert score >= 0.2
    assert detector.detect({"amount": [1, 1, 1, 2, 2, 2]}, {"amount": [100, 120, 150, 160, 170, 180]}).drifted_features == ["amount"]


def test_identical_distributions_have_near_zero_psi():
    detector = StatisticalDriftDetector()
    rng = np.random.default_rng(0)
    reference = rng.normal(100, 10, 2000)
    current = rng.normal(100, 10, 2000)
    assert abs(detector._psi(reference, current)) < 0.01


def test_current_values_above_the_reference_maximum_are_counted():
    detector = StatisticalDriftDetector()
    reference = np.linspace(0.0, 1.0, 2000)
    assert detector._psi(reference, np.concatenate([reference, np.full(2000, 50.0)])) > 0.2


def test_concept_drift_first_triggers_at_observation_75():
    detector = ConceptDriftDetector()
    triggers = [index for index, value in enumerate([0.05] * 30 + [0.30] * 45, 1) if detector.update(value)]
    assert triggers[0] == 75


def test_constant_concept_stream_never_triggers():
    detector = ConceptDriftDetector()
    assert not any(detector.update(0.05) for _ in range(75))


def test_nan_missing_modes():
    records = [{"value": float("nan")}, {"value": 1.0}]
    assert DataQualityChecker(treat_nan_as_missing=False).evaluate(records).score > DataQualityChecker(treat_nan_as_missing=True).evaluate(records).score


def test_paired_semantic_drift_identical_sets_is_zero():
    assert detect_semantic_drift(["travel", "grocery"], ["travel", "grocery"], mode="paired_best_match") == 0.0