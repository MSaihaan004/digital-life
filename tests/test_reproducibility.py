from simulation.randomness import create_rng
from domain.world import World
from simulation.engine import SimulationEngine


def make_initial_world(seed):
    """Create a world using a specific random seed."""

    rng = create_rng(seed=seed)

    world = World(rng=rng)

    world.spawn_organisms(10)
    world.spawn_food(20)

    return world, rng


def get_world_signature(world):
    """Capture the initial state of a world for comparison."""

    organisms = []

    for organism in world.organisms:
        organisms.append(
            (
                organism.organism_id,
                organism.x,
                organism.y,
                organism.energy,
                organism.health,
                organism.generation,
                organism.genome.speed,
                organism.genome.vision,
                organism.genome.metabolism,
                organism.genome.size,
                organism.genome.reproduction_threshold,
                organism.genome.mutation_rate,
            )
        )

    return organisms, list(world.food)


def test_same_seed_produces_same_initial_world():
    """Identical seeds should produce identical initial worlds."""

    world_a, _ = make_initial_world(42)
    world_b, _ = make_initial_world(42)

    assert get_world_signature(world_a) == get_world_signature(world_b)


def test_different_seeds_can_produce_different_worlds():
    """Different seeds should be capable of producing different worlds."""

    world_a, _ = make_initial_world(42)
    world_b, _ = make_initial_world(123)

    assert get_world_signature(world_a) != get_world_signature(world_b)


def test_same_seed_produces_same_simulation_metrics():
    """Identical initial conditions and seeds should produce identical metrics."""

    world_a, rng_a = make_initial_world(42)
    world_b, rng_b = make_initial_world(42)

    engine_a = SimulationEngine(world_a, rng=rng_a)
    engine_b = SimulationEngine(world_b, rng=rng_b)

    engine_a.run(20)
    engine_b.run(20)

    assert (
        engine_a.metrics.get_history()
        == engine_b.metrics.get_history()
    )
