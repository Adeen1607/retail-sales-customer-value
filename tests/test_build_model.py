import pandas as pd

from src.build_model import build_rfm, clean_transactions


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
