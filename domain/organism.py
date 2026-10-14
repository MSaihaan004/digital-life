from dataclasses import dataclass
from .genome import Genome


@dataclass
class Organism:
    organism_id: int
    x: float
    y: float

    energy: float
    health: float
    age: int

    generation: int
    genome: Genome

    parent_id: int | None = None
    offspring_count: int = 0
    alive: bool = True

    # Movement velocity set by simulation/physics.py each tick.
    # Declared explicitly (was previously an undeclared dynamic
    # attribute). Defaults preserve existing behavior.
    velocity_x: float = 0.0
    velocity_y: float = 0.0


GENE_NAMES = (
    "speed",
    "vision",
    "metabolism",
    "size",
    "reproduction_threshold",
    "mutation_rate",
)

# How each existing gene maps to simulation behavior (audited):
# - speed: px/tick in simulation/physics.py (normalized dir * speed).
# - vision: food/organism detection range = vision*200 in domain/sensors.py.
# - metabolism: flat energy/tick cost in simulation/interactions.py.
# - size: UNUSED behaviorally (display/metrics only).
# - reproduction_threshold: energy gate = gene*MAX_ENERGY in
#   evolution/reproduction.py (plus REPRODUCTION_ENERGY_COST).
# - mutation_rate: per-gene mutation probability in evolution/mutation.py.
# Health is not gene-driven and currently never decays (no damage path).


def validate_organism_state(organism) -> list[str]:
    """Return invariant violations without mutating the organism."""
    problems = []
    if organism.energy < 0:
        problems.append("energy-negative")
    if organism.health < 0:
        problems.append("health-negative")
    if organism.age < 0:
        problems.append("age-negative")
    if organism.offspring_count < 0:
        problems.append("offspring-count-negative")
    if organism.generation < 0:
        problems.append("generation-negative")
    for name in GENE_NAMES:
        value = getattr(organism.genome, name, None)
        if value is None:
            continue
        if not 0.0 <= value <= 1.0:
            problems.append(f"gene-{name}-out-of-range")
    return problems


def copy_genome(genome: Genome) -> Genome:
    """Return an independent mutable copy of a genome."""
    from dataclasses import replace

    return replace(genome)
