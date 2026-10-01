from __future__ import annotations


def drift_signal_from_psi(psi: float) -> float:
    """Convert a raw PSI value to governance drift using min(1, PSI)."""
    return min(1.0, max(0.0, float(psi)))