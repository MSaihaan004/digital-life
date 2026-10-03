from brains.rule_brain import RuleBrain
from domain.sensors import sense
from simulation.physics import move_organism
from simulation.interactions import eat_food, apply_metabolism
from config import MAX_AGE


class SimulationEngine:

    def __init__(self, world):
        self.world = world
        self.brain = RuleBrain()

    def step(self):
        """
        Advance the simulation by one tick.
        """

        for organism in self.world.organisms:

            if not organism.alive:
                continue

            # 1. Sense the environment
            sensor_data = sense(
                organism,
                self.world
            )

            # 2. Decide what to do
            action = self.brain.decide(
                sensor_data
            )

            # 3. Execute the action
            if action.value == "move":

                dx, dy = self.brain.movement_direction(
                    sensor_data
                )

                move_organism(
                    organism,
                    dx,
                    dy,
                    self.world
                )

            # 4. Try to eat nearby food
            ate_food = eat_food(
                organism,
                self.world
            )

            # 5. Apply metabolism
            apply_metabolism(organism)
            organism.age += 1

            if organism.energy <= 0:
                organism.alive = False

            if organism.age >= MAX_AGE:
                organism.alive = False

        # Advance simulation time ONCE per simulation step
        self.world.tick += 1

    def run(self, ticks):
        """
        Run the simulation for a given number of ticks.
        """

        for _ in range(ticks):
            self.step()
