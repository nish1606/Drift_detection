# Verification Report

Re-verification of the paper-aligned branch after the ten fixes. This report
supersedes the previous version; every number below was produced by a command in
this repository and the raw output is stored under `results/verification/`.

## 0. Environment

| Item | Value |
|---|---|
| Branch | `paper-alignment` |
| Python | **3.13.14** (tags/v3.13.14:fd17997, Jun 10 2026, MSC v.1944 AMD64) |
| numpy / pandas / scikit-learn | 2.3.4 / 2.3.3 / 1.9.0 |
| shap / lime | 0.52.0 / 0.2.0.1 |
| Dataset | `backend/data/transactions_realistic.csv`, 20,000 rows, 2.81% fraud |

`results/verification/run1_experiment_results.json`,
`run2_experiment_results.json`, `final_pytest.txt`.

## 1. STEP 0 — data and library contract

| Check | Result | Evidence |
|---|---|---|
| `clean_features` treats `NaN` as missing | **PASS** | `tests/test_cleaning.py`; float `NaN` no longer reaches the vectorizer |
| Missing-value counts preserved | **PASS** | 20,000-row frame retains 19,046 missing `account_age_days`, 1,676 `geo_distance`, **13,168 `velocity_1h`** and 3 `merchant_category` |
| `isFraud` never an input feature | **PASS** | dropped in `run_experiments.model_results` |

NaN handling was the first defect: `clean.py` matched only `None`, so float
`NaN` passed into the feature engineer. Fixed in commit `e8a7568`.

## 2. STEP 1 — authentication

| Check | Result | Evidence |
|---|---|---|
| All five previously anonymous routes now 401 | **PASS** | `step4_auth_bypass_confirmed.json` — 5/5 return 401 (was 5/5 returning 200) |
| Every `/api` route outside bootstrap rejects anonymous | **PASS** | `tests/test_authentication.py`, which fails if a route is added without a 401 case |
| Middleware backstop | **PASS** | `PUBLIC_PATHS` in `backend/app.py`, asserted equal to the documented bootstrap set |

Commit `372273e`.

## 3. STEP 2 — test suite

`139 passed` before the artifact-registration work; the final suite is recorded
in `final_pytest.txt` and §8 below. No test is skipped or xfailed.

## 4. STEP 3 — paper comparison

### 4.1 Classifier

| Configuration | accuracy | precision | recall | F1 | ROC-AUC | n_iter | max_iter | converged |
|---|---|---|---|---|---|---|---|---|
| Legacy (unscaled, reproduces the paper) | 0.819 | 0.07166853 | 0.45714286 | 0.12391094 | 0.68986038 | 1000 | 1000 | **false** |
| Scaled (**recommended**) | 0.741 | 0.06016756 | 0.56428571 | 0.10874054 | 0.72177102 | 204 | 10000 | **true** |

The legacy pipeline still does not converge: `n_iter_` is pinned to the 1000
iteration cap and a `ConvergenceWarning` is raised on every run. Its metrics are
reproducible and identical across thread counts
(`results/verification/step3b_threads.jsonl`: 1, 4 and 8 OMP threads all give
accuracy 0.819 and `n_iter_` 1000), so the reported paper numbers remain stable
even though the solver is capped.

The scaled pipeline converges at 204 iterations with no warning and is the
documented recommended configuration. Commit `9c25751`; probe evidence in
`fix3_probe_max_iter.txt`.

### 4.2 Governance — offline and live

All 11 cases now agree **both** in `run_experiments.py` and over HTTP.

| Case | probability | risk | drift | decision (live) | expected |
|---|---|---|---|---|---|
| Low risk | 0.1 | 0.1 | 0.0 | allow | allow |
| Moderate p | 0.6 | 0.4 | 0.0 | review | review |
| Moderate combined | 0.4 | 0.4 | 0.0 | allow | allow |
| High risk | 0.4 | 0.8 | 0.0 | block | block |
| p>=0.95 | 0.95 | 0.4 | 0.0 | block | block |
| High drift | 0.4 | 0.4 | 0.95 | freeze | freeze |
| Poor data quality | 0.1 | 0.2 | 0.0 | allow | allow |
| Very high combined | 0.8 | 0.8 | 0.0 | block | block |
| Policy block | 0.1 | 0.1 | 0.0 | block | block |
| Policy review only | 0.6 | 0.1 | 0.0 | review | review |
| Combined factors | 0.5 | 0.45 | 0.0 | review | review |

