from __future__ import annotations

from run_experiments import governance_results


def test_all_paper_governance_cases_match_expected_decisions():
    results = governance_results()
    assert len(results) == 11
    assert all(result["matches"] for result in results)