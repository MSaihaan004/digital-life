"""Optimization equivalence: squared-distance sensors/eating match sqrt reference."""
import math

from domain.genome import Genome
from domain.organism import Organism
from domain.world import World
from domain import sensors
from simulation import interactions
from simulation.randomness import create_rng
from config import EAT_DISTANCE


def make_org(oid, x, y, vision=0.7):
    g = Genome(speed=0.5, vision=vision, metabolism=0.2, size=0.5,
               reproduction_threshold=0.5, mutation_rate=0.1)
    return Organism(organism_id=oid, x=x, y=y, energy=50.0, health=100.0,
                    age=0, generation=0, genome=g)


def ref_food(organism, food):
    vr = organism.genome.vision * 200.0
    best, bdx, bdy = float("inf"), 0.0, 0.0
    for fx, fy in food:
        d = math.sqrt((fx - organism.x) ** 2 + (fy - organism.y) ** 2)
        if d > vr:
            continue
        if d < best:
            best, bdx, bdy = d, fx - organism.x, fy - organism.y
    return best, bdx, bdy


def ref_organism(organism, organisms):
    vr = organism.genome.vision * 200.0
    best, bdx, bdy = float("inf"), 0.0, 0.0
    for other in organisms:
        if other.organism_id == organism.organism_id or not other.alive:
            continue
        d = math.sqrt((other.x - organism.x) ** 2 + (other.y - organism.y) ** 2)
        if d > vr:
            continue
        if d < best:
            best, bdx, bdy = d, other.x - organism.x, other.y - organism.y
    return best, bdx, bdy


def test_ties_prefer_first_in_collection_order():
    # Two equidistant food items: the first in list order wins.
    org = make_org(1, 0.0, 0.0, vision=1.0)
    food = [(3.0, 4.0), (-3.0, -4.0), (3.0, 4.0)]
    dist, dx, dy = sensors.sense_nearest_food(org, food)
    assert dist == 5.0 and (dx, dy) == (3.0, 4.0)
    # Two equidistant organisms: first in iteration order wins.
    a = make_org(2, 3.0, 4.0)
    b = make_org(3, -3.0, -4.0)
    dist, dx, dy = sensors.sense_nearest_organism(org, [org, a, b])
    assert dist == 5.0 and (dx, dy) == (3.0, 4.0)
    # Reversed order reverses the winner (stable, documented).
    dist, dx, dy = sensors.sense_nearest_organism(org, [org, b, a])
    assert dist == 5.0 and (dx, dy) == (-3.0, -4.0)


def test_vision_boundary_inclusive():
    # Targets exactly at the vision range are detectable.
    org = make_org(1, 0.0, 0.0, vision=0.1)  # range == 20.0
    dist, _, _ = sensors.sense_nearest_food(org, [(20.0, 0.0)])
    assert dist == 20.0
    other = make_org(2, 20.0, 0.0)
    dist, _, _ = sensors.sense_nearest_organism(org, [org, other])
    assert dist == 20.0
    # Just beyond the range is invisible.
    dist, _, _ = sensors.sense_nearest_food(org, [(20.0001, 0.0)])
    assert dist == float("inf")


def test_sensor_equivalence_randomized():
    for seed in range(10):
        rng = create_rng(seed)
        org = make_org(1, rng.uniform(0, 800), rng.uniform(0, 600),
                       vision=rng.uniform(0, 1))
        food = [(rng.uniform(0, 800), rng.uniform(0, 600)) for _ in range(50)]
        others = [make_org(i + 2, rng.uniform(0, 800), rng.uniform(0, 600),
                           vision=rng.uniform(0, 1)) for i in range(10)]
        got = sensors.sense_nearest_food(org, food)
        want = ref_food(org, food)
        assert got[0] == want[0] or abs(got[0] - want[0]) < 1e-9
        assert got[1:] == want[1:]
        got = sensors.sense_nearest_organism(org, [org] + others)
        want = ref_organism(org, [org] + others)
        assert got[0] == want[0] or abs(got[0] - want[0]) < 1e-9
        assert got[1:] == want[1:]


def test_eat_equivalence_randomized():
    for seed in range(10):
        rng = create_rng(100 + seed)
        for trial in range(20):
            x, y = rng.uniform(0, 800), rng.uniform(0, 600)
            org = make_org(1, x, y)
            food = [(rng.uniform(x - 10, x + 10), rng.uniform(y - 10, y + 10))
                    for _ in range(5)]
            w = World(rng=create_rng(1))
            w.food = list(food)
            # reference decision: first item within EAT_DISTANCE
            ref_idx = next(
                (i for i, (fx, fy) in enumerate(food)
                 if math.sqrt((fx - x) ** 2 + (fy - y) ** 2) <= EAT_DISTANCE),
                None,
            )
            got = interactions.eat_food(org, w)
            assert got == (ref_idx is not None)
            if ref_idx is not None:
                assert len(w.food) == len(food) - 1
                assert w.food == food[:ref_idx] + food[ref_idx + 1:]
