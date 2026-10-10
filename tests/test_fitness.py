from domain.organism import Organism
from domain.genome import Genome


from domain.world import World
from evolution.metrics import EvolutionMetrics

from evolution.fitness import (
    measure_survival,
    measure_lifespan,
    measure_reproductive_success,
)


def make_organism():
    return Organism(
        organism_id=1,
        x=100.0,
        y=100.0,
        energy=100.0,
        health=100.0,
        age=50,
        generation=0,
        genome=Genome(
            speed=0.5,
            vision=0.5,
            metabolism=0.5,
            size=0.5,
            reproduction_threshold=0.5,
            mutation_rate=0.1,
        ),
    )


def test_living_organism_has_positive_survival_status():
    organism = make_organism()

    assert measure_survival(organism) is True


def test_dead_organism_has_negative_survival_status():
    organism = make_organism()
    organism.alive = False

    assert measure_survival(organism) is False


def test_organism_with_zero_health_is_not_surviving():
    organism = make_organism()
    organism.health = 0

    assert measure_survival(organism) is False


def test_lifespan_measurement_returns_age():
    organism = make_organism()
    organism.age = 75

    assert measure_lifespan(organism) == 75


def test_reproductive_success_returns_offspring_count():
    organism = make_organism()
    organism.offspring_count = 3

    assert measure_reproductive_success(organism) == 3


def test_metrics_record_average_age():
    world = World()

    organism1 = make_organism()
    organism1.age = 20

    organism2 = make_organism()
    organism2.organism_id = 2
    organism2.age = 40

    world.organisms.extend([organism1, organism2])

    metrics = EvolutionMetrics()
    snapshot = metrics.record(world)

    assert snapshot["average_age"] == 30


def test_metrics_record_reproductive_success():
    world = World()

    organism1 = make_organism()
    organism1.offspring_count = 2

    organism2 = make_organism()
    organism2.organism_id = 2
    organism2.offspring_count = 4

    world.organisms.extend([organism1, organism2])

    metrics = EvolutionMetrics()
    snapshot = metrics.record(world)

    assert snapshot["average_reproductive_success"] == 3
    assert snapshot["maximum_reproductive_success"] == 4


def test_metrics_record_survival_rate():
    world = World()

    living = make_organism()

    dead = make_organism()
    dead.organism_id = 2
    dead.alive = False

    world.organisms.extend([living, dead])

    metrics = EvolutionMetrics()
    snapshot = metrics.record(world)

    assert snapshot["survival_rate"] == 0.5


def test_metrics_handle_empty_world():
    world = World()

    metrics = EvolutionMetrics()
    snapshot = metrics.record(world)

    assert snapshot["survival_rate"] is None
    assert snapshot["average_age"] is None
    assert snapshot["average_reproductive_success"] is None
    assert snapshot["maximum_reproductive_success"] is None
