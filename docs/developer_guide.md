# ECGiga — Developer Guide

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Descriptions](#module-descriptions)
3. [Development Setup](#development-setup)
4. [How to Add New Pathology Detectors](#how-to-add-new-pathology-detectors)
5. [How to Add Quiz Questions](#how-to-add-quiz-questions)
6. [Testing Guide](#testing-guide)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Code Style](#code-style)
9. [Docker Development](#docker-development)
10. [Database Schema](#database-schema)
11. [Contributing](#contributing)

---

## Architecture Overview

ECGiga is a modular Python application for ECG education and analysis.  It
consists of several independent layers that communicate via well-defined
interfaces.

```
┌─────────────────────────────────────────────────┐
│                   User Interfaces                │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ CLI App  │  │ Dash Web  │  │ MCP Server   │  │
│  │ (typer)  │  │ (plotly)  │  │ (FastAPI)    │  │
│  └────┬─────┘  └─────┬─────┘  └──────┬───────┘  │
│       │              │               │           │
├───────┴──────────────┴───────────────┴───────────┤
│                  Core Modules                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ cv/        │  │ education/ │  │ simulation/ │  │
│  │ (image     │  │ (quiz,     │  │ (ECG gen,   │  │
│  │  process)  │  │  teaching) │  │  drugs,     │  │
│  │            │  │            │  │  ions)      │  │
│  └────────────┘  └────────────┘  └────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ ai/        │  │ reporting/ │  │ datasets/  │  │
│  │ (AI/ML     │  │ (PDF/HTML  │  │ (data      │  │
│  │  helpers)  │  │  reports)  │  │  loaders)  │  │
│  └────────────┘  └────────────┘  └────────────┘  │
│                                                   │
├───────────────────────────────────────────────────┤
│                 Persistence Layer                  │
│  ┌──────────────────┐  ┌───────────────────────┐  │
│  │ persistence/     │  │ data/                 │  │
│  │  database.py     │  │  ecgiga.db (SQLite)   │  │
│  │  auth.py         │  │  uploads/             │  │
│  └──────────────────┘  └───────────────────────┘  │
└───────────────────────────────────────────────────┘
```

### Key Design Principles

1. **No heavy external database** — SQLite for persistence, JSON files for config
2. **Offline-first** — All core features work without internet
3. **Portuguese-first** — UI and clinical content in Brazilian Portuguese
4. **Camera analogy** — All educational content uses the camera metaphor
5. **12-lead aware** — All analysis considers the full 12-lead context

---

## Module Descriptions

### `cli_app/`
Command-line interface built with Typer.  Entry point: `ecgcourse` command.

### `web_app/dash_app/`
Interactive Dash web application.  Provides the visual dashboard with
real-time ECG display, quiz interface, and simulation controls.

### `mcp_server.py`
FastAPI-based MCP (Model Context Protocol) server.  Exposes ECG analysis
tools as API endpoints for integration with AI assistants and external systems.

### `cv/`
Computer vision pipeline for ECG image processing:
- Grid detection and scale calibration
- Lead segmentation
- Trace extraction (pixel → voltage)
- Deskew and normalization

### `education/`
Educational content and quiz system:
- Camera analogy teaching materials
- Interactive case presentations

### `quiz/`
Quiz engine and question bank:
- `bank/` — JSON question files organized by topic
- `schema/` — JSON Schema definitions for question format
- Quiz runner and scoring logic

### `simulation/`
Synthetic ECG generation and simulation:
- `ion_channels.py` — Action potential model with ion concentration effects
- `drug_effects.py` — Drug database and ECG modification simulation
- `ecg_generator.py` — Configurable 12-lead ECG generator

### `reporting/`
Report generation:
- Structured ECG interpretation reports
- PDF and HTML export
- Template system

### `persistence/`
Data persistence:
- `database.py` — SQLite-based storage (users, quiz results, reports)
- `auth.py` — Password hashing and token-based authentication

### `ai/`
AI/ML integration helpers for enhanced analysis.

### `datasets/`
Data loaders and dataset management for ECG data sources.

### `samples/`
Sample ECG data for testing and demonstration.

---

## Development Setup

```bash
# Clone and setup
git clone https://github.com/ecgiga/ecgiga.git
cd ecgiga
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Verify
pytest
ecgcourse --help
```

### Required Python version

Python 3.10+ is required.  Python 3.12 is recommended.

### Key dependencies

| Package | Purpose |
|---------|---------|
| numpy, scipy | Signal processing |
| plotly, dash | Web visualization |
| opencv-python-headless | Image processing |
| neurokit2 | ECG signal analysis |
| fastapi, uvicorn | API server |
| typer, rich | CLI |
| pillow | Image I/O |
| pydantic | Data validation |

---

## How to Add New Pathology Detectors

### Step 1: Define the pathology in `simulation/ecg_generator.py`

Add an entry to `_PATHOLOGY_CONFIGS`:

```python
_PATHOLOGY_CONFIGS["my_new_pathology"] = {
    "hr_bpm": 72,          # Override any base param
    "qrs_ms": 130,
    "description_pt": "Descrição em português da patologia",
}
```

### Step 2: Add pathology-specific waveform modifications

In `generate_pathological_ecg()`, add an `elif` block:

```python
elif pathology == "my_new_pathology":
    # Modify specific leads
    for lead in ("V1", "V2"):
        signal = ecg_data["leads"][lead]
        # Apply your modifications
        # ...
```

### Step 3: Add quiz questions

Create questions in `quiz/bank/` that test recognition of the new pattern.

### Step 4: Add a camera analogy explanation

Add the camera metaphor to the pathology's `description_pt` and to
the clinical guide documentation.

### Step 5: Add tests

```python
def test_my_new_pathology():
    ecg = generate_pathological_ecg("my_new_pathology")
    assert ecg["pathology"] == "my_new_pathology"
    assert len(ecg["leads"]) == 12
    # Verify specific characteristics
    assert ecg["params"]["qrs_ms"] == 130
```

---

## How to Add Quiz Questions

### Question format (JSON)

Questions are stored in `quiz/bank/` as JSON files.  Each file must conform
to the MCQ schema in `quiz/schema/mcq.schema.json`.

```json
{
  "id": "unique_question_id",
  "topic": "arritmias",
  "difficulty": "intermediate",
  "question_pt": "Qual é o achado mais característico da fibrilação atrial?",
  "options": [
    {"key": "A", "text_pt": "Ritmo regular com ondas P normais"},
    {"key": "B", "text_pt": "Ritmo irregularmente irregular sem ondas P"},
    {"key": "C", "text_pt": "QRS alargado com onda delta"},
    {"key": "D", "text_pt": "Supradesnivelamento de ST difuso"}
  ],
  "correct": "B",
  "explanation_pt": "A FA é caracterizada por ritmo irregularmente irregular...",
  "camera_analogy_pt": "Na analogia da câmera, o temporizador parou...",
  "image": "optional_path_to_ecg_image.png",
  "references": ["Braunwald's Heart Disease, 12th Ed, Ch. 38"]
}
```

### Steps to add questions

1. Create or edit a JSON file in `quiz/bank/`
2. Validate against the schema: `ecgcourse quiz --validate bank/my_questions.json`
3. Test: `pytest tests/test_quiz.py`

### Topic naming conventions

Use lowercase Portuguese names with underscores:
- `arritmias`
- `intervalos`
- `eixo_eletrico`
- `isquemia_infarto`
- `bloqueios_de_ramo`
- `hipertrofia`
- `disturbios_eletroliticos`
- `efeitos_de_drogas`

---

## Testing Guide

### Running tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_simulation.py

# Specific test function
pytest tests/test_simulation.py::test_generate_ecg_12_leads

# With coverage
pytest --cov=. --cov-report=html

# Verbose output
pytest -v --tb=long
```

### Test organization

```
tests/
├── conftest.py              # Shared fixtures (in repo root)
├── test_simulation.py       # Phase 28: simulation module tests
├── test_persistence.py      # Phase 29: database and auth tests
├── test_quiz.py             # Quiz engine tests
├── test_intervals.py        # Interval calculation tests
├── test_axis.py             # Axis calculation tests
├── test_rpeaks.py           # R-peak detection tests
├── test_grid_detect.py      # Grid detection tests
├── test_trace.py            # Trace extraction tests
├── test_mcp_server.py       # API endpoint tests
└── test_reporting.py        # Report generation tests
```

### Writing tests

Follow these conventions:

1. Use `pytest` style (functions, not classes)
2. Name tests `test_<what_is_being_tested>`
3. Use fixtures from `conftest.py` for shared data
4. Keep tests independent (no shared mutable state)
5. Test edge cases and error conditions

```python
def test_example():
    """One-line description of what this tests."""
    # Arrange
    model = ActionPotentialModel(k_extra=7.5)

    # Act
    effects = model.get_ecg_effects()

    # Assert
    assert "apiculadas" in effects["t_wave_change"].lower()
```

---

## CI/CD Pipeline

### GitHub Actions workflow

The project uses GitHub Actions for CI.  The pipeline runs on every push
and pull request.

```yaml
# .github/workflows/ci.yml (conceptual)
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt && pip install -e .
      - run: pytest --tb=short
      - run: ruff check .
      - run: black --check .

  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker-compose build
      - run: docker-compose up -d
      - run: curl -f http://localhost:8000/health
      - run: docker-compose down
```

### Pre-commit hooks

Install pre-commit hooks for local development:

```bash
# Format code
black .

# Lint
ruff check . --fix

# Run tests
pytest
```

---

## Code Style

- **Formatter:** Black (line length 100)
- **Linter:** Ruff (rules: E, F, I)
- **Type hints:** Required for all public functions
- **Docstrings:** Google/NumPy style for public functions
- **Language:** Code and comments in English; user-facing text in Portuguese

### Example

```python
def calculate_qtc(qt_ms: float, rr_s: float, method: str = "bazett") -> float:
    """Calculate corrected QT interval.

    Parameters
    ----------
    qt_ms : float
        QT interval in milliseconds.
    rr_s : float
        RR interval in seconds.
    method : str
        Correction method: "bazett" or "fridericia".

    Returns
    -------
    float
        Corrected QT in milliseconds.
    """
    if method == "bazett":
        return qt_ms / (rr_s ** 0.5)
    elif method == "fridericia":
        return qt_ms / (rr_s ** (1 / 3))
    raise ValueError(f"Unknown method: {method}")
```

---

## Docker Development

### Building

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build api

# Build with no cache
docker-compose build --no-cache
```

### Running

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f web
docker-compose logs -f api

# Stop
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ECGIGA_DB_PATH` | `data/ecgiga.db` | SQLite database path |
| `ECGIGA_SECRET_KEY` | `change-me-in-production` | Token signing secret |
| `ANTHROPIC_API_KEY` | (empty) | Optional, for AI features |

---

## Database Schema

The SQLite database has four tables:

### `users`
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | UUID |
| username | TEXT UNIQUE | Login name |
| email | TEXT UNIQUE | Email address |
| password_hash | TEXT | Salted SHA-256 hash |
| created_at | TEXT | ISO 8601 timestamp |
| updated_at | TEXT | ISO 8601 timestamp |

### `sessions`
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | UUID |
| user_id | TEXT FK→users | Owner |
| token | TEXT | Auth token |
| created_at | TEXT | ISO 8601 |
| expires_at | TEXT | ISO 8601 |

### `quiz_results`
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | UUID |
| user_id | TEXT FK→users | Owner |
| quiz_type | TEXT | Topic/category |
| score | REAL | Points earned |
| total | INTEGER | Total possible |
| details | TEXT | JSON blob |
| created_at | TEXT | ISO 8601 |

### `reports`
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | UUID |
| user_id | TEXT FK→users | Owner |
| title | TEXT | Report title |
| report_json | TEXT | Full report as JSON |
| created_at | TEXT | ISO 8601 |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for your changes
4. Ensure all tests pass: `pytest`
5. Format code: `black .` and `ruff check . --fix`
6. Commit with a clear message
7. Open a pull request with a description of changes

### Commit message format

```
<type>: <short description>

<optional body>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `style`
