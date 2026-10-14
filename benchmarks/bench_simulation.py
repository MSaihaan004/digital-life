"""Lightweight simulation benchmarks (stdlib only, fixed seeds).

Usage:
    PYTHONPATH=. python benchmarks/bench_simulation.py [--quick]

Results print as JSON to stdout; nothing is written to
experiment_results/ (baselines must not overwrite results).
"""
import json
import sys
import time

sys.path.insert(0, ".")

from domain.world import World
from simulation.engine import SimulationEngine
from simulation.randomness import create_rng
from backend.state_serializer import capture_snapshot, serialize_snapshot


def build(population, food, seed=42):
    rng = create_rng(seed)
    world = World(rng=rng)
    world.spawn_organisms(population)
    world.spawn_food(food)
    engine = SimulationEngine(world, rng=rng)
    return world, engine


def time_ticks(world, engine, ticks, warmup=5):
    for _ in range(warmup):
        engine.step()
    start = time.perf_counter()
    for _ in range(ticks):
        engine.step()
    return (time.perf_counter() - start) / ticks


def profile_tick(world, engine, ticks=30):
    """Measure actual phase timings of normal engine ticks.

    Phase instrumentation lives in ``SimulationEngine.step()`` and
    is enabled only for this measurement; every timed tick executes
    the exact production code path exactly once (no duplicated
    sensing or state-changing work). Reported phases:

    - act: per-organism loop (sense, decide, move, eat,
      metabolism, aging, death, eligibility).
    - reproduce: parent selection, offspring creation, mutation.
    - housekeeping: offspring registration, food respawn, tick
      increment, death-set computation.
    - metrics: metrics.record().

    The phases cover the named instrumented regions of a normal
    tick; per-tick setup outside those regions (organism-list
    snapshot, pre-tick living set, next-ID scan) is not attributed,
    so phase timings may not sum to total tick time. Full-tick
    benchmarks (``time_ticks``) remain the comparable series.
    """
    for _ in range(5):
        engine.step()
    engine.enable_phase_timing()
    try:
        for _ in range(ticks):
            engine.step()
        return dict(engine.phase_report())
    finally:
        engine.disable_phase_timing()


def main():
    quick = "--quick" in sys.argv
    rep_ticks = 20 if quick else 60
    scenarios = [
        ("small", 10, 20),
        ("medium", 100, 200),
        ("large", 300, 400),
        ("low_food", 100, 10),
        ("high_food", 100, 400),
    ]
    out = {"env": {"quick": quick}, "tick_ms": {}, "phases_ms": {},
           "serialization": {}, "history": {}}

    for name, pop, food in scenarios:
        world, engine = build(pop, food)
        ms = time_ticks(world, engine, rep_ticks) * 1000
        out["tick_ms"][name] = round(ms, 3)

    world, engine = build(100, 200)
    engine.run(30)
    out["phases_ms"] = {k: round(v * 1000, 4)
                        for k, v in profile_tick(world, engine).items()}

    # Long run with dead historical organisms.
    world, engine = build(100, 200)
    engine.run(200 if quick else 500)
    living = sum(1 for o in world.organisms if o.alive)
    total = len(world.organisms)
    ms = time_ticks(world, engine, 20, warmup=0) * 1000
    out["tick_ms"][f"aged_living{living}_total{total}"] = round(ms, 3)

    # Serialization at different sizes.
    for label, pop in (("small", 10), ("medium", 100), ("large", 300)):
        world, engine = build(pop, 200)
        engine.run(10)
        t = time.perf_counter()
        snap = capture_snapshot(world, metrics=engine.metrics)
        t_cap = time.perf_counter() - t
        t = time.perf_counter()
        state = serialize_snapshot(snap)
        t_ser = time.perf_counter() - t
        out["serialization"][label] = {
            "capture_ms": round(t_cap * 1000, 3),
            "serialize_ms": round(t_ser * 1000, 3),
            "response_kb": round(len(json.dumps(state)) / 1024, 1),
            "organisms": len(state["organisms"]),
        }

    # Metrics-history retrieval.
    world, engine = build(50, 100)
    engine.run(100)
    history = engine.metrics.get_history()
    for limit in (10, 120, None):
        t = time.perf_counter()
        rows = history[-limit:] if limit else history
        payload = json.dumps([dict(r, generation_counts="{}") for r in rows])
        dt = (time.perf_counter() - t) * 1000
        out["history"][f"limit_{limit}"] = {
            "ms": round(dt, 3), "kb": round(len(payload) / 1024, 1),
            "rows": len(rows),
        }

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
