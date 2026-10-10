"""
Controlled metabolism experiment for Digital Life.

Compares five fixed metabolism values across multiple seeds.

Measurements:
- Final living population
- Total births
- Total deaths
- Survival fraction
- Average generation
- Maximum generation
- Average age of dead organisms
- Average energy among surviving organisms

All genome traits except metabolism continue to evolve normally.

Metabolism is reset to the experimental value after each tick,
including for newly created offspring.

Results are exported to experiment_results/.
"""

import csv
from pathlib import Path
from statistics import mean, pstdev

from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng


# ---------------------------------------------------------
# EXPERIMENT CONFIGURATION
# ---------------------------------------------------------

METABOLISM_LEVELS = (
    0.05,
    0.20,
    0.40,
    0.60,
    0.80,
)

RANDOM_SEEDS = tuple(range(42, 52))

SIMULATION_TICKS = 500

INITIAL_POPULATION = 100
INITIAL_FOOD = 200

OUTPUT_DIRECTORY = Path("experiment_results")


# ---------------------------------------------------------
# SIMULATION SETUP
# ---------------------------------------------------------

def create_initial_world(seed):
    """Create a reproducible initial world."""

    rng = create_rng(seed=seed)

    world = World(rng=rng)

    world.spawn_organisms(INITIAL_POPULATION)
    world.spawn_food(INITIAL_FOOD)

    return world, rng


def enforce_metabolism(world, metabolism_value):
    """
    Set the metabolism trait of every organism to the
    experimental value.

    This also resets the trait for newly created offspring.
    """

    for organism in world.organisms:
        organism.genome.metabolism = metabolism_value


# ---------------------------------------------------------
# SINGLE EXPERIMENT
# ---------------------------------------------------------

def run_single_experiment(metabolism_value, seed):
    """
    Run one simulation with a fixed metabolism value.

    The simulation's other mechanics remain unchanged.
    """

    world, rng = create_initial_world(seed)

    # Apply the experimental condition before the first tick.
    enforce_metabolism(world, metabolism_value)

    engine = SimulationEngine(
        world,
        rng=rng,
    )

    initial_organism_ids = {
        organism.organism_id
        for organism in world.organisms
    }

    # Advance one tick at a time so metabolism can be
    # controlled before and after every engine step.
    for _ in range(SIMULATION_TICKS):

        # Ensure every existing organism has the fixed value.
        enforce_metabolism(world, metabolism_value)

        engine.step()

        # The engine may have created and mutated an offspring.
        # Reset metabolism immediately after that step.
        enforce_metabolism(world, metabolism_value)

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

    total_population = len(all_organisms)
    living_population = len(living)
    dead_population = len(dead)

    births = sum(
        1
        for organism in all_organisms
        if organism.organism_id not in initial_organism_ids
    )

    # Count organisms that were initially present and
    # are dead at the end separately from later-born deaths.
    initial_dead = sum(
        1
        for organism in all_organisms
        if (
            organism.organism_id in initial_organism_ids
            and not organism.alive
        )
    )

    if total_population:
        survival_fraction = (
            living_population / total_population
        )
    else:
        survival_fraction = 0.0

    if living:
        average_energy_living = mean(
            organism.energy
            for organism in living
        )

        average_age_living = mean(
            organism.age
            for organism in living
        )

        average_generation_living = mean(
            organism.generation
            for organism in living
        )
    else:
        average_energy_living = None
        average_age_living = None
        average_generation_living = None

    if dead:
        average_age_dead = mean(
            organism.age
            for organism in dead
        )
    else:
        average_age_dead = None

    maximum_generation = (
        max(
            organism.generation
            for organism in all_organisms
        )
        if all_organisms
        else 0
    )

    total_offspring = sum(
        organism.offspring_count
        for organism in all_organisms
    )

    average_offspring_per_organism = (
        total_offspring / total_population
        if total_population
        else 0.0
    )

    result = {
        "metabolism": metabolism_value,
        "seed": seed,
        "ticks": world.tick,
        "initial_population": len(initial_organism_ids),
        "total_population": total_population,
        "living_population": living_population,
        "dead_population": dead_population,
        "births": births,
        "initial_dead": initial_dead,
        "survival_fraction": survival_fraction,
        "average_energy_living": average_energy_living,
        "average_age_living": average_age_living,
        "average_age_dead": average_age_dead,
        "average_generation_living": average_generation_living,
        "maximum_generation": maximum_generation,
        "total_offspring": total_offspring,
        "average_offspring_per_organism": (
            average_offspring_per_organism
        ),
    }

    print(
        f"  Seed {seed}: "
        f"living={living_population}, "
        f"total={total_population}, "
        f"births={births}, "
        f"max_generation={maximum_generation}"
    )

    return result


# ---------------------------------------------------------
# CSV EXPORT
# ---------------------------------------------------------

def export_results(results):
    """Save all individual experiment results to CSV."""

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIRECTORY
        / "metabolism_experiment.csv"
    )

    if not results:
        raise ValueError(
            "Cannot export an empty experiment."
        )

    fieldnames = list(results[0].keys())

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
        writer.writerows(results)

    return output_path


