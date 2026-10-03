import random

from config import (
    RANDOM_SEED,
    INITIAL_POPULATION,
    INITIAL_FOOD,
)

from domain.world import World
from simulation.engine import SimulationEngine


def main():

    random.seed(RANDOM_SEED)

    world = World()

    world.spawn_organisms(INITIAL_POPULATION)
    world.spawn_food(INITIAL_FOOD)

    engine = SimulationEngine(world)

    print("Digital Life started!")
    print("----------------------")

    print(f"World: {world.width} x {world.height}")
    print(f"Organisms: {len(world.organisms)}")
    print(f"Food: {len(world.food)}")

    organism = world.organisms[0]

    print("\nInitial state:")
    print(f"Position: ({organism.x:.2f}, {organism.y:.2f})")
    print(f"Energy: {organism.energy}")

    print("\nRunning simulation...")

    for tick in range(10):

        engine.step()

        print(
            f"Tick {tick + 1}: "
            f"Position = "
            f"({organism.x:.2f}, {organism.y:.2f}) "
            f"Energy = {organism.energy:.2f}"
        )

    print("\nSimulation finished.")
    print(f"World tick: {world.tick}")
    print(f"Organism age: {organism.age}")
    print(f"Organism alive: {organism.alive}")


if __name__ == "__main__":
    main()
