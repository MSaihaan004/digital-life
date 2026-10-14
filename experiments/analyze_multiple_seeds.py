"""
Multi-seed evolutionary analysis for Digital Life.

Runs independent simulations and compares:
1. Population growth and survival.
2. Initial versus final genome traits.
3. Traits of living organisms versus all organisms.
4. Correlations between genome traits and reproductive success.
5. Variation in evolutionary outcomes across random seeds.

Results are exported to experiment_results/.
"""

from math import sqrt
from pathlib import Path
from statistics import mean, pstdev

from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng


# ---------------------------------------------------------
# EXPERIMENT CONFIGURATION
# ---------------------------------------------------------

NUMBER_OF_RUNS = 20
SIMULATION_TICKS = 500
INITIAL_POPULATION = 100
INITIAL_FOOD = 200

# Seeds 42 through 61 provide 20 reproducible runs.
RANDOM_SEEDS = list(range(42, 42 + NUMBER_OF_RUNS))

GENOME_TRAITS = (
    "speed",
    "vision",
    "metabolism",
    "size",
    "reproduction_threshold",
    "mutation_rate",
)

OUTPUT_DIRECTORY = Path("experiment_results")


# ---------------------------------------------------------
# STATISTICAL HELPERS
# ---------------------------------------------------------