# ---------------------------------------------------------
# SUMMARY HELPERS
# ---------------------------------------------------------

def get_numeric_values(results, field):
    """Return available numeric values for a result field."""

    return [
        result[field]
        for result in results
        if isinstance(result[field], (int, float))
        and result[field] is not None
    ]


def print_summary_metric(results, field):
    """Print mean and standard deviation for one metric."""

    values = get_numeric_values(results, field)

    if not values:
        print(
            f"{field:<35}"
            f"{'N/A':>12}"
            f"{'N/A':>12}"
        )
        return

    print(
        f"{field:<35}"
        f"{mean(values):>12.3f}"
        f"{pstdev(values):>12.3f}"
    )


# ---------------------------------------------------------
# CROSS-CONDITION SUMMARY
# ---------------------------------------------------------

def print_condition_summary(all_results):
    """Compare average outcomes at each metabolism value."""

    print("\n")
    print("=" * 85)
    print("CONTROLLED METABOLISM EXPERIMENT — RESULTS")
    print("=" * 85)

    print(
        f"{'Metabolism':>12}"
        f"{'Living Mean':>14}"
        f"{'Living SD':>12}"
        f"{'Births Mean':>14}"
        f"{'Survival %':>12}"
        f"{'Max Gen.':>11}"
    )

    print("-" * 85)

    for metabolism_value in METABOLISM_LEVELS:

        condition_results = [
            result
            for result in all_results
            if result["metabolism"] == metabolism_value
        ]

        living_values = get_numeric_values(
            condition_results,
            "living_population",
        )

        birth_values = get_numeric_values(
            condition_results,
            "births",
        )

        survival_values = get_numeric_values(
            condition_results,
            "survival_fraction",
        )

        generation_values = get_numeric_values(
            condition_results,
            "maximum_generation",
        )

        living_mean = mean(living_values)
        living_sd = pstdev(living_values)

        births_mean = mean(birth_values)

        survival_percent = (
            100 * mean(survival_values)
        )

        maximum_generation_mean = mean(
            generation_values
        )

        print(
            f"{metabolism_value:>12.2f}"
            f"{living_mean:>14.2f}"
            f"{living_sd:>12.2f}"
            f"{births_mean:>14.2f}"
            f"{survival_percent:>11.2f}%"
            f"{maximum_generation_mean:>11.2f}"
        )

    print("\n")
    print("=" * 85)
    print("ADDITIONAL METRICS")
    print("=" * 85)

    metrics = (
        "total_population",
        "average_energy_living",
        "average_age_living",
        "average_age_dead",
        "average_generation_living",
        "total_offspring",
        "average_offspring_per_organism",
    )

    for metabolism_value in METABOLISM_LEVELS:

        condition_results = [
            result
            for result in all_results
            if result["metabolism"] == metabolism_value
        ]

        print(
            f"\nMetabolism = {metabolism_value:.2f}"
        )

        for field in metrics:
            print_summary_metric(
                condition_results,
                field,
            )

    print("\n")
    print("=" * 85)
    print("EXPERIMENT NOTES")
    print("=" * 85)

    print(
        "1. Metabolism is held fixed throughout each run."
    )
    print(
        "2. Other genome traits can still mutate."
    )
    print(
        "3. Each condition uses the same set of random seeds."
    )
    print(
        "4. Outcomes can diverge because the conditions "
        "change organism behavior."
    )
    print(
        "5. Survival fraction means living organisms divided "
        "by all organisms created."
    )
    print(
        "6. Average age among living organisms is not their "
        "eventual lifespan."
    )
    print(
        "7. Results describe this model and do not establish "
        "universal biological rules."
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    """Run all metabolism conditions."""

    print("=" * 85)
    print("DIGITAL LIFE — CONTROLLED METABOLISM EXPERIMENT")
    print("=" * 85)

    print(f"Metabolism conditions: {len(METABOLISM_LEVELS)}")
    print(f"Runs per condition:    {len(RANDOM_SEEDS)}")
    print(f"Ticks per run:         {SIMULATION_TICKS}")
    print(f"Initial population:    {INITIAL_POPULATION}")
    print(f"Initial food:          {INITIAL_FOOD}")
    print(
        f"Seeds:                 "
        f"{RANDOM_SEEDS[0]}–{RANDOM_SEEDS[-1]}"
    )

    all_results = []

    for metabolism_value in METABOLISM_LEVELS:

        print("\n")
        print("-" * 85)
        print(
            f"TESTING METABOLISM = {metabolism_value:.2f}"
        )
        print("-" * 85)

        for seed in RANDOM_SEEDS:

            result = run_single_experiment(
                metabolism_value=metabolism_value,
                seed=seed,
            )

            all_results.append(result)

    output_path = export_results(all_results)

    print_condition_summary(all_results)

    print("\n")
    print("=" * 85)
    print("EXPERIMENT COMPLETED")
    print("=" * 85)
    print(f"Completed runs: {len(all_results)}")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
