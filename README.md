# Trajectory & Trust Talent Intelligence Engine

**Codename:** Counterfactual Talent Trajectory Graph + Honeypot Shield  
An intelligent candidate ranking engine and analytics dashboard designed to process candidate pools under uncertainty.

---

## 🚀 Project Overview

Most recruitment search systems use shallow keyword matching or simple text embeddings to find candidates. This system takes a different approach, designed to solve the candidate ranking challenge on a pool of **100,000 candidates** for a Senior AI Engineering role.

Instead of just checking who matches the job description today, the engine evaluates candidates across four distinct dimensions:
1. **Static Fit (25%):** Keyword and skill relevance, current title matching, and experience thresholds.
2. **Career Trajectory (40%):** Vectorized career velocity, skill acquisition rates, and transition pathways calculated using population-scale job hops.
3. **Convertibility (35%):** Historic behavioral signals tracking responsiveness, notice periods, and offer acceptance probabilities.
4. **Honeypot Shield (Multiplicative Gate):** A defensive layer that detects synthetic profiles, impossible overlapping timelines, and keyword stuffing anomalies, demoting fakes to a score of `0.0`.

---

## 🛠️ Tech Stack

This project is optimized to run locally on a single CPU core, completing analysis on 100K profiles in **under 10 minutes** without external database dependencies.

- **Backend:** Python 3.13.1, FastAPI, Uvicorn
- **Data Science & Vectors:** Pandas, NumPy, Scikit-Learn (TF-IDF, Cosine Similarity)
- **Graph Computations:** NetworkX (Directed Job Transition Networks)
- **Code Quality & Testing:** PyTest, Ruff
- **Frontend:** Vanilla HTML5, Vanilla CSS3 (Modern Dark Theme), ES6 JavaScript

---

## 📂 Project Layout

```text
├── .github/workflows/
│   └── python-tests.yml        # GitHub Actions CI lint & test pipeline
├── src/
│   ├── static/                 # Frontend Web Assets (HTML, CSS, JS)
│   ├── main.py                 # Core CLI entry and Web server controller
│   ├── ingest.py               # Optimized JSONL streaming generator
│   ├── normalize.py            # Title and skill canonicalization maps
│   ├── features.py             # Feature extraction functions
│   ├── graph.py                # Graph building and BFS distance traversal
│   ├── shield.py               # Anomaly shield logic and Trust scoring
│   ├── ranker.py               # Formula aggregation and tie-breaker sorting
│   ├── reason.py               # Grounded reason text template generation
│   └── config.py               # Configuration constants and JD criteria
├── tests/                      # PyTest automated suite
├── pyproject.toml              # Ruff and PyTest configurations
├── requirements.txt            # Package dependencies
└── README.md
```

---

## ⚡ Setup & Run Instructions

### 1. Scaffolding Setup
Ensure you have Python 3.13.x installed. Create a virtual environment and install packages:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Prepare Data
Create a directory named `data/` in the root of the workspace and place the candidate pool inside:
```bash
mkdir data
# Place your candidates.jsonl in data/candidates.jsonl
```

### 3. Run the Web Dashboard
To launch the interactive recruiter dashboard:
```bash
python src/main.py --server
```
Visit **`http://127.0.0.1:8000`** in your browser.

### 4. Run via CLI
To run the analysis directly from your terminal and output a CSV:
```bash
python src/main.py --input data/candidates.jsonl --output output/output.csv
```

---

## 🧪 Verification & Testing

Verify that your changes pass style checks and all unit test specifications:
```bash
# Run styling linter
ruff check src/ tests/

# Execute tests
pytest
```
