from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).resolve().parent / "data"


def normalize_supplier(name: str) -> str:
    if pd.isna(name):
        return ""
    cleaned = str(name).upper().strip()
    cleaned = re.sub(r"\b(INC|LLC|CO|COMPANY|CORP|CORPORATION)\b", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" ,.-")


@st.cache_data
def load_data() -> dict[str, pd.DataFrame]:
    orders = pd.read_csv(DATA_DIR / "Copy of supplier_orders.csv")
    quality = pd.read_csv(DATA_DIR / "Copy of quality_inspections.csv")
    rfq = pd.read_csv(DATA_DIR / "Copy of rfq_responses.csv")
    drawer_meta = pd.read_csv(DATA_DIR / "mock_drawer_metadata.csv")
    drawer_sim = pd.read_csv(DATA_DIR / "mock_drawer_similarity.csv")

    orders["supplier_norm"] = orders["supplier_name"].apply(normalize_supplier)
    rfq["supplier_norm"] = rfq["supplier_name"].apply(normalize_supplier)

    orders["promised_date"] = pd.to_datetime(orders["promised_date"], errors="coerce")
    orders["actual_delivery_date"] = pd.to_datetime(orders["actual_delivery_date"], errors="coerce")
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders["days_late"] = (orders["actual_delivery_date"] - orders["promised_date"]).dt.days
    orders["days_late"] = orders["days_late"].fillna(0)

    quality["inspection_date"] = pd.to_datetime(quality["inspection_date"], errors="coerce")
    rfq["quote_date"] = pd.to_datetime(rfq["quote_date"], errors="coerce")

    master = orders.merge(drawer_meta, on=["part_number", "part_description"], how="left")
    master = master.merge(quality, on="order_id", how="left")
    master["parts_rejected"] = master["parts_rejected"].fillna(0)
    master["parts_inspected"] = master["parts_inspected"].fillna(0)
    master["rejection_rate"] = (
        master["parts_rejected"] / master["parts_inspected"].replace(0, pd.NA)
    ).fillna(0)

    return {
        "orders": orders,
        "quality": quality,
        "rfq": rfq,
        "drawer_meta": drawer_meta,
        "drawer_sim": drawer_sim,
        "master": master,
    }


def reliability_status(avg_days_late: float, rejection_rate: float) -> str:
    if avg_days_late > 10 or rejection_rate > 0.05:
        return "High Risk"
    if avg_days_late > 5 or rejection_rate > 0.02:
        return "Watch"
    return "Stable"


def quote_benchmark(part_description: str, master_part: pd.DataFrame, rfq: pd.DataFrame) -> tuple[float | None, float | None, float | None]:
    historical_avg = None
    latest_quote = None
    variance = None

    if not master_part.empty:
        historical_avg = float(master_part["unit_price"].mean())

    rfq_part = rfq[rfq["part_description"].str.lower() == part_description.lower()].copy()
    if not rfq_part.empty:
        rfq_part = rfq_part.sort_values("quote_date")
        latest_quote = float(rfq_part.iloc[-1]["quoted_price"])

    if historical_avg and latest_quote:
        variance = ((latest_quote - historical_avg) / historical_avg) * 100

    return historical_avg, latest_quote, variance


