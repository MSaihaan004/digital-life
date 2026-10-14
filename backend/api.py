"""FastAPI application for the Digital Life simulation.

Synchronization policy: a single re-entrant lock guards all
mutations and captures. Control operations (pause/resume/step/
reset/tick-rate) and snapshot capture run under the lock;
JSON serialization of the detached snapshot runs outside the
critical section so reads never observe partially updated state
and the lock is never held during expensive encoding.
"""

import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    RANDOM_SEED,
    INITIAL_POPULATION,
    INITIAL_FOOD,
    DEFAULT_TICKS_PER_SECOND,
    MIN_TICKS_PER_SECOND,
    MAX_TICKS_PER_SECOND,
    validate_config,
)
from simulation.randomness import create_rng

from domain.world import World
from simulation.engine import SimulationEngine

from backend.state_serializer import (
    capture_snapshot,
    serialize_snapshot,
)

logger = logging.getLogger("digital_life.backend")


def create_simulation(seed=RANDOM_SEED):
    """Initialize a simulation using the existing configuration.

    Seeding policy: the seed is applied only at creation/reset,
    never to a running simulation. Identical seed + configuration
    recreates identical initial conditions.
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer.")

    import random

    random.seed(seed)

    world = World(rng=create_rng(seed))
    world.spawn_organisms(INITIAL_POPULATION)
    world.spawn_food(INITIAL_FOOD)

    engine = SimulationEngine(world, rng=world.rng)

    return world, engine


world, engine = create_simulation()

_state_lock = threading.RLock()
_ticks_per_second = float(DEFAULT_TICKS_PER_SECOND)
_paused = False
_stop_event = threading.Event()
_worker_thread = None
_worker_started = False
_last_error = None
_last_tick = None


def get_ticks_per_second() -> float:
    """Return the current ticks-per-second setting (thread-safe)."""

    with _state_lock:
        return _ticks_per_second


def set_ticks_per_second(value: float) -> float:
    """Validate and apply a new ticks-per-second setting (thread-safe)."""

    try:
        ticks = float(value)
    except (TypeError, ValueError):
        raise ValueError("ticks_per_second must be a number.")

    if ticks != ticks:  # NaN check without importing math
        raise ValueError("ticks_per_second must be a number.")

    if ticks in (float("inf"), float("-inf")):
        raise ValueError("ticks_per_second must be finite.")

    if not (MIN_TICKS_PER_SECOND <= ticks <= MAX_TICKS_PER_SECOND):
        raise ValueError(
            "ticks_per_second must be between "
            f"{MIN_TICKS_PER_SECOND} and {MAX_TICKS_PER_SECOND}."
        )

    with _state_lock:
        globals()["_ticks_per_second"] = ticks
        return ticks


def _simulation_status_locked() -> str:
    if _paused:
        return "paused"
    if _worker_started and _worker_thread is not None and _worker_thread.is_alive():
        return "running"
    return "idle"


def _simulation_loop():
    """Advance the simulation in the background for the live dashboard."""

    while not _stop_event.is_set():
        with _state_lock:
            current_ticks = _ticks_per_second
            paused = _paused

        interval = 1.0 / current_ticks if current_ticks > 0 else 0.5
        if _stop_event.wait(interval):
            break

        with _state_lock:
            if _paused:
                continue

        try:
            with _state_lock:
                engine.step()
                globals()["_last_tick"] = engine.world.tick
        except Exception as exc:  # observable: stored + logged, loop survives
            with _state_lock:
                globals()["_last_error"] = f"{type(exc).__name__}: {exc}"
            logger.exception("Simulation tick failed")
            continue


def start_worker() -> bool:
    """Start the background worker once. Returns True if started."""
    global _worker_thread, _worker_started
    with _state_lock:
        if _worker_started and _worker_thread is not None and _worker_thread.is_alive():
            return False
        _stop_event.clear()
        globals()["_last_error"] = None
        thread = threading.Thread(
            target=_simulation_loop,
            name="digital-life-simulation",
            daemon=True,
        )
        _worker_thread = thread
        _worker_started = True
    thread.start()
    return True


def stop_worker(timeout: float = 5.0) -> bool:
    """Signal the worker to stop and wait. Returns True if stopped."""
    global _worker_thread, _worker_started
    with _state_lock:
        thread = _worker_thread
    _stop_event.set()
    if thread is not None and thread.is_alive():
        thread.join(timeout=timeout)
    with _state_lock:
        alive = _worker_thread is not None and _worker_thread.is_alive()
        if not alive:
            _worker_started = False
        return not alive


def worker_alive() -> bool:
    with _state_lock:
        return bool(
            _worker_started
            and _worker_thread is not None
            and _worker_thread.is_alive()
        )


@asynccontextmanager
async def lifespan(app_instance):
    errors = validate_config()
    if errors:
        logger.error("Invalid configuration at startup: %s", errors)
    start_worker()
    try:
        yield
    finally:
        stop_worker()


app = FastAPI(
    title="Digital Life API",
    description="Backend API for the Digital Life ecosystem.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TicksPerSecondUpdate(BaseModel):
    ticks_per_second: float


class ResetRequest(BaseModel):
    seed: int | None = None


def _status_payload() -> dict:
    with _state_lock:
        living = sum(
            1 for o in world.organisms if o.alive and o.health > 0
        )
        return {
            "application": "Digital Life API",
            "status": "running",
            "simulation_status": _simulation_status_locked(),
            "paused": _paused,
            "simulation_tick": world.tick,
            "ticks_per_second": _ticks_per_second,
            "living_population": living,
            "total_organisms": len(world.organisms),
            "worker_alive": worker_alive(),
            "last_tick": _last_tick,
            "last_error": _last_error,
        }


@app.get("/")
def root():
    """Return basic API information."""

    with _state_lock:
        tick = world.tick
    return {
        "application": "Digital Life API",
        "status": "running",
        "simulation_tick": tick,
        "ticks_per_second": get_ticks_per_second(),
    }


@app.get("/health")
def health():
    """Basic health/status endpoint for local debugging."""
    return _status_payload()


@app.get("/simulation/status")
def simulation_status():
    """Report operational simulation status."""
    return _status_payload()


@app.get("/simulation/config")
def get_simulation_config():
    """Return editable simulation settings."""

    return {
        "ticks_per_second": get_ticks_per_second(),
        "min_ticks_per_second": MIN_TICKS_PER_SECOND,
        "max_ticks_per_second": MAX_TICKS_PER_SECOND,
    }


@app.put("/simulation/config")
def update_simulation_config(update: TicksPerSecondUpdate):
    """Update editable simulation settings (currently ticks per second)."""

    try:
        ticks = set_ticks_per_second(update.ticks_per_second)
    except ValueError as exc:
        logger.warning("Invalid tick-rate update: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))

    return {
        "ticks_per_second": ticks,
        "min_ticks_per_second": MIN_TICKS_PER_SECOND,
        "max_ticks_per_second": MAX_TICKS_PER_SECOND,
    }


@app.post("/simulation/pause")
def pause_simulation():
    """Pause automatic advancement (idempotent, preserves state)."""
    with _state_lock:
        globals()["_paused"] = True
        payload = _status_payload()
    return {"paused": True, **payload}


@app.post("/simulation/resume")
def resume_simulation():
    """Resume automatic advancement (idempotent, no duplicate workers)."""
    with _state_lock:
        globals()["_paused"] = False
    # Ensure a worker exists without duplicating a live one.
    needs_start = not worker_alive()
    if needs_start:
        start_worker()
    with _state_lock:
        payload = _status_payload()
    return {"paused": False, **payload}


@app.post("/simulation/step")
def step_simulation():
    """Advance exactly one tick. Only available while paused."""
    with _state_lock:
        if not _paused:
            raise HTTPException(
                status_code=409,
                detail="Single-step is only available while paused. "
                "Pause the simulation first.",
            )
        try:
            engine.step()
            globals()["_last_tick"] = engine.world.tick
            tick = engine.world.tick
        except Exception as exc:
            globals()["_last_error"] = f"{type(exc).__name__}: {exc}"
            logger.exception("Single-step tick failed")
            raise HTTPException(
                status_code=500, detail="Single-step tick failed."
            )
    return {"tick": tick, "status": _status_payload()}


@app.post("/simulation/reset")
def reset_simulation(request: ResetRequest | None = None):
    """Recreate a consistent initial simulation (preserves tick rate).

    Seed policy: optional ``seed`` applies at reset only. When
    omitted, the configured RANDOM_SEED is used. Paused state is
    preserved. Historical experiment files are untouched. Worker
    is not duplicated.
    """
    seed = RANDOM_SEED if request is None or request.seed is None else request.seed
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise HTTPException(status_code=422, detail="seed must be an integer.")

    errors = validate_config()
    if errors:
        logger.error("Reset refused due to invalid configuration: %s", errors)
        raise HTTPException(status_code=500, detail="; ".join(errors))

    try:
        new_world, new_engine = create_simulation(seed=seed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Reset failed during simulation creation")
        raise HTTPException(status_code=500, detail="Reset failed.")

    with _state_lock:
        globals()["world"] = new_world
        globals()["engine"] = new_engine
        globals()["_last_error"] = None
        globals()["_last_tick"] = None
        payload = _status_payload()
    return {"reset": True, "seed": seed, **payload}


@app.get("/simulation/state")
def get_simulation_state(
    include_dead: bool = Query(default=True),
    limit: int | None = Query(default=None, ge=0),
):
    """Return the current world state without advancing the simulation.

    Snapshot is captured under the lock and serialized outside it.
    ``include_dead=False`` omits dead records from the payload
    (counts preserved); ``limit`` caps serialized organisms
    (living first). Defaults preserve frontend compatibility.
    """
    with _state_lock:
        if limit is not None and limit < 0:
            raise HTTPException(
                status_code=422, detail="limit must be non-negative."
            )
        snapshot = capture_snapshot(world, metrics=engine.metrics)
        tps = _ticks_per_second
        status = _simulation_status_locked()
        paused = _paused
    try:
        state = serialize_snapshot(
            snapshot, include_dead=include_dead, max_organisms=limit
        )
    except Exception:
        logger.exception("State serialization failed")
        raise HTTPException(status_code=500, detail="State serialization failed.")
    state["ticks_per_second"] = tps
    state["simulation_status"] = status
    state["paused"] = paused
    return state


@app.get("/simulation/metrics/history")
def get_metrics_history(limit: int | None = Query(default=None, ge=1)):
    """Return recorded per-tick metric snapshots (read-only).

    Added for dashboard charts: the live-state response carries
    only the latest snapshot. ``limit`` returns the most recent
    N entries. Empty history yields an empty list.

    Dashboard vs experiments: this endpoint serves the live,
    in-memory history of the current run (unbounded for the
    session). Complete persistent experiment results live in
    ``experiment_results/`` CSV files and are never truncated
    by dashboard requests.
    """
    with _state_lock:
        history = engine.metrics.get_history()
        tick = world.tick
        if limit is not None:
            history = history[-limit:]
        # Detach under the lock; JSON encoding happens outside it.
        detached = []
        for snap in history:
            row = dict(snap)
            row["generation_counts"] = dict(snap.get("generation_counts", {}))
            detached.append(row)
    return {"tick": tick, "count": len(detached), "history": detached}


@app.get("/simulation/organisms/{organism_id}")
def get_organism(organism_id: int):
    """Look up one organism (living or historical) by ID."""
    with _state_lock:
        snapshot = capture_snapshot(world)
    for record in snapshot["organisms"]:
        if record["id"] == organism_id:
            return record
    raise HTTPException(
        status_code=404, detail=f"Organism {organism_id} not found."
    )
