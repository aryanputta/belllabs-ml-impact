"""Train paper impact classifiers and export reproducible metrics."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

from src.ml.features import add_author_productivity_features, build_structural_features, make_binary_target

BASE = Path(__file__).resolve().parent.parent.parent


def build_dataset(papers: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    feat = build_structural_features(papers)
    feat = add_author_productivity_features(feat)
    y = make_binary_target(feat)
    return feat, y


def evaluate_models(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    text_col = "abstract"
    numeric_cols = [
        "year", "num_authors", "title_len", "abstract_len", "keyword_len",
        "team_mean_prior_productivity", "team_mean_prior_citations",
    ]
    cat_cols = ["cluster"]

    pre = ColumnTransformer(
        transformers=[
            ("text", TfidfVectorizer(max_features=300, ngram_range=(1, 2), stop_words="english"), text_col),
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ]
    )

    models = {
        "logreg": LogisticRegression(max_iter=1000, random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=300, random_state=42),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
        "svm_rbf": SVC(probability=True, kernel="rbf", C=1.5, gamma="scale", random_state=42),
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rows = []
    for name, model in models.items():
        aucs, f1s, accs = [], [], []
        for tr, te in cv.split(X, y):
            pipe = Pipeline([("pre", pre), ("model", model)])
            pipe.fit(X.iloc[tr], y.iloc[tr])
            pred = pipe.predict(X.iloc[te])
            proba = pipe.predict_proba(X.iloc[te])[:, 1]
            aucs.append(roc_auc_score(y.iloc[te], proba))
            f1s.append(f1_score(y.iloc[te], pred))
            accs.append(accuracy_score(y.iloc[te], pred))

        rows.append({
            "model": name,
            "auc_mean": round(float(pd.Series(aucs).mean()), 4),
            "f1_mean": round(float(pd.Series(f1s).mean()), 4),
            "acc_mean": round(float(pd.Series(accs).mean()), 4),
        })

    out = pd.DataFrame(rows).sort_values("auc_mean", ascending=False).reset_index(drop=True)
    return out


def run(base: Path = BASE) -> dict:
    papers = pd.read_csv(base / "data/processed/papers.csv")
    X, y = build_dataset(papers)
    metrics = evaluate_models(X, y)

    out_dir = base / "results/tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(out_dir / "ml_model_metrics.csv", index=False)

    best = metrics.iloc[0].to_dict()
    summary = {
        "n_papers": int(len(papers)),
        "positive_class_ratio": round(float(y.mean()), 4),
        "best_model": best,
    }
    with open(out_dir / "ml_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(metrics.to_string(index=False))
    print(f"\nSaved: {out_dir / 'ml_model_metrics.csv'}")
    return {"metrics": metrics, "summary": summary}


if __name__ == "__main__":
    run()
