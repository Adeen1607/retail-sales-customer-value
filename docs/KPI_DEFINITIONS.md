# KPI definitions

| KPI | Definition | Grain and exclusions |
|---|---|---|
| Positive-sales revenue (`NetRevenue` / `[Net Revenue]`, legacy names) | Sum of quantity multiplied by unit price | Valid positive sales lines only; not net of returns or cancellations |
| Orders | Distinct invoice count | Cancelled invoices excluded |
| Units sold | Sum of quantity | Non-positive quantities excluded |
| Active customers | Distinct non-null customer identifiers | Valid sales only |
| Average order value | Positive-sales revenue divided by orders | DAX returns blank when the denominator is zero |
| Revenue per customer | Net revenue divided by active customers | Transactions without customer ID affect revenue but not customer count |
| Average selling price | Net revenue divided by units sold | Weighted by unit volume |
| Monthly revenue change % | Current month revenue less prior month, divided by prior month | Requires complete date dimension |
| Top-ten customer share | Revenue from ten highest-value known customers divided by total revenue | Unknown customers remain in denominator |
| Recency | Days between snapshot date and most recent valid purchase | Snapshot is one day after the latest valid transaction |
| Frequency | Distinct valid invoices per known customer | Cancelled invoices excluded |
| Monetary value | Sum of valid line revenue per known customer | Positive sales only |

## Cancellation and return treatment

An invoice beginning with `C`, a non-positive quantity, or a non-positive price is excluded from the sales fact. Each rule is counted independently in the data-quality table, so one source record can contribute to more than one exclusion count. Cancellation and return analysis should use a separate transaction-status fact in a future iteration rather than combining signed and positive sales in one measure.

## RFM scoring

The snapshot is one day after the latest valid purchase in the entire sales fact, including purchases without a customer ID. Unknown customers do not receive RFM rows. Recency uses calendar dates, frequency counts distinct invoices, and monetary value sums positive sales.

Each metric uses average ranks followed by quantile bins. Equal values receive equal scores regardless of row order; tied bin boundaries are collapsed, and the remaining bins are scaled to 1–5. A constant metric receives the neutral score 3. Recency scores are reversed so more recent purchases score higher. Segment labels are heuristics, not predictions of future customer behaviour.

The top-ten customer measure excludes blank customer IDs and breaks revenue ties by customer ID, so it selects at most ten known customers. Its denominator includes all valid sales, including unknown-customer sales.
