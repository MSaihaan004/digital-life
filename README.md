# Digital Life 🧬

Digital Life is an artificial-life and evolutionary simulation built in Python.

The project simulates a 2D environment containing artificial organisms that can move, sense their surroundings, consume resources, manage energy, age, and eventually die.

The long-term goal is to evolve this into an experimental platform where evolutionary behavior and emergent traits can be observed and measured.

---

## Current Status

**Phase 2 — Life Loop: Complete ✅**

Implemented so far:

- Configurable 2D world
- Artificial organisms
- Numeric genomes
- Deterministic random seed
- Organism position and velocity
- Organism movement
- World boundary constraints
- Food resources
- Food sensing
- Nearby-organism sensing
- Boundary sensing
- Energy system
- Food consumption
- Metabolic energy loss
- Rule-based decision system
- Simulation engine
- Organism aging
- Death from zero energy
- Death from maximum age
- Simulation tick tracking

---

## Project Architecture

```text
Digital Life
│
├── World
│   ├── Organisms
│   └── Food
│
├── Organism
│   ├── Position
│   ├── Velocity
│   ├── Energy
│   ├── Health
│   ├── Age
│   ├── Generation
│   └── Genome
│
├── Sensors
│   ├── Food
│   ├── Organisms
│   ├── Energy
│   └── Boundaries
│
├── Brain
│   └── Rule-based Brain
│
└── Simulation Engine
    ├── Sensing
    ├── Decision
    ├── Movement
    ├── Food Interaction
    ├── Metabolism
    ├── Aging
    └── Death