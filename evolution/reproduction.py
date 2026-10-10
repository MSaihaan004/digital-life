"""Asexual reproduction mechanics for Digital Life."""

import random

from dataclasses import replace

from config import (
    MAX_ENERGY,
    REPRODUCTION_ENERGY_COST,
    STARTING_HEALTH,
)

from domain.organism import Organism


def can_reproduce(organism: Organism) -> bool:
    """Return whether a living organism has enough energy to reproduce.

    The genome's reproduction_threshold is normalized to [0, 1].
    It is converted to the simulation's energy scale using MAX_ENERGY.

    The organism must:
    - Be alive.
    - Have positive health.
    - Meet its reproduction threshold.
    - Have enough energy to pay the reproduction cost.
    """

    if not organism.alive or organism.health <= 0:
        return False

    threshold = (
        organism.genome.reproduction_threshold * MAX_ENERGY
    )

    return (
        organism.energy >= threshold
        and organism.energy >= REPRODUCTION_ENERGY_COST
    )


def create_offspring(
    parent: Organism,
    world,
    organism_id: int,
    *,
    energy_cost: float = REPRODUCTION_ENERGY_COST,
    rng=None,
) -> Organism:
    """Create an offspring without registering it in the world.

    The offspring inherits a separate copy of the parent's genome.
    Genetic mutation is handled by evolution.mutation.

    Args:
        parent: The parent organism.
        world: The world containing the parent.
        organism_id: Unique ID assigned to the offspring.
        energy_cost: Energy transferred from parent to offspring.
        rng: Optional random-number generator. When supplied, it
             controls the offspring's position.

    Returns:
        The newly created offspring.

    Raises:
        ValueError: If reproduction is invalid.
    """

    # Preserve backward compatibility when no RNG is supplied.
    if rng is None:
        rng = random

    # Validate the reproduction cost.
    if energy_cost < 0:
        raise ValueError("energy_cost cannot be negative")

    # The parent must be alive and healthy.
    if not parent.alive or parent.health <= 0:
        raise ValueError(
            "A dead or unhealthy organism cannot reproduce"
        )

    # The parent must meet its reproduction threshold.
    threshold = (
        parent.genome.reproduction_threshold * MAX_ENERGY
    )

    if parent.energy < threshold:
        raise ValueError(
            "Parent has not reached its reproduction threshold"
        )

    # The parent must be able to pay the reproduction cost.
    if parent.energy < energy_cost:
        raise ValueError(
            "Parent does not have enough energy to pay reproduction cost"
        )

    # Prevent duplicate organism IDs.
    if any(
        existing.organism_id == organism_id
        for existing in world.organisms
    ):
        raise ValueError(
            f"Organism ID {organism_id} already exists in the world"
        )

    # Generate the offspring's position near the parent.
    child_x = min(
        max(
            parent.x + rng.uniform(-5.0, 5.0),
            0.0,
        ),
        world.width,
    )

    child_y = min(
        max(
            parent.y + rng.uniform(-5.0, 5.0),
            0.0,
        ),
        world.height,
    )

    # Create the offspring with a separate genome copy.
    child = Organism(
        organism_id=organism_id,
        x=child_x,
        y=child_y,
        energy=energy_cost,
        health=STARTING_HEALTH,
        age=0,
        generation=parent.generation + 1,
        genome=replace(parent.genome),
        parent_id=parent.organism_id,
    )

    # Transfer energy only after successful offspring creation.
    parent.energy -= energy_cost
    parent.offspring_count += 1

    # Do not register the child here.
    # The simulation engine handles registration after mutation.
    return child
