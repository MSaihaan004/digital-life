"""Serialize the Digital Life world into JSON-compatible data."""


def serialize_world(world, metrics=None):
    """Return a snapshot of the current world without advancing it."""

    organisms = world.organisms

    living_organisms = [
        organism
        for organism in organisms
        if organism.alive and organism.health > 0
    ]

    def average(values):
        if not values:
            return None
        return sum(values) / len(values)

    organism_data = []

    for organism in organisms:
        genome = organism.genome

        organism_data.append({
            "id": organism.organism_id,
            "x": organism.x,
            "y": organism.y,
            "energy": organism.energy,
            "health": organism.health,
            "age": organism.age,
            "generation": organism.generation,
            "parent_id": organism.parent_id,
            "offspring_count": organism.offspring_count,
            "alive": organism.alive,
            "genome": {
                "speed": genome.speed,
                "vision": genome.vision,
                "metabolism": genome.metabolism,
                "size": genome.size,
                "reproduction_threshold": (
                    genome.reproduction_threshold
                ),
                "mutation_rate": genome.mutation_rate,
            },
        })

    food_data = [
        {"x": x, "y": y}
        for x, y in world.food
    ]

    statistics = {
        "total_organisms": len(organisms),
        "living_population": len(living_organisms),
        "dead_population": len(organisms) - len(living_organisms),
        "food_remaining": len(world.food),
        "average_energy": average(
            [organism.energy for organism in living_organisms]
        ),
        "average_health": average(
            [organism.health for organism in living_organisms]
        ),
        "average_age": average(
            [organism.age for organism in living_organisms]
        ),
        "average_metabolism": average(
            [
                organism.genome.metabolism
                for organism in living_organisms
            ]
        ),
    }

    return {
        "tick": world.tick,
        "world": {
            "width": world.width,
            "height": world.height,
        },
        "population": len(living_organisms),
        "total_organisms": len(organisms),
        "food_remaining": len(world.food),
        "organisms": organism_data,
        "food": food_data,
        "statistics": statistics,
        "latest_metrics": (
            metrics.latest() if metrics is not None else None
        ),
    }
