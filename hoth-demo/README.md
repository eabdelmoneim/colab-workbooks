# Hoth Demo: Streamlit Risk Alerts Dashboard

This folder contains a Streamlit dashboard that provides part-level risk analysis for Hoth Industries across sourcing, quality, geometric similarity, and quote benchmarking.

## Contents

- `app.py`: Streamlit application (`Hoth Industries: Risk Alerts Dashboard`)
- `requirements.txt`: Python dependencies for the dashboard
- `data/`: CSV datasets used by the dashboard
- `Hoth_Industries_Demo.ipynb`: Notebook version of the same problem space

## Dashboard Workflow

The app is designed around a single user action: selecting a part from the search box (`Part Description (PART-NUMBER)`).

After selection, it shows:

1. Selected part headers
- Part Number
- Part Description

2. Global supply health (top-level)
- Overall rejection rate
- Share of orders delayed by more than 10 days

3. Quick part metrics
- Average historical purchase price
- Historical rejection rate
- Reliability status (`Stable`, `Watch`, `High Risk`)

4. Analysis tabs
- `A. Sourcing Performance`
  - Supplier history table for the selected part
  - Highlights high-risk suppliers in red if avg days late > 10 or avg rejection rate > 5%
- `B. Producibility Advisor`
  - Shows most similar geometry part and similarity score
  - Displays top 3 historical rejection reasons (with counts) from matched geometry quality records
- `C. Quote Benchmarking`
  - Compares latest RFQ quote to historical average unit price
  - Flags alerts when latest quote is >10% above history
- `D. VA/VE Consolidation`
  - Checks for >=95% similar parts
  - Surfaces consolidation opportunity when similar part is cheaper

## Data Used

The app reads these files from `hoth-demo/data/`:

- `Copy of supplier_orders.csv`
  - Core purchasing and delivery execution data
  - Key fields: `order_id`, `supplier_name`, `part_number`, `part_description`, `promised_date`, `actual_delivery_date`, `quantity`, `unit_price`
- `Copy of quality_inspections.csv`
  - Inspection outcomes linked by `order_id`
  - Key fields: `parts_inspected`, `parts_rejected`, `rejection_reason`
- `Copy of rfq_responses.csv`
  - RFQ quote responses used for price benchmarking
  - Key fields: `part_description`, `quote_date`, `quoted_price`, `supplier_name`
- `mock_drawer_metadata.csv`
  - Simulated geometric metadata
  - Key fields: `part_number`, `part_description`, `geometry_type`, `complexity_score`
- `mock_drawer_similarity.csv`
  - Simulated geometric similarity mappings
  - Key fields: `source_part_number`, `similar_part_number`, `similarity_score`

## Preprocessing and Joins

`app.py` performs the following transformations:

- Supplier normalization (`supplier_norm`) using case normalization and suffix removal (`INC`, `LLC`, etc.)
- Delivery latency calculation: `days_late = actual_delivery_date - promised_date`
- Master warehouse assembly:
  - `orders` + `drawer metadata` on `part_number` and `part_description`
  - merged with `quality` on `order_id`
- Computed rejection rate with zero-safe handling

## Run Locally

From the repository root:

```bash
source .venv/bin/activate
pip install -r hoth-demo/requirements.txt
streamlit run hoth-demo/app.py
```

Then open the local Streamlit URL (usually `http://localhost:8501`).
