"""Brain-to-action consistency: engine dispatch matches brain decision."""
from brains.rule_brain import Action, RuleBrain
from domain.sensors import SensorData
from domain.genome import Genome
from domain.organism import Organism
from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng


def make_sensor(food_dist, energy_ratio):
    return SensorData(
        nearest_food_distance=food_dist,
        nearest_food_dx=1.0,
        nearest_food_dy=0.0,
        nearest_organism_distance=float("inf"),
        nearest_organism_dx=0.0,
        nearest_organism_dy=0.0,
        energy_ratio=energy_ratio,
        boundary_left=10.0,
        boundary_right=10.0,
        boundary_top=10.0,
        boundary_bottom=10.0,
    )


def test_brain_returns_only_known_actions():
    brain = RuleBrain()
    assert brain.decide(make_sensor(5.0, 0.2)) in (Action.MOVE, Action.REPRODUCE)
    assert brain.decide(make_sensor(float("inf"), 0.9)) == Action.REPRODUCE
    assert brain.decide(make_sensor(float("inf"), 0.5)) == Action.MOVE


def test_move_invokes_movement(monkeypatch):
    rng = create_rng(42)
    world = World(rng=rng)
    world.spawn_organisms(1)
    org = world.organisms[0]
    org.x, org.y = 100.0, 100.0
    engine = SimulationEngine(world, rng=rng)
    called = {}

    def fake_move(o, dx, dy, w):
        called["moved"] = True

    monkeypatch.setattr("simulation.engine.move_organism", fake_move)
    monkeypatch.setattr(
        "simulation.engine.sense", lambda o, w: make_sensor(5.0, 0.2)
    )
    engine.brain.decide = lambda s: Action.MOVE
    engine.brain.movement_direction = lambda s: (1.0, 0.0)
    before = (org.x, org.y)
    engine._act_organism(org)
    assert called.get("moved") is True


def test_idle_causes_no_directed_movement(monkeypatch):
    rng = create_rng(42)
    world = World(rng=rng)
    world.spawn_organisms(1)
    org = world.organisms[0]
    org.x, org.y = 100.0, 100.0
    engine = SimulationEngine(world, rng=rng)
    moved = []

    def fake_move(o, dx, dy, w):
        moved.append(True)

    monkeypatch.setattr("simulation.engine.move_organism", fake_move)
    monkeypatch.setattr(
        "simulation.engine.sense", lambda o, w: make_sensor(float("inf"), 0.5)
    )
    engine.brain.decide = lambda s: Action.IDLE
    x0, y0 = org.x, org.y
    engine._act_organism(org)
    assert moved == []
    assert (org.x, org.y) == (x0, y0)


def test_reproduce_does_not_bypass_eligibility(monkeypatch):
    rng = create_rng(42)
    world = World(rng=rng)
    world.spawn_organisms(1)
    org = world.organisms[0]
    org.energy = 5.0  # cannot pay cost / threshold
    engine = SimulationEngine(world, rng=rng)
    monkeypatch.setattr(
        "simulation.engine.sense", lambda o, w: make_sensor(float("inf"), 0.9)
    )
    engine.brain.decide = lambda s: Action.REPRODUCE
    assert engine._act_organism(org) is False


def test_eat_does_not_double_consume(monkeypatch):
    rng = create_rng(7)
    world = World(rng=rng)
    world.spawn_organisms(1)
    org = world.organisms[0]
    org.x, org.y = 50.0, 50.0
    world.food = [(50.0, 50.0), (50.0, 50.0)]
    engine = SimulationEngine(world, rng=rng)
    monkeypatch.setattr(
        "simulation.engine.sense", lambda o, w: make_sensor(0.0, 0.2)
    )
    engine.brain.decide = lambda s: Action.EAT
    engine._act_organism(org)
    # Exactly one food item consumed per tick, never two.
    assert len(world.food) == 1
