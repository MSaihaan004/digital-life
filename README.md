# Digital Life 🧬

**An experimental artificial-life simulation exploring evolution, survival, reproduction, and natural selection using Python.**

Digital Life is a Python-based artificial-life project in which digital organisms exist in a simulated environment, consume energy, age, reproduce, mutate, and die.

The long-term goal is to build an experimental platform for studying how inherited traits influence survival and reproduction across generations.

Rather than assuming that evolution always produces better organisms, Digital Life investigates how environmental conditions, resource availability, and the costs of survival influence evolutionary outcomes.

---

## 📌 Project Status

**Current milestone: MVP — Simulation correctness, backend controls, dashboard integration, performance, and experiment reliability (Batches 1–5)**

| Area | Status |
| --- | --- |
| Simulation engine and tick semantics | ✅ Stable |
| Brain-action gating and health-based death | ✅ Implemented and tested |
| Sensors (vision-limited, tie-stable) | ✅ Implemented and tested |
| Backend worker lifecycle and controls | ✅ Implemented and tested |
| Dashboard controls, status, charts | ✅ Implemented and tested |
| Experiment output safety and metadata | ✅ Implemented and tested |
| Benchmarks and deterministic replay | ✅ Implemented and tested |
| Stage 4 (advanced evolution) | 🔜 Not implemented |

The project includes the organism simulation, evolutionary mechanics, a FastAPI backend with pause/resume/step/reset controls, a vanilla HTML/CSS/JS dashboard, automated Python tests, Playwright browser tests, reproducible benchmarks, and protected experiment outputs.

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

## 🏗️ Project Architecture

```text
digital-life/
├── analytics/        # Reserved package (currently empty; metrics live in evolution/metrics.py)
├── backend/
│   ├── api.py                # FastAPI app: worker lifecycle, controls, status, state
│   └── state_serializer.py   # Snapshot capture (under lock) + serialization (outside lock)
├── brains/
│   └── rule_brain.py         # Rule-based policy: MOVE / EAT / REPRODUCE / IDLE
├── domain/
│   ├── organism.py / genome.py / world.py / sensors.py / events.py
├── evolution/
│   ├── reproduction.py / mutation.py / selection.py / fitness.py
│   ├── metrics.py    # Canonical per-tick metrics (living-only averages)
│   └── exporter.py   # CSV export (overwrite-guarded, atomic)
├── simulation/
│   ├── engine.py         # Tick pipeline + optional phase instrumentation (off by default)
│   ├── interactions.py / physics.py / randomness.py
├── experiments/
│   ├── run_metadata.py   # Shared output-safety helpers (unique run dirs, atomic writes)
│   └── analyze_*.py / validate_evolution.py
├── experiment_results/   # Committed historical outputs (never overwritten by reruns)
├── benchmarks/
│   └── bench_simulation.py   # Stdlib-only benchmark harness (fixed seeds)
├── frontend/
│   ├── index.html / style.css / app.js        # Dashboard (vanilla JS, canvas renderer)
│   └── dashboard.spec.ts                      # Playwright browser tests
├── tests/            # Python test suite
├── config.py         # Configuration defaults + validate_config()
├── app.py            # Standalone console demo (10 ticks, no backend)
└── requirements.txt  # Runtime dependencies (fastapi, uvicorn)
```

Python is authoritative for all simulation state. The frontend only fetches and renders state; it never advances the simulation except through backend control endpoints.

---

## 🌍 How the Simulation Works

Digital Life models a population of organisms living in a shared environment.

Each organism has inherited traits and a life cycle. Organisms interact with their surroundings, manage their energy, and may reproduce if the simulation's conditions permit it.

### 1. Environment

The simulated world contains organisms and food resources, configured in `config.py`:

- World dimensions (`WORLD_WIDTH`, `WORLD_HEIGHT`)
- Initial population and food (`INITIAL_POPULATION`, `INITIAL_FOOD`)
- Energy parameters (`STARTING_ENERGY`, `MAX_ENERGY`, `FOOD_ENERGY`)
- Food replenishment (`FOOD_TARGET_COUNT`, `FOOD_MAX_COUNT`, `FOOD_RESPAWN_PER_TICK`)
- Maximum age (`MAX_AGE`), eat distance (`EAT_DISTANCE`)
- Reproduction cost (`REPRODUCTION_ENERGY_COST`), tick rate bounds, `RANDOM_SEED`

`config.validate_config()` checks defaults and relationships (for example, `STARTING_ENERGY <= MAX_ENERGY`) without changing any value.

### 2. Tick pipeline (`simulation/engine.py`)

Each `step()` advances exactly one tick, in this fixed order:

1. Snapshot pre-existing organisms (newborns wait until next tick).
2. Per organism: liveness check → sense → brain decision → MOVE-only movement → one opportunistic eat → metabolism → age+1 → death check (`energy <= 0`, `health <= 0`, `age >= MAX_AGE`) → reproduction candidacy.
3. At most one global reproduction via fitness-proportionate `select_parent`.
4. Deferred offspring registration, food respawn, `tick += 1`, death accounting, one metrics snapshot.

### 3. Brain actions (`brains/rule_brain.py`)

The rule-based policy returns `MOVE`, `EAT`, `REPRODUCE`, or `IDLE`:

- Only `MOVE` causes directed movement (existing physics path).
- Food consumption is opportunistic and applied once per tick for every acting organism, regardless of action.
- Reproduction candidacy requires **both** the `REPRODUCE` action **and** `can_reproduce()` eligibility (energy/threshold/health). A brain decision never bypasses eligibility.
- Dead organisms (including `health <= 0`) never act, eat, or reproduce. Corpses are retained as historical records; metrics count only living organisms.

### 4. Sensors (`domain/sensors.py`)

Food and organism sensing share the vision model (`vision * 200.0`); out-of-range targets are invisible, missing targets report `(inf, 0.0, 0.0)`, and equidistant ties resolve to the first in collection order. Sensing never mutates world state. Distance comparisons use squared distances internally with identical selection semantics (verified by equivalence tests).

### 5. Genome (`domain/genome.py`)

Six normalized `[0, 1]` traits: `speed` (px/tick), `vision` (detection range), `metabolism` (flat energy/tick), `size` (display/metrics only — no behavioral effect), `reproduction_threshold` (energy gate), `mutation_rate` (per-gene probability). Mutation adds Gaussian noise (`mutation_strength=0.1`) and clips to range; parents are never modified.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.13 (developed and tested with Python 3.13.4) and Git.
- For the Python test suite: `pytest`, plus `httpx` for backend API tests.
- For browser tests: Node.js and Playwright browsers (see below).

### 1. Clone the repository

```bash
git clone https://github.com/MSaihaan004/digital-life.git
cd digital-life
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install pytest httpx
```

`requirements.txt` covers runtime dependencies (`fastapi`, `uvicorn[standard]`). Test tools (`pytest`, `httpx`) are install-only and add no runtime coupling.

### 3. Start the backend

From the project root (PowerShell shown; use `PYTHONPATH=.` on other shells):

```powershell
$env:PYTHONPATH="."
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

The background simulation worker starts with the application lifespan — importing the module alone never starts it. Health: `GET http://127.0.0.1:8000/health`.

### 4. Start the frontend

Serve the static dashboard (new terminal, project root):

```bash
python -m http.server 8130 --directory frontend
```

Open `http://127.0.0.1:8130/index.html`. The dashboard polls the backend at `http://127.0.0.1:8000` for state, status, and metrics history.

### 5. Console demo (no backend)

```bash
python app.py
```

---

## 🧪 Testing

### Python test suite

```powershell
$env:PYTHONPATH="."
python -m pytest -q
```

156 tests covering: tick ordering and one-tick contract, brain→action dispatch, sensor vision/ties/boundaries/purity, organism invariants, energy accounting (no double-apply), aging/death (energy/health/age), reproduction eligibility and accounting, mutation bounds/reproducibility, selection distribution, world registration and IDs, metrics-vs-state consistency, empty populations, backend lifecycle/controls/errors/concurrency, export correctness, output-safety guards, phase-timing determinism, and full-trajectory replay.

### Playwright browser tests

Prerequisites: Node.js with Playwright browsers installed. No repo dependencies are added; the runner uses `npx` cache and the config starts both servers automatically:

```bash
npx -y @playwright/test@1.64.0 test dashboard.spec.ts --reporter=list
```

12 tests: loading/connection, console cleanliness, pause/resume with tick freeze, single-step (+1 tick), 409 explanation while running, reset to tick 0, statistics rendering, organism selection + inspector, style persistence, metrics charts, responsive layout, and disconnect→stale→reconnect recovery.

---

## ⚙️ Backend API

Worker lifecycle: import starts nothing; server startup starts one worker; `stop_worker()` joins cleanly; duplicate workers are refused.

