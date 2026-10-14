"""Sensor correctness: vision, edge cases, purity."""
import math
from config import MAX_ENERGY
from domain.genome import Genome
from domain.organism import Organism
from domain.world import World
from domain import sensors
from simulation.randomness import create_rng


def make_org(oid, x, y, vision=1.0, energy=50.0, alive=True):
    g = Genome(speed=0.5, vision=vision, metabolism=0.2, size=0.5,
               reproduction_threshold=0.5, mutation_rate=0.1)
    return Organism(organism_id=oid, x=x, y=y, energy=energy,
                    health=100.0, age=0, generation=0, genome=g, alive=alive)


def test_food_vision_filter():
    org = make_org(1, 0, 0, vision=0.1)  # range 20
    d, _, _ = sensors.sense_nearest_food(org, [(100.0, 0.0)])
    assert d == float("inf")
    d2, _, _ = sensors.sense_nearest_food(org, [(10.0, 0.0)])
    assert d2 == 10.0


def test_organism_vision_filter_consistent_with_food():
    org = make_org(1, 0, 0, vision=0.1)  # range 20
    far = make_org(2, 100, 0, vision=1.0)
    near = make_org(3, 10, 0, vision=1.0)
    d, dx, dy = sensors.sense_nearest_organism(org, [org, far])
    assert d == float("inf")
    d2, _, _ = sensors.sense_nearest_organism(org, [org, far, near])
    assert d2 == 10.0


def test_zero_vision_empty_overlapping_boundaries():
    org = make_org(1, 0, 0, vision=0.0)
    # empty food
    assert sensors.sense_nearest_food(org, [])[0] == float("inf")
    # overlapping food at distance 0 visible even with zero vision
    assert sensors.sense_nearest_food(org, [(0.0, 0.0)])[0] == 0.0
    # empty population / self only / dead only
    assert sensors.sense_nearest_organism(org, [])[0] == float("inf")
    assert sensors.sense_nearest_organism(org, [org])[0] == float("inf")
    dead = make_org(2, 0, 0, alive=False)
    assert sensors.sense_nearest_organism(org, [org, dead])[0] == float("inf")
    # boundaries
    world = World(rng=create_rng(1))
    assert sensors.sense_boundaries(org, world) == (0, world.width, 0, world.height)


def test_energy_ratio_uses_config_and_no_mutation():
    org = make_org(1, 0, 0, energy=MAX_ENERGY / 2)
    assert sensors.sense_energy(org) == 0.5
    world = World(rng=create_rng(2))
    world.organisms = [org, make_org(2, 5, 5)]
    world.food = [(1.0, 1.0)]
    food_before = list(world.food)
    n_before = len(world.organisms)
    sensors.sense(org, world)
    assert list(world.food) == food_before
    assert len(world.organisms) == n_before
    assert org.x == 0 and org.y == 0
