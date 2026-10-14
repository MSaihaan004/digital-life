WORLD_WIDTH = 800
WORLD_HEIGHT = 600

INITIAL_POPULATION = 100
INITIAL_FOOD = 200

STARTING_ENERGY = 100.0
MAX_ENERGY = 100.0
FOOD_ENERGY = 25.0

STARTING_HEALTH = 100.0

# Food respawn keeps the ecosystem supplied so the simulation
# does not starve abruptly once the initial food is eaten.
# Each tick, food is replenished toward FOOD_TARGET_COUNT, but at
# most FOOD_RESPAWN_PER_TICK items, and never beyond FOOD_MAX_COUNT.
FOOD_TARGET_COUNT = 200
FOOD_MAX_COUNT = 400
FOOD_RESPAWN_PER_TICK = 5

MAX_AGE = 1000

EAT_DISTANCE = 5.0

RANDOM_SEED = 42

# Energy transferred from a parent to its offspring during reproduction.
REPRODUCTION_ENERGY_COST = 30.0

# Ticks per second for the live simulation background loop.
DEFAULT_TICKS_PER_SECOND = 2.0
MIN_TICKS_PER_SECOND = 0.5
MAX_TICKS_PER_SECOND = 60.0


def validate_config(values=None):
    """Validate simulation configuration without changing defaults.

    Args:
        values: Optional mapping overriding defaults. When omitted,
            the current module-level defaults are validated.

    Returns:
        A list of human-readable error strings (empty when valid).
    """
    src = {
        "WORLD_WIDTH": WORLD_WIDTH,
        "WORLD_HEIGHT": WORLD_HEIGHT,
        "INITIAL_POPULATION": INITIAL_POPULATION,
        "INITIAL_FOOD": INITIAL_FOOD,
        "STARTING_ENERGY": STARTING_ENERGY,
        "MAX_ENERGY": MAX_ENERGY,
        "FOOD_ENERGY": FOOD_ENERGY,
        "STARTING_HEALTH": STARTING_HEALTH,
        "FOOD_TARGET_COUNT": FOOD_TARGET_COUNT,
        "FOOD_MAX_COUNT": FOOD_MAX_COUNT,
        "FOOD_RESPAWN_PER_TICK": FOOD_RESPAWN_PER_TICK,
        "MAX_AGE": MAX_AGE,
        "EAT_DISTANCE": EAT_DISTANCE,
        "RANDOM_SEED": RANDOM_SEED,
        "REPRODUCTION_ENERGY_COST": REPRODUCTION_ENERGY_COST,
        "DEFAULT_TICKS_PER_SECOND": DEFAULT_TICKS_PER_SECOND,
        "MIN_TICKS_PER_SECOND": MIN_TICKS_PER_SECOND,
        "MAX_TICKS_PER_SECOND": MAX_TICKS_PER_SECOND,
    }
    if values:
        src.update(values)

    errors = []

    for name in (
        "INITIAL_POPULATION", "INITIAL_FOOD", "FOOD_TARGET_COUNT",
        "FOOD_MAX_COUNT", "FOOD_RESPAWN_PER_TICK",
    ):
        v = src[name]
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            errors.append(f"{name} must be a non-negative integer.")
    for name in ("WORLD_WIDTH", "WORLD_HEIGHT", "MAX_AGE"):
        v = src[name]
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            errors.append(f"{name} must be a positive integer.")
    for name in (
        "MAX_ENERGY", "STARTING_ENERGY", "FOOD_ENERGY",
        "STARTING_HEALTH", "EAT_DISTANCE", "REPRODUCTION_ENERGY_COST",
        "DEFAULT_TICKS_PER_SECOND", "MIN_TICKS_PER_SECOND",
        "MAX_TICKS_PER_SECOND",
    ):
        v = src[name]
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            errors.append(f"{name} must be a number.")
        elif not (v == v and v not in (float("inf"), float("-inf"))):
            errors.append(f"{name} must be finite.")
        elif v < 0 or (name in ("MAX_ENERGY", "DEFAULT_TICKS_PER_SECOND",
                                "MIN_TICKS_PER_SECOND", "MAX_TICKS_PER_SECOND")
                       and v <= 0):
            errors.append(f"{name} has an invalid value.")

    if (isinstance(src["STARTING_ENERGY"], (int, float))
            and isinstance(src["MAX_ENERGY"], (int, float))
            and src["STARTING_ENERGY"] > src["MAX_ENERGY"]):
        errors.append("STARTING_ENERGY cannot exceed MAX_ENERGY.")
    if (isinstance(src["FOOD_TARGET_COUNT"], int)
            and isinstance(src["FOOD_MAX_COUNT"], int)
            and src["FOOD_TARGET_COUNT"] > src["FOOD_MAX_COUNT"]):
        errors.append("FOOD_TARGET_COUNT cannot exceed FOOD_MAX_COUNT.")
    if (isinstance(src["MIN_TICKS_PER_SECOND"], (int, float))
            and isinstance(src["MAX_TICKS_PER_SECOND"], (int, float))
            and src["MIN_TICKS_PER_SECOND"] > src["MAX_TICKS_PER_SECOND"]):
        errors.append("MIN_TICKS_PER_SECOND cannot exceed MAX_TICKS_PER_SECOND.")
    if (isinstance(src["DEFAULT_TICKS_PER_SECOND"], (int, float))
            and isinstance(src["MIN_TICKS_PER_SECOND"], (int, float))
            and isinstance(src["MAX_TICKS_PER_SECOND"], (int, float))
            and not (src["MIN_TICKS_PER_SECOND"]
                     <= src["DEFAULT_TICKS_PER_SECOND"]
                     <= src["MAX_TICKS_PER_SECOND"])):
        errors.append("DEFAULT_TICKS_PER_SECOND must be within tick-rate bounds.")
    if not isinstance(src["RANDOM_SEED"], int) or isinstance(src["RANDOM_SEED"], bool):
        errors.append("RANDOM_SEED must be an integer.")

    return errors
