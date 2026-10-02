import random

from .organism import Organism
from .genome import Genome

from config import (
    WORLD_WIDTH,
    WORLD_HEIGHT,
    STARTING_ENERGY,
    STARTING_HEALTH,
)


class World:

    def __init__(self, width=WORLD_WIDTH, height=WORLD_HEIGHT):
        self.width = width
        self.height = height

        self.organisms = []
        self.food = []

        self.tick = 0

    def spawn_organism(self, organism_id, generation=0, parent_id=None):

        organism = Organism(
            organism_id=organism_id,
            x=random.uniform(0, self.width),
            y=random.uniform(0, self.height),
            energy=STARTING_ENERGY,
            health=STARTING_HEALTH,
            age=0,
            generation=generation,
            genome=Genome.random(),
            parent_id=parent_id,
        )

        self.organisms.append(organism)

        return organism

    def spawn_organisms(self, count):

        for i in range(count):
            self.spawn_organism(
                organism_id=i
            )

    def spawn_food(self, count):

        for _ in range(count):

            food = (
                random.uniform(0, self.width),
                random.uniform(0, self.height)
            )

            self.food.append(food)
