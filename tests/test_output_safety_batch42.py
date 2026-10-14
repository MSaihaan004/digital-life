"""Batch 4.2: output-safety policy across all experiment scripts."""
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from experiments import (
    analyze_energy_economy as economy,
    analyze_evolution as evolution_exp,
    analyze_metabolism as metabolism,
    validate_evolution as validate,
)
from experiments.run_metadata import OutputExistsError, write_csv_exclusive

RESULTS = Path("experiment_results")


def _header(path):
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return next(reader)


def test_guarded_writers_refuse_existing_files(tmp_path):
    target = tmp_path / "out.csv"
    target.write_text("original", encoding="utf-8")
    rows = [{"a": 1}]
    with pytest.raises(OutputExistsError):
        write_csv_exclusive(target, rows, ["a"])
    with pytest.raises(OutputExistsError):
        economy.export_csv(rows, "x.csv", output_path=target)
    with pytest.raises(OutputExistsError):
        metabolism.export_results(rows, output_path=target)
    with pytest.raises(OutputExistsError):
        validate.save_csv(rows, target)
    assert target.read_text(encoding="utf-8") == "original"
    # Explicit overwrite works when requested.
    write_csv_exclusive(target, rows, ["a"], overwrite=True)
    assert "a" in target.read_text(encoding="utf-8")


def test_individual_records_guard(tmp_path, monkeypatch):
    monkeypatch.setattr(evolution_exp, "Path", Path)
    from domain.world import World
    from simulation.randomness import create_rng
    world = World(rng=create_rng(42))
    world.spawn_organisms(3)
    target = tmp_path / "individuals_seed_42.csv"
    out = evolution_exp.export_individual_records(
        list(world.organisms), 42, output_path=target
    )
    assert out == target
    with pytest.raises(OutputExistsError):
        evolution_exp.export_individual_records(
            list(world.organisms), 42, output_path=target
        )


def test_concurrent_same_path_single_winner(tmp_path):
    target = tmp_path / "race.csv"
    rows = [{"seed": n, "ticks": 1} for n in range(3)]

    def attempt(_):
        try:
            write_csv_exclusive(target, rows, ["seed", "ticks"])
            return "won"
        except OutputExistsError:
            return "refused"

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(attempt, range(16)))
    assert outcomes.count("won") == 1
    assert outcomes.count("refused") == 15
    with open(target, newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 3


def test_csv_schemas_match_committed_results(tmp_path):
    from domain.world import World
    from simulation.engine import SimulationEngine
    from simulation.randomness import create_rng
    from evolution import exporter

    committed = {
        "multi_seed_summary.csv": None,
        "metabolism_experiment.csv": None,
        "energy_economy_summary.csv": None,
        "energy_economy_timeseries.csv": None,
        "individuals_seed_42.csv": None,
    }
    for name in committed:
        committed[name] = _header(RESULTS / name)

    world = World(rng=create_rng(42))
    world.spawn_organisms(5)
    world.spawn_food(10)
    engine = SimulationEngine(world, rng=world.rng)
    engine.run(5)

    out = exporter.export_metrics_csv(
        engine.metrics.get_history(), tmp_path / "m.csv"
    )
    assert _header(out) == [
        "tick", "total_population", "living_population", "births",
        "deaths", "average_energy", "average_speed", "average_vision",
        "average_metabolism", "average_size",
        "average_reproduction_threshold", "average_mutation_rate",
        "average_generation", "generation_counts",
    ]

    ind = evolution_exp.export_individual_records(
        list(world.organisms), 42, output_path=tmp_path / "ind.csv"
    )
    assert _header(ind) == committed["individuals_seed_42.csv"]


def test_validate_main_unique_dirs_and_statuses(tmp_path, monkeypatch):
    first = validate.main(output_dir=tmp_path / "run1", seeds=[42], ticks=5)
    assert (tmp_path / "run1" / "seed_42.csv").exists()
    assert first[1]["failed_runs"] == 0
    # Same explicit dir without overwrite fails safely.
    with pytest.raises(OutputExistsError):
        validate.main(output_dir=tmp_path / "run1", seeds=[42], ticks=5)
    assert (tmp_path / "run1" / "seed_42.csv").exists()
    # Failure recorded,Banner reflects it, legacy files untouched.
    before = (RESULTS / "seed_42.csv").read_text(encoding="utf-8")

    def boom(seed, ticks=5, output_path=None, overwrite=False):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(validate, "run_experiment", boom)
    results, metadata = validate.main(
        output_dir=tmp_path / "run2", seeds=[42], ticks=5
    )
    assert results == []
    assert metadata["failed_runs"] == 1
    assert metadata["extra"]["output_files"] == [
        str(tmp_path / "run2" / "seed_42.csv")
    ]
    sidecar = json.loads(
        (tmp_path / "run2" / "validate_evolution_run_metadata.json")
        .read_text(encoding="utf-8")
    )
    assert sidecar["failed_runs"] == 1
    assert sidecar["runs"][0]["status"] == "failed"
    assert (RESULTS / "seed_42.csv").read_text(encoding="utf-8") == before


def test_metabolism_and_economy_mains_isolated(tmp_path, monkeypatch):
    for module, exp_id, csv_name in (
        (metabolism, "metabolism_experiment", "metabolism_experiment.csv"),
        (economy, "energy_economy", "energy_economy_summary.csv"),
    ):
        monkeypatch.setattr(module, "SIMULATION_TICKS", 3)
        monkeypatch.setattr(module, "METABOLISM_LEVELS", (0.20,))
        monkeypatch.setattr(module, "RANDOM_SEEDS", (42,))
        results, metadata = module.main(output_dir=tmp_path / exp_id)
        assert metadata["failed_runs"] == 0
        assert (tmp_path / exp_id / csv_name).exists()
        sidecars = list((tmp_path / exp_id).glob("*_run_metadata.json"))
        assert len(sidecars) == 1
        loaded = json.loads(sidecars[0].read_text(encoding="utf-8"))
        assert loaded["extra"]["output_file"].endswith(csv_name)


def test_failed_runs_do_not_corrupt_existing_results(tmp_path, monkeypatch):
    monkeypatch.setattr(metabolism, "SIMULATION_TICKS", 3)
    monkeypatch.setattr(metabolism, "METABOLISM_LEVELS", (0.20, 0.40))
    monkeypatch.setattr(metabolism, "RANDOM_SEEDS", (42,))
    real = metabolism.run_single_experiment

    def flaky(metabolism_value, seed):
        if metabolism_value == 0.40:
            raise RuntimeError("bad condition")
        return real(metabolism_value, seed)

    monkeypatch.setattr(metabolism, "run_single_experiment", flaky)
    legacy = (RESULTS / "metabolism_experiment.csv").read_text(encoding="utf-8")
    results, metadata = metabolism.main(output_dir=tmp_path / "partial")
    assert metadata["successful_runs"] == 1
    assert metadata["failed_runs"] == 1
    assert len(results) == 1
    assert (RESULTS / "metabolism_experiment.csv").read_text(
        encoding="utf-8") == legacy
