"""Experiment tracking — lightweight JSON-file tracker for Phase 0.

Logs experiments with parameters, metrics, and artifact paths to a local
JSON file. Designed to be swapped for MLflow or W&B in Phase 1 without
changing the calling code interface.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Default storage location
EXPERIMENTS_DIR = Path("data/experiments")


@dataclass
class ExperimentRun:
    """A single experiment run with parameters, metrics, and artifacts."""

    run_id: str
    experiment_name: str
    params: dict
    metrics: dict
    artifacts: list[str]
    timestamp: str
    tags: dict = field(default_factory=dict)


def log_experiment(
    experiment_name: str,
    params: dict,
    metrics: dict,
    artifacts: list[str] | None = None,
    tags: dict | None = None,
    storage_dir: Path | None = None,
) -> str:
    """Log an experiment run with parameters, metrics, and artifacts.

    Args:
        experiment_name: Name of the experiment (e.g., "finbert_sentiment_v1").
        params: Hyperparameters and configuration used.
        metrics: Evaluation metrics (e.g., {"f1": 0.72, "brier_score": 0.18}).
        artifacts: Paths to saved model files, plots, etc.
        tags: Optional key-value tags for filtering.
        storage_dir: Override the default experiments directory.

    Returns:
        run_id: UUID of the logged experiment run.
    """
    run_id = str(uuid.uuid4())
    base_dir = storage_dir or EXPERIMENTS_DIR
    base_dir.mkdir(parents=True, exist_ok=True)

    run = ExperimentRun(
        run_id=run_id,
        experiment_name=experiment_name,
        params=params,
        metrics=metrics,
        artifacts=artifacts or [],
        timestamp=datetime.now(timezone.utc).isoformat(),
        tags=tags or {},
    )

    # Save individual run file
    run_file = base_dir / f"{experiment_name}_{run_id[:8]}.json"
    run_file.write_text(json.dumps(asdict(run), indent=2, default=str))

    # Append to experiment index
    index_file = base_dir / "index.json"
    index = _load_index(index_file)
    index.append({
        "run_id": run_id,
        "experiment_name": experiment_name,
        "timestamp": run.timestamp,
        "metrics": metrics,
    })
    index_file.write_text(json.dumps(index, indent=2, default=str))

    logger.info("Logged experiment %s run %s: %s", experiment_name, run_id[:8], metrics)
    return run_id


def get_experiment(
    run_id: str,
    storage_dir: Path | None = None,
) -> ExperimentRun | None:
    """Retrieve a specific experiment run by ID.

    Args:
        run_id: UUID of the experiment run.
        storage_dir: Override the default experiments directory.

    Returns:
        ExperimentRun if found, None otherwise.
    """
    base_dir = storage_dir or EXPERIMENTS_DIR
    if not base_dir.exists():
        return None

    # Search for the run file
    prefix = run_id[:8]
    for f in base_dir.glob(f"*_{prefix}.json"):
        data = json.loads(f.read_text())
        if data.get("run_id") == run_id:
            return ExperimentRun(**data)

    return None


def list_experiments(
    experiment_name: str | None = None,
    storage_dir: Path | None = None,
) -> list[dict]:
    """List all experiment runs, optionally filtered by name.

    Args:
        experiment_name: Filter by experiment name.
        storage_dir: Override the default experiments directory.

    Returns:
        List of experiment summary dicts (run_id, name, timestamp, metrics).
    """
    base_dir = storage_dir or EXPERIMENTS_DIR
    index_file = base_dir / "index.json"
    index = _load_index(index_file)

    if experiment_name is not None:
        index = [e for e in index if e.get("experiment_name") == experiment_name]

    return sorted(index, key=lambda e: e.get("timestamp", ""), reverse=True)


def compare_experiments(
    run_ids: list[str],
    metric_keys: list[str] | None = None,
    storage_dir: Path | None = None,
) -> list[dict]:
    """Compare metrics across multiple experiment runs.

    Args:
        run_ids: List of run IDs to compare.
        metric_keys: Specific metric keys to compare (default: all).
        storage_dir: Override the default experiments directory.

    Returns:
        List of dicts with run_id, experiment_name, and selected metrics.
    """
    results = []
    for run_id in run_ids:
        run = get_experiment(run_id, storage_dir)
        if run is None:
            continue
        metrics = run.metrics
        if metric_keys is not None:
            metrics = {k: v for k, v in metrics.items() if k in metric_keys}
        results.append({
            "run_id": run.run_id,
            "experiment_name": run.experiment_name,
            "timestamp": run.timestamp,
            "metrics": metrics,
        })
    return results


def _load_index(index_file: Path) -> list[dict]:
    """Load the experiment index file, or return empty list."""
    if index_file.exists():
        try:
            return json.loads(index_file.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []
