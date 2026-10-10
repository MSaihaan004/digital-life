# Digital Life 🧬

**An experimental artificial-life simulation exploring evolution, survival, reproduction, and natural selection using Python.**

Digital Life is a Python-based artificial-life project in which digital organisms exist in a simulated environment, consume energy, age, reproduce, mutate, and die.

The long-term goal is to build an experimental platform for studying how inherited traits influence survival and reproduction across generations.

Rather than assuming that evolution always produces better organisms, Digital Life investigates how environmental conditions, resource availability, and the costs of survival influence evolutionary outcomes.

---

## 📌 Project Status

**Current milestone: Stage 3 — Evolutionary Mechanics and Experiments**

| Stage | Description | Status |
| --- | --- | --- |
| Stage 1 | Initial project foundation and digital organisms | ✅ Complete |
| Stage 2 | Life cycle, aging, and death | ✅ Complete |
| Stage 3 | Evolutionary mechanics and experimental analysis | ✅ Complete |
| Stage 4 | Advanced evolutionary experiments and model improvements | 🔜 Planned |

The project currently includes an organism simulation, evolutionary mechanics, automated tests, reproducible experiments, and CSV-based experimental results.

---

## 🎯 Project Objectives

Digital Life aims to explore the following questions:

- How do inherited traits affect an organism's survival?
- How does mutation introduce variation into a population?
- How do reproduction and selection influence successive generations?
- How does metabolism affect energy consumption and survival?
- How do resource availability and environmental conditions influence population dynamics?
- Can repeated experiments reveal consistent evolutionary patterns?
- How much do experimental outcomes vary across different random seeds?

The project is designed to investigate these questions through simulation and measurable results.

---

## 🌍 How the Simulation Works

Digital Life models a population of organisms living in a shared environment.

Each organism has inherited traits and a life cycle. Organisms interact with their surroundings, manage their energy, and may reproduce if the simulation's conditions permit it.

### 1. Environment

The simulated world contains organisms and food resources.

The environment is configured using parameters such as:

- World dimensions
- Initial population
- Initial food availability
- Food interaction distance
- Organism energy limits
- Maximum age

These parameters can be adjusted to investigate different simulation conditions.

### 2. Digital Organisms

Each organism has a genome containing inherited traits.

Organisms also have life-cycle properties, including energy, health, and age.

During simulation, organisms can:

- Move through the environment.
- Interact with food resources.
- Consume energy.
- Gain energy from food.
- Age over time.
- Reproduce when eligible.
- Die when their survival conditions are no longer satisfied.

### 3. Genome and Inherited Traits

The genome represents characteristics that can be inherited by offspring.

The evolutionary implementation includes mutation and reproduction mechanisms.

The traits currently investigated include metabolism and other inherited characteristics represented by the simulation's genome.

### 4. Reproduction

Eligible organisms can produce offspring according to the simulation's reproduction rules.

Reproduction transfers energy from a parent to its offspring, introducing an energetic cost to producing descendants.

The current configuration includes:

```python
REPRODUCTION_ENERGY_COST = 30.0
```

### 5. Mutation

Mutation introduces variation into inherited traits.

This allows offspring to differ from their parents and provides variation for evolutionary experiments.

### 6. Selection and Fitness

The evolutionary system includes fitness evaluation and selection mechanisms.

These components provide a framework for investigating how inherited characteristics relate to survival and reproductive outcomes.

The project does not assume that every mutation is beneficial or that every experiment will produce an increasingly successful population.

---

## 🧬 Stage 3: Evolutionary Mechanics

Stage 3 extends the earlier life-cycle simulation with evolutionary mechanics and experimental analysis.

### Implemented capabilities

- Genome-based inherited traits
- Mutation
- Reproduction with an energy cost
- Selection strategies
- Fitness evaluation
- Evolutionary metrics
- Reproducible simulation runs
- Simulation data export
- Multi-seed experiments
- Metabolism experiments
- Energy-economy analysis
- Automated tests for evolutionary behavior

### Evolutionary experiment workflow

The general experimental workflow is:

1. Configure the simulation.
2. Initialize a population.
3. Run the simulation for a specified number of ticks.
4. Record population and evolutionary metrics.
5. Repeat the experiment with different random seeds.
6. Export results to CSV.
7. Compare results across experimental conditions.
8. Investigate patterns and limitations.

This workflow helps distinguish repeatable patterns from outcomes that may depend on a particular random seed.

---

## 🔬 Experiments and Findings

Stage 3 includes experiments investigating evolutionary outcomes, metabolism, and energy economics.

The results described below come from the experiments conducted during Stage 3 development.

### 1. Multi-Seed Evolution Analysis

An experiment was conducted using 20 random seeds, from 42 through 61, with 500 simulation ticks per run.

The analysis reported:

| Metric | Result |
| --- | ---: |
| Mean total organisms recorded | 272.9 |
| Mean living population | 41.0 |
| Mean births | 172.9 |
| Mean correlation between metabolism and survival | -0.5077 |
| Standard deviation of the correlation | 0.0476 |

The analysis found a negative relationship between metabolism and survival in the tested simulation conditions.

