"""Genome representation for Digital Life."""

from dataclasses import dataclass
import random


@dataclass
class Genome:
    speed: float
    vision: float
    metabolism: float
    size: float
    reproduction_threshold: float
    mutation_rate: float

    @staticmethod
    def random(rng=None):
        """Generate a random genome.

        Args:
            rng: Optional random-number generator.
                 If omitted, Python's global random module is used.

        Returns:
            A Genome with each trait in the range [0.0, 1.0].
        """

        if rng is None:
            rng = random

        return Genome(
            speed=rng.uniform(0.0, 1.0),
            vision=rng.uniform(0.0, 1.0),
            metabolism=rng.uniform(0.0, 1.0),
            size=rng.uniform(0.0, 1.0),
            reproduction_threshold=rng.uniform(0.0, 1.0),
            mutation_rate=rng.uniform(0.0, 1.0),
        )
