# Bell Labs Research To-Do → Implementation Checklist

This checklist maps your research bullets to concrete code/artifacts in this repository.

Legend:
- ✅ done in code/artifacts
- 🟡 partially implemented (needs extension)
- ⚪ not implemented yet

## Core goal and research question
- ✅ Define innovation question and Bell Labs case framing (`README.md`, `results/reports/research_brief.md`).
- ✅ Produce a concise explanation of what is being measured and why (`scripts/research_report.py`).

## Bell Labs identification problem
- 🟡 Affiliation field is present in `data/processed/papers.csv`, but a dedicated identity-resolution/confidence module is still needed.
- ⚪ Add a resolver that scores Bell Labs linkage from names + affiliations + years + coauthors + assignees.

## Data collection scope
- ✅ Papers/publications are represented in `data/processed/papers.csv`.
- ⚪ Patents dataset ingestion pipeline.
- ⚪ Presentations dataset ingestion pipeline.

## Search beyond obvious "Bell Labs" labels
- 🟡 Current pipeline supports author/affiliation analysis, but dedicated fuzzy matching and alias expansion is not yet isolated in one module.
- ⚪ Add canonical-name + alias table and fuzzy matching report.

## Clustering and similarity/hashing
- ✅ Paper hashing and similarity implemented (`src/similarity/paper_similarity.py`; outputs in `data/processed/paper_hash_table.csv` and `data/processed/similar_paper_pairs.csv`).
- ✅ Semantic clustering module implemented (`src/clustering/research_clustering.py`).
- 🟡 Time-aware clustering still needs explicit temporal module wiring.

## Network + researcher analysis
- ✅ Researcher profiling/archetypes implemented (`src/researcher/researcher_analysis.py`, `data/processed/researcher_profiles.csv`).
- ✅ Coauthor network metrics implemented (`src/network/author_network.py`).

## Machine learning model
- ✅ ML training module implemented (`src/ml/features.py`, `src/ml/train.py`).
- 🟡 In this restricted environment dependencies are missing, so full retraining must run in Colab/local with dependencies installed.

## Reproducibility + security
- ✅ `.gitignore` and `SECURITY.md` protect against secret leakage.
- ✅ Environment check script + CI workflow exist (`scripts/verify_environment.py`, `.github/workflows/python-ci.yml`).
- ✅ Colab helper exists (`scripts/colab_setup.py`).

## What to add next to bolster the paper most
1. Add **identity-resolution module** with confidence scoring and validation set.
2. Add **patents + presentations ingestion** and unified record schema.
3. Add **ablation + robustness tests** (temporal holdout, leave-domain-out, shuffled-label sanity check).
4. Add **causal caution section** and sensitivity analyses in paper (to avoid overclaiming from correlation).