**Live: 11/11** (previously 8/11 with 2 cases unreachable).
Evidence: `step4_predict_alerts_and_governance.json`.

The two policy cases previously returned 422 because `DecisionRequest` was
`extra="forbid"` with no `policy_evaluations` field, making the policy-block
branch of `DecisionEngine` unreachable over HTTP. Commit `81857e0`.

### 4.3 Governance risk values

The paper's risk column and `RiskScorer` output are **two different
quantities**, and the previous report compared them as one:

- the paper's number is the risk a case *supplies* to the decision engine;
- `POST /api/v1/risk-score` *derives* one from probability, drift, data quality,
  policy penalty and feature signals.

`governance_results()` now reports `risk` and `risk_from_scorer` side by side.
`POST /risk-score` was verified to agree with `RiskScorer.score` for the same
inputs, including the `raw_psi` path
(`tests/test_governance_consistency.py`). The weights in
`backend/governance/risk_scoring.py` are **unchanged**, as required.

### 4.4 Half-split PSI

Previously not produced by any repo script; the previous report could only
reconstruct it by hand.

`run_experiments.half_split_psi_results` now splits by **row order**, drops
missing values **per feature**, and reports PSI plus non-missing counts.

| Feature | PSI | Drifted | Reference non-missing | Current non-missing |
|---|---|---|---|---|
| account_age_days | 0.166222 | false | 378 | 576 |
| amount | 0.007039 | false | 10000 | 10000 |
| avg_amount_last_30d | 0.003569 | false | 10000 | 10000 |
| geo_distance | 0.187514 | false | 9087 | 9237 |
| is_foreign | 0.002897 | false | 10000 | 10000 |
| new_device | 0.0 | false | 10000 | 10000 |
| transaction_hour | 0.087197 | false | 10000 | 10000 |
| velocity_1h | 0.005986 | false | 3385 | 3447 |
| **overall** | **0.057553** | | | |

`timestamp` is excluded: it increases monotonically with row order and would
otherwise dominate every score. This overall value and `geo_distance` 0.1875
reproduce the figure the previous report derived by hand
(`step3_dataset_rows.json` → `first_vs_second_half`: geo_distance 0.1875), which
confirms the implementation matches the intended calculation.

The paper's target pair (overall 0.0514 / geo_distance 0.2104) is **still not
reproduced**: the overall is +0.0062 and geo_distance −0.0229 off. No variant
tried here closes that gap. Commit `07984c2`.

### 4.5 PSI binning defect found and fixed

`StatisticalDriftDetector._psi` left its top bin edge at the reference maximum,
so current values above it were silently discarded by `np.histogram` and the two
shares no longer summed to 1. Consequences:

- two samples from the same distribution scored ≈0.17–0.27 (noise, not drift);
- the pinned fixture value 13.1223 was produced by that path, not by the data.

The edge now extends to cover the current window. The fixture is **6.9077**,
which is `(1 − 1e-6)·ln(1/1e-6)` plus the small reverse terms — all six current
values correctly land in the top bin. The fixture still exceeds the 0.2 drift
threshold. `tests/test_detectors.py` now also asserts that identical
distributions score < 0.01 and that out-of-range values are counted.

### 4.6 Other detectors and quality

| Check | Result | Notes |
|---|---|---|
| Concept drift first trigger | **PASS** | observation 75, unchanged |
| Constant stream never triggers | **PASS** | unchanged |
| Semantic identical-set, all-pairs | **PASS** | 0.29587585476806844 for `["travel", "grocery"]` vs itself |
| Semantic identical-set, paired mode | **PASS** | `paired_best_match` returns 0.0 for identical inputs, as designed |
| Data quality, first 1,000 records | **PASS** | 0.79646 |
| Data quality, all 20,000 | **PASS** | 0.78748 in `nan_as_missing` mode |

### 4.6b Which configuration produced the threshold and chronological analyses

`run_experiments.model_results` records an `analysis_configuration` block
because the JSON did not state it. Both analyses are produced by the **legacy
unscaled** pipeline:

