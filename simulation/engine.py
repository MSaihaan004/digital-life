from domain.world import World
from simulation.rules import apply_metabolism_and_aging

class SimulationEngine:
    def __init__(self, world: World) -> None:
        self.world = world
        
    def tick(self) -> None:
        self.world.tick += 1
        apply_metabolism_and_aging(self.world)
