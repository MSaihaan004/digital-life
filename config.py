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
