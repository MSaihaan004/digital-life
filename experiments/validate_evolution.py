"""
Evolutionary behaviour validation for Digital Life.

Records population and genome statistics at regular intervals,
compares initial and final genome averages, and compares runs
using different random seeds.
"""

from pathlib import Path
from statistics import mean

from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng


SAMPLE_INTERVAL = 25
DEFAULT_TICKS = 500
DEFAULT_SEEDS = [42, 123, 456]

GENOME_TRAITS = (
    "speed",
    "vision",
    "metabolism",
    "size",
    "reproduction_threshold",
    "mutation_rate",
)


def create_initial_world(seed, population=100, food_count=200):
    """Create a reproducible world for an experiment."""

    rng = create_rng(seed=seed)
    world = World(rng=rng)

    world.spawn_organisms(population)
    world.spawn_food(food_count)

    return world, rng


def get_living_organisms(world):
    """Return organisms currently alive."""

    return [
        organism
        for organism in world.organisms
        if organism.alive
    ]


def calculate_genome_averages(organisms):
    """Calculate average values for each genome trait."""

    if not organisms:
        return {
            trait: None
            for trait in GENOME_TRAITS
        }

    return {
        trait: mean(
            getattr(organism.genome, trait)
            for organism in organisms
        )
        for trait in GENOME_TRAITS
    }


def calculate_population_statistics(world, engine, seed):
    """Create a snapshot of the current simulation state."""

    living = get_living_organisms(world)

    history = engine.metrics.get_history()

    # Metrics are recorded once per completed tick.
    cumulative_births = sum(
        snapshot["births"]
        for snapshot in history
    )

    cumulative_deaths = sum(
        snapshot["deaths"]
        for snapshot in history
    )

    genome_averages = calculate_genome_averages(living)

    snapshot = {
        "seed": seed,
        "tick": world.tick,
        "total_population": len(world.organisms),
        "living_population": len(living),
        "dead_population": len(world.organisms) - len(living),
        "cumulative_births": cumulative_births,
        "cumulative_deaths": cumulative_deaths,
        "average_energy": (
            mean(organism.energy for organism in living)
            if living else None
        ),
        "average_age": (
            mean(organism.age for organism in living)
            if living else None
        ),
        "average_generation": (
            mean(organism.generation for organism in living)
            if living else None
        ),
        "maximum_generation": max(
            (organism.generation for organism in living),
            default=None,
        ),
    }

    snapshot.update(genome_averages)

    return snapshot


def save_csv(rows, output_path, overwrite=False):
    """Write experiment snapshots to a CSV file.

    Column names and formats are unchanged. Refuses to overwrite
    an existing file unless ``overwrite`` was explicitly requested.
    """

    from experiments.run_metadata import write_csv_exclusive

    if not rows:
        return None

    return write_csv_exclusive(
        Path(output_path), rows, list(rows[0].keys()),
        overwrite=overwrite,
    )


def run_experiment(seed, ticks=DEFAULT_TICKS, output_path=None,
                     overwrite=False):
    """Run one experiment and sample its state over time."""

    world, rng = create_initial_world(seed)

    engine = SimulationEngine(
        world,
        rng=rng,
    )

    initial_population = get_living_organisms(world)

    initial_genome_averages = calculate_genome_averages(
        initial_population
    )

    samples = []

    # Record the initial state at tick zero.
    samples.append(
        calculate_population_statistics(
            world,
            engine,
            seed,
        )
    )

    print(f"\nRunning experiment with seed {seed}...")

    for _ in range(ticks):
        engine.step()

        # Record statistics at regular intervals and at the final tick.
        if (
            world.tick % SAMPLE_INTERVAL == 0
            or world.tick == ticks
        ):
            snapshot = calculate_population_statistics(
                world,
                engine,
                seed,
            )

            samples.append(snapshot)

    final_population = get_living_organisms(world)

    final_genome_averages = calculate_genome_averages(
        final_population
    )

    if output_path is None:
        output_path = (
            Path("experiment_results")
            / f"seed_{seed}.csv"
        )

    save_csv(samples, output_path, overwrite=overwrite)

    final_snapshot = samples[-1]

    print("\n" + "=" * 65)
    print(f"EXPERIMENT RESULTS — SEED {seed}")
    print("=" * 65)

    print(f"Ticks completed:       {world.tick}")
    print(f"Initial population:    {len(initial_population)}")
    print(f"Final total population:{len(world.organisms):>6}")
    print(f"Final living population:{len(final_population):>5}")
    print(f"Cumulative births:     {final_snapshot['cumulative_births']}")
    print(f"Cumulative deaths:     {final_snapshot['cumulative_deaths']}")
    print(f"Maximum generation:    {final_snapshot['maximum_generation']}")

    print("\nINITIAL VS FINAL GENOME AVERAGES")
    print("-" * 65)
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

    print(f"\nTime-series CSV saved to: {output_path}")

    return {
        "seed": seed,
        "samples": samples,
        "initial_genome_averages": initial_genome_averages,
        "final_genome_averages": final_genome_averages,
        "final_snapshot": final_snapshot,
    }


