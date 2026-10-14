"""World representation for Digital Life."""

from .organism import Organism
from .genome import Genome

from config import (
    WORLD_WIDTH,
    WORLD_HEIGHT,
    STARTING_ENERGY,
    STARTING_HEALTH,
)

from simulation.randomness import create_rng


class World:

    def __init__(
        self,
        width=WORLD_WIDTH,
        height=WORLD_HEIGHT,
        rng=None,
    ):
        self.width = width
        self.height = height

        # Use the supplied RNG or create a new one.
        self.rng = rng if rng is not None else create_rng()

        self.organisms = []
        self.food = []

        self.tick = 0

    def spawn_organism(
        self,
        organism_id,
        generation=0,
        parent_id=None,
    ):
        organism = Organism(
            organism_id=organism_id,
            x=self.rng.uniform(0, self.width),
            y=self.rng.uniform(0, self.height),
            energy=STARTING_ENERGY,
            health=STARTING_HEALTH,
            age=0,
            generation=generation,
            genome=Genome.random(rng=self.rng),
            parent_id=parent_id,
        )

        self.organisms.append(organism)

        return organism

    def spawn_organisms(self, count):

        # Allocate unique IDs above existing max (preserves uniqueness
        # across repeated calls; previously reused 0..count-1).
        next_id = (
            max(
                (o.organism_id for o in self.organisms),
                default=-1,
            )
            + 1
        )
        for _ in range(count):
            self.spawn_organism(organism_id=next_id)
            next_id += 1

    def spawn_food(self, count):

        for _ in range(count):

            food = (
                self.rng.uniform(0, self.width),
                self.rng.uniform(0, self.height),
            )

            self.food.append(food)
