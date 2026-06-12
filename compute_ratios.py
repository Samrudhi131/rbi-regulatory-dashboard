"""
RBI Regulatory Dashboard — Ratio Computation Engine
=====================================================
Computes Basel III and RBI-mandated KPIs from raw financial inputs
and persists results for Power BI consumption.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import logging
import argparse
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DB_URL", "mysql+mysqlconnector://root:password@localhost/rbi_compliance")


def safe_div(numerator, denominator, scale=100.0):
    """Division guard — returns None if denominator is zero or None."""
    if not denominator or float(denominator) == 0:
        return None
    return round(float(numerator or 0) / float(denominator) * scale, 3)


def compute_ratios(row: pd.Series) -> dict:
    """
    Compute all regulatory ratios for a single reporting unit / period.

    Basel III definitions (RBI guidelines):
    ─────────────────────────────────────────────────────────────────────
    CAR   = (Tier 1 + Tier 2 Capital) / Risk Weighted Assets  × 100
    CET1  = CET1 Capital / Risk Weighted Assets               × 100
    LCR   = HQLA / Net Cash Outflows (30-day stressed)        × 100
    NSFR  = Available Stable Funding / Required Stable Funding × 100

    RBI Asset Quality:
    ─────────────────────────────────────────────────────────────────────
    Gross NPA %  = Gross NPA / Gross Advances                 × 100
    Net NPA %    = Net NPA   / (Gross Advances - Provisions)  × 100
    PCR          = Provisions / Gross NPA                     × 100

    Profitability:
    ─────────────────────────────────────────────────────────────────────
    NIM = Net Interest Income / Average Earning Assets         × 100
    ROA = Net Profit          / Average Total Assets           × 100
    """
    net_advances = (row.get("gross_advances", 0) or 0) - (row.get("provisions", 0) or 0)

    return {
        "report_date":     row["report_date"],
        "period_label":    row["period_label"],
        "business_unit":   row["business_unit"],

        # Basel III — Capital
        "car_ratio":  safe_div(row["total_capital"],    row["risk_weighted_assets"]),
        "cet1_ratio": safe_div(row["cet1_capital"],     row["risk_weighted_assets"]),

        # Basel III — Liquidity
        "lcr_ratio":  safe_div(row["hqla"],                      row["net_cash_outflows"]),
        "nsfr_ratio": safe_div(row["available_stable_funding"],  row["required_stable_funding"]),

        # Asset Quality
        "gnpa_ratio":     safe_div(row["gross_npa"],  row["gross_advances"]),
        "net_npa_ratio":  safe_div(row["net_npa"],    net_advances if net_advances > 0 else None),
        "pcr_ratio":      safe_div(row["provisions"], row["gross_npa"]),

        # Profitability
        "nim_ratio": safe_div(row["net_interest_income"], row["average_earning_assets"]),
        "roa_ratio": safe_div(row["net_profit"],          row["average_total_assets"]),
    }


def run(period_label: str):
    engine = create_engine(DB_URL)

    # Load inputs for the specified period
    query = "SELECT * FROM regulatory_inputs WHERE period_label = :period"
    with engine.connect() as conn:
        inputs_df = pd.read_sql(text(query), conn, params={"period": period_label})

    if inputs_df.empty:
        logger.warning(f"No regulatory inputs found for period: {period_label}")
        return

    logger.info(f"Computing KPIs for {len(inputs_df)} business units — period: {period_label}")

    # Compute ratios
    results = [compute_ratios(row) for _, row in inputs_df.iterrows()]
    results_df = pd.DataFrame(results)

    # Persist to kpi_results
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM kpi_results WHERE period_label = :period"),
            {"period": period_label}
        )
        conn.commit()

    results_df["computed_at"] = datetime.now()
    results_df.to_sql("kpi_results", engine, if_exists="append", index=False, method="multi")

    logger.info(f"KPIs computed and saved for period {period_label}")

    # Print summary
    logger.info("\n── KPI Summary ──────────────────────────────────────────")
    display_cols = ["business_unit", "car_ratio", "cet1_ratio", "lcr_ratio",
                    "gnpa_ratio", "net_npa_ratio", "pcr_ratio"]
    logger.info("\n" + results_df[display_cols].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", required=True, help="e.g. 2024-Q1")
    args = parser.parse_args()
    run(args.period)
