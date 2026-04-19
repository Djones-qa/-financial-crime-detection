"""
Generates realistic financial transaction data
with embedded fraud patterns for detection analysis.
"""
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import sqlite3
import os

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

COUNTRIES = ["US", "UK", "CA", "AU", "DE", "FR", "JP", "BR", "NG", "RU"]
MERCHANT_CATEGORIES = [
    "Grocery", "Electronics", "Gas Station", "Restaurant",
    "Online Shopping", "Travel", "ATM", "Pharmacy", "Hotel", "Casino"
]
FRAUD_PATTERNS = [
    "velocity_abuse", "geographic_anomaly",
    "account_takeover", "money_laundering", "coordinated_fraud"
]


def generate_accounts(num_accounts: int = 500) -> pd.DataFrame:
    """Generate realistic customer account data."""
    records = []
    for i in range(1, num_accounts + 1):
        country = random.choice(COUNTRIES[:5])
        records.append({
            "account_id": i,
            "name": fake.name(),
            "email": fake.unique.email(),
            "country": country,
            "account_age_days": random.randint(30, 3650),
            "credit_limit": random.choice([1000, 2500, 5000, 10000, 25000]),
            "risk_score": round(random.uniform(0, 1), 3),
            "is_flagged": False,
            "created_date": (datetime.now() - timedelta(
                days=random.randint(30, 3650))).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(records)


def generate_transactions(accounts_df: pd.DataFrame,
                          num_transactions: int = 5000) -> pd.DataFrame:
    """Generate transaction data with embedded fraud patterns."""
    records = []
    base_date = datetime.now() - timedelta(days=90)

    for i in range(1, num_transactions + 1):
        account = accounts_df.sample(1).iloc[0]
        is_fraud = random.random() < 0.08  # 8% fraud rate
        fraud_type = random.choice(FRAUD_PATTERNS) if is_fraud else None

        # Base transaction
        amount = round(random.uniform(1, 500), 2)
        country = account["country"]
        merchant = random.choice(MERCHANT_CATEGORIES)
        timestamp = base_date + timedelta(
            seconds=random.randint(0, 90 * 24 * 3600))

        # Inject fraud patterns
        if is_fraud:
            if fraud_type == "velocity_abuse":
                amount = round(random.uniform(1, 50), 2)
            elif fraud_type == "geographic_anomaly":
                country = random.choice([c for c in COUNTRIES
                                        if c != account["country"]])
                amount = round(random.uniform(200, 2000), 2)
            elif fraud_type == "account_takeover":
                amount = round(random.uniform(500, 5000), 2)
                merchant = "Online Shopping"
            elif fraud_type == "money_laundering":
                amount = round(random.uniform(8000, 9999), 2)
            elif fraud_type == "coordinated_fraud":
                amount = round(random.uniform(100, 300), 2)

        records.append({
            "transaction_id": f"TXN{i:06d}",
            "account_id": int(account["account_id"]),
            "amount": amount,
            "currency": "USD",
            "merchant_category": merchant,
            "country": country,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "hour_of_day": timestamp.hour,
            "day_of_week": timestamp.weekday(),
            "is_fraud": is_fraud,
            "fraud_type": fraud_type if is_fraud else "none",
            "device": random.choice(["mobile", "desktop", "tablet"]),
            "ip_country": country if not is_fraud else random.choice(COUNTRIES),
            "declined": random.random() < 0.03,
        })
    return pd.DataFrame(records)


def generate_fraud_network(num_nodes: int = 50) -> pd.DataFrame:
    """Generate coordinated fraud network data."""
    records = []
    for i in range(1, num_nodes + 1):
        records.append({
            "node_id": i,
            "account_id": random.randint(1, 500),
            "ip_address": f"192.168.{random.randint(1,10)}."
                         f"{random.randint(1,255)}",
            "device_fingerprint": fake.uuid4()[:16],
            "transactions_count": random.randint(5, 50),
            "total_amount": round(random.uniform(100, 10000), 2),
            "network_cluster": random.randint(1, 5),
            "first_seen": (datetime.now() - timedelta(
                days=random.randint(1, 30))).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(records)


def save_to_sqlite(accounts_df, transactions_df,
                   network_df, db_path="data/financial_crimes.db"):
    """Save all datasets to SQLite database."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    accounts_df.to_sql("accounts", conn, if_exists="replace", index=False)
    transactions_df.to_sql("transactions", conn,
                           if_exists="replace", index=False)
    network_df.to_sql("fraud_network", conn, if_exists="replace", index=False)
    conn.close()
    return db_path


def save_to_csv(accounts_df, transactions_df, network_df):
    """Save all datasets to CSV files."""
    os.makedirs("data", exist_ok=True)
    accounts_df.to_csv("data/accounts.csv", index=False)
    transactions_df.to_csv("data/transactions.csv", index=False)
    network_df.to_csv("data/fraud_network.csv", index=False)
    print("CSVs saved!")
