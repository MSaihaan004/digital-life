from dataclasses import dataclass
import math

from config import MAX_ENERGY

from .organism import Organism


@dataclass
class SensorData:
    nearest_food_distance: float
    nearest_food_dx: float
    nearest_food_dy: float

    nearest_organism_distance: float
    nearest_organism_dx: float
    nearest_organism_dy: float

    energy_ratio: float

    boundary_left: float
    boundary_right: float
    boundary_top: float
    boundary_bottom: float


def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Food Sensing


def sense_nearest_food(organism, food):
    vision_range = organism.genome.vision * 200.0
    vision_squared = vision_range * vision_range

    nearest_squared = float("inf")
    nearest_dx = 0.0
    nearest_dy = 0.0

    for food_x, food_y in food:

        dx = food_x - organism.x
        dy = food_y - organism.y

        # Squared comparison preserves nearest-target ordering
        # (monotonic for non-negative distances) and avoids one
        # sqrt per candidate; sqrt is applied once below.
        squared = dx * dx + dy * dy

        # Ignore food outside the organism's vision
        if squared > vision_squared:
            continue

        if squared < nearest_squared:
            nearest_squared = squared
            nearest_dx = dx
            nearest_dy = dy

    if nearest_squared == float("inf"):
        return float("inf"), 0.0, 0.0

    return nearest_squared ** 0.5, nearest_dx, nearest_dy


# Organism Sensing

def sense_nearest_organism(organism, organisms):
    """Return nearest living organism within vision range.

    Vision restriction is applied consistently with food sensing:
    vision_range = vision * 200.0. Organisms beyond range are
    not detectable. Returns (inf, 0.0, 0.0) when none detectable.
    Pure read-only: never mutates world state.
    """
    vision_range = organism.genome.vision * 200.0
    vision_squared = vision_range * vision_range

    nearest_squared = float("inf")
    nearest_dx = 0.0
    nearest_dy = 0.0

    for other in organisms:

        if other.organism_id == organism.organism_id:
            continue

        if not other.alive:
            continue

        dx = other.x - organism.x
        dy = other.y - organism.y

        squared = dx * dx + dy * dy

        if squared > vision_squared:
            continue

        if squared < nearest_squared:
            nearest_squared = squared
            nearest_dx = dx
            nearest_dy = dy

    if nearest_squared == float("inf"):
        return float("inf"), 0.0, 0.0

    return nearest_squared ** 0.5, nearest_dx, nearest_dy

# Energy Sensing


def sense_energy(organism):

    return organism.energy / MAX_ENERGY

# Boundary Sensing


def sense_boundaries(organism, world):

    return (
        organism.x,
        world.width - organism.x,
        organism.y,
        world.height - organism.y
    )

# Combined Sensing Function


def sense(organism, world):

    (
        food_distance,
        food_dx,
        food_dy
    ) = sense_nearest_food(
        organism,
        world.food
    )

    (
        organism_distance,
        organism_dx,
        organism_dy
    ) = sense_nearest_organism(
        organism,
        world.organisms
    )

    energy_ratio = sense_energy(organism)

    (
        boundary_left,
        boundary_right,
        boundary_top,
        boundary_bottom
    ) = sense_boundaries(
        organism,
        world
    )

    return SensorData(
        nearest_food_distance=food_distance,
        nearest_food_dx=food_dx,
        nearest_food_dy=food_dy,

        nearest_organism_distance=organism_distance,
        nearest_organism_dx=organism_dx,
        nearest_organism_dy=organism_dy,

        energy_ratio=energy_ratio,

        boundary_left=boundary_left,
        boundary_right=boundary_right,
        boundary_top=boundary_top,
        boundary_bottom=boundary_bottom,
    )
