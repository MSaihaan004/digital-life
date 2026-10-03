from dataclasses import dataclass
import math

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

    nearest_distance = float("inf")
    nearest_dx = 0.0
    nearest_dy = 0.0

    for food_x, food_y in food:

        dx = food_x - organism.x
        dy = food_y - organism.y

        distance = math.sqrt(dx * dx + dy * dy)

        # Ignore food outside the organism's vision
        if distance > vision_range:
            continue

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_dx = dx
            nearest_dy = dy

    return nearest_distance, nearest_dx, nearest_dy


# Organism Sensing

def sense_nearest_organism(organism, organisms):

    nearest_distance = float("inf")
    nearest_dx = 0.0
    nearest_dy = 0.0

    for other in organisms:

        if other.organism_id == organism.organism_id:
            continue

        if not other.alive:
            continue

        dx = other.x - organism.x
        dy = other.y - organism.y

        distance = math.sqrt(dx * dx + dy * dy)

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_dx = dx
            nearest_dy = dy

    return nearest_distance, nearest_dx, nearest_dy

# Energy Sensing


def sense_energy(organism):

    return organism.energy / 100.0

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
