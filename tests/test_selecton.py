from domain.organism import Organism
from domain.genome import Genome
from evolution.selection import calculate_fitness


def make_organism(organism_id, parent_id=None):
    return Organism(
        organism_id=organism_id,
        x=100.0,
        y=100.0,
        energy=100.0,
        health=100.0,
        age=10,
        generation=0,
        genome=Genome(
            speed=0.5,
            vision=0.5,
            metabolism=0.5,
            size=0.5,
            reproduction_threshold=0.5,
            mutation_rate=0.1,
        ),
        parent_id=parent_id,
    )


def test_fitness_is_zero_without_offspring():
    parent = make_organism(1)

    organisms = [parent]

    assert calculate_fitness(parent, organisms) == 0


def test_fitness_counts_direct_offspring():
    parent = make_organism(1)

    child1 = make_organism(2, parent_id=1)
    child2 = make_organism(3, parent_id=1)
    child3 = make_organism(4, parent_id=1)

    organisms = [parent, child1, child2, child3]

    assert calculate_fitness(parent, organisms) == 3


def test_fitness_does_not_count_unrelated_offspring():
    parent = make_organism(1)

    child1 = make_organism(2, parent_id=1)
    child2 = make_organism(3, parent_id=99)

    organisms = [parent, child1, child2]

    assert calculate_fitness(parent, organisms) == 1


def test_fitness_uses_persistent_offspring_count():
    parent = make_organism(1)
    parent.offspring_count = 4

    # No offspring need to remain in the supplied collection.
    assert calculate_fitness(parent, []) == 4
