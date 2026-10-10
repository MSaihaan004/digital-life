import random

import pytest

from config import REPRODUCTION_ENERGY_COST
from domain.genome import Genome
from domain.organism import Organism
from domain.world import World
from evolution.reproduction import can_reproduce, create_offspring


def make_parent(**overrides):
    values = dict(
        organism_id=7, x=100.0, y=100.0, energy=90.0, health=100.0, age=12,
        generation=2,
        genome=Genome(0.5, 0.6, 0.2, 0.4, 0.5, 0.1),
        parent_id=None, alive=True,
    )
    values.update(overrides)
    return Organism(**values)


def test_can_reproduce_when_alive_and_threshold_and_cost_are_met():
    assert can_reproduce(make_parent()) is True


def test_cannot_reproduce_when_dead_or_unhealthy():
    assert can_reproduce(make_parent(alive=False)) is False
    assert can_reproduce(make_parent(health=0)) is False


def test_cannot_reproduce_below_threshold():
    parent = make_parent(energy=49.9)
    assert can_reproduce(parent) is False


def test_create_offspring_inherits_metadata_and_copies_genome():
    random.seed(42)
    world = World()
    parent = make_parent()
    world.organisms.append(parent)
    original_energy = parent.energy

    child = create_offspring(parent, world, organism_id=8)

    assert child.organism_id == 8
    assert child.parent_id == parent.organism_id
    assert child.generation == parent.generation + 1
    assert child.age == 0
    assert child.alive is True
    assert child.genome == parent.genome
    assert child.genome is not parent.genome
    assert parent.energy == original_energy - REPRODUCTION_ENERGY_COST
    assert child.energy == REPRODUCTION_ENERGY_COST
    assert child not in world.organisms
    assert 0 <= child.x <= world.width
    assert 0 <= child.y <= world.height


def test_rejects_duplicate_id_without_changing_parent_energy():
    world = World()
    parent = make_parent()
    world.organisms.append(parent)
    energy_before = parent.energy

    with pytest.raises(ValueError, match="already exists"):
        create_offspring(parent, world, organism_id=7)

    assert parent.energy == energy_before
    assert len(world.organisms) == 1


def test_rejects_reproduction_when_parent_cannot_pay_cost():
    world = World()
    parent = make_parent(energy=20.0, genome=Genome(
        0.5, 0.6, 0.2, 0.4, 0.1, 0.1))
    world.organisms.append(parent)

    with pytest.raises(ValueError, match="enough energy"):
        create_offspring(parent, world, organism_id=8)

    assert len(world.organisms) == 1


def test_new_organism_starts_with_zero_offspring():
    parent = make_parent()

    assert parent.offspring_count == 0


def test_reproduction_increments_parent_offspring_count():
    world = World()
    parent = make_parent()
    world.organisms.append(parent)

    initial_count = parent.offspring_count

    create_offspring(
        parent=parent,
        world=world,
        organism_id=100,
    )

    assert parent.offspring_count == initial_count + 1
