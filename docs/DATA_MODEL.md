# Power BI data model

## Recommended star schema

| Table | Grain | Primary key | Role |
|---|---|---|---|
| `fact_sales` | One valid invoice line | Composite invoice and line position | Revenue and unit activity |
| `dim_date` | One calendar date | Date | Time intelligence |
| `dim_customer` | One known customer | CustomerID | Customer slicing |
| `dim_product` | One stock code | ProductKey | Product slicing |
| `dim_country` | One country | Country | Geographic slicing |
| `customer_rfm` | One known customer at refresh date | CustomerID | Value and lifecycle segment |
| `data_quality_exclusions` | One exclusion rule | exclusion_reason | Refresh-quality reporting |

## Relationships

- `dim_date[Date]` one-to-many `fact_sales[InvoiceDateKey]`
- `dim_customer[CustomerID]` one-to-many `fact_sales[CustomerID]`
- `dim_product[ProductKey]` one-to-many `fact_sales[ProductKey]`
- `dim_country[Country]` one-to-many `fact_sales[Country]`
- `dim_customer[CustomerID]` one-to-one `customer_rfm[CustomerID]`

Use single-direction filtering from dimensions to facts. Do not relate pre-aggregated monthly, product, or country tables to the transaction fact when the same page can calculate those results from the star schema; those exports are included for audit and non-Power-BI consumers.

## Date table

Create `dim_date` from the minimum through maximum `InvoiceDateKey`, add year, quarter, month number, month label, and year-month fields, then mark it as the model's date table. Sort month labels by month number.

## Refresh sequence

1. Download the source archive.
2. Validate and clean transactions.
3. Review `data_quality_exclusions.csv`.
4. Load dimensions before facts.
5. Refresh the semantic model.
6. Confirm row counts and latest transaction date.
7. Publish only after quality checks pass.
