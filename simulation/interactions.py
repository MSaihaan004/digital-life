import math

from config import MAX_ENERGY, FOOD_ENERGY, EAT_DISTANCE


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
