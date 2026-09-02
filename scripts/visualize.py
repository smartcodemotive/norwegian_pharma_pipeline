"""Generate business visualisations from output.csv."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from norwegian_pipeline.config import OUTPUT_CSV, VIZ_DIR

logger = logging.getLogger(__name__)

INTERPRETATIONS: dict[str, str] = {}


def _save(fig: plt.Figure, name: str, interpretation: str) -> None:
    VIZ_DIR.mkdir(parents=True, exist_ok=True)
    path = VIZ_DIR / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    INTERPRETATIONS[name] = interpretation
    logger.info("Saved %s", path)


def plot_estimated_value_by_molecule(df: pd.DataFrame) -> None:
    subset = df.copy()
    subset["estimatedValue"] = pd.to_numeric(subset["estimatedValue"], errors="coerce")
    agg = (
        subset.dropna(subset=["estimatedValue"])
        .groupby("productMolecule", as_index=False)["estimatedValue"]
        .max()
        .sort_values("estimatedValue", ascending=False)
    )
    if agg.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=agg, x="productMolecule", y="estimatedValue", ax=ax, palette="Blues_d")
    ax.set_title("Headline estimated tender value by molecule (max per molecule)")
    ax.set_ylabel("Estimated value (NOK)")
    ax.set_xlabel("Molecule")
    ax.ticklabel_format(style="plain", axis="y")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    _save(
        fig,
        "01_value_by_molecule",
        "Lenalidomide and oncology-bundle tenders (Axitinib via LIS 2207) dominate "
        "headline NOK, but these are framework ceilings — not addressable pack revenue. "
        "Anagrelide's published ~10 MNOK competition is far smaller but may be fully contestable.",
    )


def plot_notice_lifecycle(df: pd.DataFrame) -> None:
    if df.empty:
        return
    counts = df.groupby(["productMolecule", "noticeType"]).size().reset_index(name="count")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=counts, x="productMolecule", y="count", hue="noticeType", ax=ax)
    ax.set_title("Notice lifecycle stages captured per molecule")
    ax.set_ylabel("Row count")
    ax.set_xlabel("Molecule")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    _save(
        fig,
        "02_notice_lifecycle",
        "Lenalidomide and Paliperidone show multiple notice types (prior information, "
        "competition, intent), reflecting the assessment's lifecycle point. Axitinib appears "
        "mainly inside bundled oncology tenders — a different buying route with less standalone visibility.",
    )


def plot_pack_strength_distribution(df: pd.DataFrame) -> None:
    pack = df[df["strength"].astype(str).str.len() > 0]
    if pack.empty:
        return
    counts = pack.groupby(["productMolecule", "strength"]).size().reset_index(name="packs")
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(data=counts, x="productMolecule", y="packs", hue="strength", ax=ax)
    ax.set_title("Pack-level strength spread (from parsed virkestoffliste)")
    ax.set_ylabel("Pack lines")
    ax.set_xlabel("Molecule")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    _save(
        fig,
        "03_strength_distribution",
        "Everolimus and Lenalidomide span many strengths — typical for immunosuppressant and "
        "myeloma portfolios. Fewer Axitinib strengths but oncology bundle procurement means "
        "winning requires competing across a wide co-formulary, not a single SKU.",
    )


def plot_detection_methods(df: pd.DataFrame) -> None:
    if df.empty:
        return
    counts = df["detectionMethod"].value_counts().reset_index()
    counts.columns = ["method", "count"]
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=counts, y="method", x="count", ax=ax, palette="viridis")
    ax.set_title("How molecules were identified")
    ax.set_xlabel("Rows")
    _save(
        fig,
        "04_detection_methods",
        "Name matching alone would miss Axitinib (ATC-only in attachments) and supplemental "
        "Paliperidone lines (N05AX13). Combining name, LIS ref, and ATC code matching is necessary "
        "for Norwegian LIS data.",
    )


def plot_timing(df: pd.DataFrame) -> None:
    subset = df.copy()
    subset["publicationDate"] = pd.to_datetime(subset["publicationDate"], errors="coerce")
    subset = subset.dropna(subset=["publicationDate"])
    if subset.empty:
        return
    subset["year"] = subset["publicationDate"].dt.year
    counts = subset.groupby(["year", "productMolecule"]).size().reset_index(name="notices")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=counts, x="year", y="notices", hue="productMolecule", marker="o", ax=ax)
    ax.set_title("Publication timing of captured notices")
    ax.set_ylabel("Notice rows")
    ax.set_xlabel("Year")
    _save(
        fig,
        "05_publication_timing",
        "Active 2025–2026 competitions (Everolimus 2632a, Paliperidone 2601c) sit in the bid window "
        "now, while Lenalidomide's main LIS 2234 cycle is older — suggesting near-term bid effort "
        "should focus on live tenders, not historic high-value frameworks.",
    )


def write_interpretations_md() -> None:
    lines = ["# Visualisation interpretations\n"]
    for name, text in INTERPRETATIONS.items():
        lines.append(f"## {name}\n\n{text}\n")
    (VIZ_DIR / "interpretations.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=OUTPUT_CSV)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    if not args.input.exists():
        logger.error("Input CSV not found: %s", args.input)
        return 1

    df = pd.read_csv(args.input, encoding="utf-8")
    sns.set_theme(style="whitegrid")

    plot_estimated_value_by_molecule(df)
    plot_notice_lifecycle(df)
    plot_pack_strength_distribution(df)
    plot_detection_methods(df)
    plot_timing(df)
    write_interpretations_md()
    print(f"Visualisations written to {VIZ_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
