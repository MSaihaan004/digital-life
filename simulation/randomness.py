"""Central random-number generator for Digital Life."""

import random

from config import RANDOM_SEED


def create_rng(seed=RANDOM_SEED):
    """Create a random-number generator for a simulation run."""
    return random.Random(seed)