This is an observed result for the current model, not a universal biological rule.

### 2. Controlled Metabolism Experiment

A controlled experiment compared five fixed metabolism values across ten random seeds, from 42 through 51, with 500 ticks per run.

The reported average results were:

| Metabolism | Mean living population | Mean births |
| ---: | ---: | ---: |
| 0.05 | 322.0 | 260.0 |
| 0.20 | 15.2 | 209.7 |
| 0.40 | 1.3 | 165.4 |
| 0.60 | 0.4 | 132.0 |
| 0.80 | 0.1 | 108.7 |

Under these experimental conditions, higher metabolism was associated with substantially lower population survival and fewer births.

This suggests that the current energy model strongly penalizes higher metabolism.

Further investigation is needed before changing the model, because the results may depend on the interaction between energy consumption, food access, reproduction, and population dynamics.

### 3. Energy-Economy Experiment

An additional experiment investigated food acquisition, energy gained, metabolic energy consumed, and uneaten food.

The experiment reported the following mean values:

| Metabolism | Food events | Food energy gained | Metabolic energy consumed | Food left |
| ---: | ---: | ---: | ---: | ---: |
| 0.05 | 199.9 | 2536.94 | 6809.50 | 0.1 |
| 0.20 | 199.3 | 3152.24 | 12926.80 | 0.7 |
| 0.40 | 190.6 | 3561.06 | 13534.86 | 9.4 |
| 0.60 | 174.1 | 3507.50 | 13500.94 | 25.9 |
| 0.80 | 147.6 | 3052.90 | 13050.90 | 52.4 |

The results suggest that food access and metabolic expenditure interact in ways that influence survival.

Higher-metabolism conditions left more food uneaten on average, while organisms under those conditions consumed substantially more metabolic energy.

This raises a useful research question:

**Are high-metabolism organisms dying primarily because of energy expenditure, reduced food acquisition, or the interaction between these mechanisms?**

Future experiments can investigate this question more precisely.

### Scientific Interpretation

These experiments are preliminary investigations of the current simulation.

Their results should be interpreted within the model's assumptions and parameter settings.

They do not establish universal biological laws, and further controlled experiments are needed to distinguish causal mechanisms.

---

## 📊 Data and Analysis

Experimental scripts and results are organized separately from the core simulation.

### Experiment scripts

The `experiments/` directory contains:

| File | Purpose |
| --- | --- |
| `validate_evolution.py` | Validates evolutionary behavior under experimental conditions |
| `analyze_evolution.py` | Analyzes evolutionary outcomes |
| `analyze_multiple_seeds.py` | Compares results across multiple random seeds |
| `analyze_metabolism.py` | Investigates the relationship between metabolism and population outcomes |
| `analyze_energy_economy.py` | Examines food acquisition and energy expenditure |

### Experimental results

The `experiment_results/` directory contains CSV data generated during Stage 3.

Examples include:

- `seed_42.csv`
- `seed_123.csv`
- `seed_456.csv`
- `individuals_seed_42.csv`
- `multi_seed_summary.csv`
- `metabolism_experiment.csv`
- `energy_economy_summary.csv`
- `energy_economy_timeseries.csv`

These files preserve experimental outputs for later inspection, comparison, and analysis.

---

## 🏗️ Project Structure

The repository is organized into modules separating the environment, organisms, simulation mechanics, evolutionary behavior, analysis, experiments, and tests.

```text
digital-life/
│
├── analytics/
│   ├── __init__.py
│   └── metrics.py
│
├── brains/
│   ├── __init__.py
│   └── rule_brain.py
│
├── domain/
│   ├── __init__.py
│   ├── events.py
│   ├── genome.py
│   ├── organism.py
│   ├── sensors.py
│   └── world.py
│
├── evolution/
│   ├── __init__.py
│   ├── exporter.py
│   ├── fitness.py
│   ├── metrics.py
│   ├── mutation.py
│   ├── reproduction.py
│   └── selection.py
│
├── simulation/
│   ├── __init__.py
│   ├── engine.py
│   ├── interactions.py
│   ├── physics.py
│   ├── randomness.py
│   └── rules.py
│
├── experiments/
│   ├── validate_evolution.py
│   ├── analyze_evolution.py
│   ├── analyze_multiple_seeds.py
│   ├── analyze_metabolism.py
│   └── analyze_energy_economy.py
│
├── experiment_results/
│   ├── seed_42.csv
│   ├── seed_123.csv
│   ├── seed_456.csv
│   ├── individuals_seed_42.csv
│   ├── multi_seed_summary.csv
│   ├── metabolism_experiment.csv
│   ├── energy_economy_summary.csv
│   └── energy_economy_timeseries.csv
│
├── tests/
│   ├── test_evolution_integration.py
│   ├── test_exporter.py
│   ├── test_fitness.py
│   ├── test_genome.py
│   ├── test_metrics.py
│   ├── test_mutation.py
│   ├── test_organism.py
│   ├── test_reproducibility.py
│   ├── test_reproduction.py
│   ├── test_selection_strategy.py
│   ├── test_simulation_engine.py
│   └── test_world.py
│
├── app.py
├── config.py
├── requirements.txt
├── .gitignore
└── README.md
```

