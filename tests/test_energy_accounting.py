"""Energy and food interaction accounting (isolated per operation)."""
from config import MAX_ENERGY, FOOD_ENERGY, EAT_DISTANCE, FOOD_TARGET_COUNT, FOOD_MAX_COUNT
from domain.genome import Genome
from domain.organism import Organism
from domain.world import World
from simulation import interactions
from simulation.randomness import create_rng


def make_org(x=0.0, y=0.0, energy=50.0, metabolism=0.3):
    g = Genome(speed=0.5, vision=1.0, metabolism=metabolism, size=0.5,
               reproduction_threshold=0.5, mutation_rate=0.1)
    return Organism(organism_id=1, x=x, y=y, energy=energy, health=100.0,
                    age=0, generation=0, genome=g)


def make_world(rng_seed=1):
    return World(rng=create_rng(rng_seed))


def test_food_consumption_increases_energy_capped():
    w = make_world()
    org = make_org(energy=MAX_ENERGY - 5.0)
    w.food = [(0.0, 0.0)]
    assert interactions.eat_food(org, w) is True
    assert org.energy == MAX_ENERGY
    assert w.food == []


def test_food_consumed_once_and_nonexistent_safe():
    w = make_world()
    org = make_org()
    w.food = [(0.0, 0.0), (0.0, 0.0)]
    assert interactions.eat_food(org, w) is True
    assert len(w.food) == 1  # only first in-range item
    w.food = [(1000.0, 1000.0)]
    before = org.energy
    assert interactions.eat_food(org, w) is False
    assert org.energy == before
    w.food = []
    assert interactions.eat_food(org, w) is False


def test_metabolism_reduces_and_floors_at_zero():
    org = make_org(energy=0.2, metabolism=0.5)
    interactions.apply_metabolism(org)
    assert org.energy == 0  # floored, never negative


def test_no_double_energy_application_per_tick():
    w = make_world()
    w.organisms = [make_org(energy=50.0, metabolism=0.3)]
    w.food = []
    from simulation.engine import SimulationEngine
    eng = SimulationEngine(w, rng=w.rng)
    # force no reproduction side effects
    before = w.organisms[0].energy
    eng.step()
    assert w.organisms[0].energy == before - 0.3


def test_food_replenishment_caps():
    w = make_world()
    w.food = [(0.0, 0.0)] * FOOD_TARGET_COUNT
    assert interactions.respawn_food(w) == 0
    w.food = []
    n = interactions.respawn_food(w)
    assert 0 < n <= 5
    w.food = [(0.0, 0.0)] * FOOD_MAX_COUNT
    assert interactions.respawn_food(w) == 0


def test_eat_distance_boundary():
    w = make_world()
    org = make_org(x=0.0, y=0.0, energy=10.0)
    w.food = [(EAT_DISTANCE, 0.0)]
    assert interactions.eat_food(org, w) is True
    assert org.energy == 10.0 + FOOD_ENERGY
