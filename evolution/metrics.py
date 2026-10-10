"""Population and evolutionary metrics for Digital Life."""


class EvolutionMetrics:
    """Collect population statistics after every simulation tick."""

    def __init__(self):
        self.history = []

    def record(self, world, births=0, deaths=0):
        """Record a snapshot of the current world state."""

        organisms = world.organisms

        living = [
            organism
            for organism in organisms
            if organism.alive and organism.health > 0
        ]

        def average(values):
            if not values:
                return None

            return sum(values) / len(values)

        generation_counts = {}

        for organism in living:
            generation = organism.generation

            generation_counts[generation] = (
                generation_counts.get(generation, 0) + 1
            )

        total_population = len(organisms)
        living_population = len(living)

        reproductive_success = [
            organism.offspring_count
            for organism in living
        ]

        survival_rate = (
            living_population / total_population
            if total_population > 0
            else None
        )

        snapshot = {
            "tick": world.tick,
            "total_population": total_population,
            "living_population": living_population,
            "births": births,
            "deaths": deaths,

            "survival_rate": survival_rate,

            "average_age": average(
                [organism.age for organism in living]
            ),

            "average_reproductive_success": average(
                reproductive_success
            ),

            "maximum_reproductive_success": (
                max(reproductive_success)
                if reproductive_success
                else None
            ),

            "average_energy": average(
                [organism.energy for organism in living]
            ),

            "average_speed": average(
                [organism.genome.speed for organism in living]
            ),

            "average_vision": average(
                [organism.genome.vision for organism in living]
            ),

            "average_metabolism": average(
                [organism.genome.metabolism for organism in living]
            ),

            "average_size": average(
                [organism.genome.size for organism in living]
            ),

            "average_reproduction_threshold": average(
                [
                    organism.genome.reproduction_threshold
                    for organism in living
                ]
            ),

            "average_mutation_rate": average(
                [organism.genome.mutation_rate for organism in living]
            ),

            "average_generation": average(
                [organism.generation for organism in living]
            ),

            "generation_counts": generation_counts,
        }

        self.history.append(snapshot)

        return snapshot

    def latest(self):
        """Return the latest snapshot, or None if no snapshot exists."""

        if not self.history:
            return None

        return self.history[-1]

    def get_history(self):
        """Return all recorded snapshots."""

        return list(self.history)
