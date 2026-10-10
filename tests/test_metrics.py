import pytest

from domain.world import World
from evolution.metrics import EvolutionMetrics


def test_records_empty_world():
    world = World()
    metrics = EvolutionMetrics()

    snapshot = metrics.record(world)

    assert snapshot["tick"] == 0
    assert snapshot["total_population"] == 0
    assert snapshot["living_population"] == 0
    assert snapshot["average_energy"] is None
    assert snapshot["generation_counts"] == {}


def test_records_initial_population():
    world = World()
    world.spawn_organisms(3)

    metrics = EvolutionMetrics()
    snapshot = metrics.record(world)

    assert snapshot["total_population"] == 3
    assert snapshot["living_population"] == 3


def test_calculates_average_energy():
    world = World()
    world.spawn_organisms(2)

    world.organisms[0].energy = 20.0
    world.organisms[1].energy = 60.0

    metrics = EvolutionMetrics()
    snapshot = metrics.record(world)

    assert snapshot["average_energy"] == pytest.approx(40.0)


def test_excludes_dead_organisms_from_living_statistics():
    world = World()
    world.spawn_organisms(2)

    world.organisms[0].alive = False
    world.organisms[0].energy = 10.0
    world.organisms[1].energy = 80.0

    metrics = EvolutionMetrics()
    snapshot = metrics.record(world)

    assert snapshot["total_population"] == 2
    assert snapshot["living_population"] == 1
    assert snapshot["average_energy"] == pytest.approx(80.0)


def test_records_births_and_deaths():
    world = World()
    world.spawn_organisms(3)

    metrics = EvolutionMetrics()

    snapshot = metrics.record(
        world,
        births=2,
        deaths=1,
    )

    assert snapshot["births"] == 2
    assert snapshot["deaths"] == 1


def test_tracks_generation_distribution():
    world = World()
    world.spawn_organisms(3)

    world.organisms[0].generation = 0
    world.organisms[1].generation = 1
    world.organisms[2].generation = 1

    metrics = EvolutionMetrics()
    snapshot = metrics.record(world)

    assert snapshot["generation_counts"] == {
        0: 1,
        1: 2,
    }

    assert snapshot["average_generation"] == pytest.approx(2 / 3)


def test_history_keeps_multiple_snapshots():
    world = World()
    world.spawn_organisms(2)

    metrics = EvolutionMetrics()

    first = metrics.record(world)

    world.tick = 1
    world.organisms[0].energy = 50.0

    second = metrics.record(world)

    assert len(metrics.get_history()) == 2
    assert metrics.latest() == second
    assert first["tick"] == 0
    assert second["tick"] == 1
    assert first["average_energy"] != second["average_energy"]
