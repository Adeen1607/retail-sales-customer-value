# KPI definitions

| KPI | Definition | Grain and exclusions |
|---|---|---|
| Net revenue | Sum of quantity multiplied by unit price | Valid positive sales lines only |
| Orders | Distinct invoice count | Cancelled invoices excluded |
| Units sold | Sum of quantity | Non-positive quantities excluded |
| Active customers | Distinct non-null customer identifiers | Valid sales only |
| Average order value | Net revenue divided by orders | Returns zero only through safe division |
| Revenue per customer | Net revenue divided by active customers | Transactions without customer ID affect revenue but not customer count |
| Average selling price | Net revenue divided by units sold | Weighted by unit volume |
| Monthly revenue change % | Current month revenue less prior month, divided by prior month | Requires complete date dimension |
| Top-ten customer share | Revenue from ten highest-value known customers divided by total revenue | Unknown customers remain in denominator |
| Recency | Days between snapshot date and most recent valid purchase | Snapshot is one day after the latest valid transaction |
| Frequency | Distinct valid invoices per known customer | Cancelled invoices excluded |
| Monetary value | Sum of valid line revenue per known customer | Positive sales only |

## Cancellation and return treatment

An invoice beginning with `C`, a non-positive quantity, or a non-positive price is excluded from the sales fact. Each rule is counted independently in the data-quality table, so one source record can contribute to more than one exclusion count. Cancellation and return analysis should use a separate transaction-status fact in a future iteration rather than combining signed and positive sales in one measure.
