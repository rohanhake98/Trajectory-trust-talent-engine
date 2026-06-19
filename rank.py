import argparse
import os
import sys

# Ensure src subdirectory is in python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from ranker import process_and_rank


def main():
    parser = argparse.ArgumentParser(description="Talent Intelligence Engine Ranker CLI")
    parser.add_argument("--candidates", required=True, help="Path to input JSONL candidate pool")
    parser.add_argument("--out", required=True, help="Path to write output CSV")
    args = parser.parse_args()

    print(f"Ranking candidates from {args.candidates}...")
    try:
        process_and_rank(args.candidates, export_csv_path=args.out)
        print(f"Ranking completed successfully. Output saved to {args.out}")
    except Exception as e:
        print(f"Error during ranking: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