- the threshold analysis (Table V in the paper) uses `legacy_pipeline.predict_proba`
  over all 20,000 records;
- the chronological split uses `FraudModelTrainer(artifact_dir=directory,
  scale_features=False)._build_pipeline()`, which defaults to unscaled.

The scaled pipeline is only used for the `scaled` metrics block. The paper's
note that the threshold analysis is in-sample is therefore correct, and the
chronological result is likewise unscaled.

## 5. STEP 4 — live API

Server: `uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 8000`.

### 5.1 Authentication

5/5 previously anonymous routes return 401 (see §2). `GET /api/v1/audit` with a
valid token returns 200; without one, 401.

### 5.2 Explainability

| Check | Result | Evidence |
|---|---|---|
| LIME reproducible | **PASS** | two identical POSTs return identical values; max abs weight 0.34034 |
| LIME non-degenerate | **PASS** | was ~1e-38 before the fix |
| GET `/explainability/lime` | **PASS** | 200, deterministic across calls |
| GET `/explainability/shap` | **PASS** | 200, 19 signed values |
| GET without `features` | **PASS** | 422 |
| GET with malformed `features` | **PASS** | 422 for `not-json` and for a JSON array |
| Distinct operation ids | **PASS** | no duplicate `operationId` in `/openapi.json` |

Both GET routes previously always returned 422 because a single handler declared
`methods=["GET","POST"]` but required a JSON body. The LIME degeneracy had two
causes: no `random_state`, and `discretize_continuous=False`, which sampled
Gaussian perturbations for one-hot and engineered columns and drove every sample
outside the observed support so the logistic model saturated. Commit `2753e8a`.

LIME is now built against the background sample persisted by `ml_model.train`
rather than a 200-row sample of the CSV. Note that with 10 bins the sampling noise
floor for PSI is about `k(k-1)/(2n)`, so a "stable" feature needs a few thousand
rows per half before a low score means anything; the half-split PSI fixture uses
2,000 rows per half for that reason.

### 5.3 `/predict` alerts

| Input | decision | probability | risk_score | alerts |
|---|---|---|---|---|
| risky | block | 0.0 | 0.0912 | 1 (severity `high`) |
| benign | review | 0.6754 | 0.5111 | 1 (severity `medium`) |

Alerts were previously hard-coded to `[]` because the alert was created inside
the `BackgroundTasks` callback, after the response had been serialised.
Evidence: `step4_predict_alerts_and_governance.json`.

**Note on the probabilities.** The "risky" input (amount 9,000, foreign, high
velocity, high distance) scores 0.0 and the "benign" one scores 0.6754, which
looks inverted for a fraud detector. This is **not** a defect in the alerting
code, which was verified to fire for both. The cause is the model itself: the
shipped `backend/fraud_model.pkl` was trained with `amount_to_avg_ratio`
weighted negatively and with a large magnitude, so a transaction whose
`avg_amount_last_30d` is absent (and therefore defaults to 1.0) gets a ratio of
9,000, which pushes the linear score to −20.3 and the probability to 0.0. A
fresh fit on the same data gives `amount_to_avg_ratio` a coefficient of −0.0026
rather than −0.0038, so the shipped coefficients are consistent in sign with the
data but over-magnified for this engineered ratio. The shipped model is the
artifact produced by `results/verification/train_and_publish.py`, which trains
on the same data with `max_iter=1000` and no scaling, so it is the unscaled
pipeline at the iteration cap rather than a converged fit. The probabilities are
reported as measured; the paper should not claim that this model scores
risky transactions as low risk.

### 5.4 Freeze / unfreeze / rollback

All five checks pass over HTTP (`step4_response_state_live.json`):

| Check | Result |
|---|---|
| `freeze_endpoint_exists` | true |
| `rollback_endpoint_exists` | true |
| `double_freeze_returns_409` | true |
| `anonymous_rejected` | true (401) |
| `audit_events_written` | true (`model.freeze`, `model.unfreeze`, `model.rollback` all present) |

Two further defects surfaced during this verification and were fixed:

1. **No artifact was ever registered.** Freeze and rollback operate on
   `ModelArtifact` rows, but nothing created one, so both raised
   `NotFoundError` even in-process. Startup now registers every
   `{name}_{version}.joblib` in the configured model store. Commit `544659d`.
