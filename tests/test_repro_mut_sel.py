"""Reproduction edge cases + mutation + selection distribution."""
import pytest
from config import REPRODUCTION_ENERGY_COST, MAX_ENERGY
from domain.genome import Genome
from domain.organism import Organism
from domain.world import World
from evolution import reproduction, mutation, selection
from simulation.randomness import create_rng


def make_org(oid=1, energy=100.0, threshold=0.2, alive=True, health=100.0):
    g = Genome(speed=0.5, vision=0.5, metabolism=0.2, size=0.5,
               reproduction_threshold=threshold, mutation_rate=0.2)
    return Organism(organism_id=oid, x=10.0, y=10.0, energy=energy,
                    health=health, age=5, generation=2, genome=g, alive=alive)


def make_world_with(org):
    w = World(rng=create_rng(42))
    w.organisms = [org]
    w.food = []
    return w


def test_failed_reproduction_creates_nothing_and_deducts_nothing():
    org = make_org(energy=5.0)
    w = make_world_with(org)
    with pytest.raises(ValueError):
        reproduction.create_offspring(org, w, organism_id=99, rng=create_rng(1))
    assert len(w.organisms) == 1
    assert org.energy == 5.0 and org.offspring_count == 0
    # dead parent
    dead = make_org(energy=100.0, alive=False)
    w2 = make_world_with(dead)
    with pytest.raises(ValueError):
        reproduction.create_offspring(dead, w2, organism_id=99, rng=create_rng(1))


def test_successful_reproduction_accounting_once():
    org = make_org(energy=100.0, threshold=0.2)
    w = make_world_with(org)
    child = reproduction.create_offspring(org, w, organism_id=7, rng=create_rng(5))
    assert child.organism_id == 7
    assert child.parent_id == org.organism_id
    assert child.generation == org.generation + 1
    assert child.age == 0 and child.health == 100.0
    assert child.energy == REPRODUCTION_ENERGY_COST
    assert org.energy == 100.0 - REPRODUCTION_ENERGY_COST
    assert org.offspring_count == 1
    assert child.genome == org.genome and child.genome is not org.genome
    # duplicate ID rejected
    w.organisms.append(child)
    with pytest.raises(ValueError):
        reproduction.create_offspring(org, w, organism_id=7, rng=create_rng(5))


def test_mutation_zero_max_clip_independence_repro():
    base = Genome(speed=0.5, vision=0.5, metabolism=0.5, size=0.5,
                  reproduction_threshold=0.5, mutation_rate=0.0)
    m0 = mutation.mutate(base, rng=create_rng(1))
    assert m0 == base
    full = Genome(speed=0.5, vision=0.5, metabolism=0.5, size=0.5,
                  reproduction_threshold=0.5, mutation_rate=1.0)
    m1 = mutation.mutate(full, rng=create_rng(2), mutation_strength=5.0)
    for name in ("speed", "vision", "metabolism", "size",
                 "reproduction_threshold", "mutation_rate"):
        assert 0.0 <= getattr(m1, name) <= 1.0
    assert base.mutation_rate == 0.0  # parent untouched
    a = mutation.mutate(full, rng=create_rng(77))
    b = mutation.mutate(full, rng=create_rng(77))
    assert a == b


def test_selection_distribution_fixed_seed():
    rng = create_rng(123)
    orgs = [make_org(oid=i) for i in range(3)]
    orgs[0].offspring_count = 0
    orgs[1].offspring_count = 1
    orgs[2].offspring_count = 3
    counts = {0: 0, 1: 0, 2: 0}
    N = 2000
    for _ in range(N):
        p = selection.select_parent(orgs, rng=rng)
        counts[p.organism_id] += 1
    # fitness 0 never selected when total > 0 (except zero-total fallback)
    assert counts[0] == 0
    # proportion ~1:3 within tolerance (non-flaky wide band)
    ratio = counts[2] / max(counts[1], 1)
    assert 2.0 < ratio < 4.5
    # zero-fitness uniform fallback
    for o in orgs:
        o.offspring_count = 0
    seen = {selection.select_parent(orgs, rng=create_rng(i)).organism_id for i in range(20)}
    assert len(seen) > 1
    # single + empty + negative
    assert selection.select_parent([orgs[0]], rng=create_rng(1)) is orgs[0]
    with pytest.raises(ValueError):
        selection.select_parent([], rng=create_rng(1))
