from __future__ import annotations

from typing import Any


def build_grad_cam_attribution(prediction_result: Any) -> dict[str, object]:
    """Return a Grad-CAM-style heatmap payload for the tabular fraud model.

    CNN Grad-CAM uses spatial gradients; this project has tabular features, so
    the existing local feature attributions are normalized into heat values.
    """
    pairs = prediction_result.explanations.get("top_features", [])
    raw_attributions = []
    for pair in pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        try:
            value = float(pair[1])
        except (TypeError, ValueError):
            continue
        raw_attributions.append((str(pair[0]), value))

    maximum = max((abs(value) for _, value in raw_attributions), default=1.0)
    attributions = [
        {
            "feature": feature,
            "value": round(value, 6),
            "heat": round(abs(value) / maximum, 6),
            "direction": "increases_fraud_score" if value >= 0 else "decreases_fraud_score",
        }
        for feature, value in raw_attributions
    ]
    return {
        "method": "tabular_grad_cam",
        "model_name": prediction_result.model_name,
        "model_version": prediction_result.model_version,
        "prediction": prediction_result.prediction,
        "probability": prediction_result.probability,
        "baseline": round(1.0 - prediction_result.probability, 6),
        "attributions": attributions,
    }