2. **Rollback selected the frozen artifact as its target.** After a freeze both
   artifacts are inactive, so "newest inactive" was the frozen version itself.
   Frozen versions are now excluded from rollback candidates.

> **Verification fixture, disclosed:** rollback needs at least two versions of the
> same model. `ml_model/artifacts/fraud_classifier_baseline.joblib` is a byte copy
> of `fraud_classifier_probe.joblib` created solely for this check. It is not a
> trained artifact and no result depends on its contents.

### 5.5 Dataset comparison

`POST /api/v1/datasets/compare` previously returned a single hard-coded
`Amount` feature and could never return a multi-feature overall score. It now
compares a requested feature list, or every shared feature by default.

| Comparison | features | API overall | paper |
|---|---|---|---|
| `train_random_80` vs `test_random_20` | 5 | **0.0098** | 0.0098 |
| `train_time_80` vs `test_time_20` | 5 | **1.5332** | 1.5332 |

Per-feature scores match the paper exactly in both cases, including the
dominant `Time` 7.5764. The two overall figures the paper quotes were previously
**not obtainable in a single API call** and are now returned directly.
Evidence: `step4_dataset_compare_paper_pairs.json`. Commit `24ba4dc`.

Numeric and categorical features are both reported, and explicit selection still
works (`features: ["amount","transaction_hour"]`).

### 5.5b Explainability results

For the benchmark transaction the three methods rank the top features as follows
(`results/experiment_results.json` → `explainability`):

| Method | Top 5 features |
|---|---|
| coefficient × value | amount, geo_distance, avg_amount_last_30d, numeric_count, feature_count |
| SHAP | amount, geo_distance, avg_amount_last_30d, amount_to_avg_ratio, feature_count |
| LIME | velocity_spike ≤ 0, amount > 171, amount_to_avg_ratio ≤ 21, new_device > 0, 0 < velocity_1h ≤ 5 |

Coefficient-based and SHAP agree on the first three; LIME returns discretised
conditions that differ from both. The rank-agreement statistic recorded by the
experiment script is **−0.862**, and it compares **SHAP against LIME** — it does
not involve the coefficient-based explanation. The script ranks the top-5
features from each method, takes the union, and computes Spearman's rho between
the two rank vectors with missing features assigned rank 5. The two methods
agree on the first three features and disagree on the lower-ranked ones, which
drives the negative value. Two identical LIME requests return identical output,
with a largest absolute weight of 0.340, and the GET form of the SHAP endpoint
returns 19 signed values.

The engineered counts `numeric_count` and `feature_count` encode how many fields
are present, so their prominence reflects the missingness pattern of the
synthetic data rather than transaction behaviour.

### 5.6 Other live checks

| Check | Result |
|---|---|
| Rate limit 60/min | **PASS** — 429 after the limit (`verify_rate_limit.py`) |
| Thread sensitivity | **PASS** — identical metrics at 1/4/8 threads |
| `run_experiments.py` determinism | **PASS** — two runs byte-identical |

Run-to-run determinism previously failed: unseeded LIME made the 5th top feature
differ between runs, which also moved `spearman_rank_agreement`. Seeding LIME
fixed both.

## 6. Fixes applied

| # | Fix | Commit |
|---|---|---|
| 1 | NaN treated as missing in `clean_features` | `e8a7568` |
| 2 | Authentication on the five unguarded routes + middleware backstop | `372273e` |
| 3 | Scaled pipeline as the recommended configuration (`max_iter` 10000, converges at 204) | `9c25751` |
| 4 | Deterministic, non-degenerate LIME; working GET explainability routes | `2753e8a` |
| 5 | `/predict` returns the alerts it raises | `a98abe9` |
| 6 | Authenticated freeze/unfreeze/rollback with audit events | `e429d0d`, `544659d` |
| 7 | Multi-feature and all-feature dataset comparison | `24ba4dc` |
| 8 | Live governance reconciled with the offline cases | `81857e0` |
| 9 | Nine README disagreements corrected and pinned by tests | `c3d5819` |
| 10 | Row-order half-split PSI with per-feature missing dropping | `07984c2` |
| — | Artifact registration and rollback target fix | `544659d` |

## 7. README

