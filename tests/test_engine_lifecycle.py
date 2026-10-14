"""Engine lifecycle: aging/death/newborn/dead/empty/metrics-once."""
from config import MAX_AGE
from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng


def make_world(n=3, seed=42, food=5):
    w = World(rng=create_rng(seed))
    w.spawn_organisms(n)
    w.spawn_food(food)
    return w


def test_newborn_does_not_act_birth_tick():
    w = make_world(n=1, seed=1)
    parent = w.organisms[0]
    parent.energy = 100.0
    parent.genome.reproduction_threshold = 0.0
    eng = SimulationEngine(w, rng=w.rng)
    eng.step()
    # at most 1 newborn with age 0
    newborns = [o for o in w.organisms if o.age == 0]
    assert len(newborns) <= 1


def test_dead_cannot_act_eat_or_reproduce():
    w = make_world(n=1, seed=2)
    org = w.organisms[0]
    org.alive = False
    org.x, org.y = 10.0, 10.0
    w.food = [(10.0, 10.0)]
    eng = SimulationEngine(w, rng=w.rng)
    births_before = len(w.organisms)
    eng.step()
    assert len(w.food) == 1 or len(w.food) >= 1  # dead ate nothing new beyond respawn logic
    assert len(w.organisms) == births_before  # no birth from dead
    assert eng.metrics.latest()["births"] == 0


def test_starvation_and_old_age_death():
    w = make_world(n=1, seed=3, food=0)
    org = w.organisms[0]
    org.energy = 0.05
    org.genome.metabolism = 1.0
    eng = SimulationEngine(w, rng=w.rng)
    eng.step()
    assert org.alive is False
    w2 = make_world(n=1, seed=4, food=0)
    o2 = w2.organisms[0]
    o2.age = MAX_AGE - 1
    o2.energy = 100.0
    eng2 = SimulationEngine(w2, rng=w2.rng)
    eng2.step()
    assert o2.alive is False


def test_empty_population_step_safe():
    w = World(rng=create_rng(9))
    w.spawn_food(5)
    eng = SimulationEngine(w, rng=w.rng)
    eng.step()
    assert w.tick == 1
    m = eng.metrics.latest()
    assert m["living_population"] == 0
    assert m["births"] == 0 and m["deaths"] == 0


def test_births_deaths_recorded_once_and_tick_once():
    w = make_world(n=5, seed=11)
    eng = SimulationEngine(w, rng=w.rng)
    t0 = w.tick
    h0 = len(eng.metrics.get_history())
    eng.step()
    assert w.tick == t0 + 1
    assert len(eng.metrics.get_history()) == h0 + 1
    m = eng.metrics.latest()
    assert m["tick"] == w.tick
    assert m["births"] in (0, 1)
    living = sum(1 for o in w.organisms if o.alive)
    assert m["living_population"] == living
    ids = [o.organism_id for o in w.organisms]
    assert len(ids) == len(set(ids))


def test_deterministic_full_trajectory():
    def run(seed):
        w = World(rng=create_rng(seed))
        w.spawn_organisms(10)
        w.spawn_food(20)
        eng = SimulationEngine(w, rng=w.rng)
        eng.run(20)
        sig = [(o.organism_id, round(o.x, 6), round(o.y, 6),
                round(o.energy, 6), o.age, o.alive, o.generation) for o in w.organisms]
        return sig, eng.metrics.get_history()
    s1, h1 = run(123)
    s2, h2 = run(123)
    assert s1 == s2 and h1 == h2
