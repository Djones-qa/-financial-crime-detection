"""
Financial crime detection engine —
behavioral analysis, anomaly detection, and risk scoring.
"""
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta


def calculate_velocity_score(transactions_df: pd.DataFrame,
                              window_hours: int = 1) -> pd.DataFrame:
    """
    Detect velocity abuse — too many transactions in short time window.
    High velocity = potential fraud or bot activity.
    """
    df = transactions_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["account_id", "timestamp"])

    velocity = df.groupby("account_id").apply(
        lambda x: x.set_index("timestamp").resample("1h").size().max()
    ).reset_index()
    velocity.columns = ["account_id", "max_txn_per_hour"]
    velocity["velocity_flag"] = velocity["max_txn_per_hour"] > 5
    return velocity


def detect_geographic_anomalies(transactions_df: pd.DataFrame,
                                 accounts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect transactions from unexpected countries.
    Country mismatch between account and transaction = red flag.
    """
    merged = transactions_df.merge(
        accounts_df[["account_id", "country"]],
        on="account_id", suffixes=("_txn", "_account")
    )
    merged["geo_mismatch"] = merged["country_txn"] != merged["country_account"]
    merged["ip_mismatch"] = merged["ip_country"] != merged["country_txn"]
    merged["geo_risk_score"] = (
        merged["geo_mismatch"].astype(int) * 0.6 +
        merged["ip_mismatch"].astype(int) * 0.4
    ).round(2)
    return merged[["transaction_id", "account_id", "amount",
                   "country_txn", "country_account",
                   "geo_mismatch", "ip_mismatch", "geo_risk_score"]]


def detect_amount_anomalies(transactions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect statistically unusual transaction amounts using Z-score.
    Amounts > 3 standard deviations from mean = anomaly.
    """
    df = transactions_df.copy()
    account_stats = df.groupby("account_id")["amount"].agg(
        ["mean", "std"]).reset_index()
    account_stats.columns = ["account_id", "avg_amount", "std_amount"]
    account_stats["std_amount"] = account_stats["std_amount"].fillna(0)

    merged = df.merge(account_stats, on="account_id")
    merged["z_score"] = np.where(
        merged["std_amount"] > 0,
        (merged["amount"] - merged["avg_amount"]) / merged["std_amount"],
        0
    ).round(3)
    merged["amount_anomaly"] = merged["z_score"].abs() > 3
    return merged[["transaction_id", "account_id", "amount",
                   "avg_amount", "z_score", "amount_anomaly"]]


def detect_structuring(transactions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect structuring (smurfing) — transactions just below reporting threshold.
    Amounts between $8000-$9999 are suspicious — avoiding $10K reporting.
    """
    df = transactions_df.copy()
    df["is_structured"] = df["amount"].between(8000, 9999)
    structuring = df.groupby("account_id").agg(
        structured_count=("is_structured", "sum"),
        total_structured_amount=("amount", lambda x:
                                 x[df.loc[x.index, "is_structured"]].sum())
    ).reset_index()
    structuring["structuring_flag"] = structuring["structured_count"] >= 2
    return structuring


def calculate_risk_score(transactions_df: pd.DataFrame,
                          accounts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate composite risk score per account
    combining multiple detection signals.
    """
    velocity = calculate_velocity_score(transactions_df)
    geo = detect_geographic_anomalies(transactions_df, accounts_df)
    amounts = detect_amount_anomalies(transactions_df)
    structuring = detect_structuring(transactions_df)

    # Aggregate geo risk per account
    geo_risk = geo.groupby("account_id")["geo_risk_score"].max().reset_index()

    # Aggregate amount anomalies per account
    amount_risk = amounts.groupby("account_id")["amount_anomaly"].sum().reset_index()
    amount_risk.columns = ["account_id", "anomaly_count"]

    # Build composite score
    risk = accounts_df[["account_id", "name", "country"]].copy()
    risk = risk.merge(velocity[["account_id", "velocity_flag"]], on="account_id", how="left")
    risk = risk.merge(geo_risk, on="account_id", how="left")
    risk = risk.merge(amount_risk, on="account_id", how="left")
    risk = risk.merge(structuring[["account_id", "structuring_flag"]], on="account_id", how="left")

    risk = risk.fillna(0)
    risk["composite_risk_score"] = (
        risk["velocity_flag"].astype(float) * 0.25 +
        risk["geo_risk_score"].astype(float) * 0.30 +
        (risk["anomaly_count"] / 10).clip(0, 1) * 0.25 +
        risk["structuring_flag"].astype(float) * 0.20
    ).round(3)

    risk["risk_level"] = pd.cut(
        risk["composite_risk_score"],
        bins=[-0.01, 0.15, 0.30, 0.75, 1.01],
        labels=["Low", "Medium", "High", "Critical"]
    )
    return risk.sort_values("composite_risk_score", ascending=False)


def run_sql_investigations(db_path: str = "data/financial_crimes.db") -> dict:
    """Run SQL-based fraud investigation queries."""
    conn = sqlite3.connect(db_path)
    queries = {
        "fraud_by_type": """
            SELECT fraud_type,
                   COUNT(*) as count,
                   ROUND(AVG(amount), 2) as avg_amount,
                   ROUND(SUM(amount), 2) as total_amount
            FROM transactions
            WHERE is_fraud = 1
            GROUP BY fraud_type
            ORDER BY count DESC
        """,
        "high_risk_accounts": """
            SELECT a.account_id, a.name, a.country,
                   COUNT(t.transaction_id) as txn_count,
                   ROUND(SUM(t.amount), 2) as total_amount,
                   SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count
            FROM accounts a
            JOIN transactions t ON a.account_id = t.account_id
            GROUP BY a.account_id
            HAVING fraud_count > 0
            ORDER BY fraud_count DESC
            LIMIT 10
        """,
        "fraud_by_country": """
            SELECT country,
                   COUNT(*) as total_txns,
                   SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_txns,
                   ROUND(100.0 * SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END)
                         / COUNT(*), 2) as fraud_rate_pct
            FROM transactions
            GROUP BY country
            ORDER BY fraud_rate_pct DESC
        """,
        "fraud_by_hour": """
            SELECT hour_of_day,
                   COUNT(*) as total_txns,
                   SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_txns,
                   ROUND(AVG(amount), 2) as avg_amount
            FROM transactions
            GROUP BY hour_of_day
            ORDER BY hour_of_day
        """,
        "large_transactions": """
            SELECT t.transaction_id, a.name, a.country,
                   t.amount, t.merchant_category,
                   t.timestamp, t.is_fraud
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE t.amount > 5000
            ORDER BY t.amount DESC
            LIMIT 10
        """,
        "structuring_suspects": """
            SELECT a.name, a.country,
                   COUNT(*) as structured_count,
                   ROUND(SUM(t.amount), 2) as total_structured
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE t.amount BETWEEN 8000 AND 9999
            GROUP BY t.account_id
            HAVING structured_count >= 2
            ORDER BY structured_count DESC
        """,
    }
    results = {}
    for name, query in queries.items():
        results[name] = pd.read_sql_query(query, conn)
    conn.close()
    return results
