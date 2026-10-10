"""
Individual-level evolutionary analysis for Digital Life.

Measures:
- Survival and mortality
- Genome traits of living and dead organisms
- Reproductive success
- Correlations between genome traits and offspring counts
- Individual organism records exported to CSV
"""

import csv
from math import sqrt
from pathlib import Path
from statistics import mean

from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng


GENOME_TRAITS = (
    "speed",
    "vision",
    "metabolism",
    "size",
    "reproduction_threshold",
    "mutation_rate",
)


def create_initial_world(seed, population=100, food_count=200):
    """Create a reproducible initial world."""

    rng = create_rng(seed=seed)

    world = World(rng=rng)

    world.spawn_organisms(population)
    world.spawn_food(food_count)

    return world, rng


def calculate_correlation(x_values, y_values):
    """
    Calculate the Pearson correlation coefficient.

    Returns:
        A float between -1 and 1, or None if the
        correlation cannot be calculated.
    """

    if len(x_values) != len(y_values):
        raise ValueError(
            "Both lists must have the same number of values."
        )

    if len(x_values) < 2:
        return None

    x_mean = mean(x_values)
    y_mean = mean(y_values)

    x_differences = [
        value - x_mean
        for value in x_values
    ]

    y_differences = [
        value - y_mean
        for value in y_values
    ]

    numerator = sum(
        x_diff * y_diff
        for x_diff, y_diff in zip(
            x_differences,
            y_differences,
        )
    )

    x_squared = sum(
        difference ** 2
        for difference in x_differences
    )

    y_squared = sum(
        difference ** 2
        for difference in y_differences
    )

    denominator = sqrt(
        x_squared * y_squared
    )

    if denominator == 0:
        return None

    return numerator / denominator


def get_trait_values(organisms, trait):
    """Return a list of values for a particular genome trait."""

    return [
        getattr(organism.genome, trait)
        for organism in organisms
    ]


def calculate_trait_averages(organisms):
    """Calculate the average value of each genome trait."""

    if not organisms:
        return {
            trait: None
            for trait in GENOME_TRAITS
        }

    return {
        trait: mean(
            get_trait_values(organisms, trait)
        )
        for trait in GENOME_TRAITS
    }


def export_individual_records(organisms, seed):
    """Export organism information to a CSV file."""

    output_path = (
        Path("experiment_results")
        / f"individuals_seed_{seed}.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "organism_id",
        "parent_id",
        "generation",
        "alive_at_end",
        "age_at_end",
        "offspring_count",
        "speed",
        "vision",
        "metabolism",
        "size",
        "reproduction_threshold",
        "mutation_rate",
    ]

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for organism in organisms:

            writer.writerow({
                "organism_id": organism.organism_id,
                "parent_id": organism.parent_id,
                "generation": organism.generation,
                "alive_at_end": organism.alive,
                "age_at_end": organism.age,
                "offspring_count": organism.offspring_count,
                "speed": organism.genome.speed,
                "vision": organism.genome.vision,
                "metabolism": organism.genome.metabolism,
                "size": organism.genome.size,
                "reproduction_threshold": (
                    organism.genome.reproduction_threshold
                ),
                "mutation_rate": organism.genome.mutation_rate,
            })

    return output_path


def print_survival_comparison(living, dead):
    """Compare genome traits between living and dead organisms."""

    living_averages = calculate_trait_averages(living)
    dead_averages = calculate_trait_averages(dead)

    print("\nSURVIVAL GROUP COMPARISON")
    print("-" * 65)

    print(
        f"{'Trait':<27}"
        f"{'Living Avg.':>15}"
        f"{'Dead Avg.':>15}"
    )

    for trait in GENOME_TRAITS:

        living_value = living_averages[trait]
        dead_value = dead_averages[trait]

        living_text = (
            f"{living_value:.4f}"
            if living_value is not None
            else "N/A"
        )

        dead_text = (
            f"{dead_value:.4f}"
            if dead_value is not None
            else "N/A"
        )

        print(
            f"{trait:<27}"
            f"{living_text:>15}"
            f"{dead_text:>15}"
        )


