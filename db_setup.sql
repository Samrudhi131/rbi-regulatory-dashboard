-- ============================================================
-- RBI Regulatory Dashboard — Database Schema
-- Basel III + RBI KPI computation tables
-- ============================================================

CREATE DATABASE IF NOT EXISTS rbi_compliance;
USE rbi_compliance;

-- Bank Financial Data (input to ratio calculations)
CREATE TABLE regulatory_inputs (
    input_id            INT             AUTO_INCREMENT PRIMARY KEY,
    report_date         DATE            NOT NULL,
    period_label        VARCHAR(10)     NOT NULL,   -- e.g. 2024-Q1
    business_unit       VARCHAR(20)     NOT NULL,   -- BU or 'CONSOLIDATED'

    -- Capital Components (INR Crore)
    tier1_capital       DECIMAL(15,2),
    tier2_capital       DECIMAL(15,2),
    cet1_capital        DECIMAL(15,2),
    total_capital       DECIMAL(15,2),
    risk_weighted_assets DECIMAL(15,2),

    -- Liquidity
    hqla                DECIMAL(15,2),  -- High Quality Liquid Assets
    net_cash_outflows   DECIMAL(15,2),  -- Next 30 days
    available_stable_funding DECIMAL(15,2),
    required_stable_funding  DECIMAL(15,2),

    -- NPA (Non-Performing Assets)
    gross_advances      DECIMAL(15,2),
    gross_npa           DECIMAL(15,2),
    net_npa             DECIMAL(15,2),
    provisions          DECIMAL(15,2),

    -- Profitability
    net_interest_income DECIMAL(15,2),
    average_earning_assets DECIMAL(15,2),
    net_profit          DECIMAL(15,2),
    average_total_assets   DECIMAL(15,2),

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_period_bu (period_label, business_unit)
);

-- Computed KPI Results
CREATE TABLE kpi_results (
    kpi_id              INT             AUTO_INCREMENT PRIMARY KEY,
    report_date         DATE            NOT NULL,
    period_label        VARCHAR(10)     NOT NULL,
    business_unit       VARCHAR(20)     NOT NULL,

    -- Basel III Ratios (%)
    car_ratio           DECIMAL(6,3),   -- Capital Adequacy Ratio
    cet1_ratio          DECIMAL(6,3),   -- CET1 Ratio
    lcr_ratio           DECIMAL(6,3),   -- Liquidity Coverage Ratio
    nsfr_ratio          DECIMAL(6,3),   -- Net Stable Funding Ratio

    -- RBI Asset Quality KPIs (%)
    gnpa_ratio          DECIMAL(6,3),   -- Gross NPA %
    net_npa_ratio       DECIMAL(6,3),   -- Net NPA %
    pcr_ratio           DECIMAL(6,3),   -- Provision Coverage Ratio

    -- Profitability KPIs (%)
    nim_ratio           DECIMAL(6,3),   -- Net Interest Margin
    roa_ratio           DECIMAL(6,3),   -- Return on Assets

    computed_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_period (period_label),
    KEY idx_bu (business_unit)
);

-- Alert Log
CREATE TABLE alert_log (
    alert_id            INT             AUTO_INCREMENT PRIMARY KEY,
    alert_timestamp     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    period_label        VARCHAR(10),
    business_unit       VARCHAR(20),
    kpi_name            VARCHAR(20),
    kpi_value           DECIMAL(8,3),
    threshold_value     DECIMAL(8,3),
    breach_type         ENUM('BREACH','WARNING','NEAR_BREACH'),
    regulatory_minimum  DECIMAL(8,3),
    alert_message       TEXT,
    status              ENUM('OPEN','ACKNOWLEDGED','RESOLVED') DEFAULT 'OPEN'
);

SELECT 'Schema created successfully' AS status;
