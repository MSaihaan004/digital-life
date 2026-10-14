"""Genome random/copy behavior (fills previously empty file)."""
from domain.genome import Genome
from simulation.randomness import create_rng


def test_random_genome_in_range():
    rng = create_rng(42)
    for _ in range(50):
        g = Genome.random(rng=rng)
        for name in ("speed", "vision", "metabolism", "size",
                     "reproduction_threshold", "mutation_rate"):
            assert 0.0 <= getattr(g, name) <= 1.0


def test_random_reproducible():
    a = Genome.random(rng=create_rng(9))
    b = Genome.random(rng=create_rng(9))
    assert a == b
