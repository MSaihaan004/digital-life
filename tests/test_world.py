import random
from domain.world import World
from domain.food import Food

def test_world_initialization():
    world = World(width=100.0, height=200.0)
    assert world.width == 100.0
    assert world.height == 200.0
    assert world.organisms == []
    assert world.food == []
    assert world.tick == 0

def test_spawn_organism():
    random.seed(42)
    world = World()
    
    organism = world.spawn_organism(organism_id=10, generation=2, parent_id=5)
    
    assert len(world.organisms) == 1
    assert world.organisms[0] is organism
    assert organism.organism_id == 10
    assert organism.generation == 2
    assert organism.parent_id == 5
    assert 0 <= organism.x <= world.width
    assert 0 <= organism.y <= world.height

def test_spawn_organisms():
    world = World()
    world.spawn_organisms(5)
    
    assert len(world.organisms) == 5
    for i, org in enumerate(world.organisms):
        assert org.organism_id == i
        assert org.generation == 0
        assert org.parent_id is None

def test_spawn_food():
    world = World()
    world.spawn_food(3)
    
    assert len(world.food) == 3
    for f in world.food:
        assert isinstance(f, Food)
        assert 0 <= f.x <= world.width
        assert 0 <= f.y <= world.height

def test_deterministic_initialization():
    random.seed(42)
    world1 = World(width=100.0, height=100.0)
    world1.spawn_organisms(2)
    world1.spawn_food(2)
    
    random.seed(42)
    world2 = World(width=100.0, height=100.0)
    world2.spawn_organisms(2)
    world2.spawn_food(2)
    
    assert world1.organisms[0].x == world2.organisms[0].x
    assert world1.organisms[1].y == world2.organisms[1].y
    assert world1.food[0].x == world2.food[0].x
    assert world1.food[1].y == world2.food[1].y

