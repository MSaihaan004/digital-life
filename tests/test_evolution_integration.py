from types import SimpleNamespace

from config import REPRODUCTION_ENERGY_COST
from domain.genome import Genome
from domain.organism import Organism
from domain.world import World

import simulation.engine as engine_module
from simulation.engine import SimulationEngine


def make_parent():
    return Organism(
        organism_id=7,
        x=100.0,
        y=100.0,
        energy=90.0,
        health=100.0,
        age=12,
        generation=2,
        genome=Genome(
            0.5, 0.6, 0.2, 0.4, 0.5, 0.1
        ),
        parent_id=None,
        alive=True,
    )


class IdleBrain:

    def decide(self, sensor_data):
        return SimpleNamespace(value="idle")


def prepare_engine(monkeypatch, world):
    """Create a predictable engine for integration tests."""

    monkeypatch.setattr(
        engine_module,
        "sense",
        lambda organism, world: {},
    )

    monkeypatch.setattr(
        engine_module,
        "eat_food",
        lambda organism, world: False,
    )

    monkeypatch.setattr(
        engine_module,
        "apply_metabolism",
        lambda organism: None,
    )

    engine = SimulationEngine(world)
    engine.brain = IdleBrain()

    return engine


def test_eligible_organism_reproduces(monkeypatch):
    world = World()
    parent = make_parent()
    world.organisms.append(parent)

    engine = prepare_engine(monkeypatch, world)

    engine.step()

    assert len(world.organisms) == 2

    child = next(
        organism
        for organism in world.organisms
        if organism.organism_id != parent.organism_id
    )

    assert child.parent_id == parent.organism_id
    assert child.generation == parent.generation + 1


def test_parent_pays_reproduction_cost(monkeypatch):
    world = World()
    parent = make_parent()
    world.organisms.append(parent)

    engine = prepare_engine(monkeypatch, world)

    engine.step()

    assert parent.energy == (
        90.0 - REPRODUCTION_ENERGY_COST
    )


def test_offspring_does_not_act_during_birth_tick(monkeypatch):
    world = World()
    parent = make_parent()
    world.organisms.append(parent)

    engine = prepare_engine(monkeypatch, world)

    engine.step()

    child = next(
        organism
        for organism in world.organisms
        if organism.organism_id != parent.organism_id
    )

    assert child.age == 0


def test_offspring_receives_mutated_genome(monkeypatch):
    world = World()
    parent = make_parent()
    world.organisms.append(parent)

    def fake_mutate(genome, rng=None):
        mutated = Genome(
            genome.speed,
            genome.vision,
            genome.metabolism,
            genome.size,
            genome.reproduction_threshold,
            genome.mutation_rate,
        )

        mutated.speed = 0.9
        return mutated

    monkeypatch.setattr(
        engine_module,
        "mutate",
        fake_mutate,
    )

    engine = prepare_engine(monkeypatch, world)

    engine.step()

    child = next(
        organism
        for organism in world.organisms
        if organism.organism_id != parent.organism_id
    )

    assert child.genome.speed == 0.9
    assert parent.genome.speed == 0.5
    assert child.genome is not parent.genome


def test_ineligible_organism_does_not_reproduce(monkeypatch):
    world = World()
    parent = make_parent()
    parent.energy = 20.0
    world.organisms.append(parent)

    engine = prepare_engine(monkeypatch, world)

    engine.step()

    assert len(world.organisms) == 1


def test_tick_advances_once(monkeypatch):
    world = World()
    world.organisms.append(make_parent())

    engine = prepare_engine(monkeypatch, world)

    engine.step()

    assert world.tick == 1


def test_engine_records_metrics_after_each_tick(monkeypatch):
    world = World()
    parent = make_parent()
    world.organisms.append(parent)

    engine = prepare_engine(monkeypatch, world)

    # Run the first simulation tick.
    engine.step()

    snapshot = engine.metrics.latest()

    # Verify that metrics were recorded.
    assert snapshot is not None
    assert snapshot["tick"] == 1

    # The parent should have reproduced.
    assert snapshot["total_population"] == 2
    assert snapshot["living_population"] == 2

    # Verify birth and death statistics.
    assert snapshot["births"] == 1
    assert snapshot["deaths"] == 0

    # Run a second simulation tick.
    engine.step()

    # Verify that a new snapshot was recorded.
    assert len(engine.metrics.get_history()) == 2
    assert engine.metrics.latest()["tick"] == 2
