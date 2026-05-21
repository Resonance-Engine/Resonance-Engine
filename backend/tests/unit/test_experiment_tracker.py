"""Tests for experiment tracking."""

import json
from pathlib import Path

import pytest

from src.evaluation.experiment_tracker import (
    compare_experiments,
    get_experiment,
    list_experiments,
    log_experiment,
)


@pytest.fixture
def tmp_experiments_dir(tmp_path):
    """Temporary directory for experiment storage."""
    return tmp_path / "experiments"


def test_log_experiment(tmp_experiments_dir):
    run_id = log_experiment(
        experiment_name="test_model_v1",
        params={"learning_rate": 0.01, "epochs": 10},
        metrics={"f1": 0.72, "brier_score": 0.18},
        storage_dir=tmp_experiments_dir,
    )
    assert isinstance(run_id, str)
    assert len(run_id) == 36  # UUID format


def test_log_and_retrieve(tmp_experiments_dir):
    run_id = log_experiment(
        experiment_name="test_model_v1",
        params={"lr": 0.01},
        metrics={"f1": 0.72},
        artifacts=["model.pt"],
        tags={"version": "v1"},
        storage_dir=tmp_experiments_dir,
    )
    run = get_experiment(run_id, storage_dir=tmp_experiments_dir)
    assert run is not None
    assert run.run_id == run_id
    assert run.experiment_name == "test_model_v1"
    assert run.metrics["f1"] == 0.72
    assert run.artifacts == ["model.pt"]
    assert run.tags["version"] == "v1"


def test_get_nonexistent(tmp_experiments_dir):
    result = get_experiment("nonexistent-id", storage_dir=tmp_experiments_dir)
    assert result is None


def test_list_experiments(tmp_experiments_dir):
    log_experiment("model_a", {"lr": 0.01}, {"f1": 0.70}, storage_dir=tmp_experiments_dir)
    log_experiment("model_b", {"lr": 0.02}, {"f1": 0.75}, storage_dir=tmp_experiments_dir)
    log_experiment("model_a", {"lr": 0.03}, {"f1": 0.73}, storage_dir=tmp_experiments_dir)

    all_runs = list_experiments(storage_dir=tmp_experiments_dir)
    assert len(all_runs) == 3

    model_a_runs = list_experiments(experiment_name="model_a", storage_dir=tmp_experiments_dir)
    assert len(model_a_runs) == 2


def test_compare_experiments(tmp_experiments_dir):
    id1 = log_experiment("model", {"lr": 0.01}, {"f1": 0.70, "brier": 0.20}, storage_dir=tmp_experiments_dir)
    id2 = log_experiment("model", {"lr": 0.02}, {"f1": 0.75, "brier": 0.15}, storage_dir=tmp_experiments_dir)

    comparison = compare_experiments([id1, id2], storage_dir=tmp_experiments_dir)
    assert len(comparison) == 2

    # Filter to specific metrics
    comparison = compare_experiments([id1, id2], metric_keys=["f1"], storage_dir=tmp_experiments_dir)
    assert "f1" in comparison[0]["metrics"]
    assert "brier" not in comparison[0]["metrics"]


def test_index_file_created(tmp_experiments_dir):
    log_experiment("test", {}, {"accuracy": 0.9}, storage_dir=tmp_experiments_dir)
    index_file = tmp_experiments_dir / "index.json"
    assert index_file.exists()
    index = json.loads(index_file.read_text())
    assert len(index) == 1
    assert index[0]["experiment_name"] == "test"
