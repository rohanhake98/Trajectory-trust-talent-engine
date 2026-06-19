# Project Plan: Trajectory & Trust Talent Intelligence Engine

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
│   ├── features.py                 # Feature extraction functions
│   ├── graph.py                    # NetworkX career graph computations
│   ├── shield.py                   # TrustScore and anomaly rule triggers
│   ├── ranker.py                   # Aggregate formula and calibration
│   ├── reason.py                   # Explanatory template generators
│   └── config.py                   # System scoring weights and JD configs
├── tests/                          # Automated Verification Suite
│   ├── __init__.py
│   ├── test_features.py
│   ├── test_shield.py
│   └── test_ranker.py
├── .gitignore                      # Ignore virtual env, data/ and output/ folders
├── rank.py                         # Root wrapper entry point (Stage 3 check)
├── submission_metadata.yaml        # Portal metadata checklist (Stage 3 check)
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
import os
import sys
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

# Ensure current directory is in Python path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
```

---

## 5. Scoring Engine Mathematics

The core ranking logic aggregates the sub-scores and applies the **TrustScore** as a multiplicative filter:

$$\text{FinalScore} = \text{TrustScore} \times \left( 0.25 \cdot \text{StaticFit} + 0.40 \cdot \text{TrajectoryScore} + 0.35 \cdot \text{ConvertibilityScore} \right)$$

This means any profile with a TrustScore of $0.0$ (due to timeline anomalies or keyword-stuffing indicators) is instantly zeroed out, preventing it from ranking.

---

## 6. Project Execution Steps (0% to 100% Roadmap)

The project follows a strict 13-step pipeline to transform raw dataset lines into validated submissions.

### Step 1: Setup Project (0% - 10%) - [COMPLETED]
Configure the directory layout (`src/`, `output/`, `data/`), setup Python virtual environments, and construct the `.gitignore` rules preventing gzipped database leaks. Configure linter settings under `[tool.ruff.lint]` in `pyproject.toml`.

### Step 2: Extract & Load Data (10% - 20%) - [COMPLETED]
Ingest candidate JSONL profiles memory-efficiently using Python generator loops, performing schema-level constraints checks with Pydantic v2.

### Step 3: Data Cleaning (20% - 30%) - [COMPLETED]
Develop regex-based normalizations for job titles and skill variations (standardizing case capitalizations and common abbreviations) to support high-fidelity matching. Translate career start and end dates into employment durations in months.

### Step 4: Feature Engineering (CORE) (30% - 45%) - [COMPLETED]
Compute TF-IDF current title similarity, target skill overlap scores, candidate career promotions velocity, target skill growth rates, and extract 23 recruiter convertibility signals.

### Step 5: Build Trust / Shield Layer (45% - 55%) - [COMPLETED]
Construct chronological date validation algorithms to flag timeline overlaps. Formulate skill stuffing checks (high skill counts with near-zero endorsements) and title inflation triggers to output a candidate `TrustScore`.

### Step 6: Build Scoring System (55% - 65%) - [COMPLETED]
Combine the sub-scores using the multiplicative trust formula. Normalizes all scoring values to a standard $[0.0 - 1.0]$ range.

### Step 7: Rank Candidates (65% - 75%) - [COMPLETED]
Compute final scores for the candidate database. Sort candidates descending by score and break ties alphabetically by candidate ID ascending. Select the top 100 profiles.

### Step 8: Generate Reasoning (75% - 85%) - [COMPLETED]
Generate 1-2 sentence template explanations incorporating specific profile facts (such as years of experience, current title, matched vector DBs, and notice period concerns) to satisfy manual review checks with zero hallucination.

### Step 9: Create Output CSV (85% - 90%) - [COMPLETED]
Format results to output the CSV using the exact column ordering (`candidate_id,rank,score,reasoning`) and row limits (exactly 100 rows). Round scores to 4 decimal places before sorting to align tie-breaks.

### Step 10: Validate Output (90% - 93%) - [COMPLETED]
Verify that the output has no candidate ID duplicates and strictly non-increasing score order. Confirm compliance by executing the official validator script.

### Step 11: Prepare Demo (93% - 96%) - [IN PROGRESS]
Configure the single-page recruiter dashboard server. Retrieve three contrasted candidate profiles (a standard title match, an underrated high-trajectory gem, and a flagged honeypot profile) to demonstrate live score differentiation.

### Step 12: Prepare Story (96% - 98%) - [COMPLETED]
Formulate the hackathon narrative: problem framing is career trajectory and authenticity trust, not a simple ATS text matching task. Highlight honeypot avoidance.

### Step 13: Final Touch (98% - 100%) - [COMPLETED]
Push the clean codebase to the remote GitHub repository. Complete the `README.md` and include target submission metadata.

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

## 8. Run Guide & CLI Usage

### Running the CLI Engine (Stage 3 Sandboxed Execution)
Execute the official hackathon runner command from the repository root:
```bash
python rank.py --candidates ./data/candidates.jsonl --out ./output/submission.csv
```

### Running the Web Server Dashboard
Start the FastAPI server:
```bash
python src/main.py --server
```
Visit **`http://127.0.0.1:8000`** in your browser.

---

## 9. Risk & Mitigation Matrix

| Risk | Cause | Mitigation |
| :--- | :--- | :--- |
| **Out of Memory Error** | Loading 100K JSON dict structures simultaneously. | Stream files using generators and dump directly into structured Pandas/NumPy arrays. |
| **Slow Graph Computations** | Running Dijkstra on all node variants. | Canonicalize titles prior to adding nodes; use BFS adjacency hops limited to target nodes. |
| **Honeypot Disqualification** | System failing to catch synthetic profiles. | Implement a multiplicative trust score gate that zeros out candidates containing timeline anomalies. |
