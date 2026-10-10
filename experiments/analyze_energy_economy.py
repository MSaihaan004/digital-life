"""
Energy economy analysis for Digital Life.

Measures:
- Energy consumed through metabolism.
- Energy gained through food.
- Food-consumption events.
- Population size and survival over time.
- Births and deaths.
- Organism ages and energy reserves.
- Reproductive output.

Runs five fixed metabolism conditions across ten seeds.

The experiment temporarily wraps existing interaction functions
to collect measurements without permanently modifying the
simulation implementation.
"""

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from unittest.mock import patch

from config import FOOD_ENERGY
from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng
from simulation import interactions


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
SNAPSHOT_INTERVAL = 25

OUTPUT_DIRECTORY = Path("experiment_results")


# ---------------------------------------------------------
# WORLD SETUP
# ---------------------------------------------------------

def create_initial_world(seed):
    """Create a reproducible initial world."""

    rng = create_rng(seed=seed)

    world = World(rng=rng)

    world.spawn_organisms(INITIAL_POPULATION)
    world.spawn_food(INITIAL_FOOD)

    return world, rng


def enforce_metabolism(world, metabolism_value):
    """Keep metabolism fixed for every organism."""

    for organism in world.organisms:
        organism.genome.metabolism = metabolism_value


# ---------------------------------------------------------
# ENERGY MEASUREMENT
# ---------------------------------------------------------

class EnergyTracker:
    """
    Collect energy measurements for one simulation.

    Counters are reset for every experiment.
    """

    def __init__(self):
        self.metabolic_energy_consumed = 0.0
        self.energy_gained_from_food = 0.0
        self.food_consumption_events = 0
        self.metabolism_events = 0

    def record_metabolism(self, organism):
        """
        Record the energy cost before applying metabolism.

        The value follows the current implementation:
        the metabolism gene determines energy lost per tick.
        """

        cost = organism.genome.metabolism

        self.metabolic_energy_consumed += max(
            0.0,
            min(cost, organism.energy),
        )

        self.metabolism_events += 1

    def record_food(self, energy_gained):
        """Record energy gained from a successful food event."""

        self.energy_gained_from_food += energy_gained
        self.food_consumption_events += 1


# ---------------------------------------------------------
# POPULATION SNAPSHOTS
# ---------------------------------------------------------

def create_population_snapshot(
    world,
    metabolism_value,
    seed,
    births,
    deaths,
):
    """Create a measurement row for the current tick."""

    organisms = list(world.organisms)

    living = [
        organism
        for organism in organisms
        if organism.alive
    ]

    dead = [
        organism
        for organism in organisms
        if not organism.alive
    ]

    if living:
        average_energy = mean(
            organism.energy
            for organism in living
        )

        minimum_energy = min(
            organism.energy
            for organism in living
        )

        maximum_energy = max(
            organism.energy
            for organism in living
        )

        average_living_age = mean(
            organism.age
            for organism in living
        )

    else:
        average_energy = None
        minimum_energy = None
        maximum_energy = None
        average_living_age = None

    if dead:
        average_dead_age = mean(
            organism.age
            for organism in dead
        )
    else:
        average_dead_age = None

    return {
        "seed": seed,
        "metabolism": metabolism_value,
        "tick": world.tick,
        "total_population": len(organisms),
        "living_population": len(living),
        "dead_population": len(dead),
        "food_remaining": len(world.food),
        "births_so_far": births,
        "deaths_so_far": deaths,
        "average_living_energy": average_energy,
        "minimum_living_energy": minimum_energy,
        "maximum_living_energy": maximum_energy,
        "average_living_age": average_living_age,
        "average_dead_age": average_dead_age,
    }


# ---------------------------------------------------------
# ONE SIMULATION
# ---------------------------------------------------------

