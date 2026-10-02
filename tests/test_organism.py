from domain.organism import Organism
from domain.genome import Genome

def test_organism_construction():
    genome = Genome.random()
    organism = Organism(
        organism_id=1,
        x=10.0,
        y=20.0,
        energy=100.0,
        health=100.0,
        age=0,
        generation=0,
        genome=genome
    )
    
    assert organism.organism_id == 1
    assert organism.x == 10.0
    assert organism.y == 20.0
    assert organism.energy == 100.0
    assert organism.health == 100.0
    assert organism.age == 0
    assert organism.generation == 0
    assert organism.genome is genome
    assert organism.parent_id is None
    assert organism.alive is True

def test_organism_default_values():
    genome = Genome.random()
    organism = Organism(
        organism_id=2,
        x=5.0,
        y=5.0,
        energy=50.0,
        health=50.0,
        age=1,
        generation=1,
        genome=genome,
        parent_id=1
    )
    
    assert organism.parent_id == 1
    assert organism.alive is True

