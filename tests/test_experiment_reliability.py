"""Experiment reliability: metadata recording, aggregation, export."""
import csv
import json

import config
from experiments import run_metadata
from evolution import exporter
from evolution.metrics import EvolutionMetrics
from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng


def test_config_snapshot_records_values_and_validation():
    snap = run_metadata.collect_config_snapshot()
    assert snap["values"]["MAX_ENERGY"] == config.MAX_ENERGY
    assert snap["values"]["RANDOM_SEED"] == config.RANDOM_SEED
    assert snap["validation_errors"] == []
    assert len(snap["values"]) == len(run_metadata.CONFIG_FIELDS)


def test_metadata_counts_success_and_failure(tmp_path):
    meta = run_metadata.build_run_metadata(
        experiment_id="test_exp",
        seeds=[42, 43, 44],
        ticks=10,
        run_statuses=[
            {"seed": 42, "status": "success"},
            {"seed": 43, "status": "failed", "error": "boom"},
            {"seed": 44, "status": "success"},
        ],
    )
    assert meta["successful_runs"] == 2
    assert meta["failed_runs"] == 1
    assert meta["code_revision"]
    path = run_metadata.write_metadata_sidecar(tmp_path, meta)
    assert path.name == "test_exp_run_metadata.json"
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["seeds"] == [42, 43, 44]
    assert loaded["ticks"] == 10


def test_export_matches_source_metrics(tmp_path):
    world = World(rng=create_rng(42))
    world.spawn_organisms(10)
    world.spawn_food(20)
    engine = SimulationEngine(world, rng=world.rng)
    engine.run(15)
    history = engine.metrics.get_history()
    out = exporter.export_metrics_csv(history, tmp_path / "m.csv")
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert len(rows) == len(history)
    for row, snap in zip(rows, history):
        assert int(row["tick"]) == snap["tick"]
        assert int(row["living_population"]) == snap["living_population"]
        assert int(row["births"]) == snap["births"]
        assert int(row["deaths"]) == snap["deaths"]
        if snap["average_energy"] is None:
            assert row["average_energy"] == ""
        else:
            assert abs(float(row["average_energy"]) - snap["average_energy"]) < 1e-9
        assert json.loads(row["generation_counts"]) == {
            str(k): v for k, v in snap["generation_counts"].items()
        }


def test_export_empty_history_header_only(tmp_path):
    out = exporter.export_metrics_csv([], tmp_path / "empty.csv")
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert rows == []
    header = out.read_text(encoding="utf-8").splitlines()[0]
    assert "living_population" in header


def test_export_repeated_is_deterministic(tmp_path):
    metrics = EvolutionMetrics()
    world = World(rng=create_rng(7))
    world.spawn_organisms(5)
    metrics.record(world)
    first = exporter.export_metrics_csv(
        metrics.get_history(), tmp_path / "a.csv").read_text()
    second = exporter.export_metrics_csv(
        metrics.get_history(), tmp_path / "b.csv").read_text()
    assert first == second


def test_metrics_history_ordering_and_limits():
    world = World(rng=create_rng(11))
    world.spawn_organisms(5)
    world.spawn_food(10)
    engine = SimulationEngine(world, rng=world.rng)
    engine.run(10)
    history = engine.metrics.get_history()
    assert [s["tick"] for s in history] == list(range(1, 11))
    assert len(history[-3:]) == 3
    assert history[-3]["tick"] == 8
    empty = EvolutionMetrics().get_history()
    assert empty == []
