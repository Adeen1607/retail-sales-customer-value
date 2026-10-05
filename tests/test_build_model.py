import pandas as pd

from src.build_model import build_rfm, build_tables, clean_transactions, quantile_score


def sample_transactions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "InvoiceNo": ["100", "100", "C101", "102", "103"],
            "StockCode": ["A", "B", "A", "C", "D"],
            "Description": ["Alpha", "Beta", "Alpha", "Gamma", "Delta"],
            "Quantity": [2, 1, -1, 3, 1],
            "InvoiceDate": [
                "2011-01-01 10:00",
                "2011-01-01 10:00",
                "2011-01-02 11:00",
                "2011-01-03 12:00",
                "2011-01-04 09:00",
            ],
            "UnitPrice": [10.0, 5.0, 10.0, 0.0, 7.0],
            "CustomerID": [1, 1, 1, 2, 3],
            "Country": ["United Kingdom"] * 5,
        }
    )


def test_clean_transactions_excludes_invalid_sales() -> None:
    sales, exclusions = clean_transactions(sample_transactions())

    assert len(sales) == 3
    assert sales["LineRevenue"].sum() == 32.0

    counts = exclusions.set_index("exclusion_reason")["record_count"]
    assert counts["cancelled_invoice"] == 1
    assert counts["non_positive_quantity"] == 1
    assert counts["non_positive_price"] == 1


def test_rfm_is_customer_grained() -> None:
    sales, _ = clean_transactions(sample_transactions())
    rfm = build_rfm(sales)

    assert rfm["CustomerID"].is_unique
    assert set(rfm["CustomerID"]) == {1, 3}

    customer_one = rfm.set_index("CustomerID").loc[1]
    assert customer_one["Frequency"] == 1
    assert customer_one["MonetaryValue"] == 25.0


def test_quantile_scores_preserve_ties_and_ignore_row_order() -> None:
    values = pd.Series([1, 1, 1, 2, 3, 5, 5, 8], index=list("abcdefgh"))
    scores = quantile_score(values)
    shuffled = quantile_score(values.sample(frac=1, random_state=42))

    pd.testing.assert_series_equal(scores.sort_index(), shuffled.sort_index())
    assert scores.loc[["a", "b", "c"]].nunique() == 1
    assert scores.loc[["f", "g"]].nunique() == 1
    assert scores.between(1, 5).all()
    assert scores.loc["a"] < scores.loc["h"]
    pd.testing.assert_series_equal(quantile_score(values, False), 6 - scores)


def test_identical_quantile_values_receive_neutral_scores() -> None:
    scores = quantile_score(pd.Series([10] * 8))
    assert scores.eq(3).all()


def test_rfm_snapshot_includes_sales_with_unknown_customer() -> None:
    raw = sample_transactions().iloc[[0, 4]].copy()
    raw.loc[4, "CustomerID"] = None
    raw.loc[4, "InvoiceDate"] = "2011-02-01 09:00"
    sales, _ = clean_transactions(raw)

    rfm = build_rfm(sales).set_index("CustomerID")

    assert list(rfm.index) == [1]
    assert rfm.loc[1, "RecencyDays"] == 32


def test_workbook_pipeline_exports_reconciled_reporting_tables(tmp_path) -> None:
    workbook = tmp_path / "transactions.xlsx"
    sample_transactions().to_excel(workbook, index=False)
    output = tmp_path / "processed"

    build_tables(workbook, output)

    assert {path.name for path in output.iterdir()} == {
        "fact_sales.csv", "monthly_kpis.csv", "product_performance.csv",
        "country_performance.csv", "customer_rfm.csv", "data_quality_exclusions.csv",
    }
    fact = pd.read_csv(output / "fact_sales.csv")
    monthly = pd.read_csv(output / "monthly_kpis.csv")
    country = pd.read_csv(output / "country_performance.csv")
    assert len(fact) == 3
    assert fact["LineRevenue"].sum() == monthly["NetRevenue"].sum() == 32
    assert country["NetRevenue"].sum() == 32
    assert monthly.loc[0, "Orders"] == 2
    assert monthly.loc[0, "AverageOrderValue"] == 16
