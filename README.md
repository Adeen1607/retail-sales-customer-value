# Retail Sales & Customer Value Analytics

A business-intelligence case study that converts transaction-level retail data into a clean reporting model for revenue, order quality, customer value, product performance, and geographic trends.

## Business questions

- How are net revenue, order volume, units sold, and average order value changing over time?
- Which customers contribute the greatest value based on recency, frequency, and monetary value?
- Which products and countries drive revenue, volume, cancellations, and returns?
- Are changes caused by more customers, larger baskets, or pricing?
- Which customer segments should receive retention, reactivation, or high-value service campaigns?

## Data source

This project uses the [Online Retail dataset from the UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/352/online+retail). It contains 541,909 transactions from a UK-based non-store retailer between December 2010 and December 2011.

Raw data is downloaded from UCI at runtime and is not committed to this repository.

## Deliverables

- validated and cleaned transaction fact table;
- monthly KPI table;
- product and country performance tables;
- customer-level RFM segmentation;
- Power BI star-schema design and DAX measures;
- refreshable Python pipeline and automated tests;
- documented assumptions, exclusions, and data-quality checks.

## Repository structure

| Path | Purpose |
|---|---|
| `src/download_data.py` | Download and extract the official UCI workbook |
| `src/build_model.py` | Validate, clean, and build reporting tables |
| `powerbi/measures.dax` | Core measures for the Power BI semantic model |
| `docs/DATA_MODEL.md` | Fact, dimension, relationship, and grain definitions |
| `docs/KPI_DEFINITIONS.md` | Business rules for every reported KPI |
| `tests/` | Unit tests for cleaning and KPI logic |
| `data/processed/` | Generated reporting tables; not versioned |
| `artifacts/` | Generated visuals and summaries; not versioned |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/download_data.py
python src/build_model.py
pytest
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

## Dashboard pages

1. **Executive overview** — net revenue, orders, customers, units, average order value, and monthly trend.
2. **Customer value** — RFM segments, repeat-customer rate, revenue concentration, and reactivation candidates.
3. **Product performance** — revenue, units, average selling price, cancellation rate, and product ranking.
4. **Geographic performance** — country revenue, customers, orders, basket value, and growth.
5. **Data quality** — excluded records, missing customers, cancellations, negative quantities, and refresh status.

## Responsible interpretation

The dataset represents one retailer and one historical period. Customer identifiers are incomplete for some transactions, product descriptions are operational rather than standardized catalogue labels, and cancellation codes require explicit treatment. Findings demonstrate analytical workflow design and should not be generalized to the wider retail market.


## Rebuild the reading edition

```bash
python -m pip install -r requirements-research.txt
python scripts/build_research_site.py
```

This renders saved notebook outputs without rerunning model training or external APIs. To refresh findings, run the analysis commands above first, update `reports/research-findings.md`, and rebuild.

<!-- research-edition:start -->
## Research edition

[Research report and final visual results](research/report.md) · [Browser-ready notebook catalogue](research/notebooks.html)

Fresh pipeline execution on 11 October 2026. The **13 monthly reporting buckets** contain aggregate net revenue of **10,666,684.54 GBP**. The customer RFM table contains **4,338 identified customers**. These totals follow the cleaning and return rules in src/build_model.py. The first and last buckets are incomplete calendar months and should not be used as comparable growth endpoints.

| Measure | Value |
|---|---:|
| monthly buckets | 13 |
| net revenue GBP | 10666684.5440 |
| identified RFM customers | 4338 |



The `research/` folder contains a professional static reading edition. The Pages workflow deploys it after GitHub Pages is enabled with **GitHub Actions** as the publishing source. Intended URL: `https://adeen1607.github.io/retail-sales-customer-value/`. Deployment status must be checked in Actions before treating that address as live.

<!-- research-edition:end -->
