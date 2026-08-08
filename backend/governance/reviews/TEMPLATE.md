# Governance Review: [Rule / Policy Name]

## Metadata
- **Rule ID:** `RULE-001`
- **Status:** `draft` | `active` | `deprecated`
- **Owner:** Risk Engineering / Compliance
- **Effective Date:** YYYY-MM-DD
- **Review Cadence:** Monthly / Quarterly

## Objective
One-paragraph description of what this rule is meant to prevent or enforce.

## Scope
- **Model versions covered:** v1.0, v1.1
- **Transaction segments:** card-present, card-not-present
- **Geography:** US, CA, EU

## Thresholds & Parameters
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Drift threshold (PSI) | `0.25` | Based on historical backtesting |
| Confidence floor | `0.70` | Minimum acceptable AUC |
| Fairness delta (DP) | `0.10` | Regulatory guidance |

## Testing & Validation
- [ ] Historical backtest completed
- [ ] Shadow-mode evaluation passed
- [ ] Bias/fairness report reviewed
- [ ] False-positive impact assessed

## Sign-off
| Role | Name | Signature | Date |
|------|------|-----------|------|
| Risk Engineer | | | |
| Compliance | | | |
| Data Scientist | | | |

## Change Log
- YYYY-MM-DD — Initial draft by [Name]
