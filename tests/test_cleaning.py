from __future__ import annotations

import math

from backend.preprocessing.clean import clean_features
from backend.preprocessing.feature_engineering import FeatureEngineer


def test_clean_features_skips_none_and_float_nan():
    cleaned = clean_features({
        "amount": float("nan"),
        "velocity_1h": None,
        "geo_distance": float("nan"),
        "transaction_hour": 23,
        "new_device": True,
    })
    assert "amount" not in cleaned
    assert "velocity_1h" not in cleaned
    assert "geo_distance" not in cleaned
    assert cleaned["transaction_hour"] == 23.0
    assert cleaned["new_device"] == 1


def test_clean_features_keeps_infinities():
    cleaned = clean_features({"amount": math.inf, "geo_distance": -math.inf})
    assert math.isinf(cleaned["amount"])
    assert math.isinf(cleaned["geo_distance"])


def test_feature_engineer_drops_nan_values_without_raising():
    engineered = FeatureEngineer().build({
        "amount": float("nan"),
        "transaction_hour": float("nan"),
        "is_foreign": 1,
        "velocity_1h": float("nan"),
        "new_device": 0,
        "account_age_days": float("nan"),
        "avg_amount_last_30d": 800.0,
        "merchant_category": "travel",
        "geo_distance": float("nan"),
    })
    assert not any(isinstance(value, float) and math.isnan(value) for value in engineered.values())
    assert engineered["feature_count"] == 4.0
    assert engineered["numeric_count"] == 4.0
    assert engineered["amount_log"] == 0.0


def test_feature_engineer_nan_matches_missing_value_result():
    engineer = FeatureEngineer()
    with_nan = engineer.build({"amount": float("nan"), "transaction_hour": 23, "merchant_category": "travel"})
    with_none = engineer.build({"amount": None, "transaction_hour": 23, "merchant_category": "travel"})
    assert with_nan == with_none