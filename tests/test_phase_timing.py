"""Phase instrumentation: optional, exact-path, deterministic."""
import hashlib
import json

from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng


def _signature(world):
    return [
        (o.organism_id, o.x, o.y, o.energy, o.health, o.age, o.alive,
         o.generation, o.parent_id, o.offspring_count)
        for o in world.organisms
    ]


def test_timing_disabled_by_default():
    world = World(rng=create_rng(42))
    engine = SimulationEngine(world, rng=world.rng)
    assert engine._phase_timing is None
    assert engine.phase_report() == {}
    engine.step()
    assert engine.phase_report() == {}


def test_timed_ticks_match_untimed_trajectory():
    def run(timed):
        world = World(rng=create_rng(42))
        world.spawn_organisms(20)
        world.spawn_food(30)
        engine = SimulationEngine(world, rng=world.rng)
        if timed:
            engine.enable_phase_timing()
        engine.run(15)
        return world, engine

    plain_world, _ = run(False)
    timed_world, timed_engine = run(True)
    assert _signature(plain_world) == _signature(timed_world)
    report = timed_engine.phase_report()
    assert set(report) == {"act", "reproduce", "housekeeping", "metrics"}
    assert all(value >= 0 for value in report.values())
    timed_engine.disable_phase_timing()
    assert timed_engine.phase_report() == {}


def test_phase_totals_cover_measured_ticks():
    world = World(rng=create_rng(7))
    world.spawn_organisms(10)
    world.spawn_food(10)
    engine = SimulationEngine(world, rng=world.rng)
    engine.enable_phase_timing()
    engine.run(5)
    assert engine._phase_timing["ticks"] == 5
    # No wall-clock threshold: only structural sanity, no flakiness.
    assert set(engine._phase_timing) == {
        "act", "reproduce", "housekeeping", "metrics", "ticks"
    }
