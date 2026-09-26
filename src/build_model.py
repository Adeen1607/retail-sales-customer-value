"""Build clean retail reporting tables and customer-value features."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = {
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
}


def validate_schema(frame: pd.DataFrame) -> None:
    missing = sorted(EXPECTED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")


def clean_transactions(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return valid sales and an exclusion summary."""
    validate_schema(frame)
    data = frame.copy()
    data["InvoiceNo"] = data["InvoiceNo"].astype("string").str.strip()
    data["StockCode"] = data["StockCode"].astype("string").str.strip()
    data["Description"] = data["Description"].astype("string").str.strip()
    data["Country"] = data["Country"].astype("string").str.strip()
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data["Quantity"] = pd.to_numeric(data["Quantity"], errors="coerce")
    data["UnitPrice"] = pd.to_numeric(data["UnitPrice"], errors="coerce")
    data["CustomerID"] = pd.to_numeric(data["CustomerID"], errors="coerce").astype(
        "Int64"
    )

    reasons = pd.DataFrame(index=data.index)
    reasons["invalid_date"] = data["InvoiceDate"].isna()
    reasons["missing_invoice"] = data["InvoiceNo"].isna() | data["InvoiceNo"].eq("")
    reasons["missing_product"] = data["StockCode"].isna() | data["StockCode"].eq("")
    reasons["non_positive_quantity"] = data["Quantity"].le(0) | data["Quantity"].isna()
    reasons["non_positive_price"] = data["UnitPrice"].le(0) | data["UnitPrice"].isna()
    reasons["cancelled_invoice"] = data["InvoiceNo"].str.startswith("C", na=False)

    excluded = reasons.any(axis=1)
    exclusion_summary = (
        reasons.sum()
        .rename_axis("exclusion_reason")
        .reset_index(name="record_count")
        .sort_values("record_count", ascending=False)
    )

    sales = data.loc[~excluded].copy()
    sales["LineRevenue"] = sales["Quantity"] * sales["UnitPrice"]
    sales["InvoiceDateKey"] = sales["InvoiceDate"].dt.normalize()
    sales["InvoiceMonth"] = sales["InvoiceDate"].dt.to_period("M").astype(str)
    sales["CustomerKey"] = sales["CustomerID"].astype("string").fillna("Unknown")
    sales["ProductKey"] = sales["StockCode"].astype("string")
    return sales, exclusion_summary


def quantile_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Assign stable one-to-five quantile scores."""
    ranked = series.rank(method="first")
    bins = min(5, len(ranked))
    if bins < 2:
        return pd.Series(3, index=series.index, dtype="int64")
    labels = list(range(1, bins + 1))
    scores = pd.qcut(ranked, q=bins, labels=labels).astype(int)
    if bins < 5:
        scores = ((scores - 1) * 4 / (bins - 1) + 1).round().astype(int)
    return scores if higher_is_better else 6 - scores


def build_rfm(sales: pd.DataFrame) -> pd.DataFrame:
    customer_sales = sales.dropna(subset=["CustomerID"]).copy()
    if customer_sales.empty:
        return pd.DataFrame(
            columns=[
                "CustomerID",
                "RecencyDays",
                "Frequency",
                "MonetaryValue",
                "RScore",
                "FScore",
                "MScore",
                "RFMScore",
                "Segment",
            ]
        )

    snapshot_date = customer_sales["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)
    rfm = (
        customer_sales.groupby("CustomerID")
        .agg(
            LastPurchase=("InvoiceDate", "max"),
            Frequency=("InvoiceNo", "nunique"),
            MonetaryValue=("LineRevenue", "sum"),
        )
        .reset_index()
    )
    rfm["RecencyDays"] = (snapshot_date - rfm["LastPurchase"].dt.normalize()).dt.days
    rfm["RScore"] = quantile_score(rfm["RecencyDays"], higher_is_better=False)
    rfm["FScore"] = quantile_score(rfm["Frequency"])
    rfm["MScore"] = quantile_score(rfm["MonetaryValue"])
    rfm["RFMScore"] = rfm[["RScore", "FScore", "MScore"]].sum(axis=1)

    conditions = [
        rfm["RFMScore"].ge(13),
        rfm["RScore"].ge(4) & rfm["FScore"].ge(3),
        rfm["RScore"].le(2) & rfm["FScore"].ge(3),
        rfm["RScore"].le(2),
    ]
    labels = ["Champions", "Loyal", "At Risk", "Hibernating"]
    rfm["Segment"] = "Developing"
    for condition, label in zip(conditions, labels):
        rfm.loc[condition & rfm["Segment"].eq("Developing"), "Segment"] = label

    return rfm.drop(columns="LastPurchase").sort_values(
        "MonetaryValue", ascending=False
    )


def build_tables(workbook: Path, output_dir: Path) -> None:
    raw = pd.read_excel(workbook)
    sales, exclusions = clean_transactions(raw)
    output_dir.mkdir(parents=True, exist_ok=True)

    monthly = (
        sales.groupby("InvoiceMonth")
        .agg(
            NetRevenue=("LineRevenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Units=("Quantity", "sum"),
            Customers=("CustomerID", "nunique"),
        )
        .reset_index()
    )
    monthly["AverageOrderValue"] = monthly["NetRevenue"] / monthly["Orders"]

    product = (
        sales.groupby(["ProductKey", "Description"], dropna=False)
        .agg(
            NetRevenue=("LineRevenue", "sum"),
            Units=("Quantity", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
        )
        .reset_index()
        .sort_values("NetRevenue", ascending=False)
    )

    country = (
        sales.groupby("Country", dropna=False)
        .agg(
            NetRevenue=("LineRevenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Units=("Quantity", "sum"),
            Customers=("CustomerID", "nunique"),
        )
        .reset_index()
    )
    country["AverageOrderValue"] = country["NetRevenue"] / country["Orders"]

    tables = {
        "fact_sales.csv": sales,
        "monthly_kpis.csv": monthly,
        "product_performance.csv": product,
        "country_performance.csv": country,
        "customer_rfm.csv": build_rfm(sales),
        "data_quality_exclusions.csv": exclusions,
    }
    for filename, table in tables.items():
        table.to_csv(output_dir / filename, index=False)

    print(f"Wrote {len(tables)} reporting tables to {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build retail BI reporting tables.")
    parser.add_argument(
        "--workbook",
        type=Path,
        default=Path("data/raw/online_retail.xlsx"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build_tables(arguments.workbook, arguments.output_dir)
