import math

from config import (
    MAX_ENERGY,
    FOOD_ENERGY,
    EAT_DISTANCE,
    FOOD_TARGET_COUNT,
    FOOD_MAX_COUNT,
    FOOD_RESPAWN_PER_TICK,
)


def eat_food(organism, world):
    """
    Check whether the organism is close enough to food to eat it.

    Returns True if food was consumed, otherwise False.
    """

    for index, (food_x, food_y) in enumerate(world.food):

        dx = food_x - organism.x
        dy = food_y - organism.y

        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= EAT_DISTANCE:

            # Remove the food from the world.
            world.food.pop(index)

            # Increase organism energy.
            organism.energy = min(
                organism.energy + FOOD_ENERGY,
                MAX_ENERGY
            )

            return True

    return False

# Metabolism


def apply_metabolism(organism):
    """
    Consume energy based on the organism's metabolism gene.
    """

    metabolism_cost = organism.genome.metabolism

    organism.energy -= metabolism_cost

    if organism.energy < 0:
        organism.energy = 0


def respawn_food(world):
    """
    Replenish food toward the configured target level.

    Food is only ever consumed during the act phase, so without
    replenishment the world starves and the simulation ends
    abruptly. Each call spawns at most FOOD_RESPAWN_PER_TICK
    items (gradual regrowth, not an instant refill) and never
    lets the total exceed FOOD_MAX_COUNT.

    Returns the number of food items spawned.
    """

    current = len(world.food)

    if current >= FOOD_TARGET_COUNT:
        return 0

    room = FOOD_MAX_COUNT - current

    if room <= 0:
        return 0

    count = min(
        FOOD_TARGET_COUNT - current,
        FOOD_RESPAWN_PER_TICK,
        room,
    )

    if count <= 0:
        return 0

    world.spawn_food(count)

    return count
