import random

from config import (
    RANDOM_SEED,
    INITIAL_POPULATION,
    INITIAL_FOOD,
    SIMULATION_TICKS,
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

    print("\nInitial organism [0]:")
    organism = world.organisms[0]
    print(f"ID: {organism.organism_id}")
    print(f"Age: {organism.age}")
    print(f"Energy: {organism.energy:.2f}")
    print(f"Alive: {organism.alive}")

    print(f"\nRunning {SIMULATION_TICKS} ticks...")
    for _ in range(SIMULATION_TICKS):
        engine.tick()
        
    print("\nSimulation complete!")
    print(f"Current Tick: {world.tick}")
    alive_count = sum(1 for o in world.organisms if o.alive)
    print(f"Population Alive: {alive_count} / {len(world.organisms)}")
    
    print("\nFinal organism [0]:")
    print(f"ID: {organism.organism_id}")
    print(f"Age: {organism.age}")
    print(f"Energy: {organism.energy:.2f}")
    print(f"Alive: {organism.alive}")


if __name__ == "__main__":
    main()

