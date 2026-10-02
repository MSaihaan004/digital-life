from dataclasses import dataclass
from .genome import Genome


@dataclass
class Organism:
    organism_id: int
    x: float
    y: float

    energy: float
    health: float
    age: int

    generation: int
    genome: Genome

    parent_id: int | None = None
    alive: bool = True
