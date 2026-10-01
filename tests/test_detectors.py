from __future__ import annotations

from backend.detection.concept_drift import ConceptDriftDetector
from backend.detection.data_quality import DataQualityChecker
from backend.detection.semantic_drift import detect_semantic_drift
from backend.detection.statistical_drift import StatisticalDriftDetector


def test_paper_psi_fixture_is_drifted():
    detector = StatisticalDriftDetector()
    score = detector._psi([1, 1, 1, 2, 2, 2], [100, 120, 150, 160, 170, 180])
    assert round(score, 4) == 13.1223
    assert detector.detect({"amount": [1, 1, 1, 2, 2, 2]}, {"amount": [100, 120, 150, 160, 170, 180]}).drifted_features == ["amount"]


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