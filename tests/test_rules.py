from domain.world import World
from simulation.rules import apply_metabolism_and_aging
import config

def test_apply_metabolism_and_aging():
    world = World()
    
    org1 = world.spawn_organism(organism_id=1)
    org1.genome.metabolism = 0.5
    org1.energy = 10.0
    org1.age = 0
    org1.alive = True
    
    org2 = world.spawn_organism(organism_id=2)
    org2.genome.metabolism = 0.8
    org2.energy = 1.0
    org2.age = 0
    org2.alive = True
    
    org3_dead = world.spawn_organism(organism_id=3)
    org3_dead.energy = 0.0
    org3_dead.age = 5
    org3_dead.alive = False

    config.METABOLISM_COST_MULTIPLIER = 2.0
    
    apply_metabolism_and_aging(world)
    
    # Check org1
    assert org1.age == 1
    assert org1.energy == 9.0  # 10.0 - (2.0 * 0.5)
    assert org1.alive is True
    
    # Check org2 (should die)
    assert org2.age == 1
    assert org2.energy == 0.0  # 1.0 - (2.0 * 0.8) clamped to 0.0
    assert org2.alive is False
    
    # Check dead org3 (should not age or lose energy)
    assert org3_dead.age == 5
    assert org3_dead.energy == 0.0
    assert org3_dead.alive is False
