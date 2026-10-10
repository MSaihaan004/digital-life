import random
import pytest

from domain.organism import Organism
from domain.genome import Genome
from evolution.selection import (
    calculate_fitness,
    select_parent,
)


def make_organism(organism_id, offspring_count=0):
    return Organism(
        organism_id=organism_id,
        x=100.0,
        y=100.0,
        energy=100.0,
        health=100.0,
        age=10,
        generation=0,
        genome=Genome(
            speed=0.5,
            vision=0.5,
            metabolism=0.5,
            size=0.5,
            reproduction_threshold=0.5,
            mutation_rate=0.1,
        ),
        offspring_count=offspring_count,
    )


def test_select_parent_rejects_empty_population():
    with pytest.raises(ValueError):
        select_parent([])


def test_select_parent_returns_an_eligible_organism():
    organisms = [
        make_organism(1),
        make_organism(2),
        make_organism(3),
    ]

    selected = select_parent(
        organisms,
        rng=random.Random(42),
    )

    assert selected in organisms


def test_zero_fitness_uses_uniform_fallback():
    organisms = [
        make_organism(1),
        make_organism(2),
        make_organism(3),
    ]

    rng = random.Random(42)

    selected = select_parent(
        organisms,
        rng=rng,
    )

    assert selected in organisms


def test_higher_fitness_has_a_larger_selection_interval():
    low_fitness = make_organism(1, offspring_count=1)
    high_fitness = make_organism(2, offspring_count=9)

    # A random selection point of 0.5 gives a point of 5.
    class FixedRNG:
        def random(self):
            return 0.5

    selected = select_parent(
        [low_fitness, high_fitness],
        rng=FixedRNG(),
    )

    assert selected is high_fitness


def test_negative_fitness_is_rejected():
    organisms = [
        make_organism(1, offspring_count=-1),
        make_organism(2, offspring_count=2),
    ]

    with pytest.raises(ValueError):
        select_parent(organisms)
