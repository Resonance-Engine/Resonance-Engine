"""Experiment tracking — MLflow or W&B integration for model versioning."""


def log_experiment(
    experiment_name: str,
    params: dict,
    metrics: dict,
    artifacts: list[str] | None = None,
) -> str:
    """Log an experiment run with parameters, metrics, and artifacts.

    Returns: run_id

    TODO: Phase 0 deliverable — choose MLflow vs W&B and implement
    """
    raise NotImplementedError("Experiment tracking — Phase 0 deliverable")
