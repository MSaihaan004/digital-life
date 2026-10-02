from domain.world import World
from config import METABOLISM_COST_MULTIPLIER

def apply_metabolism_and_aging(world: World) -> None:
    for organism in world.organisms:
        if organism.alive:
            organism.age += 1
            
            energy_loss = METABOLISM_COST_MULTIPLIER * organism.genome.metabolism
            organism.energy -= energy_loss
            
            if organism.energy <= 0.0:
                organism.energy = 0.0
                organism.alive = False
