import pytest
from domain.world import World
from simulation.engine import SimulationEngine
import config

def test_engine_stores_the_supplied_world():
    world = World()
    engine = SimulationEngine(world)
    assert engine.world is world

def test_one_tick_increments_world_tick_exactly_once():
    world = World()
    world.tick = 5
    engine = SimulationEngine(world)
    engine.tick()
    assert world.tick == 6

def test_one_tick_applies_metabolism_aging():
    world = World()
    org = world.spawn_organism(organism_id=1)
    org.age = 0
    engine = SimulationEngine(world)
    engine.tick()
    assert org.age == 1

def test_multiple_ticks_increment_correctly():
    world = World()
    world.tick = 0
    engine = SimulationEngine(world)
    engine.tick()
    engine.tick()
    assert world.tick == 2

def test_multiple_ticks_produce_expected_age_energy_changes():
    world = World()
    org = world.spawn_organism(organism_id=1)
    org.age = 0
    org.energy = 10.0
    org.genome.metabolism = 0.5
    
    engine = SimulationEngine(world)
    engine.tick()
    engine.tick()
    
    expected_energy = 10.0 - 2 * (config.METABOLISM_COST_MULTIPLIER * 0.5)
    
    assert org.age == 2
    assert org.energy == pytest.approx(expected_energy)

def test_unrelated_world_state_remains_unchanged():
    world = World()
    world.spawn_food(3)
    world.width = 500
    
    engine = SimulationEngine(world)
    engine.tick()
    
    assert len(world.food) == 3
    assert world.width == pytest.approx(500)

