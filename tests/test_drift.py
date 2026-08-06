from __future__ import annotations

from backend.detection.concept_drift import ConceptDriftDetector
from backend.detection.data_quality import DataQualityChecker
from backend.detection.semantic_drift import detect_semantic_drift
from backend.detection.statistical_drift import StatisticalDriftDetector


def test_statistical_drift_detects_shift():
    detector = StatisticalDriftDetector(threshold=0.05)
    result = detector.detect({"amount": [1, 1, 1, 2, 2, 2]}, {"amount": [100, 120, 150, 160, 170, 180]})
    assert result.drift_score >= 0.0
    assert "amount" in result.drifted_features


def test_concept_drift_threshold():
    detector = ConceptDriftDetector(threshold=0.05, min_samples=3)
    drifted = False
    for error in [0.05, 0.05, 0.05, 0.3, 0.35, 0.4]:
        drifted = detector.update(error) or drifted
    assert drifted


def test_semantic_drift_returns_score():
    drift = detect_semantic_drift(["fraud review required"], ["manual review needed"])
    assert 0.0 <= drift <= 1.0


def test_data_quality_checker_reports_issues():
    result = DataQualityChecker().evaluate([{"amount": 1}, {"amount": None}, {"amount": 1000}])
    assert result.score <= 1.0
    assert result.issues
