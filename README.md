# belllabs-ml-impact

**Where Does Innovation Come From? A Machine Learning Analysis of Bell Laboratories (1928–1986)**

*Aryan Singh — Rutgers University CS · Benjamin Lowe — Seton Hall University (former Director, Bell Labs North America)*

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

python -m src.ml.train              # impact classification (5 models, 5-fold CV)
python -m src.ml.explain            # SHAP analysis
python -m src.similarity.paper_similarity   # MinHash + cosine similarity
python -m src.researcher.researcher_analysis  # archetype classification
python -m src.figures.generate_figures  # all 13 figures
python run_all_tests.py             # 68 tests
```

---

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

---

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
@article{singh2024belllabs,
  title   = {Where Does Innovation Come From? A Machine Learning Analysis of Bell Laboratories (1928--1986)},
  author  = {Singh, Aryan and Lowe, Benjamin},
  journal = {Scientometrics},
  year    = {2024},
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
