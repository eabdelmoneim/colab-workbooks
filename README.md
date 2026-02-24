# Colab Workbooks

Example Google Colab notebooks for prototyping AI-enabled sourcing and manufacturing intelligence workflows.

## Repository Contents

- `Hoth_Industries_Demo.ipynb`: End-to-end demo notebook showing how to clean procurement data, join it with CADDi-style drawing metadata, and generate practical sourcing/design alerts.

## Notebook Overview

### `Hoth_Industries_Demo.ipynb`

This workbook demonstrates a 3-phase pipeline:

1. Data Cleansing and Normalization
- Normalizes supplier names into a canonical `supplier_key`
- Computes delivery latency metrics (`days_late`)

2. Unified Data Warehouse Build
- Merges order history, quality inspections, and drawing metadata
- Produces a master dataset for analytics apps

3. Intelligence Applications
- Supplier Reliability Scorecard (rejection rate + lateness by geometry)
- Geometric DfM Advisor (uses similarity history for design-risk warnings)
- Quote Benchmarking Tool (flags RFQ prices above historical average)

## Expected Input Files (Colab)

Upload these CSV files to the Colab Files sidebar before running notebook cells:

- `Copy of supplier_orders.csv`
- `Copy of quality_inspections.csv`
- `Copy of rfq_responses.csv`
- `mock_drawer_metadata.csv`
- `mock_drawer_similarity.csv`

## How to Run

1. Open the notebook in Google Colab.
2. Upload the required CSV files to the Colab runtime.
3. Run cells top-to-bottom.
4. Review generated outputs:
- Standardized order/quality tables
- Supplier risk scorecard
- DfM advisory message for target part (example: `HX-5530`)
- Quote benchmark alert vs historical pricing

## Use Case

This repo is intended as a working example for moving from fragmented tribal-knowledge workflows to a structured, data-driven sourcing intelligence approach.

## Notes

- Current notebook is demo-oriented and uses mocked CADDi-related metadata/similarity files.
- Extend this repo by adding more notebooks for new scenarios (supplier onboarding, lead-time forecasting, cost optimization, etc.).
