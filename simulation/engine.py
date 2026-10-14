from brains.rule_brain import RuleBrain
from domain.sensors import sense

from simulation.physics import move_organism
from simulation.interactions import eat_food, apply_metabolism, respawn_food

from evolution.reproduction import can_reproduce, create_offspring
from evolution.mutation import mutate
from evolution.selection import select_parent
from evolution.metrics import EvolutionMetrics

from config import MAX_AGE

from time import perf_counter


class SimulationEngine:
    """Advance the Digital Life world one tick at a time.

    Tick order (preserved, made explicit):

    1. Snapshot organisms alive at tick start (newborns wait).
    2. For each pre-existing organism, in order:
       liveness check (alive and health>0) -> sense ->
       brain.decide (recorded) -> execute movement for MOVE only ->
       eat once (opportunistic, all actions) -> metabolism once ->
       age+1 -> death check (energy<=0, health<=0, age>=MAX_AGE) ->
       reproduction candidacy only if action is REPRODUCE and
       can_reproduce() passes.
    3. At most one global reproduction via select_parent.
    4. Register offspring (deferred so newborns never act birth tick).
    5. Respawn food, advance tick once, record metrics once.

    Action semantics (action-gated model): MOVE causes directed
    movement; EAT/REPRODUCE/IDLE cause no directed movement. Food
    consumption is opportunistic and applied once for every acting
    organism regardless of action (preserved economy). REPRODUCE is
    required for reproduction candidacy but never bypasses
    can_reproduce()/energy costs. IDLE means no directed movement
    but the organism still eats opportunistically if food is in
    range and still metabolizes/ages.
    """

    def __init__(self, world, rng=None):
        self.world = world

        # Use the explicitly supplied RNG, or reuse the world's RNG.
        self.rng = (
            rng
            if rng is not None
            else getattr(world, "rng", None)
        )

        # Backward compatibility for worlds without an RNG.
        if self.rng is None:
            import random
            self.rng = random

        self.brain = RuleBrain()
        self.metrics = EvolutionMetrics()

        # Optional phase instrumentation for benchmarking.
        # Disabled by default: ordinary ticks take the exact same
        # code path with only one extra attribute check per step.
        self._phase_timing = None

    def enable_phase_timing(self):
        """Record per-phase timings of the real step() path."""
        self._phase_timing = {
            "act": 0.0,
            "reproduce": 0.0,
            "housekeeping": 0.0,
            "metrics": 0.0,
            "ticks": 0,
        }

    def disable_phase_timing(self):
        """Stop recording phase timings (ordinary behavior)."""
        self._phase_timing = None

    def phase_report(self):
        """Return average seconds per timed tick for each phase.

        Phases (measured on the normal step() execution path):
        - act: per-organism loop (sense, decide, move, eat,
          metabolism, aging, death, eligibility).
        - reproduce: parent selection, offspring creation, mutation.
        - housekeeping: offspring registration, food respawn, tick
          increment, death-set computation.
        - metrics: metrics.record().

        Note: the phases cover the named instrumented regions only.
        Per-tick setup outside those regions (snapshotting the
        organism list, the pre-tick living set, and the next-ID
        scan) is intentionally not attributed, so phase timings
        may not sum to total tick time.
        """
        timing = self._phase_timing
        if not timing or not timing["ticks"]:
            return {}
        count = timing["ticks"]
        return {
            phase: timing[phase] / count
            for phase in ("act", "reproduce", "housekeeping", "metrics")
        }

    def _execute_action(self, organism, action, sensor_data):
        """Execute directed movement for an action.

        Only MOVE causes movement via the existing physics path.
        EAT/REPRODUCE/IDLE cause no directed movement. Food
        consumption and metabolism are handled by the caller
        exactly once per tick (never duplicated here).
        """
        if action is not None and getattr(action, "value", None) == "move":
            dx, dy = self.brain.movement_direction(sensor_data)
            move_organism(organism, dx, dy, self.world)

    def _act_organism(self, organism):
        """Run sense->decide->act->eat->metabolize->age->die.

        Returns True only if the brain selected REPRODUCE and the
        organism is living and passes can_reproduce() after acting.
        Dead organisms (alive False or health<=0 at entry) are
        marked dead, never act, eat, or reproduce.
        """
        if not organism.alive or organism.health <= 0:
            organism.alive = False
            return False

        sensor_data = sense(organism, self.world)
        action = self.brain.decide(sensor_data)
        self._execute_action(organism, action, sensor_data)

        # Single opportunistic food interaction per tick (all actions).
        eat_food(organism, self.world)

        # Single energy/aging update per tick.
        apply_metabolism(organism)
        organism.age += 1

        if organism.energy <= 0:
            organism.alive = False

        if organism.health <= 0:
            organism.alive = False

        if organism.age >= MAX_AGE:
            organism.alive = False

        if not organism.alive:
            return False

        if getattr(action, "value", None) != "reproduce":
            return False

        return bool(can_reproduce(organism))

    def _handle_reproduction(self, eligible_parents, next_organism_id):
        """Select at most one parent and produce one mutated child."""
        if not eligible_parents:
            return None
        parent = select_parent(eligible_parents, rng=self.rng)
        child = create_offspring(
            parent=parent,
            world=self.world,
            organism_id=next_organism_id,
            rng=self.rng,
        )
        child.genome = mutate(child.genome, rng=self.rng)
        return child

    def step(self):
        """
        Advance the simulation by one tick.

        Existing organisms act first. After their actions finish,
        one eligible parent is selected to reproduce at most once.
        Newborns are registered at the end of the tick.
        """

        # Process only organisms that existed at the start of this tick.
        existing_organisms = list(self.world.organisms)

        # Keep newborns separate until the tick finishes.
        pending_offspring = []

        # Track living organisms before the tick.
        alive_before = {
            organism.organism_id
            for organism in existing_organisms
            if organism.alive
        }

        # Generate IDs above all existing organism IDs.
        next_organism_id = (
            max(
                (
                    organism.organism_id
                    for organism in self.world.organisms
                ),
                default=-1,
            )
            + 1
        )

        # Collect organisms that may reproduce after acting.
        eligible_parents = []

        timed = self._phase_timing is not None
        if timed:
            phase_start = perf_counter()

        # 1. Existing organisms act (newborns deferred).
        for organism in existing_organisms:
            if self._act_organism(organism):
                eligible_parents.append(organism)

        if timed:
            self._phase_timing["act"] += perf_counter() - phase_start
            phase_start = perf_counter()

        # 2-4. At most one reproduction per tick.
        if eligible_parents:
            child = self._handle_reproduction(
                eligible_parents, next_organism_id
            )
            if child is not None:
                pending_offspring.append(child)

        if timed:
            self._phase_timing["reproduce"] += perf_counter() - phase_start
            phase_start = perf_counter()

        # --------------------------------------------------
        # 5. Register offspring.
        # --------------------------------------------------
        self.world.organisms.extend(pending_offspring)

        # --------------------------------------------------
        # 6. Replenish food eaten during this tick.
        # --------------------------------------------------
        respawn_food(self.world)

        # Advance simulation time exactly once.
        self.world.tick += 1

        # Identify organisms that died during this tick.
        alive_after = {
            organism.organism_id
            for organism in self.world.organisms
            if organism.alive
        }

        deaths_this_tick = len(
            alive_before - alive_after
        )

        if timed:
            self._phase_timing["housekeeping"] += (
                perf_counter() - phase_start
            )
            phase_start = perf_counter()

        # --------------------------------------------------
        # 7. Record simulation and evolutionary metrics.
        # --------------------------------------------------
        self.metrics.record(
            self.world,
            births=len(pending_offspring),
            deaths=deaths_this_tick,
        )

        if timed:
            self._phase_timing["metrics"] += perf_counter() - phase_start
            self._phase_timing["ticks"] += 1

    def run(self, ticks):
        """Run the simulation for the specified number of ticks."""

        for _ in range(ticks):
            self.step()
