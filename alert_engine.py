"""
RBI Regulatory Dashboard — Alert Engine
========================================
Detects threshold breaches in computed KPIs and logs alerts.
Configurable thresholds loaded from alert_thresholds.json.
"""

import pandas as pd
import json
from sqlalchemy import create_engine, text
from datetime import datetime
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

DB_URL          = os.getenv("DB_URL", "mysql+mysqlconnector://root:password@localhost/rbi_compliance")
THRESHOLDS_FILE = os.path.join(os.path.dirname(__file__), "..", "alerts", "alert_thresholds.json")


def load_thresholds() -> dict:
    with open(THRESHOLDS_FILE) as f:
        return json.load(f)


def evaluate_kpi(kpi_name: str, value: float, thresholds: dict) -> tuple:
    """
    Returns (breach_type, message) or (None, None) if no issue.
    breach_type: 'BREACH' | 'WARNING' | 'NEAR_BREACH'
    """
    if value is None:
        return None, None

    config = thresholds.get(kpi_name)
    if not config:
        return None, None

    direction = config["direction"]  # 'min' = must be above threshold; 'max' = must be below
    reg_min   = config.get("regulatory_minimum")
    breach_at = config["breach_threshold"]
    warn_at   = config["warning_threshold"]

    if direction == "min":
        if value < breach_at:
            breach_type = "BREACH" if (reg_min and value < reg_min) else "WARNING"
            return breach_type, (
                f"{kpi_name} at {value:.2f}% is BELOW {'regulatory minimum' if reg_min and value < reg_min else 'internal'} "
                f"threshold of {breach_at:.2f}%"
            )
        elif value < warn_at:
            return "NEAR_BREACH", (
                f"{kpi_name} at {value:.2f}% is approaching threshold of {breach_at:.2f}%"
            )
    elif direction == "max":
        if value > breach_at:
            return "BREACH", (
                f"{kpi_name} at {value:.2f}% EXCEEDS breach threshold of {breach_at:.2f}%"
            )
        elif value > warn_at:
            return "NEAR_BREACH", (
                f"{kpi_name} at {value:.2f}% approaching threshold of {breach_at:.2f}%"
            )

    return None, None


def run():
    engine     = create_engine(DB_URL)
    thresholds = load_thresholds()

    # Get latest KPI results
    with engine.connect() as conn:
        kpi_df = pd.read_sql(
            text("""
                SELECT * FROM kpi_results
                WHERE period_label = (SELECT MAX(period_label) FROM kpi_results)
            """),
            conn
        )

    if kpi_df.empty:
        logger.warning("No KPI results found. Run compute_ratios.py first.")
        return

    period = kpi_df["period_label"].iloc[0]
    logger.info(f"Running alert evaluation for period: {period}")

    kpi_columns = [
        "car_ratio", "cet1_ratio", "lcr_ratio", "nsfr_ratio",
        "gnpa_ratio", "net_npa_ratio", "pcr_ratio", "nim_ratio", "roa_ratio"
    ]

    alert_records = []
    alert_count   = {"BREACH": 0, "WARNING": 0, "NEAR_BREACH": 0}

    for _, row in kpi_df.iterrows():
        bu = row["business_unit"]
        for kpi_col in kpi_columns:
            value = row.get(kpi_col)
            if value is None:
                continue

            breach_type, message = evaluate_kpi(kpi_col, float(value), thresholds)

            if breach_type:
                config = thresholds.get(kpi_col, {})
                alert_records.append({
                    "alert_timestamp":   datetime.now(),
                    "period_label":      period,
                    "business_unit":     bu,
                    "kpi_name":          kpi_col,
                    "kpi_value":         value,
                    "threshold_value":   config.get("breach_threshold"),
                    "breach_type":       breach_type,
                    "regulatory_minimum": config.get("regulatory_minimum"),
                    "alert_message":     message,
                    "status":            "OPEN",
                })
                alert_count[breach_type] += 1
                log_fn = logger.error if breach_type == "BREACH" else logger.warning
                log_fn(f"  [{bu}] {breach_type}: {message}")

    if alert_records:
        alerts_df = pd.DataFrame(alert_records)
        alerts_df.to_sql("alert_log", engine, if_exists="append", index=False, method="multi")

        # Export to CSV
        os.makedirs(os.path.join(os.path.dirname(__file__), "..", "alerts"), exist_ok=True)
        alerts_df.to_csv(
            os.path.join(os.path.dirname(__file__), "..", "alerts", "alert_log.csv"),
            index=False
        )
    else:
        logger.info("  ✓ No threshold breaches detected")

    logger.info(
        f"\nAlert summary — BREACH: {alert_count['BREACH']} | "
        f"WARNING: {alert_count['WARNING']} | NEAR_BREACH: {alert_count['NEAR_BREACH']}"
    )


if __name__ == "__main__":
    run()
