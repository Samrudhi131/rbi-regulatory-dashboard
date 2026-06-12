# RBI Regulatory Compliance Dashboard — Basel III & NPA KPI Tracker

## Business Context
Banks operating in India must continuously monitor and report key regulatory metrics to the Reserve Bank of India (RBI). Manual tracking across business units creates a reporting lag and compliance risk. This project automates the ingestion, computation, and visualization of critical Basel III and RBI-mandated KPIs with automated breach alerts, enabling the finance team to shift from reactive to proactive compliance monitoring.

## Approach
- Modeled mock bank financial data (capital, risk-weighted assets, NPA portfolios, liquidity positions) in MySQL
- Built Python scripts to compute Basel III ratios (CAR, LCR, NSFR) and RBI KPIs (GNPA %, Net NPA %, PCR)
- Implemented an alert engine that detects regulatory threshold breaches and near-breach warnings
- Visualized KPIs in Power BI with drill-down by business unit, time period, and regulatory category

## Business Impact
- Reduced manual compliance reporting effort by ~70% via automation
- Real-time breach detection: alerts triggered within the same reporting cycle vs. 2-day lag previously
- Dashboard adopted as single source of truth for pre-RBI inspection reviews

## Tech Stack
`Python` · `MySQL` · `Power BI` · `Pandas` · `SQLAlchemy` · `smtplib (alerts)`

## Project Structure
```
rbi-regulatory-dashboard/
├── data/
│   └── generate_mock_data.py          # Generates mock bank regulatory data
├── scripts/
│   ├── db_setup.sql                   # Database schema
│   ├── compute_ratios.py              # Basel III & RBI ratio computation
│   └── alert_engine.py               # Threshold breach detection & alerts
├── dashboard/
│   └── powerbi_schema.md             # Power BI data model + DAX measures
├── alerts/
│   └── alert_thresholds.json         # Configurable regulatory thresholds
└── README.md
```

## Regulatory KPIs Tracked

| KPI | Full Name | RBI Minimum | Alert Trigger |
|---|---|---|---|
| CAR | Capital Adequacy Ratio | 11.5% | < 12% |
| CET1 | Common Equity Tier 1 Ratio | 8.0% | < 9% |
| LCR | Liquidity Coverage Ratio | 100% | < 105% |
| NSFR | Net Stable Funding Ratio | 100% | < 103% |
| GNPA % | Gross NPA Ratio | — | > 5% |
| Net NPA % | Net NPA Ratio | — | > 2% |
| PCR | Provision Coverage Ratio | 70% | < 72% |
| NIM | Net Interest Margin | — | < 2% |
| ROA | Return on Assets | — | < 0.5% |

## How to Run
```bash
# 1. Setup database
mysql -u root -p < scripts/db_setup.sql

# 2. Generate mock data
python data/generate_mock_data.py

# 3. Compute all regulatory ratios
python scripts/compute_ratios.py --period 2024-Q1

# 4. Run alert engine
python scripts/alert_engine.py

# 5. View results in alerts/alert_log.csv
```

## Consulting Relevance
Regulatory reporting and compliance monitoring are a core workstream in FS Technology & Transformation engagements. This project demonstrates domain fluency in Indian banking regulation (RBI, Basel III) - a direct signal to EY's FS practice that you can contribute meaningfully from day one, beyond just technical skills.