def run_single_experiment(metabolism_value, seed):
    """Run one instrumented simulation."""

    print(
        f"  Running seed {seed}, "
        f"metabolism={metabolism_value:.2f}..."
    )

    world, rng = create_initial_world(seed)

    enforce_metabolism(
        world,
        metabolism_value,
    )

    engine = SimulationEngine(
        world,
        rng=rng,
    )

    tracker = EnergyTracker()

    initial_ids = {
        organism.organism_id
        for organism in world.organisms
    }

    snapshots = []

    # Preserve the original functions so they can be restored
    # automatically after the experiment.
    original_metabolism = interactions.apply_metabolism
    original_eat_food = interactions.eat_food

    def tracked_metabolism(organism):
        tracker.record_metabolism(organism)
        return original_metabolism(organism)

    def tracked_eat_food(organism, target_world):
        energy_before = organism.energy

        ate_food = original_eat_food(
            organism,
            target_world,
        )

        if ate_food:
            energy_gained = organism.energy - energy_before

            tracker.record_food(energy_gained)

        return ate_food

    # The engine imports these functions directly, so we patch
    # the names in simulation.engine as well as interactions.
    import simulation.engine as engine_module

    initial_death_ids = set()

    with (
        patch.object(
            interactions,
            "apply_metabolism",
            tracked_metabolism,
        ),
        patch.object(
            interactions,
            "eat_food",
            tracked_eat_food,
        ),
        patch.object(
            engine_module,
            "apply_metabolism",
            tracked_metabolism,
        ),
        patch.object(
            engine_module,
            "eat_food",
            tracked_eat_food,
        ),
    ):

        for _ in range(SIMULATION_TICKS):

            enforce_metabolism(
                world,
                metabolism_value,
            )

            previously_alive = {
                organism.organism_id
                for organism in world.organisms
                if organism.alive
            }

            engine.step()

            enforce_metabolism(
                world,
                metabolism_value,
            )

            currently_alive = {
                organism.organism_id
                for organism in world.organisms
                if organism.alive
            }

            initial_death_ids.update(
                previously_alive - currently_alive
            )

            if (
                world.tick % SNAPSHOT_INTERVAL == 0
                or world.tick == SIMULATION_TICKS
            ):
                all_ids = {
                    organism.organism_id
                    for organism in world.organisms
                }

                births_so_far = len(
                    all_ids - initial_ids
                )

                deaths_so_far = sum(
                    1
                    for organism in world.organisms
                    if not organism.alive
                )

                snapshots.append(
                    create_population_snapshot(
                        world=world,
                        metabolism_value=metabolism_value,
                        seed=seed,
                        births=births_so_far,
                        deaths=deaths_so_far,
                    )
                )

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

    births = total_population - len(initial_ids)

    deaths = len(dead)

    # Organisms may die from energy depletion or from reaching
    # the configured maximum age. We do not yet instrument the
    # engine to distinguish these causes reliably.
    initial_deaths = len(
        initial_death_ids.intersection(initial_ids)
    )

    if living:
        average_living_energy = mean(
            organism.energy
            for organism in living
        )

        average_living_age = mean(
            organism.age
            for organism in living
        )

    else:
        average_living_energy = None
        average_living_age = None

    if dead:
        average_dead_age = mean(
            organism.age
            for organism in dead
        )
    else:
        average_dead_age = None

    total_offspring = sum(
        organism.offspring_count
        for organism in all_organisms
    )

    result = {
        "seed": seed,
        "metabolism": metabolism_value,
        "ticks": world.tick,
        "initial_population": len(initial_ids),
        "total_population": total_population,
        "living_population": len(living),
        "dead_population": deaths,
        "births": births,
        "initial_organisms_that_died": initial_deaths,
        "food_remaining": len(world.food),
        "food_consumption_events": (
            tracker.food_consumption_events
        ),
        "energy_gained_from_food": (
            tracker.energy_gained_from_food
        ),
        "metabolism_events": tracker.metabolism_events,
        "energy_consumed_by_metabolism": (
            tracker.metabolic_energy_consumed
        ),
        "average_metabolic_cost_per_event": (
            tracker.metabolic_energy_consumed
            / tracker.metabolism_events
            if tracker.metabolism_events
            else 0.0
        ),
        "average_living_energy": average_living_energy,
        "average_living_age": average_living_age,
        "average_dead_age": average_dead_age,
        "total_offspring": total_offspring,
        "average_offspring_per_organism": (
            total_offspring / total_population
            if total_population
            else 0.0
        ),
        "maximum_generation": (
            max(
                organism.generation
                for organism in all_organisms
            )
            if all_organisms
            else 0
        ),
    }

    print(
        f"    Living={result['living_population']}, "
        f"Births={births}, "
        f"Food events={tracker.food_consumption_events}, "
        f"Metabolic energy={tracker.metabolic_energy_consumed:.2f}"
    )

    return result, snapshots


