"""Output-safety: no silent overwrites; unique runs; partial failures."""
import json

import pytest

from experiments import analyze_multiple_seeds as multi
from experiments.run_metadata import (
    OutputExistsError,
    unique_run_dir,
    write_metadata_sidecar,
    write_text_exclusive,
)


def test_existing_csv_not_overwritten(tmp_path):
    target = tmp_path / "multi_seed_summary.csv"
    target.write_text("original", encoding="utf-8")
    with pytest.raises(OutputExistsError):
        multi.export_results(
            [{"seed": 42, "ticks": 1}], output_path=target
        )
    assert target.read_text(encoding="utf-8") == "original"
    # Explicit overwrite is honored when requested.
    multi.export_results(
        [{"seed": 42, "ticks": 1}], output_path=target, overwrite=True
    )
    assert "seed" in target.read_text(encoding="utf-8")


def test_existing_metadata_not_overwritten(tmp_path):
    from experiments.run_metadata import build_run_metadata
    meta = build_run_metadata("exp", [42], 1)
    first = write_metadata_sidecar(tmp_path, meta)
    assert first.exists()
    with pytest.raises(OutputExistsError):
        write_metadata_sidecar(tmp_path, meta)
    assert json.loads(first.read_text(encoding="utf-8"))["seeds"] == [42]


def test_repeated_invocations_receive_separate_outputs(tmp_path):
    first = unique_run_dir(tmp_path, "multi_seed_analysis")
    second = unique_run_dir(tmp_path, "multi_seed_analysis")
    assert first != second and first.exists() and second.exists()
    (first / "multi_seed_summary.csv").write_text("a", encoding="utf-8")
    assert (second / "multi_seed_summary.csv").exists() is False


def test_partial_failures_recorded_accurately(tmp_path, monkeypatch):
    monkeypatch.setattr(multi, "SIMULATION_TICKS", 3)
    real = multi.run_single_experiment

    def flaky(seed):
        if seed == 43:
            raise RuntimeError("simulated seed failure")
        return real(seed)

    monkeypatch.setattr(multi, "run_single_experiment", flaky)
    results, statuses = multi.run_seeds([42, 43])
    assert len(results) == 1 and results[0]["seed"] == 42
    assert statuses == [
        {"seed": 42, "status": "success"},
        {"seed": 43, "status": "failed", "error": "simulated seed failure"},
    ]
    from experiments.run_metadata import build_run_metadata
    meta = build_run_metadata("multi_seed_analysis", [42, 43], 3,
                              run_statuses=statuses)
    assert meta["successful_runs"] == 1 and meta["failed_runs"] == 1


def test_metadata_points_to_actual_outputs(tmp_path, monkeypatch):
    monkeypatch.setattr(multi, "SIMULATION_TICKS", 3)
    monkeypatch.setattr(multi, "RANDOM_SEEDS", [42, 43])
    results, metadata = multi.main(output_dir=tmp_path / "run1")
    assert metadata["extra"]["output_file"].endswith("multi_seed_summary.csv")
    assert (tmp_path / "run1" / "multi_seed_summary.csv").exists()
    assert (tmp_path / "run1" / "multi_seed_analysis_run_metadata.json").exists()
    loaded = json.loads(
        (tmp_path / "run1" / "multi_seed_analysis_run_metadata.json")
        .read_text(encoding="utf-8")
    )
    assert loaded["extra"]["output_file"].endswith("multi_seed_summary.csv")
    assert loaded["seeds"] == [42, 43]
    assert len(results) == 2


def test_existing_results_unchanged_after_runs(tmp_path, monkeypatch):
    keep = tmp_path / "keep.csv"
    keep.write_text("protected", encoding="utf-8")
    monkeypatch.setattr(multi, "SIMULATION_TICKS", 2)
    monkeypatch.setattr(multi, "RANDOM_SEEDS", [42])
    multi.main(output_dir=tmp_path / "fresh")
    assert keep.read_text(encoding="utf-8") == "protected"
    # Reusing the same explicit dir without overwrite fails safely.
    with pytest.raises(OutputExistsError):
        multi.main(output_dir=tmp_path / "fresh")


def test_exclusive_write_is_atomic_and_guarded(tmp_path):
    target = tmp_path / "out.json"
    write_text_exclusive(target, '{"a": 1}')
    assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1}
    assert list(tmp_path.glob("out.json.*.tmp")) == []
