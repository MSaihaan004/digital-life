"""Post-implementation corrections: action-gating, health death, metrics."""
from types import SimpleNamespace
from config import MAX_AGE, REPRODUCTION_ENERGY_COST
from domain.genome import Genome
from domain.organism import Organism
from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng

REPRO = SimpleNamespace(value="reproduce")
MOVE = SimpleNamespace(value="move")
IDLE = SimpleNamespace(value="idle")
EAT = SimpleNamespace(value="eat")


def make_org(oid=1, energy=90.0, health=100.0, age=5, threshold=0.2):
    g = Genome(speed=0.5, vision=0.5, metabolism=0.1, size=0.5,
               reproduction_threshold=threshold, mutation_rate=0.0)
    return Organism(organism_id=oid, x=50.0, y=50.0, energy=energy,
                    health=health, age=age, generation=1, genome=g)


def make_engine(seed=42, n=1, food=0):
    w = World(rng=create_rng(seed))
    for i in range(n):
        o = make_org(oid=i)
        o.x, o.y = 50.0 + i, 50.0
        w.organisms.append(o)
    w.food = []
    for _ in range(food):
        w.food.append((50.0, 50.0))
    return w, SimulationEngine(w, rng=w.rng)


# Section 2: action-gated reproduction
def test_move_eligible_does_not_reproduce(monkeypatch):
    w, eng = make_engine()
    monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {})
    eng.brain.decide = lambda s: MOVE
    eng.brain.movement_direction = lambda s: (1.0, 0.0)
    eng.step()
    assert eng.metrics.latest()["births"] == 0
    assert len(w.organisms) == 1


def test_reproduce_eligible_reproduces(monkeypatch):
    w, eng = make_engine()
    monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {})
    eng.brain.decide = lambda s: REPRO
    eng.step()
    assert eng.metrics.latest()["births"] == 1
    assert len(w.organisms) == 2
    child = w.organisms[-1]
    assert child.parent_id == 0 and child.age == 0
    assert child.energy == REPRODUCTION_ENERGY_COST


def test_reproduce_ineligible_no_birth_no_charge(monkeypatch):
    w, eng = make_engine()
    w.organisms[0].energy = 5.0
    monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {})
    eng.brain.decide = lambda s: REPRO
    eng.step()
    assert eng.metrics.latest()["births"] == 0
    assert w.organisms[0].energy < 5.0 + 0.01  # only metabolism, no repro charge


def test_idle_eligible_does_not_reproduce(monkeypatch):
    w, eng = make_engine()
    monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {})
    eng.brain.decide = lambda s: IDLE
    eng.step()
    assert eng.metrics.latest()["births"] == 0


# Section 3: health-based death
def test_zero_health_dies_and_counts_once(monkeypatch):
    w, eng = make_engine()
    w.organisms[0].health = 0.0
    monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {})
    eng.brain.decide = lambda s: REPRO
    eng.step()
    assert w.organisms[0].alive is False
    m = eng.metrics.latest()
    assert m["living_population"] == 0
    assert m["deaths"] == 1


def test_zero_health_cannot_eat_or_reproduce(monkeypatch):
    w, eng = make_engine(food=1)
    w.organisms[0].health = 0.0
    w.organisms[0].x, w.organisms[0].y = 50.0, 50.0
    monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {})
    eng.brain.decide = lambda s: REPRO
    food_before = len(w.food)
    eng.step()
    # dead eats nothing: food count only grows via respawn, never shrinks by eating
    assert len(w.food) >= food_before
    assert eng.metrics.latest()["births"] == 0


def test_already_dead_no_double_count(monkeypatch):
    w, eng = make_engine()
    w.organisms[0].alive = False
    monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {})
    eng.brain.decide = lambda s: REPRO
    eng.step()
    assert eng.metrics.latest()["deaths"] == 0
    assert eng.metrics.latest()["births"] == 0


def test_zero_energy_and_max_age_death(monkeypatch):
    w, eng = make_engine()
    w.organisms[0].energy = 0.05
    w.organisms[0].genome.metabolism = 1.0
    monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {})
    eng.brain.decide = lambda s: MOVE
    eng.brain.movement_direction = lambda s: (1.0, 0.0)
    eng.step()
    assert w.organisms[0].alive is False
    w2, eng2 = make_engine(seed=9)
    w2.organisms[0].age = MAX_AGE - 1
    w2.organisms[0].energy = 100.0
    monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {})
    eng2.brain.decide = lambda s: MOVE
    eng2.brain.movement_direction = lambda s: (1.0, 0.0)
    eng2.step()
    assert w2.organisms[0].alive is False


# Section 4: action semantics - single eat, move only for MOVE
def test_each_action_eats_at_most_once():
    for action in (MOVE, EAT, REPRO, IDLE):
        w, eng = make_engine(seed=3, food=0)
        w.organisms[0].x, w.organisms[0].y = 10.0, 10.0
        w.food = [(10.0, 10.0), (10.0, 10.0)]
        eng.brain.decide = lambda s, a=action: a
        from domain import sensors as sens
        # real sense; organism at food
        eng.step()
        # newborn possible only for REPRO; food eaten at most 1 + respawn effects
        # key invariant: never eats 2 in one tick -> at least 1 remains before respawn logic
        # respawn adds at most 5; starting 2, eating 1 -> 1 + respawn
        assert len(w.food) >= 1


def test_only_move_changes_position(monkeypatch):
    for action, should_move in ((MOVE, True), (EAT, False), (REPRO, False), (IDLE, False)):
        w, eng = make_engine(seed=4)
        w.organisms[0].x, w.organisms[0].y = 100.0, 100.0
        w.organisms[0].genome.speed = 1.0
        monkeypatch.setattr("simulation.engine.sense", lambda o, ww: {"d": 1})
        eng.brain.decide = lambda s, a=action: a
        eng.brain.movement_direction = lambda s: (1.0, 0.0)
        eng._act_organism(w.organisms[0])
        moved = (w.organisms[0].x, w.organisms[0].y) != (100.0, 100.0)
        assert moved is should_move


# Section 5: metrics agreement
def test_metrics_agree_with_world():
    w = World(rng=create_rng(21))
    w.spawn_organisms(6)
    w.spawn_food(10)
    eng = SimulationEngine(w, rng=w.rng)
    for _ in range(5):
        eng.step()
        snap = eng.metrics.latest()
        living = [o for o in w.organisms if o.alive and o.health > 0]
        assert snap["living_population"] == len(living)
        assert snap["total_population"] == len(w.organisms)
        assert snap["tick"] == w.tick
        assert snap["births"] in (0, 1)
        if living:
            avg_e = sum(o.energy for o in living) / len(living)
            avg_a = sum(o.age for o in living) / len(living)
            assert abs(snap["average_energy"] - avg_e) < 1e-9
            assert abs(snap["average_age"] - avg_a) < 1e-9
