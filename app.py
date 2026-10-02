import random

from config import (
    RANDOM_SEED,
    INITIAL_POPULATION,
    INITIAL_FOOD,
)

from domain.world import World


def main():

    random.seed(RANDOM_SEED)

    world = World()

    world.spawn_organisms(INITIAL_POPULATION)
    world.spawn_food(INITIAL_FOOD)

    print("Digital Life started!")
    print("----------------------")

    print(f"World: {world.width} x {world.height}")
    print(f"Organisms: {len(world.organisms)}")
    print(f"Food: {len(world.food)}")

    print("\nFirst organism:")

    organism = world.organisms[0]

    print(f"ID: {organism.organism_id}")
    print(f"Position: ({organism.x:.2f}, {organism.y:.2f})")
    print(f"Energy: {organism.energy}")
    print(f"Health: {organism.health}")
    print(f"Generation: {organism.generation}")

    print("\nGenome:")
    print(organism.genome)


if __name__ == "__main__":
    main()
