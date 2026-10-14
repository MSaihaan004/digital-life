"""World registration, IDs, boundaries, reset (fills empty file)."""
from domain.world import World
from simulation.randomness import create_rng


def test_spawn_ids_unique_across_calls():
    world = World(rng=create_rng(42))
    world.spawn_organisms(5)
    world.spawn_organisms(5)
    ids = [o.organism_id for o in world.organisms]
    assert len(ids) == len(set(ids)) == 10


def test_spawn_positions_inside_bounds():
    world = World(width=100, height=50, rng=create_rng(3))
    world.spawn_organisms(20)
    world.spawn_food(20)
    for o in world.organisms:
        assert 0 <= o.x <= 100 and 0 <= o.y <= 50
    for x, y in world.food:
        assert 0 <= x <= 100 and 0 <= y <= 50


def test_tick_starts_zero_and_rng_deterministic():
    a = World(rng=create_rng(42))
    b = World(rng=create_rng(42))
    a.spawn_organisms(5)
    b.spawn_organisms(5)
    assert a.tick == 0
    assert [(o.x, o.y) for o in a.organisms] == [(o.x, o.y) for o in b.organisms]
