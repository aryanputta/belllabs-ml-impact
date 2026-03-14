"""Helpers for running this repository smoothly in Google Colab."""

from __future__ import annotations

import subprocess
import sys


def install_requirements() -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def run_all_key_modules() -> None:
    commands = [
        [sys.executable, "scripts/verify_environment.py"],
        [sys.executable, "-m", "src.ml.train"],
        [sys.executable, "-m", "src.similarity.paper_similarity"],
        [sys.executable, "-m", "src.network.author_network"],
        [sys.executable, "-m", "src.clustering.research_clustering"],
        [sys.executable, "-m", "src.researcher.researcher_analysis"],
    ]
    for cmd in commands:
        print("Running:", " ".join(cmd))
        subprocess.check_call(cmd)


if __name__ == "__main__":
    install_requirements()
    run_all_key_modules()
