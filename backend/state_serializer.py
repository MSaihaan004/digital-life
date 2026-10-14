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


def capture_snapshot(world, metrics=None):
    """Capture detached organism/food data under the caller's lock."""
    organisms = []
    for organism in world.organisms:
        genome = organism.genome
        organisms.append({
            "id": organism.organism_id,
            "x": organism.x,
            "y": organism.y,
            "energy": organism.energy,
            "health": organism.health,
            "age": organism.age,
            "generation": organism.generation,
            "parent_id": organism.parent_id,
            "offspring_count": organism.offspring_count,
            "alive": bool(organism.alive and organism.health > 0),
            "genome": {
                "speed": genome.speed,
                "vision": genome.vision,
                "metabolism": genome.metabolism,
                "size": genome.size,
                "reproduction_threshold": genome.reproduction_threshold,
                "mutation_rate": genome.mutation_rate,
            },
        })
    latest = None
    if metrics is not None:
        current = metrics.latest()
        if current is not None:
            latest = dict(current)
            latest["generation_counts"] = dict(
                current.get("generation_counts", {})
            )
    return {
        "tick": world.tick,
        "width": world.width,
        "height": world.height,
        "organisms": organisms,
        "food": list(world.food),
        "latest_metrics": latest,
    }


def serialize_snapshot(snapshot, include_dead=True, max_organisms=None):
    """Serialize a detached snapshot (no lock needed).

    Historical records are never deleted; ``include_dead=False``
    or ``max_organisms`` only limits what is sent per response
    (living first). Defaults preserve existing behavior.
    """
    organisms = list(snapshot["organisms"])
    if not include_dead:
        organisms = [o for o in organisms if o["alive"]]
    else:
        organisms = sorted(organisms, key=lambda o: (not o["alive"]))
    if max_organisms is not None:
        organisms = organisms[:max(0, int(max_organisms))]

    total = len(snapshot["organisms"])
    living = [o for o in snapshot["organisms"] if o["alive"]]

    def average(values):
        if not values:
            return None
        return sum(values) / len(values)

    statistics = {
        "total_organisms": total,
        "living_population": len(living),
        "dead_population": total - len(living),
        "food_remaining": len(snapshot["food"]),
        "average_energy": average([o["energy"] for o in living]),
        "average_health": average([o["health"] for o in living]),
        "average_age": average([o["age"] for o in living]),
        "average_metabolism": average(
            [o["genome"]["metabolism"] for o in living]
        ),
    }
    return {
        "tick": snapshot["tick"],
        "world": {"width": snapshot["width"], "height": snapshot["height"]},
        "population": len(living),
        "total_organisms": total,
        "food_remaining": len(snapshot["food"]),
        "organisms": organisms,
        "food": [{"x": x, "y": y} for x, y in snapshot["food"]],
        "statistics": statistics,
        "latest_metrics": snapshot.get("latest_metrics"),
    }
