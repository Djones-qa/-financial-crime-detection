"""
Financial crime detection visualizations.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os

sns.set_theme(style="darkgrid")
os.makedirs("visuals", exist_ok=True)

COLORS = {
    "red": "#E74C3C",
    "orange": "#F39C12",
    "blue": "#1B4F8A",
    "green": "#2ECC71",
    "gray": "#95A5A6",
    "dark": "#2C3E50",
}


def save(fig, name):
    path = f"visuals/{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_fraud_distribution(transactions_df):
    """Pie chart — fraud vs legitimate transactions."""
    fraud_count = transactions_df["is_fraud"].sum()
    legit_count = len(transactions_df) - fraud_count
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.pie([legit_count, fraud_count],
           labels=["Legitimate", "Fraudulent"],
           colors=[COLORS["green"], COLORS["red"]],
           autopct="%1.1f%%", startangle=90,
           wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax.set_title("Transaction Distribution — Fraud vs Legitimate",
                 fontsize=13, fontweight="bold", pad=20)
    return save(fig, "01_fraud_distribution")


def plot_fraud_by_type(transactions_df):
    """Bar chart — fraud count by fraud type."""
    fraud_df = transactions_df[transactions_df["is_fraud"] == True]
    type_counts = fraud_df["fraud_type"].value_counts()
    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(type_counts.index, type_counts.values,
                  color=COLORS["red"], alpha=0.85, edgecolor="white")
    for bar, val in zip(bars, type_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                str(val), ha="center", fontsize=10, fontweight="bold")
    ax.set_title("Fraud Cases by Type",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Fraud Type")
    ax.set_ylabel("Number of Cases")
    plt.xticks(rotation=20, ha="right")
    return save(fig, "02_fraud_by_type")


def plot_amount_distribution(transactions_df):
    """Histogram — transaction amount distribution."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    legit = transactions_df[transactions_df["is_fraud"] == False]["amount"]
    fraud = transactions_df[transactions_df["is_fraud"] == True]["amount"]
    axes[0].hist(legit, bins=50, color=COLORS["blue"], alpha=0.8)
    axes[0].set_title("Legitimate Transaction Amounts",
                      fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Amount ($)")
    axes[0].set_ylabel("Frequency")
    axes[1].hist(fraud, bins=50, color=COLORS["red"], alpha=0.8)
    axes[1].set_title("Fraudulent Transaction Amounts",
                      fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Amount ($)")
    fig.suptitle("Transaction Amount Distribution — Fraud vs Legitimate",
                 fontsize=14, fontweight="bold", y=1.02)
    return save(fig, "03_amount_distribution")


def plot_fraud_by_hour(transactions_df):
    """Line chart — fraud activity by hour of day."""
    hourly = transactions_df.groupby("hour_of_day").agg(
        total=("transaction_id", "count"),
        fraud=("is_fraud", "sum")
    ).reset_index()
    hourly["fraud_rate"] = (hourly["fraud"] / hourly["total"] * 100).round(2)
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(hourly["hour_of_day"], hourly["fraud_rate"],
            color=COLORS["red"], linewidth=2.5, marker="o", markersize=5)
    ax.fill_between(hourly["hour_of_day"], hourly["fraud_rate"],
                    alpha=0.2, color=COLORS["red"])
    ax.set_title("Fraud Rate by Hour of Day",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Hour of Day (0-23)")
    ax.set_ylabel("Fraud Rate (%)")
    ax.set_xticks(range(0, 24))
    return save(fig, "04_fraud_by_hour")


def plot_risk_score_distribution(risk_df):
    """Histogram — composite risk score distribution."""
    fig, ax = plt.subplots(figsize=(11, 6))
    colors_map = {"Low": COLORS["green"], "Medium": COLORS["orange"],
                  "High": COLORS["red"], "Critical": COLORS["dark"]}
    for level, color in colors_map.items():
        subset = risk_df[risk_df["risk_level"] == level]
        ax.hist(subset["composite_risk_score"], bins=20,
                color=color, alpha=0.7, label=level)
    ax.set_title("Account Risk Score Distribution",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Composite Risk Score")
    ax.set_ylabel("Number of Accounts")
    ax.legend(title="Risk Level")
    return save(fig, "05_risk_score_distribution")


def plot_fraud_by_country(transactions_df):
    """Bar chart — fraud rate by country."""
    country_stats = transactions_df.groupby("country").agg(
        total=("transaction_id", "count"),
        fraud=("is_fraud", "sum")
    ).reset_index()
    country_stats["fraud_rate"] = (
        country_stats["fraud"] / country_stats["total"] * 100
    ).round(2)
    country_stats = country_stats.sort_values("fraud_rate", ascending=False)
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(country_stats["country"], country_stats["fraud_rate"],
                  color=[COLORS["red"] if r > 10 else COLORS["orange"]
                         if r > 7 else COLORS["blue"]
                         for r in country_stats["fraud_rate"]],
                  alpha=0.85)
    ax.axhline(y=8, color=COLORS["gray"], linestyle="--",
               linewidth=2, label="Average fraud rate 8%")
    ax.set_title("Fraud Rate by Country",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Country")
    ax.set_ylabel("Fraud Rate (%)")
    ax.legend()
    return save(fig, "06_fraud_by_country")


def plot_merchant_fraud(transactions_df):
    """Horizontal bar — fraud count by merchant category."""
    merchant_fraud = transactions_df[
        transactions_df["is_fraud"] == True
    ]["merchant_category"].value_counts()
    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(merchant_fraud.index, merchant_fraud.values,
                   color=COLORS["orange"], alpha=0.85)
    for bar, val in zip(bars, merchant_fraud.values):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9, fontweight="bold")
    ax.set_title("Fraud Cases by Merchant Category",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Number of Fraud Cases")
    return save(fig, "07_merchant_fraud")
