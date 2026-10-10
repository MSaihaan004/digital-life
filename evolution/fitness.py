"""Fitness-related measurements for Digital Life."""


def measure_survival(organism):
    """
    Return whether an organism is alive.

    Returns:
        bool: True if the organism is alive and has positive health.
    """
    return organism.alive and organism.health > 0


def measure_lifespan(organism):
    """
    Return the organism's current age in simulation ticks.

    Returns:
        int: Number of ticks the organism has lived.
    """
    return organism.age


def measure_reproductive_success(organism):
    """
    Return the organism's lifetime offspring count.

    Returns:
        int: Number of offspring produced.
    """
    return organism.offspring_count