| Endpoint | Description |
| --- | --- |
| `GET /health`, `GET /simulation/status` | Connection, running/paused, tick, tick rate, living population, worker health, last tick/error |
| `GET /simulation/state` | Consistent snapshot (`?include_dead=false`, `?limit=N` supported; history never deleted) |
| `GET /simulation/metrics/history?limit=N` | Most recent N per-tick metric snapshots (dashboard charts) |
| `GET /simulation/organisms/{id}` | Living or historical organism by ID (404 when absent) |
| `GET /simulation/config`, `PUT /simulation/config` | Tick-rate settings (validated, 422 on invalid) |
| `POST /simulation/pause` | Idempotent pause; state and RNG preserved; remains inspectable |
| `POST /simulation/resume` | Idempotent resume; never duplicates the worker |
| `POST /simulation/step` | Exactly one tick; only while paused (409 otherwise) |
| `POST /simulation/reset` | Fresh world/engine/metrics; same config unless `{"seed": N}`; paused flag preserved |

Errors use structured HTTP statuses (422 validation, 409 step-while-running, 404 missing organism, 500 with server-side logging and `last_error` — stack traces never leak to clients).

---

## 📊 Benchmarks

Stdlib-only harness with fixed seeds (nothing written to `experiment_results/`):

```powershell
$env:PYTHONPATH="."
python benchmarks/bench_simulation.py --quick
```

Measures full-tick duration across scenarios (small/medium/large populations, low/high food, aged worlds with historical dead), instrumented phase timings of the real `step()` path (`act`, `reproduce`, `housekeeping`, `metrics` — disabled by default via `enable_phase_timing()`), serialization cost/size, and history-retrieval cost. Phase regions exclude per-tick setup, so phases may not sum to tick time; full-tick timings are the comparable series. No wall-clock thresholds exist in unit tests. Representative reading: medium workload ≈7ms/tick with `act` ≈98% of instrumented time.

---

## 🔬 Experiments and Outputs

Scripts in `experiments/` (`validate_evolution`, `analyze_evolution`, `analyze_metabolism`, `analyze_energy_economy`, `analyze_multiple_seeds`) share `experiments/run_metadata.py` output-safety helpers.

Output-safety policy:

- Every invocation writes into a **unique run directory** (`experiment_results/<experiment>_YYYYMMDD_HHMMSS[_n]`), so committed results are never silently overwritten.
- Explicit paths refuse to overwrite unless `overwrite=True` (`OutputExistsError` otherwise); concurrent same-path creation is atomic — one winner, the rest refused.
- Writes are atomic (temp file + rename/link); CSV schemas and formats are unchanged.
- Each run writes a `<experiment>_run_metadata.json` sidecar: seeds, ticks, full config snapshot + validation, code revision, per-run success/failure, and the actual output file paths (`output_files`, `output_file`, `metadata_file`).
- Failed seeds are recorded with errors, banners print `COMPLETED WITH FAILURES`, and incomplete runs are never reported as fully successful.

Example (small smoke run into a temp dir — never the full 20×500 in development):

```powershell
$env:PYTHONPATH="."
python -c "from experiments import validate_evolution as v; v.main(output_dir='C:/Temp/dl_smoke', seeds=[42], ticks=10)"
```

Committed `experiment_results/*.csv` files are historical records; reruns create new run directories alongside them.

---

## 🔁 Reproducibility

Centralized RNG (`simulation/randomness.py`, seeded from `config.RANDOM_SEED`, applied at creation/reset only). Identical seed + configuration reproduces identical initial conditions and full trajectories (fingerprinted in `benchmarks/baseline_fingerprints.json` and asserted by replay tests). Sensor/eating optimizations were verified trajectory-identical.

---

## 🔐 Version Control

Repository: <https://github.com/MSaihaan004/digital-life>

Work proceeds on feature branches merged to preserve history. Generated artifacts (`__pycache__/`, `.pytest_cache/`, `test-results/`, `playwright-report/`, `.playwright-mcp/`) are git-ignored and must not be committed.

---

## ⚠️ Known Limitations and Troubleshooting

- `size` gene affects display/metrics only; `health` never depletes (enforced as a death condition only).
- At most one birth per tick globally; corpses accumulate as historical records (by design; live views filter them).
- `analytics/` package is reserved and currently empty — canonical metrics live in `evolution/metrics.py`.
- In-memory metrics history is unbounded per session (required for experiments); dashboard requests page it with `limit`.
- **Backend won't start:** ensure `PYTHONPATH` includes the project root (`PYTHONPATH=.`), port 8000 is free, and `fastapi`/`uvicorn` are installed.
- **Dashboard shows disconnected:** start the backend first; the UI keeps the last valid state and recovers automatically.
- **Step rejected (409):** pause the simulation before single-stepping — this is the API contract, not a bug.
- **Experiment refuses to write:** an output already exists — use a new run directory (the default) or pass `overwrite=True` deliberately.
- **Playwright failures:** ensure Node.js, Playwright browsers, and free ports 8000/8130; rerun with `--reporter=list` for per-test logs.

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