The tree describes the intended project organization. Individual files may evolve as the implementation grows.

---

## ⚙️ Technology Stack

- **Python** — Core simulation and evolutionary mechanics
- **pytest** — Automated testing
- **CSV** — Experimental data export and storage
- **Git** — Version control
- **GitHub** — Remote repository and project history

The current simulation and analysis pipeline is implemented primarily in Python.

---

## 🚀 Getting Started

### Prerequisites

Install Python and Git.

The project has been developed and tested with Python 3.13.4.

### 1. Clone the repository

```bash
git clone https://github.com/MSaihaan004/digital-life.git
cd digital-life
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, you can use the Command Prompt activation script instead:

```bat
.venv\Scripts\activate.bat
```

### 3. Install testing dependencies

The project currently uses pytest for its automated tests.

```bash
python -m pip install pytest
```

The repository's `requirements.txt` may be expanded as additional external dependencies are introduced.

### 4. Run the automated tests

```bash
python -m pytest -v
```

During Stage 3 development, the complete test suite reported:

**59 passed.**

This records the result obtained during development; rerun the tests after making changes to verify the current state.

### 5. Run an experiment

From the project root, experiment scripts can be executed with Python.

For example:

```bash
python experiments/analyze_evolution.py
```

Other scripts can be run similarly:

```bash
python experiments/analyze_multiple_seeds.py
python experiments/analyze_metabolism.py
python experiments/analyze_energy_economy.py
```

Some experiments may take longer because they run multiple simulations.

Check each script's configuration before changing its parameters or rerunning it, particularly if you want to preserve existing experimental results.

---

## 🧪 Testing Strategy

Automated tests help verify the behavior of the simulation and evolutionary components.

The test suite covers areas including:

- Genome behavior
- Organism behavior
- World mechanics
- Mutation
- Reproduction
- Selection strategies
- Fitness evaluation
- Evolutionary metrics
- Data export
- Reproducibility
- Simulation integration

Tests should be run whenever simulation mechanics or evolutionary rules are changed.

The goal is to preserve previously working behavior while introducing new capabilities.

---

## 🔁 Reproducibility

Randomness plays an important role in artificial-life simulations.

Digital Life includes support for seeded experiments so that runs can be repeated under controlled conditions.

Using multiple random seeds also helps investigate whether observed outcomes are consistent across different simulation runs.

Reproducibility is important when evaluating evolutionary patterns and comparing alternative configurations.

---

## 🛣️ Roadmap

### Stage 1 — Foundation

- Establish the Python project structure.
- Create the initial simulation components.
- Introduce digital organisms and their environment.

**Status: Complete**

### Stage 2 — Life Cycle

- Implement organism aging.
- Introduce death and life-cycle mechanics.
- Establish the core simulation loop.

**Status: Complete**

### Stage 3 — Evolutionary Mechanics and Experiments

- Implement inherited traits and mutation.
- Add reproduction and selection.
- Introduce fitness evaluation and evolutionary metrics.
- Export simulation data.
- Run reproducible experiments.
- Investigate metabolism and energy economics.

**Status: Complete**

### Stage 4 — Deeper Evolutionary Investigation

Potential next steps include:

- Investigating the causes of high-metabolism mortality.
- Separating energy expenditure from food-access effects in controlled experiments.
- Improving the measurement of birth, survival, and death causes.
- Comparing alternative selection strategies.
- Evaluating evolutionary outcomes over longer simulations.
- Improving experiment summaries and visualizations.

**Status: Planned**

### Future Directions

Longer-term possibilities include:

- More sophisticated organism behavior.
- Additional inherited traits.
- More complex environmental conditions.
- Improved experimental analysis.
- Visualization of population dynamics.
- Interactive exploration of evolutionary outcomes.

These are future possibilities, not claims about currently implemented functionality.

---

## 🔐 Version Control

Digital Life is maintained in Git and hosted on GitHub.

Repository:

<https://github.com/MSaihaan004/digital-life>

The repository history preserves the project's development milestones.

Current version tags include:

- `v0.1.0` — Initial foundation
- `v0.2.0` — Life cycle with aging and death

Stage 3 evolutionary mechanics and experiments were subsequently committed to the `main` branch.

Future development should continue in the existing repository to preserve the project history and avoid duplicate working copies.

---

## 📚 Project Philosophy

Digital Life is an experimental software project, not a claim to reproduce biological evolution in full.

Its purpose is to create a controlled environment in which hypotheses about survival, resource competition, inheritance, and reproduction can be explored through code and data.

A simulation is most useful when its assumptions are explicit, its outcomes are measurable, and its conclusions remain open to testing.

The goal is not to make every digital organism survive.

**The goal is to understand why some survive, why others fail, and how the rules of the environment shape the population over time.**

---

## 👨‍💻 Author

**Mohammad Saihaan**

GitHub: [@MSaihaan004](https://github.com/MSaihaan004)

---

*Digital Life — A step toward exploring artificial life through simulation, experimentation, and evolutionary computation.*
