import random

from simulation.engine import SimulationEngine
from simulation.randomness import create_rng
from domain.world import World


def make_test_world(seed=42):
    """Create a reproducible world for engine tests."""

    rng = create_rng(seed=seed)
    world = World(rng=rng)

    world.spawn_organisms(10)
    world.spawn_food(20)

    return world, rng


def test_no_eligible_parents_produce_no_offspring(monkeypatch):
    """No eligible parents should mean no births."""

    world, rng = make_test_world()
    engine = SimulationEngine(world, rng=rng)

    monkeypatch.setattr(
        "simulation.engine.can_reproduce",
        lambda organism: False,
    )

    initial_population = len(world.organisms)

    engine.step()

    assert len(world.organisms) == initial_population
    assert engine.metrics.latest()["births"] == 0


def test_at_most_one_offspring_per_tick(monkeypatch):
    """Multiple eligible organisms should produce at most one child."""

    world, rng = make_test_world()
    engine = SimulationEngine(world, rng=rng)

    monkeypatch.setattr(
        "simulation.engine.can_reproduce",
        lambda organism: True,
    )

    initial_population = len(world.organisms)

    engine.step()

    births = len(world.organisms) - initial_population

    assert births == 1
    assert engine.metrics.latest()["births"] == 1


def test_engine_advances_tick_once():
    """One engine step should advance the world by one tick."""

    world, rng = make_test_world()
    engine = SimulationEngine(world, rng=rng)

    initial_tick = world.tick

    engine.step()

    assert world.tick == initial_tick + 1


def test_engine_records_metrics():
    """Each step should record a metrics snapshot."""

    world, rng = make_test_world()
    engine = SimulationEngine(world, rng=rng)

    initial_history_length = len(engine.metrics.get_history())

    engine.step()

    assert len(engine.metrics.get_history()) == initial_history_length + 1


def test_engine_calls_parent_selection(monkeypatch):
    """The engine should use select_parent to choose a parent."""

    world, rng = make_test_world()
    engine = SimulationEngine(world, rng=rng)

    selected_parents = []

    def fake_select_parent(eligible_parents, rng=None):
        selected_parents.extend(eligible_parents)
        return eligible_parents[0]

    monkeypatch.setattr(
        "simulation.engine.can_reproduce",
        lambda organism: True,
    )

    monkeypatch.setattr(
        "simulation.engine.select_parent",
        fake_select_parent,
    )

    engine.step()

    assert len(selected_parents) == 10
    assert engine.metrics.latest()["births"] == 1
