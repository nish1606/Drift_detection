from __future__ import annotations

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except Exception:  # pragma: no cover - optional dependency
    DAG = None
    PythonOperator = None

from datetime import datetime, timedelta


def _monitor_drift():
    return "drift_checked"


if DAG is not None:
    with DAG(
        dag_id="fraud_drift_monitor_dag",
        start_date=datetime(2024, 1, 1),
        schedule="*/30 * * * *",
        catchup=False,
        default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    ) as dag:
        monitor = PythonOperator(task_id="monitor_drift", python_callable=_monitor_drift)
else:
    dag = None
