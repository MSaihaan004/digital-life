# Digital Life

Digital Life is an artificial-life simulation built in Python.

The project explores how complex behavior and evolutionary patterns can emerge
from simple rules, environmental constraints, reproduction, mutation, and
selection.

## Current Status

### Stage 1 — Foundation ✅

- 2D world
- Organism model
- Genome model
- Configurable population
- Food resources
- Deterministic random seed

### Upcoming

- [ ] Sensors
- [ ] Movement
- [ ] Food consumption
- [ ] Energy system
- [ ] Aging and death
- [ ] Reproduction
- [ ] Mutation
- [ ] Evolution experiments
- [ ] Pygame visualization
- [ ] Neural-network brain

## Tech Stack

- Python
- NumPy — planned
- Pygame — planned
- PyTorch — future

## Project Structure

```text
digital-life/
├── app.py
├── config.py
├── domain/
│   ├── genome.py
│   ├── organism.py
│   └── world.py
└── tests/