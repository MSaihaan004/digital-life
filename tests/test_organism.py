"""Organism/genome invariants, boundaries, copying."""
from dataclasses import replace
from domain.genome import Genome
from domain.organism import Organism, validate_organism_state, copy_genome, GENE_NAMES


def make_genome(**kw):
    base = dict(speed=0.5, vision=0.5, metabolism=0.5, size=0.5,
                reproduction_threshold=0.5, mutation_rate=0.1)
    base.update(kw)
    return Genome(**base)


def make_org(**kw):
    base = dict(organism_id=1, x=0.0, y=0.0, energy=50.0, health=100.0,
                age=5, generation=0, genome=make_genome())
    base.update(kw)
    return Organism(**base)


def test_valid_state_has_no_violations():
    assert validate_organism_state(make_org()) == []


def test_negative_states_reported():
    org = make_org(energy=-1, health=-1, age=-1, offspring_count=-1, generation=-1)
    problems = validate_organism_state(org)
    assert "energy-negative" in problems
    assert "health-negative" in problems
    assert "age-negative" in problems


def test_genome_boundary_values():
    assert validate_organism_state(make_org(genome=make_genome(speed=0.0))) == []
    assert validate_organism_state(make_org(genome=make_genome(speed=1.0))) == []
    bad = make_org(genome=make_genome(speed=1.5))
    assert "gene-speed-out-of-range" in validate_organism_state(bad)


def test_genome_copy_independent():
    g = make_genome(speed=0.3)
    c = copy_genome(g)
    assert c == g and c is not g
    c.speed = 0.9
    assert g.speed == 0.3
    # replace() same guarantee used by reproduction
    c2 = replace(g)
    c2.vision = 0.0
    assert g.vision == 0.5


def test_organism_velocity_fields_declared_with_defaults():
    org = make_org()
    assert org.velocity_x == 0.0 and org.velocity_y == 0.0


def test_gene_names_documented():
    assert set(GENE_NAMES) == {"speed", "vision", "metabolism", "size",
                               "reproduction_threshold", "mutation_rate"}
