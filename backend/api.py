"""FastAPI application for the Digital Life simulation."""

import random

from fastapi import FastAPI

from config import (
    RANDOM_SEED,
    INITIAL_POPULATION,
    INITIAL_FOOD,
)

from domain.world import World
from simulation.engine import SimulationEngine

from backend.state_serializer import serialize_world


app = FastAPI(
    title="Digital Life API",
    description="Backend API for the Digital Life ecosystem.",
    version="0.1.0",
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


@app.get("/")
def root():
    """Return basic API information."""

    return {
        "application": "Digital Life API",
        "status": "running",
        "simulation_tick": world.tick,
    }


@app.get("/simulation/state")
def get_simulation_state():
    """Return the current world state without advancing the simulation."""

    return serialize_world(
        world,
        metrics=engine.metrics,
    )