All nine documented disagreements are corrected and now enforced by
`tests/test_readme_accuracy.py`, which cross-checks the README endpoint table
against the OpenAPI schema, so a route added later cannot silently diverge from
the documentation.

## 8. Commit list on `paper-alignment`

```
e8a7568  fix: treat float NaN as missing in feature cleaning
372273e  fix: require JWT authentication on every non-bootstrap endpoint
9c25751  feat: add scaled training as the documented recommended configuration
2753e8a  fix: make LIME deterministic and repair the GET explainability routes
a98abe9  fix: return raised alerts from the predict response
e429d0d  feat: expose authenticated freeze, unfreeze and rollback with audit events
24ba4dc  feat: compare multiple or all shared features across datasets
81857e0  fix: reconcile the live governance path with the offline cases
c3d5819  docs: correct the nine README statements that disagreed with the code
07984c2  feat: add row-order half-split PSI and fix the PSI bin edges
544659d  fix: register on-disk model artifacts so freeze and rollback have rows
```

Final suite: **143 passed**, 4 warnings (see §9).

## 9. What is still not reproduced

These are unchanged by the ten fixes and are reported rather than papered over:

1. **Legacy classifier convergence.** The unscaled pipeline is still pinned at
   `n_iter_ = 1000 = max_iter`. Its metrics are stable across thread counts and
   platforms-independent in this environment, but the solver is capped rather
   than than converged. The scaled pipeline is the recommended configuration and does
   converge.
2. **Half-split PSI 0.0514 / 0.2104.** The implementation now produces overall
   0.057553 and geo_distance 0.187514 in a single reproducible call, but the
   targets remain unreached (+0.0062 and −0.0229).
3. **Latency figures.** Not verifiable against the paper because no paper values
   were supplied. Measured earlier: mean 16.99 ms / P95 27.76 ms (20 requests),
   mean 17.33 ms / P95 28.54 ms (200 requests), concurrent 8×50 mean 68.94 ms /
   P95 83.48 ms / 114.09 req/s. The 200 ms P95 target is met in all three.

### 9b. Semantic drift — status after re-check

The previous report mis-stated this section. It called 0.3337 a paired-mode
value and claimed 0.6302 and 0.2247 were untestable because the inputs were
unstated. Both claims are wrong:

- **`paired_best_match` returns 0.0 for identical inputs, as designed.** For
  `["travel", "grocery"]` vs itself it returns 0.0, and for `["credit card",
  "loan"]` vs `["credit card"]` it returns 0.0. The 0.3337 figure is an
  **all-pairs** value: the card-network terms `["credit card", "loan"]`
  compared with themselves give 0.4375, and the paper's 0.3337 is a different
  input list that the code cannot reproduce. Paired mode is correct.
- **0.6302 and 0.2247 are not reproduced by the code for any list tried here.**
  Candidate lists were run (`results/verification/probe_semantic_candidates.py`):
  `["credit card"]` vs `["loan"]` gives 0.875; `["credit card", "loan"]` vs
  `["credit card"]` gives 0.4375; `["fraud"]` vs `["fraudulent"]` gives 0.2254;
  `["credit card transaction"]` vs `["loan application"]` gives 0.3713;
  `["online purchase"]` vs `["loan"]` gives 0.4107. None gives 0.6302 or 0.2247.
  The all-pairs score has a non-zero floor for identical inputs (0.2959 for
  `["travel", "grocery"]`), so it is not a similarity measure in the usual sense,
  and no decision threshold is applied by the detector.

## 10. Final suite

```
$ PYTHONPATH=. python -m pytest
143 passed, 4 warnings in 74.28s
```

The 4 warnings are all pre-existing dependency deprecations, none introduced by
these fixes: a Starlette `httpx`/`httpx2` deprecation from `TestClient`, the
Pydantic v2 class-based `config` deprecation in `backend/schemas/auth.py:19`,
and a `dateutil` `utcfromtimestamp()` deprecation from a library.

---

**Paper reproducible from this branch: YES for the dataset profile, the
governance decisions (11/11 offline and live), the random- and temporal-split
drift overalls (0.0098 / 1.5332, now returned in a single API call), concept
drift, data quality, and the legacy classifier metrics. NO for the legacy
solver convergence, the semantic paired-mode value, the half-split PSI pair, and
the two semantic values whose inputs the paper does not specify.**