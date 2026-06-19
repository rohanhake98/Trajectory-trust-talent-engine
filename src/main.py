import argparse
import os
import sys

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Ensure current directory is in Python path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ranker import process_and_rank

app = FastAPI(
    title="Trajectory & Trust Talent Intelligence Engine",
    description="Hackathon portfolio candidate discovery and ranking dashboard.",
)

# Ensure data and output directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("output", exist_ok=True)


@app.post("/api/upload-and-rank")
async def upload_and_rank(file: UploadFile = File(...)):
    """Receives a JSONL file, runs the ranker engine, and returns the top 100 results."""
    if not file.filename.endswith((".jsonl", ".jsonl.gz")):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Please upload a .jsonl candidate file."
        )

    # Save uploaded file locally
    uploaded_path = os.path.join("data", "uploaded_candidates.jsonl")
    try:
        with open(uploaded_path, "wb") as buffer:
            buffer.write(await file.read())

        csv_output_path = os.path.join("output", "web_submission.csv")
        results = process_and_rank(uploaded_path, export_csv_path=csv_output_path)
        return {"status": "success", "results": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# Mount the static files (HTML, CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def get_index():
    """Serves the main single-page recruiter dashboard."""
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)


def main():
    parser = argparse.ArgumentParser(description="Talent Intelligence Engine entry point")
    parser.add_argument(
        "--server", action="store_true", help="Start the FastAPI web server dashboard"
    )
    parser.add_argument("--input", help="CLI input candidate JSONL path")
    parser.add_argument("--output", help="CLI output CSV path")
    args = parser.parse_args()

    if args.server:
        print("Starting local dashboard at http://127.0.0.1:8000")
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    elif args.input and args.output:
        print(f"CLI mode initiated. Analyzing {args.input}...")
        process_and_rank(args.input, export_csv_path=args.output)
        print(f"Ranking completed. CSV output saved to {args.output}")
    else:
        # Default behavior: print help
        parser.print_help()


if __name__ == "__main__":
    main()
