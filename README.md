# belllabs-ml-impact

**Where Does Innovation Come From? A Machine Learning Analysis of Bell Laboratories (1928–1986)**

*Aryan Putta — Rutgers University CS · Benjamin Lowe — Seton Hall University (former Director, Bell Labs North America)*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Kaggle Dataset](https://img.shields.io/badge/Kaggle-Dataset-20BEFF)](https://kaggle.com/datasets/aryanputta/bell-labs-research-corpus)
[![Kaggle Notebook](https://img.shields.io/badge/Kaggle-Notebook-20BEFF)](https://kaggle.com/aryanputta/bell-labs-ml-analysis)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/YOUR-NOTEBOOK-ID)

---

## What This Repo Is

This is the full reproducible codebase for our paper applying ML to Bell Labs' publication record (71 papers, 1928–1986) to answer: what made Bell Labs produce so many breakthroughs, and can we measure it?

**Five questions, five answers:**

1. **Impact prediction** — Gradient Boosting AUC = 0.674 predicting high-citation papers
2. **Feature attribution** — Semantic content (63%) >> network centrality (6%) via SHAP
3. **Paper hashing & clustering** — MinHash fingerprints + cosine similarity detect related papers across domain boundaries
4. **Researcher archetypes** — Long-Horizon Researchers have highest impact; predictor AUC = 0.72
5. **Why Bell Labs worked** — 5 institutional factors, all quantitatively grounded

---

## Quickstart

```bash
git clone https://github.com/aryanputta/belllabs-ml-impact
cd belllabs-ml-impact
pip install -r requirements.txt

python scripts/verify_environment.py               # dependency/file sanity check
python -m src.ml.train                              # impact classification (5-fold CV)
python -m src.similarity.paper_similarity           # MinHash + cosine similarity
python -m src.network.author_network                # co-author network metrics
python -m src.clustering.research_clustering        # semantic clustering + ARI
python -m src.researcher.researcher_analysis        # researcher archetypes and findings
python scripts/research_report.py                   # paper-ready summary from generated artifacts
python scripts/validate_data_integrity.py            # sanity-check core dataset fields
python scripts/generate_cluster_hash_figures.py      # creates cluster + hashing SVG figures
python scripts/prepare_submission_bundle.py         # builds 2 canonical outputs for paper citation
python scripts/check_project_progress.py            # maps your to-do checklist to implementation status
```

---


## Google Colab

Use this one-shot helper in Colab after mounting/cloning the repo:

```bash
python scripts/colab_setup.py
```

This installs requirements and runs all major analysis modules end-to-end.

## Where key things are

- **Google Colab runner:** `scripts/colab_setup.py` (this is the main Colab execution file).
- **Primary dataset:** `data/processed/papers.csv` (paper-level records).
- **Model training code:** `src/ml/train.py` (with feature building in `src/ml/features.py`).
- **Paper network + similarity code:** `src/similarity/paper_similarity.py` and `scripts/generate_cluster_hash_figures.py`.

## Why `.env` if we already have `.gitignore`?

- `.env` is where local secrets should live (API keys, tokens, credentials).
- `.gitignore` makes sure those files are never committed by accident.
- `SECURITY.md` documents additional branch-protection steps for GitHub.

## Repository Structure

```
belllabs-ml-impact/
├── src/
│   ├── collection/         # Dataset construction + Bell Labs ID method
│   ├── ml/
│   │   ├── features.py     # Structural + network + LSA features
│   │   ├── train.py        # 5-model CV evaluation
│   │   └── explain.py      # SHAP interpretability
│   ├── similarity/
│   │   └── paper_similarity.py  # MinHash fingerprints + cosine sim matrix
│   ├── researcher/
│   │   └── researcher_analysis.py  # Archetypes, WHY Bell Labs worked
│   ├── network/            # Co-authorship graph + centrality
│   ├── clustering/         # K-Means + hierarchical domain clustering
│   ├── topics/             # TF-IDF + NMF topic extraction
│   ├── temporal/           # Decade analysis, emergence dating
│   ├── metrics/            # Innovation metrics (h-index, collab rate)
│   ├── figures/            # All 13 publication figures
│   └── validation/         # Nobel + timeline validation
├── data/
│   ├── processed/          # All generated CSVs + JSONs
│   └── kaggle/             # Files for Kaggle dataset upload
├── results/
│   ├── figures/            # fig1–fig13 (PNG + PDF, 300 DPI)
│   ├── tables/             # Metrics tables
│   └── reports/            # Validation reports
├── paper/
│   └── paper.tex           # IEEE-format LaTeX (compile-ready)
├── notebooks/
│   └── bell_labs_ml_impact.ipynb  # Colab-ready notebook
├── tests/                  # 68 tests across 3 suites
├── run_all_tests.py
└── requirements.txt
```

---

## Submission-ready canonical outputs (2-file set)

If you only cite two stable outputs in the paper, use:

- `results/submission/canonical_evidence_table.csv`
- `results/submission/canonical_evidence.json`

These are generated by:

```bash
python scripts/prepare_submission_bundle.py
```

The bundle prioritizes exactly what you asked to preserve for citation:
- machine learning metrics
- hash/similarity pair evidence
- cluster distribution summary

## Testing Strategy (what each check proves)

- `python scripts/validate_data_integrity.py`
  - Proves core CSV quality: required columns, valid years/citations, no duplicate paper IDs, no empty titles.
- `python scripts/research_report.py`
  - Proves artifacts can be summarized into a paper-ready narrative + machine-readable report.
- `python scripts/generate_cluster_hash_figures.py`
  - Proves cluster/hashing visuals are reproducible from current dataset artifacts.
- `python scripts/prepare_submission_bundle.py`
  - Proves the 2-file canonical citation bundle can be regenerated for submission.
- `python -m py_compile ...`
  - Proves scripts/modules are syntactically valid Python.
- `python scripts/verify_environment.py`
  - Proves whether runtime dependencies are installed in the current environment.
## Project Checklist Tracking

To track which research bullets are implemented in code vs still pending:

```bash
python scripts/check_project_progress.py
```

Outputs:
- `results/reports/project_checklist_status.md`
- `results/reports/project_checklist_status.json`

## Environment Validation

A paper-ready summary is generated at `results/reports/research_brief.md` and machine-readable stats at `results/reports/research_report.json` after running:

```bash
python scripts/research_report.py
```


Run this to verify Python dependencies and required files are in place:

```bash
python scripts/verify_environment.py
```

## ML Results Summary

| Model | AUC | F1 | Accuracy |
|---|---|---|---|
| **Gradient Boosting** | **0.674** | **0.668** | 0.65 |
| Logistic Regression | 0.646 | 0.551 | 0.52 |
| XGBoost | 0.578 | 0.578 | 0.54 |
| SVM (RBF) | 0.566 | 0.507 | 0.45 |
| Random Forest | 0.540 | 0.539 | 0.49 |

**Feature group importance (SHAP):**
- Text / LSA: **63.3%**
- Structural (year, abstract length): **25.3%**
- Network centrality: **6.3%**
- Domain label: **5.1%**

**Researcher impact prediction:** AUC = 0.72 (Random Forest, 3-fold CV)

---

## Figures

| # | Description |
|---|---|
| 1 | Citation distribution + domain breakdown |
| 2 | Feature importance (Random Forest) |
| 3 | ROC curves (5-fold CV, all 5 models) |
| 4 | Confusion matrix — Gradient Boosting |
| 5 | SHAP summary plot |
| 6 | Learning curve |
| 7 | Feature group ablation |
| 8 | Model comparison (AUC / F1 / Acc) |
| 9 | Per-domain classification accuracy |
| 10 | Temporal hold-out (leave-one-decade-out) |
| 11 | Researcher success: high vs low impact |
| 12 | Paper similarity heatmap (MinHash + cosine) |
| 13 | Researcher archetype distribution and impact |
| 14 | Cluster distribution across Bell Labs technical domains |
| 15 | Hash-similarity graph of linked paper pairs |
| 16 | Directed paper flow network (arrows over time) |

---

## Science-Fair Style Project Explanation

Imagine you walked up to our booth and asked: *"What is your project?"*

**Short answer:**
We are studying why Bell Labs produced so many breakthroughs. We turned that question into data and machine learning.

**What we built:**
1. A cleaned dataset of Bell Labs papers (title, authors, year, citations, topics).
2. A similarity + hashing system to connect related papers, even across different labels.
3. A researcher network view showing who collaborates and who bridges ideas.
4. A machine-learning model that predicts which papers are likely to be high-impact.

**Why it matters:**
Instead of saying "Bell Labs was special" in a vague way, we measure patterns (topic clusters, similarity links, network roles, model performance) and show evidence for how innovation happened.

**What your figures show:**
- Cluster distribution: where Bell Labs output concentrated.
- Hash/similarity graph: which papers are closely linked.
- Directed paper flow network: how related work flows over time with arrows.

## Dataset

→ Available on **Kaggle**: [`aryanputta/bell-labs-research-corpus`](https://kaggle.com/datasets/aryanputta/bell-labs-research-corpus)

71 publications, 56 researchers, 1928–1986, 8 research domains.  
Verified against Nobel Prize records, Bell System Technical Journal, IEEE/ACM archives.

---

## The Five Reasons Bell Labs Worked

1. **Long employment horizons** — avg 24 years for high-impact researchers vs 19 for low-impact
2. **Physical co-location** — highest cross-domain similarity between Information Theory ↔ Network Theory (Nyquist + Shannon shared a building)
3. **Quality over connections** — semantic content predicts impact 10× more than network centrality
4. **Institutional stability** — modularity Q = 0.896 reflects 50 years of stable team formation
5. **Freedom within structure** — 4 bridge researchers (Tukey, Nyquist, Hamming, Pierce) bridged domains organically, not by mandate

---

## Paper

`paper/paper.tex` — IEEE two-column format, 5 RQs, 13 figures embedded, ready to compile.

```bash
cd paper && pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex
```

Target venues: **Scientometrics**, **PLOS ONE**, **IEEE Access**, **Journal of Informetrics**

---

## Citation

```bibtex
@article{putta2026belllabs,
  title   = {Where Does Innovation Come From? A Machine Learning Analysis of Bell Laboratories (1928--1986)},
  author  = {Putta, Aryan and Lowe, Benjamin},
  journal = {Scientometrics},
  year    = {2026},
  note    = {Under review}
}
```

---

## GitHub Push Commands

```bash
cd belllabs-ml-impact
git init
git add .
git commit -m "Initial release: Bell Labs ML innovation analysis"
git branch -M main
git remote add origin https://github.com/aryanputta/belllabs-ml-impact.git
git push -u origin main
```

Replace `aryanputta` with your GitHub handle everywhere before pushing.