def print_comparison(results):
    """Compare the final results of multiple experiments."""

    print("\n\n" + "=" * 85)
    print("EXPERIMENT COMPARISON")
    print("=" * 85)

    print(
        f"{'Seed':<10}"
        f"{'Living':<12}"
        f"{'Births':<12}"
        f"{'Deaths':<12}"
        f"{'Max Gen.':<12}"
        f"{'Outcome':<15}"
    )

    print("-" * 85)

    for result in results:
        final = result["final_snapshot"]

        outcome = (
            "Surviving"
            if final["living_population"] > 0
            else "Extinct"
        )

        print(
            f"{result['seed']:<10}"
            f"{final['living_population']:<12}"
            f"{final['cumulative_births']:<12}"
            f"{final['cumulative_deaths']:<12}"
            f"{str(final['maximum_generation']):<12}"
            f"{outcome:<15}"
        )


def main(output_dir=None, overwrite=False, seeds=None, ticks=None):
    """Run the standard collection of experiments.

    Each invocation writes per-seed CSVs into a unique run
    directory so existing results are never silently overwritten.
    Failures are recorded per seed and reported explicitly.
    """

    from experiments.run_metadata import (
        build_run_metadata,
        unique_run_dir,
        write_metadata_sidecar,
    )

    seeds = list(DEFAULT_SEEDS if seeds is None else seeds)
    ticks = DEFAULT_TICKS if ticks is None else ticks

    if output_dir is None:
        run_dir = unique_run_dir(
            Path("experiment_results"), "validate_evolution"
        )
    else:
        run_dir = Path(output_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

    results = []
    run_statuses = []

    for seed in seeds:
        try:
            results.append(
                run_experiment(
                    seed=seed,
                    ticks=ticks,
                    output_path=run_dir / f"seed_{seed}.csv",
                    overwrite=overwrite,
                )
            )
            run_statuses.append({"seed": seed, "status": "success"})
        except Exception as exc:
            run_statuses.append(
                {"seed": seed, "status": "failed", "error": str(exc)}
            )
            print(f"  Seed {seed} FAILED: {exc}")

    metadata = build_run_metadata(
        experiment_id="validate_evolution",
        seeds=seeds,
        ticks=ticks,
        run_statuses=run_statuses,
    )
    sidecar = write_metadata_sidecar(run_dir, metadata, overwrite=overwrite)
    metadata["extra"] = {
        "output_files": [str(run_dir / f"seed_{seed}.csv") for seed in seeds],
        "output_file": str(run_dir / f"seed_{seeds[0]}.csv") if seeds else None,
        "metadata_file": str(sidecar),
    }
    write_metadata_sidecar(run_dir, metadata, overwrite=True)

    print_comparison([r for r in results if r is not None])

    if metadata["failed_runs"]:
        print(
            f"\nExperiment completed with failures "
            f"({metadata['failed_runs']} failed). "
            "Inspect the run metadata for details."
        )
    else:
        print(
            "\nAll experiments completed. "
            f"Inspect {run_dir}/ to compare the CSV files."
        )

    return results, metadata


if __name__ == "__main__":
    main()