def calculate_correlation(x_values, y_values):
    """
    Calculate the Pearson correlation coefficient.

    Returns:
        A value between -1 and +1, or None if the
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
        value - x_mean for value in x_values
    ]

    y_differences = [
        value - y_mean for value in y_values
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

    denominator = sqrt(x_squared * y_squared)

    if denominator == 0:
        return None

    return numerator / denominator


def get_trait_values(organisms, trait):
    """Return one genome trait value per organism."""

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
        trait: mean(get_trait_values(organisms, trait))
        for trait in GENOME_TRAITS
    }


def safe_correlation(x_values, y_values):
    """Format a correlation safely for CSV output."""

    result = calculate_correlation(x_values, y_values)

    if result is None:
        return ""

    return result


# ---------------------------------------------------------
# SIMULATION SETUP
# ---------------------------------------------------------

def create_initial_world(seed):
    """
    Create a reproducible world for one experiment.

    Each seed gets its own random-number generator.
    """

    rng = create_rng(seed=seed)

    world = World(rng=rng)

    world.spawn_organisms(INITIAL_POPULATION)
    world.spawn_food(INITIAL_FOOD)

    return world, rng


# ---------------------------------------------------------
# ONE EXPERIMENT
# ---------------------------------------------------------

def run_single_experiment(seed):
    """
    Run one simulation and return its measurements.
    """

    print(
        f"\nRunning seed {seed} "
        f"({SIMULATION_TICKS} ticks)..."
    )

    world, rng = create_initial_world(seed)

    engine = SimulationEngine(
        world,
        rng=rng,
    )

    # Capture the initial population before simulation.
    initial_organisms = list(world.organisms)

    initial_trait_averages = calculate_trait_averages(
        initial_organisms
    )

    # Run the simulation.
    engine.run(SIMULATION_TICKS)

    # Capture every organism, including dead organisms.
    all_organisms = list(world.organisms)

    living_organisms = [
        organism
        for organism in all_organisms
        if organism.alive
    ]

    dead_organisms = [
        organism
        for organism in all_organisms
        if not organism.alive
    ]

    # Calculate genome averages.
    living_trait_averages = calculate_trait_averages(
        living_organisms
    )

    all_trait_averages = calculate_trait_averages(
        all_organisms
    )

    # Population measurements.
    total_population = len(all_organisms)
    living_population = len(living_organisms)
    dead_population = len(dead_organisms)

    births = total_population - len(initial_organisms)
    deaths = dead_population

    if total_population:
        survival_fraction = (
            living_population / total_population
        )
    else:
        survival_fraction = 0.0

    if all_organisms:
        maximum_generation = max(
            organism.generation
            for organism in all_organisms
        )
    else:
        maximum_generation = 0

    # Correlations between traits and offspring counts.
    offspring_counts = [
        organism.offspring_count
        for organism in all_organisms
    ]

    reproductive_correlations = {}

    for trait in GENOME_TRAITS:
        trait_values = get_trait_values(
            all_organisms,
            trait,
        )

        reproductive_correlations[trait] = (
            safe_correlation(
                trait_values,
                offspring_counts,
            )
        )

    # Correlations between traits and survival status.
    #
    # A value of 1 means alive; 0 means dead.
    # This measures association, not causation.
    survival_status = [
        1 if organism.alive else 0
        for organism in all_organisms
    ]

    survival_correlations = {}

    for trait in GENOME_TRAITS:
        trait_values = get_trait_values(
            all_organisms,
            trait,
        )

        survival_correlations[trait] = (
            safe_correlation(
                trait_values,
                survival_status,
            )
        )

    # Construct a single summary record.
    result = {
        "seed": seed,
        "ticks": world.tick,
        "initial_population": len(initial_organisms),
        "total_population": total_population,
        "living_population": living_population,
        "dead_population": dead_population,
        "births": births,
        "deaths": deaths,
        "survival_fraction": survival_fraction,
        "maximum_generation": maximum_generation,
    }

    # Record initial, living, and all-organism trait averages.
    for trait in GENOME_TRAITS:
        result[f"initial_{trait}"] = (
            initial_trait_averages[trait]
        )

        result[f"living_{trait}"] = (
            living_trait_averages[trait]
        )

        result[f"all_{trait}"] = (
            all_trait_averages[trait]
        )

        result[f"reproduction_correlation_{trait}"] = (
            reproductive_correlations[trait]
        )

        result[f"survival_correlation_{trait}"] = (
            survival_correlations[trait]
        )

    # Return the results without retaining unnecessary
    # organism lists from every simulation.
    print(
        f"  Total: {total_population} | "
        f"Living: {living_population} | "
        f"Dead: {dead_population} | "
        f"Births: {births} | "
        f"Max generation: {maximum_generation}"
    )

    return result


# ---------------------------------------------------------
# CSV EXPORT
# ---------------------------------------------------------

def export_results(results, output_path=None, overwrite=False):
    """Save individual-run measurements to CSV.

    Column names and formats are unchanged. The write is atomic
    (temporary file + rename) and refuses to overwrite an existing
    file unless ``overwrite`` was explicitly requested.
    """

    from experiments.run_metadata import write_csv_exclusive

    if output_path is None:
        OUTPUT_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            OUTPUT_DIRECTORY
            / "multi_seed_summary.csv"
        )
    else:
        output_path = Path(output_path)

    if not results:
        raise ValueError(
            "No experiment results are available to export."
        )

    fieldnames = list(results[0].keys())

    return write_csv_exclusive(
        output_path, results, fieldnames, overwrite=overwrite
    )


# ---------------------------------------------------------
# CROSS-SEED SUMMARY
# ---------------------------------------------------------

def print_numeric_summary(results, field):
    """
    Print the mean, population standard deviation,
    minimum, and maximum across independent runs.
    """

    values = [
        result[field]
        for result in results
        if isinstance(result[field], (int, float))
        and result[field] is not None
    ]

    if not values:
        print(f"{field:<35} No data")
        return

    print(
        f"{field:<35}"
        f"{mean(values):>12.4f}"
        f"{pstdev(values):>12.4f}"
        f"{min(values):>12.4f}"
        f"{max(values):>12.4f}"
    )


def print_cross_seed_summary(results):
    """Display variation in outcomes across all runs."""

    print("\n")
    print("=" * 85)
    print("CROSS-SEED SUMMARY")
    print("=" * 85)

    print(f"Independent runs:       {len(results)}")
    print(f"Ticks per run:          {SIMULATION_TICKS}")
    print(f"Initial population:     {INITIAL_POPULATION}")
    print(f"Initial food:           {INITIAL_FOOD}")

    print("\nPOPULATION OUTCOMES")
    print("-" * 85)

    print(
        f"{'Metric':<35}"
        f"{'Mean':>12}"
        f"{'Std Dev':>12}"
        f"{'Minimum':>12}"
        f"{'Maximum':>12}"
    )

    population_fields = (
        "total_population",
        "living_population",
        "dead_population",
        "births",
        "deaths",
        "survival_fraction",
        "maximum_generation",
    )

    for field in population_fields:
        print_numeric_summary(results, field)

    print("\nFINAL TRAIT AVERAGES AMONG SURVIVORS")
    print("-" * 85)

    print(
        f"{'Trait':<35}"
        f"{'Mean':>12}"
        f"{'Std Dev':>12}"
        f"{'Minimum':>12}"
        f"{'Maximum':>12}"
    )

    for trait in GENOME_TRAITS:
        print_numeric_summary(
            results,
            f"living_{trait}",
        )

    print("\nFINAL TRAIT AVERAGES ACROSS ALL ORGANISMS")
    print("-" * 85)

    print(
        f"{'Trait':<35}"
        f"{'Mean':>12}"
        f"{'Std Dev':>12}"
        f"{'Minimum':>12}"
        f"{'Maximum':>12}"
    )

    for trait in GENOME_TRAITS:
        print_numeric_summary(
            results,
            f"all_{trait}",
        )

    print("\nTRAIT CORRELATIONS WITH REPRODUCTIVE SUCCESS")
    print("-" * 85)

    print(
        f"{'Trait':<35}"
        f"{'Mean correlation':>18}"
        f"{'Std Dev':>12}"
    )

    for trait in GENOME_TRAITS:
        field = f"reproduction_correlation_{trait}"

        values = [
            result[field]
            for result in results
            if isinstance(result[field], (int, float))
        ]

        if values:
            print(
                f"{trait:<35}"
                f"{mean(values):>18.4f}"
                f"{pstdev(values):>12.4f}"
            )
        else:
            print(
                f"{trait:<35}"
                f"{'N/A':>18}"
                f"{'N/A':>12}"
            )

    print("\nTRAIT CORRELATIONS WITH SURVIVAL")
    print("-" * 85)

    print(
        f"{'Trait':<35}"
        f"{'Mean correlation':>18}"
        f"{'Std Dev':>12}"
    )

    for trait in GENOME_TRAITS:
        field = f"survival_correlation_{trait}"

        values = [
            result[field]
            for result in results
            if isinstance(result[field], (int, float))
        ]

        if values:
            print(
                f"{trait:<35}"
                f"{mean(values):>18.4f}"
                f"{pstdev(values):>12.4f}"
            )
        else:
            print(
                f"{trait:<35}"
                f"{'N/A':>18}"
                f"{'N/A':>12}"
            )

    print("\nINTERPRETATION NOTES")
    print("-" * 85)
    print(
        "1. Each row represents one independent random seed."
    )
    print(
        "2. Standard deviation measures variation between runs."
    )
    print(
        "3. Trait-survival correlations describe associations, "
        "not causation."
    )
    print(
        "4. Lifetime offspring counts are affected by age and "
        "opportunity to reproduce."
    )
    print(
        "5. Living-organism averages are affected by both "
        "selection and mutation."
    )
    print(
        "6. Correlations across runs should be interpreted "
        "alongside their variation."
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def run_seeds(seeds):
    """Run one experiment per seed; return (results, run_statuses).

    Successful runs append their measurement record; failed seeds
    are recorded in ``run_statuses`` with their error and never
    reported as successful.
    """
    results = []
    run_statuses = []

    for seed in seeds:
        try:
            result = run_single_experiment(seed)
            results.append(result)
            run_statuses.append({"seed": seed, "status": "success"})
        except Exception as exc:
            run_statuses.append(
                {"seed": seed, "status": "failed", "error": str(exc)}
            )
            print(f"  Seed {seed} FAILED: {exc}")

    return results, run_statuses


def main(output_dir=None, overwrite=False):
    """Run all experiments and export the results.

    Each invocation writes to a unique run directory so existing
    ``experiment_results`` files are never silently overwritten.
    Pass an explicit ``output_dir`` (and ``overwrite=True`` to
    reuse it) only for testing or deliberate replacement.
    """

    print("=" * 85)
    print("DIGITAL LIFE — MULTI-SEED EVOLUTIONARY ANALYSIS")
    print("=" * 85)

    print(f"Number of runs:         {NUMBER_OF_RUNS}")
    print(f"Ticks per run:          {SIMULATION_TICKS}")
    print(f"Initial population:     {INITIAL_POPULATION}")
    print(f"Initial food:           {INITIAL_FOOD}")
    print(
        f"Seed range:             "
        f"{RANDOM_SEEDS[0]}–{RANDOM_SEEDS[-1]}"
    )

    results, run_statuses = run_seeds(RANDOM_SEEDS)

    from experiments.run_metadata import (
        build_run_metadata,
        unique_run_dir,
        write_metadata_sidecar,
    )

    if output_dir is None:
        run_dir = unique_run_dir(OUTPUT_DIRECTORY, "multi_seed_analysis")
    else:
        run_dir = Path(output_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

    metadata = build_run_metadata(
        experiment_id="multi_seed_analysis",
        seeds=RANDOM_SEEDS,
        ticks=SIMULATION_TICKS,
        extra={
            "initial_population": INITIAL_POPULATION,
            "initial_food": INITIAL_FOOD,
        },
        run_statuses=run_statuses,
    )
    sidecar = write_metadata_sidecar(run_dir, metadata, overwrite=overwrite)

    output_path = None
    if results:
        output_path = export_results(
            results, output_path=run_dir / "multi_seed_summary.csv",
            overwrite=overwrite,
        )
        metadata["extra"]["output_file"] = str(output_path)
    else:
        metadata["extra"]["output_file"] = None
    metadata["extra"]["output_files"] = [metadata["extra"]["output_file"]]
    metadata["extra"]["metadata_file"] = str(sidecar)
    write_metadata_sidecar(run_dir, metadata, overwrite=True)

    print_cross_seed_summary(results)

    print("\n")
    print("=" * 85)
    if metadata["failed_runs"]:
        print("EXPERIMENT COMPLETED WITH FAILURES")
    else:
        print("EXPERIMENT COMPLETED")
    print("=" * 85)
    print(f"Runs completed: {len(results)}")
    print(f"Successful runs: {metadata['successful_runs']}")
    print(f"Failed runs: {metadata['failed_runs']}")
    print(f"Results saved to: {output_path}")
    print(f"Run metadata saved to: {sidecar}")

    return results, metadata


if __name__ == "__main__":
    main()
