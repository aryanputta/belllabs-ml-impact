"""Quick project environment sanity checker."""

from __future__ import annotations

import importlib
from pathlib import Path

REQUIRED_MODULES = ["numpy", "pandas", "sklearn", "networkx"]
REQUIRED_FILES = [
    Path("data/processed/papers.csv"),
    Path("src/similarity/paper_similarity.py"),
    Path("src/researcher/researcher_analysis.py"),
]


def main() -> int:
    print("[1/2] Checking python dependencies...")
    missing = []
    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
            print(f"  ✓ {mod}")
        except ModuleNotFoundError:
            missing.append(mod)
            print(f"  ✗ {mod}")

    print("[2/2] Checking required project files...")
    missing_files = [str(p) for p in REQUIRED_FILES if not p.exists()]
    for p in REQUIRED_FILES:
        print(f"  {'✓' if p.exists() else '✗'} {p}")

    if missing or missing_files:
        print("\nEnvironment check failed.")
        if missing:
            print("Missing modules:", ", ".join(missing))
            print("Install with: pip install -r requirements.txt")
        if missing_files:
            print("Missing files:", ", ".join(missing_files))
        return 1

    print("\nEnvironment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
