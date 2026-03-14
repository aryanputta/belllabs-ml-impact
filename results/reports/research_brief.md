# Bell Labs Analysis Report (Auto-generated)

## 1) What data is in this repo
- Papers dataset size: **71** publications spanning **1928–1986**.
- Distinct research domains (clusters): **8**.
- Researcher profiles available: **58**.

## 2) How this helps answer your Bell Labs question
Your question is essentially: *what conditions enabled repeated innovation at Bell Labs?*
This repo addresses that via four measurable lenses:
1. **Impact prediction (ML)** — estimate which paper characteristics track high impact.
2. **Similarity + hashing** — connect related outputs even when labels differ.
3. **Network structure** — quantify which researchers were central or bridging.
4. **Archetypes/outcomes** — compare high-impact vs lower-impact researcher traits.

## 3) Key quantitative observations from current artifacts
- Similar pair records: **11** with mean similarity **0.6428**.
- Hash coverage: **71** records and **71** unique fingerprints.
- High-impact researchers in profiles: **13**.
- Best model currently recorded: Gradient Boosting with AUC=0.674

## 4) Suggested "Methods" section text (you can adapt)
- Construct a curated Bell Labs corpus with metadata: title, abstract, year, authors, domain label, and citation count.
- Build a paper fingerprinting system using deterministic hashes and MinHash/cosine similarity to detect related research streams.
- Build co-authorship networks and compute centrality metrics (degree, betweenness, eigenvector).
- Train multiple supervised classifiers for high-impact prediction using text + structural + team features with cross-validation.
- Compare unsupervised semantic clusters to curated labels (e.g., ARI) to test whether emergent themes align with known domains.

## 5) Suggested "Results" section text (you can adapt)
- Report model ranking by AUC/F1/accuracy and discuss which features are most predictive.
- Show that similarity/hashing recovers coherent clusters and potential cross-domain bridges.
- Show how high-impact researchers differ in career span, domain breadth, and network role.
- Discuss whether the evidence supports a replicable organizational model: long horizons, cross-domain interaction, and institutional stability.

## 6) Suggested "Limitations" section text
- Small sample size and historical curation may introduce selection bias.
- Citation-based impact can undercount practical/industrial influence.
- Affiliation/entity matching can still miss hidden Bell Labs ties.

## 7) Next run commands (for Colab/local)
```bash
python scripts/verify_environment.py
python -m src.ml.train
python -m src.similarity.paper_similarity
python -m src.network.author_network
python -m src.clustering.research_clustering
python -m src.researcher.researcher_analysis
```
