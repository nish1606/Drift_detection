from __future__ import annotations

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except Exception:  # pragma: no cover - optional dependency
    DAG = None
    PythonOperator = None

from datetime import datetime, timedelta

from backend.response.retraining import RetrainingService


def _trigger_retraining():
    return "retraining_triggered"


if DAG is not None:
    with DAG(
        dag_id="fraud_retraining_dag",
        start_date=datetime(2024, 1, 1),
        schedule="0 2 * * *",
        catchup=False,
        default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
    ) as dag:
        trigger = PythonOperator(task_id="trigger_retraining", python_callable=_trigger_retraining)
else:
    dag = None
