# Source Package Layout

Implemented modules:
- `src/similarity/paper_similarity.py` — paper fingerprinting + MinHash/cosine similarity.
- `src/researcher/researcher_analysis.py` — researcher profile modeling and Bell Labs findings.
- `src/ml/features.py` + `src/ml/train.py` — paper-level feature engineering + ML benchmarking.
- `src/network/author_network.py` — co-authorship network + centrality exports.
- `src/clustering/research_clustering.py` — KMeans semantic clustering + ARI evaluation.

Scaffolded packages for future extension:
- `collection`, `topics`, `temporal`, `metrics`, `figures`, `validation`.
