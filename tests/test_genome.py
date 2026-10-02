import random
from domain.genome import Genome

def test_genome_random_bounds():
    genome = Genome.random()
    assert 0.0 <= genome.speed <= 1.0
    assert 0.0 <= genome.vision <= 1.0
    assert 0.0 <= genome.metabolism <= 1.0
    assert 0.0 <= genome.size <= 1.0
    assert 0.0 <= genome.reproduction_threshold <= 1.0
    assert 0.0 <= genome.mutation_rate <= 1.0

def test_genome_random_deterministic():
    random.seed(42)
    genome1 = Genome.random()
    
    random.seed(42)
    genome2 = Genome.random()
    
    assert genome1.speed == genome2.speed
    assert genome1.vision == genome2.vision
    assert genome1.metabolism == genome2.metabolism
    assert genome1.size == genome2.size
    assert genome1.reproduction_threshold == genome2.reproduction_threshold
    assert genome1.mutation_rate == genome2.mutation_rate