# ---------------------------------------------------------
# CSV EXPORT
# ---------------------------------------------------------

def export_csv(rows, filename):
    """Export rows to a CSV file."""

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = OUTPUT_DIRECTORY / filename

    if not rows:
        raise ValueError(
            f"No data available for {filename}"
        )

    fieldnames = list(rows[0].keys())

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
        writer.writerows(rows)

    return output_path


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

def numeric_values(rows, field):
    """Extract valid numeric values."""

    return [
        row[field]
        for row in rows
        if isinstance(row[field], (int, float))
        and row[field] is not None
    ]


def print_summary(rows):
    """Print energy-economy measurements by condition."""

    print("\n")
    print("=" * 115)
    print("ENERGY ECONOMY EXPERIMENT — SUMMARY")
    print("=" * 115)

    columns = (
        ("living_population", "Living"),
        ("births", "Births"),
        ("food_consumption_events", "Food events"),
        ("energy_gained_from_food", "Food energy"),
        ("energy_consumed_by_metabolism", "Metabolic cost"),
        ("food_remaining", "Food remaining"),
    )

    print(
        f"{'Metabolism':>12}"
        f"{'Metric':>28}"
        f"{'Mean':>16}"
        f"{'Std Dev':>16}"
    )

    print("-" * 115)

    for metabolism_value in METABOLISM_LEVELS:

        condition_rows = [
            row
            for row in rows
            if row["metabolism"] == metabolism_value
        ]

        for field, label in columns:

            values = numeric_values(
                condition_rows,
                field,
            )

            if values:
                average = mean(values)
                deviation = pstdev(values)

                print(
                    f"{metabolism_value:>12.2f}"
                    f"{label:>28}"
                    f"{average:>16.3f}"
                    f"{deviation:>16.3f}"
                )

        print("-" * 115)

    print("\nINTERPRETATION NOTES")
    print("-" * 115)
    print(
        "1. Food energy is measured from successful eat_food calls."
    )
    print(
        "2. Metabolic energy is measured before metabolism is applied."
    )
    print(
        "3. Food energy gained may be lower than FOOD_ENERGY if "
        "an organism is already near MAX_ENERGY."
    )
    print(
        "4. Metabolism-event counts are organism-tick events, "
        "not unique organisms."
    )
    print(
        "5. Death causes are not separated reliably in this experiment."
    )
    print(
        "6. Energy consumption and food acquisition may both depend "
        "on population size and organism behavior."
    )
    print(
        "7. Results describe this simulation's current mechanics."
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    """Run all energy-economy conditions."""

    print("=" * 85)
    print("DIGITAL LIFE — ENERGY ECONOMY EXPERIMENT")
    print("=" * 85)

    all_results = []
    all_snapshots = []

    for metabolism_value in METABOLISM_LEVELS:

        print("\n")
        print("-" * 85)
        print(
            f"METABOLISM CONDITION: {metabolism_value:.2f}"
        )
        print("-" * 85)

        for seed in RANDOM_SEEDS:

            result, snapshots = run_single_experiment(
                metabolism_value,
                seed,
            )

            all_results.append(result)
            all_snapshots.extend(snapshots)

    summary_path = export_csv(
        all_results,
        "energy_economy_summary.csv",
    )

    snapshots_path = export_csv(
        all_snapshots,
        "energy_economy_timeseries.csv",
    )

    print_summary(all_results)

    print("\n")
    print("=" * 85)
    print("ENERGY ECONOMY EXPERIMENT COMPLETED")
    print("=" * 85)
    print(f"Completed runs: {len(all_results)}")
    print(f"Food energy constant: {FOOD_ENERGY}")
    print(f"Summary CSV: {summary_path}")
    print(f"Time-series CSV: {snapshots_path}")


if __name__ == "__main__":
    main()
