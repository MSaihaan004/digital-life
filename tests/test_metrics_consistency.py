"""Metrics vs actual world state + exporter preservation."""
from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng
from evolution.metrics import EvolutionMetrics
from evolution.exporter import export_metrics_csv


def test_metrics_match_world_state():
    w = World(rng=create_rng(42))
    w.spawn_organisms(5)
    w.spawn_food(10)
    w.organisms[0].alive = False
    m = EvolutionMetrics()
    w.tick = 7
    snap = m.record(w, births=1, deaths=1)
    assert snap["tick"] == 7
    assert snap["total_population"] == 5
    assert snap["living_population"] == 4
    assert snap["births"] == 1 and snap["deaths"] == 1
    assert snap["survival_rate"] == 4 / 5
    assert m.latest() == snap


def test_empty_population_metrics_no_exception(tmp_path):
    w = World(rng=create_rng(1))
    m = EvolutionMetrics()
    snap = m.record(w)
    assert snap["living_population"] == 0
    assert snap["average_energy"] is None
    assert snap["generation_counts"] == {}
    out = export_metrics_csv(m.get_history(), tmp_path / "m.csv")
    assert out.exists()
    assert "tick" in out.read_text()


def test_engine_metrics_correspond_to_state():
    w = World(rng=create_rng(5))
    w.spawn_organisms(8)
    w.spawn_food(10)
    eng = SimulationEngine(w, rng=w.rng)
    eng.run(5)
    assert len(eng.metrics.get_history()) == 5
    for i, snap in enumerate(eng.metrics.get_history(), start=1):
        assert snap["tick"] == i
