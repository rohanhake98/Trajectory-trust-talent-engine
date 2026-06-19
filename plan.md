# Student Project Plan: Trajectory & Trust Talent Intelligence Engine

**Codename:** Counterfactual Talent Trajectory Graph + Honeypot Shield  
**Track:** AI Hiring Intelligence — Candidate Ranking System  
**Format:** Full-Stack Web Application (FastAPI Backend + HTML/CSS/JS Frontend) & CLI  
**Target Environment:** Local Machine (CPU-Only) & GitHub (CI/CD Testing)

---

## 1. Executive Summary & Project Goals

This project is a lightweight, CPU-efficient candidate ranking engine and dashboard designed to run locally. The system processes a dataset of **100,000 candidates** in a JSONL file and yields a ranked list of the top **100 candidates** for a Senior AI Engineering role.

### Full-Stack Scope
1. **Core Scoring Engine (CLI & Backend):** Vectorized Python algorithms compute candidate suitability based on four pillars: Static Fit, Career Trajectory, Recruitability/Convertibility, and a Multiplicative Trust Gate (Honeypot Shield).
2. **Interactive UI (Frontend):** A modern, responsive single-page web dashboard. Users can upload raw files, run the ranking engine, visualize the top 100 candidate cards, search profiles, view career trajectory graphs, and witness keyword-stuffed fake profiles being caught in real time.

---

## 2. Technology Stack & Version Matrix

The application runs entirely in memory on a single CPU core, completing the processing of 100,000 candidates in **under 10 minutes**.

### 2.1 Backend & Analytics
- **Python (v3.13.x):** Core language runtime (supports modern async and improved performance).
- **FastAPI (v0.111.0):** Asynchronous API framework for file uploading and database-less querying.
- **Uvicorn (v0.29.0):** ASGI server for running the FastAPI web backend.
- **Pandas (>=2.2.3) & NumPy (>=2.1.0):** Data structures and vectorized metric computations (compatible with Python 3.13).
- **NetworkX (v3.3):** Graph structures for career transition hop calculations.
- **Scikit-Learn (>=1.5.2):** Cosine similarity and TF-IDF for text/skill relevance (compatible with Python 3.13).
- **PyTest (v8.2.2) & Ruff (v0.4.9):** Testing and formatting frameworks.

### 2.2 Frontend (Vanilla Web Stack)
- **HTML5:** Semantic layouts (headers, cards, tables, modal screens).
- **CSS3 (Vanilla):** Modern styling featuring glassmorphism, responsive grid system, dark-mode styling, and micro-animations.
- **JavaScript (ES6+):** Async `fetch()` requests, DOM manipulation, and interactive tables.

---

## 3. Directory Structure

The repository workspace is organized as follows:
```text
talent-intelligence-engine/
├── .github/
│   └── workflows/
│       └── python-tests.yml        # GitHub Actions test runner
├── data/                           # (Excluded from git) Raw candidate source files
│   └── candidates.jsonl            # Place raw 100k dataset here
├── src/                            # Backend & Web Server
│   ├── static/                     # Frontend Web Assets (Served by FastAPI)
│   │   ├── index.html              # Core Recruiters Dashboard UI
│   │   ├── styles.css              # Dark-theme modern styling definitions
│   │   └── app.js                  # Frontend Fetch, table rendering, search logic
│   ├── __init__.py
│   ├── main.py                     # Web API Controller & CLI entry routing
│   ├── ingest.py                   # Data ingestion and schema validation
│   ├── normalize.py                # Job titles and skills canonicalization maps
│   ├── features.py                 # Extractor functions (Fit, Trajectory, Convertibility)
│   ├── graph.py                    # NetworkX career graph computations
│   ├── shield.py                   # TrustScore and anomaly rule triggers
│   ├── ranker.py                   # Aggregation mathematical weights
│   ├── reason.py                   # Explanatory template generators
│   └── config.py                   # System scoring weights and JD configs
├── tests/                          # Automated Verification Suite
│   ├── __init__.py
│   ├── test_features.py
│   ├── test_shield.py
│   └── test_ranker.py
├── .gitignore                      # Ignore virtual env, data/ and output/ folders
├── Dockerfile                      # Optional docker build for local running
├── requirements.txt                # Project dependency pins
├── pyproject.toml                  # Linter (Ruff) and Pytest configs
└── README.md                       # Instructions on running the engine
```

