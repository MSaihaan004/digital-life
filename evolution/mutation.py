import random
from copy import deepcopy
from dataclasses import fields


def mutate(genome, rng=None, mutation_strength=0.1):
    """
    Create a mutated copy of a genome.

    Each gene has a probability equal to the genome's mutation_rate
    of being mutated.

    Mutation adds Gaussian noise to the selected gene. The resulting
    value is clipped to the range [0.0, 1.0].

    Args:
        genome: The original Genome object.
        rng: Optional random number generator.
        mutation_strength: Standard deviation of Gaussian mutation noise.

    Returns:
        A new Genome object with possible mutations.
    """

    if rng is None:
        rng = random

    if not 0.0 <= mutation_strength:
        raise ValueError("mutation_strength must be non-negative")

    mutation_rate = genome.mutation_rate

    if not 0.0 <= mutation_rate <= 1.0:
        raise ValueError("mutation_rate must be between 0.0 and 1.0")

    mutated_genome = deepcopy(genome)

    for gene in fields(mutated_genome):
        gene_name = gene.name

        original_value = getattr(mutated_genome, gene_name)

        if not isinstance(original_value, (int, float)):
            continue

        if not 0.0 <= original_value <= 1.0:
            raise ValueError(
                f"Gene '{gene_name}' must be between 0.0 and 1.0"
            )

        if rng.random() < mutation_rate:
            noise = rng.gauss(0.0, mutation_strength)

            mutated_value = original_value + noise

            mutated_value = max(0.0, min(1.0, mutated_value))

            setattr(mutated_genome, gene_name, mutated_value)

    return mutated_genome
