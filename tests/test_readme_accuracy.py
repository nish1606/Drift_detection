"""README statements must match what the code actually does."""
from __future__ import annotations

import re

import pytest

from backend.app import PUBLIC_PATHS, create_app


@pytest.fixture(scope="module")
def routes(tmp_path_factory) -> dict[str, set[str]]:
    from backend.core.config import Settings

    settings = Settings(
        database_url=f"sqlite:///{tmp_path_factory.mktemp('readme') / 'fraud.db'}",
        model_store_path=str(tmp_path_factory.mktemp("artifacts")),
        policies_path="backend/governance/policies",
    )
    paths = create_app(settings).openapi()["paths"]
    return {path: {method.upper() for method in operations} for path, operations in paths.items()}


def _readme() -> str:
    from pathlib import Path

    return (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


def _documented_endpoint_rows() -> list[tuple[str, str, str]]:
    """(path, methods, auth) for each row of the README API table."""
    rows = []
    for line in _readme().splitlines():
        match = re.match(r"^\|\s*`(/api/v1[^`]*)`\s*\|\s*`([A-Z, ]+)`\s*\|\s*(Yes|No)\s*\|", line)
        if match:
            rows.append((match.group(1), match.group(2), match.group(3)))
    return rows


def test_endpoint_table_has_no_duplicate_rows():
    rows = _documented_endpoint_rows()
    assert len(rows) > 20
    assert len(rows) == len(set(rows)), [row for row in rows if rows.count(row) > 1]


def _match_route(routes: dict[str, set[str]], documented: str) -> str | None:
    """Prefer an exact path, then a template path with the same literal segments."""
    if documented in routes:
        return documented
    literals = documented.split("{")
    for path in routes:
        if path.split("{") == literals:
            return path
    return None


def test_every_documented_endpoint_exists(routes):
    missing = []
    for path, methods, _ in _documented_endpoint_rows():
        actual = _match_route(routes, path)
        if actual is None:
            missing.append(path)
            continue
        for method in methods.split(","):
            assert method.strip() in routes[actual], f"{path} does not support {method.strip()}"
    assert not missing, missing


def test_response_endpoints_are_documented(routes):
    documented = {path for path, _, _ in _documented_endpoint_rows()}
    for path in routes:
        if "/models/" in path and "/api/v1" in path:
            assert path in documented, f"{path} is implemented but undocumented"


def test_auth_column_matches_public_paths(routes):
    public = {path.split("{")[0].rstrip("/") for path in PUBLIC_PATHS}
    for path, _, auth in _documented_endpoint_rows():
        if path.split("{")[0].rstrip("/") in public:
            assert auth == "No", f"{path} is public but documented as {auth}"
        else:
            assert auth == "Yes", f"{path} requires auth but documented as {auth}"


def test_readme_documents_the_bootstrap_paths_exactly():
    readme = _readme()
    assert "/health" in readme and "/ready" in readme and "/auth/login" in readme and "/auth/register" in readme
    assert "bootstrap" in readme


def test_readme_documents_oauth2_form_encoding_for_login():
    readme = _readme().lower()
    assert "application/x-www-form-urlencoded" in readme


def test_readme_requires_both_requirements_files():
    readme = _readme()
    assert "pip install -r requirements.txt -r backend/requirements.txt" in readme


def test_readme_states_freeze_and_rollback_are_wired():
    readme = _readme()
    assert "/api/v1/models/{model_name}/freeze" in readme
    assert "/api/v1/models/{model_name}/rollback" in readme


def test_readme_does_not_claim_untouched_artifacts():
    readme = _readme()
    assert "`fraud_model.pkl`" not in readme
    assert "{model_name}_{model_version}.joblib" in readme


def test_readme_disambiguates_the_lockfiles():
    readme = _readme()
    assert "NOT the frontend one" in readme
    assert "frontend/package-lock.json" in readme


def test_readme_documents_multi_feature_dataset_compare():
    assert "every shared feature" in _readme()