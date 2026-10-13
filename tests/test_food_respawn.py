"""Tests for food respawn (sustainable ecosystem)."""

from config import (
    FOOD_TARGET_COUNT,
    FOOD_MAX_COUNT,
    FOOD_RESPAWN_PER_TICK,
)
from domain.world import World
from simulation.engine import SimulationEngine
from simulation.interactions import respawn_food
from simulation.randomness import create_rng


def make_world(seed=42, organisms=10, food=20):
    rng = create_rng(seed=seed)
    world = World(rng=rng)
    world.spawn_organisms(organisms)
    world.spawn_food(food)
    return world, rng


def test_respawn_replenishes_depleted_world():
    """An empty world should regain food gradually, not instantly."""

    world, _ = make_world(food=0)

    spawned = respawn_food(world)

    assert spawned == FOOD_RESPAWN_PER_TICK
    assert len(world.food) == FOOD_RESPAWN_PER_TICK


def test_respawn_does_nothing_at_target():
    """Food at or above target should not trigger a respawn."""

    world, _ = make_world(food=0)
    world.spawn_food(FOOD_TARGET_COUNT)

    assert respawn_food(world) == 0
    assert len(world.food) == FOOD_TARGET_COUNT


def test_respawn_does_nothing_above_target():
    """Overstocked worlds should not gain more food."""

    world, _ = make_world(food=0)
    world.spawn_food(FOOD_TARGET_COUNT + 50)

    assert respawn_food(world) == 0
    assert len(world.food) == FOOD_TARGET_COUNT + 50


def test_respawn_never_exceeds_max():
    """Respawn must respect the hard maximum food cap."""

    world, _ = make_world(food=0)
    world.spawn_food(FOOD_MAX_COUNT)

    assert respawn_food(world) == 0
    assert len(world.food) == FOOD_MAX_COUNT


def test_respawn_recovers_to_target_over_time():
    """Repeated ticks should bring a starved world back to target."""

    world, rng = make_world(food=0)
    engine = SimulationEngine(world, rng=rng)

    for _ in range(100):
        engine.step()
        assert len(world.food) <= FOOD_MAX_COUNT

    assert len(world.food) == FOOD_TARGET_COUNT


def test_engine_sustains_food_and_population():
    """A long run should not end abruptly from starvation."""

    world, rng = make_world(seed=7, organisms=100, food=200)
    engine = SimulationEngine(world, rng=rng)

    engine.run(500)

    living = [
        organism
        for organism in world.organisms
        if organism.alive and organism.health > 0
    ]

    assert len(world.food) > 0
    assert len(living) > 0


def test_respawn_is_deterministic_for_same_seed():
    """Identical seeds must produce identical food after the same ticks."""

    world_a, rng_a = make_world(seed=99)
    world_b, rng_b = make_world(seed=99)

    engine_a = SimulationEngine(world_a, rng=rng_a)
    engine_b = SimulationEngine(world_b, rng=rng_b)

    engine_a.run(20)
    engine_b.run(20)

    assert list(world_a.food) == list(world_b.food)
