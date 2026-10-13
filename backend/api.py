"""FastAPI application for the Digital Life simulation."""

import random
import threading
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    RANDOM_SEED,
    INITIAL_POPULATION,
    INITIAL_FOOD,
    DEFAULT_TICKS_PER_SECOND,
    MIN_TICKS_PER_SECOND,
    MAX_TICKS_PER_SECOND,
)

from domain.world import World
from simulation.engine import SimulationEngine

from backend.state_serializer import serialize_world


app = FastAPI(
    title="Digital Life API",
    description="Backend API for the Digital Life ecosystem.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_simulation():
    """Initialize a simulation using the existing configuration."""

    random.seed(RANDOM_SEED)

    world = World()
    world.spawn_organisms(INITIAL_POPULATION)
    world.spawn_food(INITIAL_FOOD)

    engine = SimulationEngine(world)

    return world, engine


world, engine = create_simulation()

_state_lock = threading.Lock()
_ticks_per_second = float(DEFAULT_TICKS_PER_SECOND)
_simulation_thread_started = False


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
            f"ticks_per_second must be between "
            f"{MIN_TICKS_PER_SECOND} and {MAX_TICKS_PER_SECOND}."
        )

    with _state_lock:
        globals()["_ticks_per_second"] = ticks
        return ticks


class TicksPerSecondUpdate(BaseModel):
    ticks_per_second: float


def _simulation_loop():
    """Advance the simulation in the background for the live dashboard."""

    while True:
        with _state_lock:
            current_ticks = _ticks_per_second

        # Guard against a zero/negative value ever slipping through.
        interval = 1.0 / current_ticks if current_ticks > 0 else 0.5
        time.sleep(interval)

        try:
            with _state_lock:
                engine.step()
        except Exception:
            # Keep the background loop alive even if a tick fails.
            continue


def _ensure_simulation_thread():
    global _simulation_thread_started

    if _simulation_thread_started:
        return

    _simulation_thread_started = True

    thread = threading.Thread(
        target=_simulation_loop,
        name="digital-life-simulation",
        daemon=True,
    )
    thread.start()


_ensure_simulation_thread()


@app.get("/")
def root():
    """Return basic API information."""

    return {
        "application": "Digital Life API",
        "status": "running",
        "simulation_tick": world.tick,
        "ticks_per_second": get_ticks_per_second(),
    }


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
        raise HTTPException(status_code=422, detail=str(exc))

    return {
        "ticks_per_second": ticks,
        "min_ticks_per_second": MIN_TICKS_PER_SECOND,
        "max_ticks_per_second": MAX_TICKS_PER_SECOND,
    }


@app.get("/simulation/state")
def get_simulation_state():
    """Return the current world state without advancing the simulation."""

    with _state_lock:
        state = serialize_world(
            world,
            metrics=engine.metrics,
        )
        state["ticks_per_second"] = _ticks_per_second
        return state
