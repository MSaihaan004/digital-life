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
    def random():
        return Genome(
            speed=random.uniform(0.0, 1.0),
            vision=random.uniform(0.0, 1.0),
            metabolism=random.uniform(0.0, 1.0),
            size=random.uniform(0.0, 1.0),
            reproduction_threshold=random.uniform(0.0, 1.0),
            mutation_rate=random.uniform(0.0, 1.0)
        )