def main() -> None:
    st.set_page_config(page_title="Hoth Industries Control Tower", layout="wide")
    st.title("Hoth Industries: Risk Alerts Dashboard")
    st.caption("Unified quality, sourcing, and geometric intelligence for part-level decisions.")

    data = load_data()
    orders = data["orders"]
    master = data["master"]
    rfq = data["rfq"]
    quality = data["quality"]
    drawer_meta = data["drawer_meta"]
    drawer_sim = data["drawer_sim"]

    with st.sidebar:
        st.header("About the Data")
        st.markdown("""
- Unified Warehouse: Merges Hoth execution history (PO/Quality/RFQ) with a simulated geometric intelligence layer.
- Complexity Proxy (1–10): A simplified stand-in for the CADDi Drawer API’s high-dimensional feature extraction (e.g., hole counts, tolerances, and setups). Used here to investigate the link between design intricacy and sourcing performance.
- Similarity Logic: Emulates CADDi’s Vector Embeddings. Parts with a Match Score $\\ge 0.95$ are flagged as "Geometric Twins" for VA/VE and volume consolidation.
- Producibility Loop: Maps historical quality failures to specific geometric profiles to simulate a proactive risk-warning system.
- Quote Benchmarking: Replaces price "prediction" with a complexity-aware comparison between new RFQ responses and historical purchase data.
- Try these parts for high-similarity analysis (at least one match with score >= 0.95): FINS-7715 (max: 0.98), FINS-7725 (max: 0.98), HX-5512 (max: 0.99), HX-5515 (max: 0.98), HX-5525 (max: 0.98), HX-5530 (max: 0.95).
""")

    overall_rej = (master["parts_rejected"].sum() / master["parts_inspected"].replace(0, pd.NA).sum()) if master["parts_inspected"].sum() else 0
    late_share = (master["days_late"] > 10).mean() if len(master) else 0

    with st.container():
        st.subheader("Global Supply Chain Health")
        g1, g2 = st.columns(2)
        g1.metric("Overall Rejection Rate", f"{overall_rej:.2%}")
        g2.metric("Orders >10 Days Late", f"{late_share:.1%}")
        st.divider()

    option_df = (
        orders[["part_number", "part_description"]]
        .dropna()
        .drop_duplicates()
        .sort_values(["part_description", "part_number"])
    )
    option_df["label"] = option_df.apply(
        lambda r: f"{r['part_description']} ({r['part_number']})",
        axis=1,
    )
    selected_label = st.selectbox(
        "Search Part Description",
        options=option_df["label"].tolist(),
        index=None,
        placeholder="Type or select a part description",
    )

    if not selected_label:
        st.info("Select a part description to run the full analysis.")
        return

    selected_row = option_df[option_df["label"] == selected_label].iloc[0]
    selected_part_number = str(selected_row["part_number"])
    selected_description = str(selected_row["part_description"])

    selected_orders = orders[orders["part_number"] == selected_part_number].copy()

    if selected_orders.empty:
        st.warning("Part not found in CADDi Archive.")
        return

    part_master = master[master["part_number"] == selected_part_number].copy()

    st.header(selected_part_number)
    st.subheader(selected_description)

    hist_avg_price = float(part_master["unit_price"].mean()) if not part_master.empty else 0.0
    inspected = part_master["parts_inspected"].sum()
    rejected = part_master["parts_rejected"].sum()
    hist_rej_rate = (rejected / inspected) if inspected else 0.0
    avg_days_late = float(part_master["days_late"].mean()) if not part_master.empty else 0.0
    status = reliability_status(avg_days_late=avg_days_late, rejection_rate=hist_rej_rate)

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Purchase Price (Historical)", f"${hist_avg_price:,.2f}")
    c2.metric("Historical Rejection Rate", f"{hist_rej_rate:.2%}")
    c3.metric("Reliability Status", status)

    st.divider()

    tab_a, tab_b, tab_c, tab_d = st.tabs([
        "A. Sourcing Performance",
        "B. Producibility Advisor",
        "C. Quote Benchmarking",
        "D. VA/VE Consolidation",
    ])

    with tab_a:
        st.subheader("Supplier History for this Part")
        supplier_hist = (
            part_master.groupby(["supplier_norm", "supplier_name"], as_index=False)
            .agg(
                total_qty_ordered=("quantity", "sum"),
                total_rejected=("parts_rejected", "sum"),
                total_inspected=("parts_inspected", "sum"),
                avg_days_late=("days_late", "mean"),
            )
        )
        supplier_hist["avg_rejection_rate"] = (
            supplier_hist["total_rejected"] / supplier_hist["total_inspected"].replace(0, pd.NA)
        ).fillna(0)
        supplier_hist["risk_flag"] = supplier_hist.apply(
            lambda r: "HIGH RISK" if r["avg_days_late"] > 10 or r["avg_rejection_rate"] > 0.05 else "OK",
            axis=1,
        )

        view = supplier_hist[["supplier_name", "total_qty_ordered", "avg_rejection_rate", "avg_days_late", "risk_flag"]].copy()
        view.columns = [
            "Supplier Name",
            "Total Qty Ordered",
            "Avg Rejection Rate",
            "Avg Days Late",
            "Status",
        ]

        def highlight_risk(row: pd.Series) -> list[str]:
            is_risk = row["Status"] == "HIGH RISK"
            style = "background-color: #ffdddd; color: #900; font-weight: 600;" if is_risk else ""
            return [style] * len(row)

        st.dataframe(
            view.style.format({"Avg Rejection Rate": "{:.2%}", "Avg Days Late": "{:.1f}"}).apply(highlight_risk, axis=1),
            use_container_width=True,
        )

    with tab_b:
        st.subheader("Geometric Similarity and Producibility Risk")
        sim_rows = drawer_sim[drawer_sim["source_part_number"] == selected_part_number].copy()
        if sim_rows.empty:
            st.info("No geometric matches found for this part in CADDi similarity data.")
        else:
            top_match = sim_rows.sort_values("similarity_score", ascending=False).iloc[0]
            match_part = str(top_match["similar_part_number"])
            match_score = float(top_match["similarity_score"])
            match_desc_series = drawer_meta[drawer_meta["part_number"] == match_part]["part_description"]
            if match_desc_series.empty:
                match_orders_for_desc = orders[orders["part_number"] == match_part]["part_description"].dropna()
                match_desc = match_orders_for_desc.mode().iloc[0] if not match_orders_for_desc.empty else "Description unavailable"
            else:
                match_desc = str(match_desc_series.iloc[0])
            st.write(f"**Geometric Match:** `{match_part}` - {match_desc} ({match_score:.0%} Similar)")

            match_orders = orders[orders["part_number"] == match_part]
            if match_orders.empty:
                st.success("No production quality history found for the matched geometry.")
            else:
                match_order_ids = set(match_orders["order_id"].tolist())
                quality_match = quality[quality["order_id"].isin(match_order_ids)].copy()
                failed = quality_match[quality_match["parts_rejected"] > 0]
                if failed.empty:
                    st.success("Matched geometry shows no recorded rejection history.")
                else:
                    top_reasons = failed["rejection_reason"].fillna("Unspecified").value_counts().head(3)
                    reason_lines = "\n".join([f"- {reason}: {count}" for reason, count in top_reasons.items()])
                    st.error(
                        "WARNING: Similar geometry previously had quality failures.\n\n"
                        f"Top 3 rejection reasons (inspection count):\n{reason_lines}"
                    )

    with tab_c:
        st.subheader("Latest Quote vs Historical Price")
        historical_avg, latest_quote, variance = quote_benchmark(
            part_description=selected_description,
            master_part=part_master,
            rfq=rfq,
        )

        q1, q2, q3 = st.columns(3)
        q1.metric("Historical Average", f"${historical_avg:,.2f}" if historical_avg is not None else "N/A")
        q2.metric("Latest Quote", f"${latest_quote:,.2f}" if latest_quote is not None else "N/A")
        q3.metric("Variance", f"{variance:.1f}%" if variance is not None else "N/A")

        if variance is not None and variance > 10:
            st.warning("Price Alert: Latest quote is more than 10% above historical average.")
        elif variance is not None:
            st.success("Latest quote is within acceptable benchmark range.")
        else:
            st.info("Insufficient data to compute quote benchmark for this part.")

    with tab_d:
        st.subheader("Value Analysis / Value Engineering Opportunity")
        candidates = drawer_sim[
            (drawer_sim["source_part_number"] == selected_part_number)
            & (drawer_sim["similarity_score"] >= 0.95)
            & (drawer_sim["similar_part_number"] != selected_part_number)
        ].copy()

        if candidates.empty:
            st.info("No >=95% similar part found for consolidation analysis.")
        else:
            best_candidate = candidates.sort_values("similarity_score", ascending=False).iloc[0]
            other_part = str(best_candidate["similar_part_number"])
            current_avg = float(part_master["unit_price"].mean()) if not part_master.empty else None
            other_avg_series = master[master["part_number"] == other_part]["unit_price"]
            other_avg = float(other_avg_series.mean()) if not other_avg_series.empty else None

            st.write(f"Closest high-similarity part: `{other_part}` ({float(best_candidate['similarity_score']):.0%} similar)")

            if current_avg and other_avg:
                price_delta = ((current_avg - other_avg) / current_avg) * 100
                if price_delta > 0:
                    st.success(
                        f"Cost Saving Opportunity: This part is 95%+ identical to {other_part}, which is {price_delta:.1f}% cheaper. Consider design consolidation."
                    )
                else:
                    st.info("No cost-saving upside detected from current 95%+ similar candidate.")
            else:
                st.info("Not enough historical price data to evaluate consolidation savings.")


if __name__ == "__main__":
    main()
