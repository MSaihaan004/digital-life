"""Selection strategies for Digital Life."""

import random


def calculate_fitness(organism, organisms=None):
    """
    Calculate reproductive fitness.

    When a non-empty collection is supplied, count the
    organism's direct offspring in that collection.

    Otherwise, use its persistent offspring counter.
    """
    if organisms:
        return sum(
            1
            for candidate in organisms
            if candidate.parent_id == organism.organism_id
        )

    return organism.offspring_count


def select_parent(organisms, rng=None):
    """
    Select a parent using fitness-proportionate selection.

    Organisms with greater reproductive fitness have a
    proportionally greater probability of selection.

    If all fitness values are zero, select uniformly
    from the eligible organisms.

    Args:
        organisms: Collection of eligible organisms.
        rng: Optional random-number generator.

    Returns:
        The selected organism.

    Raises:
        ValueError: If no organisms are supplied.
    """
    if not organisms:
        raise ValueError("Cannot select a parent from an empty population")

    if rng is None:
        rng = random

    fitness_values = [
        calculate_fitness(organism)
        for organism in organisms
    ]

    if any(fitness < 0 for fitness in fitness_values):
        raise ValueError("Fitness values cannot be negative")

    total_fitness = sum(fitness_values)

    if total_fitness == 0:
        return rng.choice(organisms)

    selection_point = rng.random() * total_fitness
    cumulative_fitness = 0

    for organism, fitness in zip(organisms, fitness_values):
        cumulative_fitness += fitness

        if selection_point < cumulative_fitness:
            return organism

    # Protect against floating-point edge cases.
    return organisms[-1]
