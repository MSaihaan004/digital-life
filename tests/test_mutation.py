import random
from dataclasses import fields

from domain.genome import Genome
from evolution.mutation import mutate


def test_mutation_returns_a_separate_genome():
    genome = Genome(
        speed=0.7,
        vision=0.6,
        metabolism=0.4,
        size=0.5,
        reproduction_threshold=0.8,
        mutation_rate=0.1,
    )

    mutated = mutate(genome, rng=random.Random(42))

    assert mutated is not genome


def test_original_genome_is_not_modified():
    genome = Genome(
        speed=0.7,
        vision=0.6,
        metabolism=0.4,
        size=0.5,
        reproduction_threshold=0.8,
        mutation_rate=0.1,
    )

    original_values = {
        field.name: getattr(genome, field.name)
        for field in fields(genome)
    }

    mutate(
        genome,
        rng=random.Random(42),
        mutation_strength=0.5,
    )

    for name, value in original_values.items():
        assert getattr(genome, name) == value


def test_zero_mutation_rate_preserves_all_genes():
    genome = Genome(
        speed=0.7,
        vision=0.6,
        metabolism=0.4,
        size=0.5,
        reproduction_threshold=0.8,
        mutation_rate=0.0,
    )

    mutated = mutate(genome, rng=random.Random(42))

    for field in fields(genome):
        assert getattr(mutated, field.name) == getattr(
            genome, field.name
        )


def test_full_mutation_rate_keeps_genes_within_bounds():
    genome = Genome(
        speed=0.7,
        vision=0.6,
        metabolism=0.4,
        size=0.5,
        reproduction_threshold=0.8,
        mutation_rate=1.0,
    )

    mutated = mutate(
        genome,
        rng=random.Random(42),
        mutation_strength=0.5,
    )

    for field in fields(mutated):
        value = getattr(mutated, field.name)

        assert 0.0 <= value <= 1.0


def test_same_seed_produces_same_mutations():
    genome = Genome(
        speed=0.7,
        vision=0.6,
        metabolism=0.4,
        size=0.5,
        reproduction_threshold=0.8,
        mutation_rate=0.5,
    )

    first = mutate(genome, rng=random.Random(123))
    second = mutate(genome, rng=random.Random(123))

    for field in fields(genome):
        assert getattr(first, field.name) == getattr(
            second, field.name
        )


def test_invalid_mutation_rate_is_rejected():
    genome = Genome(
        speed=0.7,
        vision=0.6,
        metabolism=0.4,
        size=0.5,
        reproduction_threshold=0.8,
        mutation_rate=1.5,
    )

    try:
        mutate(genome, rng=random.Random(42))
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid mutation rate was accepted")
