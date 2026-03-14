"""Feature engineering utilities for Bell Labs paper-level ML tasks."""

from __future__ import annotations

import re
from typing import Iterable

import numpy as np
import pandas as pd


def _token_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", str(text).lower()))


def build_structural_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create deterministic numeric features from the papers table."""
    feat = df.copy()
    feat["year"] = pd.to_numeric(feat["year"], errors="coerce").fillna(0).astype(int)
    feat["citations"] = pd.to_numeric(feat["citations"], errors="coerce").fillna(0)
    feat["num_authors"] = pd.to_numeric(feat.get("num_authors", 1), errors="coerce").fillna(1)
    feat["title_len"] = feat["title"].fillna("").map(_token_count)
    feat["abstract_len"] = feat["abstract"].fillna("").map(_token_count)
    feat["keyword_len"] = feat["keywords"].fillna("").map(_token_count)
    feat["is_bell_labs"] = feat["is_bell_labs"].astype(str).str.lower().isin(["true", "1", "yes"]).astype(int)
    feat["decade"] = (feat["year"] // 10) * 10
    return feat


def add_author_productivity_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add author-level aggregate features to each paper row."""
    feat = df.copy()

    def parse_authors(cell: str) -> list[str]:
        return [a.strip() for a in str(cell).split(";") if a.strip()]

    feat["author_list"] = feat["authors"].map(parse_authors)
    exploded = feat[["paper_id", "author_list", "citations"]].explode("author_list")
    author_stats = exploded.groupby("author_list").agg(
        author_papers=("paper_id", "count"),
        author_mean_citations=("citations", "mean"),
    )

    def author_agg(authors: Iterable[str], column: str, default: float = 0.0) -> float:
        vals = [float(author_stats.loc[a, column]) for a in authors if a in author_stats.index]
        return float(np.mean(vals)) if vals else default

    feat["team_mean_prior_productivity"] = feat["author_list"].map(
        lambda names: author_agg(names, "author_papers", default=1.0)
    )
    feat["team_mean_prior_citations"] = feat["author_list"].map(
        lambda names: author_agg(names, "author_mean_citations", default=0.0)
    )
    return feat.drop(columns=["author_list"])


def make_binary_target(df: pd.DataFrame, quantile: float = 0.70) -> pd.Series:
    threshold = float(df["citations"].quantile(quantile))
    return (df["citations"] >= threshold).astype(int)
