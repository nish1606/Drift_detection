from __future__ import annotations


class FraudGovernanceError(Exception):
    """Base exception for the backend."""


class ValidationError(FraudGovernanceError):
    """Raised when request or data validation fails."""


class ModelUnavailableError(FraudGovernanceError):
    """Raised when a model artifact cannot be loaded."""


class PolicyViolationError(FraudGovernanceError):
    """Raised when a governance policy blocks an action."""


class DriftDetectedError(FraudGovernanceError):
    """Raised when drift exceeds the configured threshold."""


class NotFoundError(FraudGovernanceError):
    """Raised when a requested record is missing."""
