from brains.rule_brain import RuleBrain
from domain.sensors import sense

from simulation.physics import move_organism
from simulation.interactions import eat_food, apply_metabolism

from evolution.reproduction import can_reproduce, create_offspring
from evolution.mutation import mutate
from evolution.selection import select_parent
from evolution.metrics import EvolutionMetrics

from config import MAX_AGE


class SimulationEngine:

    def __init__(self, world, rng=None):
        self.world = world

        # Use the explicitly supplied RNG, or reuse the world's RNG.
        self.rng = (
            rng
            if rng is not None
            else getattr(world, "rng", None)
        )

        # Backward compatibility for worlds without an RNG.
        if self.rng is None:
            import random
            self.rng = random

        self.brain = RuleBrain()
        self.metrics = EvolutionMetrics()

    def step(self):
        """
        Advance the simulation by one tick.

        Existing organisms act first. After their actions finish,
        one eligible parent is selected to reproduce at most once.
        Newborns are registered at the end of the tick.
        """

        # Process only organisms that existed at the start of this tick.
        existing_organisms = list(self.world.organisms)

        # Keep newborns separate until the tick finishes.
        pending_offspring = []

        # Track living organisms before the tick.
        alive_before = {
            organism.organism_id
            for organism in existing_organisms
            if organism.alive
        }

        # Generate IDs above all existing organism IDs.
        next_organism_id = (
            max(
                (
                    organism.organism_id
                    for organism in self.world.organisms
                ),
                default=-1,
            )
            + 1
        )

        # Collect organisms that may reproduce after acting.
        eligible_parents = []

        # --------------------------------------------------
        # 1. Existing organisms act.
        # --------------------------------------------------
        for organism in existing_organisms:

            if not organism.alive:
                continue

            # Sense the environment.
            sensor_data = sense(
                organism,
                self.world,
            )

            # Decide what to do.
            action = self.brain.decide(sensor_data)

            # Execute the action.
            if action.value == "move":

                dx, dy = self.brain.movement_direction(
                    sensor_data,
                )

                move_organism(
                    organism,
                    dx,
                    dy,
                    self.world,
                )

            # Try to eat nearby food.
            eat_food(
                organism,
                self.world,
            )

            # Apply metabolism and aging.
            apply_metabolism(organism)
            organism.age += 1

            # Check whether the organism dies.
            if organism.energy <= 0:
                organism.alive = False

            if organism.age >= MAX_AGE:
                organism.alive = False

            # Collect eligible parents after their actions.
            if can_reproduce(organism):
                eligible_parents.append(organism)

        # --------------------------------------------------
        # 2. Select at most one parent.
        # --------------------------------------------------
        if eligible_parents:

            parent = select_parent(
                eligible_parents,
                rng=self.rng,
            )

            # --------------------------------------------------
            # 3. Create one offspring.
            # --------------------------------------------------
            child = create_offspring(
                parent=parent,
                world=self.world,
                organism_id=next_organism_id,
                rng=self.rng,
            )

            # --------------------------------------------------
            # 4. Mutate the offspring's genome.
            # --------------------------------------------------
            child.genome = mutate(
                child.genome,
                rng=self.rng,
            )

            # Defer registration until the end of the tick.
            pending_offspring.append(child)

        # --------------------------------------------------
        # 5. Register offspring.
        # --------------------------------------------------
        self.world.organisms.extend(pending_offspring)

        # Advance simulation time exactly once.
        self.world.tick += 1

        # Identify organisms that died during this tick.
        alive_after = {
            organism.organism_id
            for organism in self.world.organisms
            if organism.alive
        }

        deaths_this_tick = len(
            alive_before - alive_after
        )

        # --------------------------------------------------
        # 6. Record simulation and evolutionary metrics.
        # --------------------------------------------------
        self.metrics.record(
            self.world,
            births=len(pending_offspring),
            deaths=deaths_this_tick,
        )

    def run(self, ticks):
        """Run the simulation for the specified number of ticks."""

        for _ in range(ticks):
            self.step()