---

## 4. Web API Architecture

FastAPI serves two purposes: routing command line flags and hosting API endpoints to power the static UI.

```
                  ┌──────────────────────┐
                  │   Browser Frontend   │
                  │   (HTML / CSS / JS)  │
                  └──────────────────────┘
                             │ (AJAX Fetch)
                             ▼
    ┌──────────────────────────────────────────────────┐
    │                 FastAPI Backend                  │
    │                                                  │
    │  POST /api/upload-and-rank                       │
    │  - Stream raw JSONL                              │
    │  - Run Shield + Ranker                           │
    │  - Cache Top 100 in memory                       │
    │                                                  │
    │  GET /api/candidates                             │
    │  - Return ranked JSON array                      │
    │                                                  │
    │  GET /api/stats                                  │
    │  - Return dashboard summary numbers              │
    └──────────────────────────────────────────────────┘
```

### 4.1 Server Integration Setup
File location: [main.py](file:///d:/INDIA%20RUN/src/main.py)

```python
import argparse
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from ranker import process_and_rank

app = FastAPI(title="Trajectory & Trust Engine API")

# Serve the static UI files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("src/static/index.html")

@app.post("/api/upload-and-rank")
async def upload_and_rank(file: UploadFile = File(...)):
    # Stream file bytes directly to parser
    temp_path = "data/uploaded_candidates.jsonl"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    
    top_candidates = process_and_rank(temp_path)
    return {"status": "success", "results": top_candidates}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true", help="Start the web server dashboard")
    parser.add_argument("--input", help="CLI input JSONL path")
    parser.add_argument("--output", help="CLI output CSV path")
    args = parser.parse_args()

    if args.server:
        print("Starting local dashboard at http://localhost:8000")
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    elif args.input and args.output:
        # Standard CLI run
        process_and_rank(args.input, export_csv_path=args.output)
    else:
        parser.print_help()
```

---

## 5. Scoring Engine Mathematics

The core ranking logic aggregates the sub-scores and applies the **TrustScore** as a multiplicative filter:

$$\text{FinalScore} = \text{TrustScore} \times \left( 0.25 \cdot \text{StaticFit} + 0.40 \cdot \text{TrajectoryScore} + 0.35 \cdot \text{ConvertibilityScore} \right)$$

This means any profile with a TrustScore of $0.0$ (due to timeline anomalies or keyword-stuffing indicators) is instantly zeroed out, preventing it from ranking.

---

## 6. Project Phases (0% to 100% Roadmap)

### Phase 1: Local Setup & Scaffolding (0% - 15%)
- **Objective:** Configure local development environment and workspace files.
- **Tasks:**
  1. Create local python environment and configure [requirements.txt](file:///d:/INDIA%20RUN/requirements.txt):
     ```bash
     python -m venv .venv
     source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
     pip install -r requirements.txt
     ```
  2. Setup Ruff and Pytest configs in [pyproject.toml](file:///d:/INDIA%20RUN/pyproject.toml).
  3. Set up the basic directory folders, including the `src/static` directory.

---

### Phase 2: Ingest & Normalization (15% - 30%)
- **Objective:** Build the JSONL file parsing engine and standardized skill/title canonicalization regex lookup.
- **Tasks:**
  1. Write [ingest.py](file:///d:/INDIA%20RUN/src/ingest.py) using generator patterns.
  2. Build regex normalization dictionary mappings in [normalize.py](file:///d:/INDIA%20RUN/src/normalize.py).

---

### Phase 3: Core Analytics (Static, Trajectory, Convertibility) (30% - 50%)
- **Objective:** Compute basic relevance, progression metrics, and behavioral scores.
- **Tasks:**
  1. Use Scikit-Learn TF-IDF to score semantic title matches in [features.py](file:///d:/INDIA%20RUN/src/features.py).
  2. Calculate `career_velocity` (promotions normalized by workforce tenure) and aggregate convertibility signals.

---

### Phase 4: Graph & Shield Implementation (50% - 70%)
- **Objective:** Map career jumps and check profile chronological integrity.
- **Tasks:**
  1. Write [graph.py](file:///d:/INDIA%20RUN/src/graph.py). Use NetworkX to build a directed career path graph to compute hop distances.
  2. Implement chronological date validation and skill density checks in [shield.py](file:///d:/INDIA%20RUN/src/shield.py) to flag anomalies.

---

### Phase 5: Calibration & API Layer (70% - 85%)
- **Objective:** Package the scoring engine, implement deterministic ranking, and construct FastAPI API endpoints.
- **Tasks:**
  1. Write final scoring weights and sorting logic in [ranker.py](file:///d:/INDIA%20RUN/src/ranker.py).
  2. Implement API routing in [main.py](file:///d:/INDIA%20RUN/src/main.py) to parse uploaded files and return structured JSON records.

---

### Phase 6: Frontend Development (85% - 95%)
- **Objective:** Build a modern, dark-mode single-page recruiter dashboard using Vanilla HTML/CSS/JS.
- **Tasks:**
  1. Write [index.html](file:///d:/INDIA%20RUN/src/static/index.html) with input file fields, scoreboard lists, and three-candidate contrast cards.
  2. Write [styles.css](file:///d:/INDIA%20RUN/src/static/styles.css) featuring a responsive layout, dark-mode palette, and transition animations.
  3. Write [app.js](file:///d:/INDIA%20RUN/src/static/app.js) to upload files asynchronously, populate candidate tables dynamically, filter results by keyword, and trigger popups detailing trust scores.

---

### Phase 7: GitHub CI & Verification (95% - 100%)
- **Objective:** Establish automatic tests on GitHub and perform local validation.
- **Tasks:**
  1. Write GitHub Actions workflow at [.github/workflows/python-tests.yml](file:///d:/INDIA%20RUN/.github/workflows/python-tests.yml).
  2. Perform testing of local server startup and execution on the 100K dataset.

---

## 7. GitHub Integration & CI Workflow

### GitHub Actions Configuration
File location: [.github/workflows/python-tests.yml](file:///d:/INDIA%20RUN/.github/workflows/python-tests.yml)

```yaml
name: Python Code Verification

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13.x'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff pytest

      - name: Run Code Style Lint (Ruff)
        run: ruff check src/ tests/

      - name: Run Test Suite (PyTest)
        run: pytest
```

---

## 8. Local Run Guide & CLI Usage

### Requirements file setup
File: [requirements.txt](file:///d:/INDIA%20RUN/requirements.txt)
```text
pandas>=2.2.3
numpy>=2.1.0
networkx==3.3
scikit-learn>=1.5.2
fastapi==0.111.0
uvicorn==0.29.0
pytest==8.2.2
ruff==0.4.9
```

### Running the Web Server Dashboard
Start the server from the repository root:
```bash
python src/main.py --server
```
Once running, open your web browser to: **`http://127.0.0.1:8000`**

### Running the CLI Engine
Alternatively, process data silently in the terminal:
```bash
python src/main.py --input data/candidates.jsonl --output output/output.csv
```

---

## 9. QA and Anomaly Verification

### Unit Test Setup
File location: [test_shield.py](file:///d:/INDIA%20RUN/tests/test_shield.py)

```python
import pytest
from src.shield import check_timeline_overlap

def test_anomaly_overlap_caught():
    career_jobs = [
        {"company": "Google", "start_date": "2023-01-01", "end_date": "2023-12-31"},
        {"company": "Meta", "start_date": "2023-06-01", "end_date": "2024-06-01"}
    ]
    overlap_flag = check_timeline_overlap(career_jobs)
    assert overlap_flag > 0.0, "Timeline overlaps should trigger a penalty."
```

---

## 10. Risk & Mitigation Matrix

| Risk | Cause | Mitigation |
| :--- | :--- | :--- |
| **Out of Memory Error** | Loading 100K JSON dict structures simultaneously. | Stream files using generators and dump directly into structured Pandas/NumPy arrays. |
| **Slow Graph Computations** | Running Dijkstra on all node variants. | Canonicalize titles prior to adding nodes; use BFS adjacency hops limited to target nodes. |
| **Web Upload Limits** | Uploading heavy JSONL files over API. | Implement chunk-by-chunk streaming in the frontend and background parsing in FastAPI. |
| **UI Freeze during Ingestion**| Blocking UI thread while server processes 100K records. | Add an animated spinner/progress bar in the UI; return response codes instantly and execute processing asynchronously. |
