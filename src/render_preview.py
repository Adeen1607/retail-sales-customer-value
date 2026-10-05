"""Render a reproducible portfolio preview from generated reporting tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd


def render_preview(data_dir: Path, output: Path) -> None:
    monthly = pd.read_csv(data_dir / "monthly_kpis.csv").sort_values("InvoiceMonth")
    rfm = pd.read_csv(data_dir / "customer_rfm.csv")
    dates = pd.read_csv(data_dir / "fact_sales.csv", usecols=["InvoiceDate"])
    dates = pd.to_datetime(dates["InvoiceDate"])
    if monthly.empty or dates.empty:
        raise ValueError("Build non-empty reporting tables before rendering a preview.")

    periods = pd.PeriodIndex(monthly["InvoiceMonth"], freq="M")
    labels = periods.strftime("%b %Y").tolist()
    # The source ends on 9 December 2011, so that month is not comparable
    # with a complete month. Derive this flag from the fact rather than hardcode it.
    partial = periods == dates.max().to_period("M")
    partial &= dates.max().date() < periods[-1].end_time.date()
    labels = [label + ("*" if flag else "") for label, flag in zip(labels, partial)]
    segments = rfm.groupby("Segment")["CustomerID"].nunique().sort_values()

    with plt.rc_context({"svg.fonttype": "none", "svg.hashsalt": "retail-preview"}):
        figure, axes = plt.subplots(1, 2, figsize=(13, 5))
        figure.suptitle("Retail sales and customer value | UCI Online Retail", fontsize=16)
        bars = axes[0].bar(labels, monthly["NetRevenue"], color="#2563eb")
        for bar, flag in zip(bars, partial):
            if flag:
                bar.set_color("#94a3b8")
                bar.set_hatch("//")
        axes[0].set_title("Positive-sales revenue by month")
        axes[0].set_ylabel("GBP (returns excluded)")
        axes[0].yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"£{value / 1e6:.1f}m"))
        axes[0].tick_params(axis="x", rotation=55, labelsize=9)
        axes[1].barh(segments.index, segments.values, color="#059669")
        axes[1].set_title("Known customers by RFM segment")
        axes[1].set_xlabel("Customers")
        for axis in axes:
            axis.spines[["top", "right"]].set_visible(False)
        figure.text(0.02, 0.02, "* Partial final month. Segments are descriptive heuristics, not churn predictions.", fontsize=9)
        figure.tight_layout(rect=(0, 0.06, 1, 0.92))
        output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output, metadata={"Date": None})
        plt.close(figure)
    print(f"Wrote preview to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output", type=Path, default=Path("docs/retail-preview.svg"))
    args = parser.parse_args()
    render_preview(args.data_dir, args.output)