def print_reproductive_success_analysis(organisms):
    """
    Examine correlations between genome traits
    and lifetime offspring counts.
    """

    print("\nREPRODUCTIVE SUCCESS ANALYSIS")
    print("-" * 80)

    print(
        f"{'Trait':<27}"
        f"{'Correlation':>15}"
        f"{'Interpretation':>30}"
    )

    offspring_counts = [
        organism.offspring_count
        for organism in organisms
    ]

    for trait in GENOME_TRAITS:

        trait_values = get_trait_values(
            organisms,
            trait,
        )

        correlation = calculate_correlation(
            trait_values,
            offspring_counts,
        )

        if correlation is None:
            correlation_text = "N/A"
            interpretation = "Undefined"

        else:
            correlation_text = f"{correlation:+.4f}"

            if correlation > 0.3:
                interpretation = "Positive association"

            elif correlation < -0.3:
                interpretation = "Negative association"

            else:
                interpretation = "Weak linear association"

        print(
            f"{trait:<27}"
            f"{correlation_text:>15}"
            f"{interpretation:>30}"
        )

    print(
        "\nNote: These correlations describe associations, "
        "not causation."
    )

    print(
        "Offspring counts are lifetime totals, so organisms "
        "of different ages have had different opportunities "
        "to reproduce."
    )


def run_experiment(seed=42, ticks=500):
    """Run a simulation and analyze its final population."""

    world, rng = create_initial_world(seed)

    engine = SimulationEngine(
        world,
        rng=rng,
    )

    # Preserve initial organisms for baseline comparisons.
    initial_organisms = list(world.organisms)

    initial_genome_averages = calculate_trait_averages(
        initial_organisms
    )

    # Run the simulation.
    engine.run(ticks)

    # Dead organisms remain in the world.
    all_organisms = list(world.organisms)

    living = [
        organism
        for organism in all_organisms
        if organism.alive
    ]

    dead = [
        organism
        for organism in all_organisms
        if not organism.alive
    ]

    final_genome_averages = calculate_trait_averages(
        living
    )

    # --------------------------------------------------
    # Experiment summary
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print(f"INDIVIDUAL-LEVEL ANALYSIS — SEED {seed}")
    print("=" * 70)

    print(f"Simulation ticks:        {world.tick}")
    print(f"Initial population:      {len(initial_organisms)}")
    print(f"Total organisms:         {len(all_organisms)}")
    print(f"Living organisms:        {len(living)}")
    print(f"Dead organisms:          {len(dead)}")

    # --------------------------------------------------
    # Initial versus final genome averages
    # --------------------------------------------------

    print("\nINITIAL VS FINAL GENOME AVERAGES")
    print("-" * 70)

    print(
        f"{'Trait':<27}"
        f"{'Initial':>12}"
        f"{'Final':>12}"
        f"{'Change':>12}"
    )

    for trait in GENOME_TRAITS:

        initial_value = initial_genome_averages[trait]
        final_value = final_genome_averages[trait]

        if initial_value is None or final_value is None:
            change = None
        else:
            change = final_value - initial_value

        initial_text = (
            f"{initial_value:.4f}"
            if initial_value is not None
            else "N/A"
        )

        final_text = (
            f"{final_value:.4f}"
            if final_value is not None
            else "N/A"
        )

        change_text = (
            f"{change:+.4f}"
            if change is not None
            else "N/A"
        )

        print(
            f"{trait:<27}"
            f"{initial_text:>12}"
            f"{final_text:>12}"
            f"{change_text:>12}"
        )

    # --------------------------------------------------
    # Survival analysis
    # --------------------------------------------------

    print_survival_comparison(
        living,
        dead,
    )

    # --------------------------------------------------
    # Reproductive success analysis
    # --------------------------------------------------

    if all_organisms:

        offspring_counts = [
            organism.offspring_count
            for organism in all_organisms
        ]

        print(
            "\nAverage lifetime offspring count:",
            f"{mean(offspring_counts):.3f}",
        )

        print_reproductive_success_analysis(
            all_organisms,
        )

    else:
        print("\nNo organisms are available for analysis.")

    # --------------------------------------------------
    # Export individual records
    # --------------------------------------------------

    output_path = export_individual_records(
        all_organisms,
        seed,
    )

    print(f"\nIndividual records saved to: {output_path}")

    return {
        "seed": seed,
        "ticks": world.tick,
        "total_population": len(all_organisms),
        "living_population": len(living),
        "dead_population": len(dead),
        "initial_genome_averages": initial_genome_averages,
        "final_genome_averages": final_genome_averages,
        "organisms": all_organisms,
    }


if __name__ == "__main__":
    run_experiment(
        seed=42,
        ticks=500,
    )
