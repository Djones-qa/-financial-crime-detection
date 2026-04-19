"""
Tests for fraud detection visualizations.
"""
import pytest
import os
import sys
import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, os.path.abspath("."))
from scripts.data_generator import (
    generate_accounts, generate_transactions
)
from scripts.fraud_detector import calculate_risk_score
from scripts.visualizations import (
    plot_fraud_distribution, plot_fraud_by_type,
    plot_amount_distribution, plot_fraud_by_hour,
    plot_risk_score_distribution, plot_fraud_by_country,
    plot_merchant_fraud
)


@pytest.fixture(scope="module")
def accounts():
    return generate_accounts(500)


@pytest.fixture(scope="module")
def transactions(accounts):
    return generate_transactions(accounts, 5000)


@pytest.fixture(scope="module")
def risk_df(accounts, transactions):
    return calculate_risk_score(transactions, accounts)


class TestVisualizations:

    def test_fraud_distribution_chart_created(self, transactions):
        path = plot_fraud_distribution(transactions)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_fraud_by_type_chart_created(self, transactions):
        path = plot_fraud_by_type(transactions)
        assert os.path.exists(path)

    def test_amount_distribution_chart_created(self, transactions):
        path = plot_amount_distribution(transactions)
        assert os.path.exists(path)

    def test_fraud_by_hour_chart_created(self, transactions):
        path = plot_fraud_by_hour(transactions)
        assert os.path.exists(path)

    def test_risk_score_chart_created(self, risk_df):
        path = plot_risk_score_distribution(risk_df)
        assert os.path.exists(path)

    def test_fraud_by_country_chart_created(self, transactions):
        path = plot_fraud_by_country(transactions)
        assert os.path.exists(path)

    def test_merchant_fraud_chart_created(self, transactions):
        path = plot_merchant_fraud(transactions)
        assert os.path.exists(path)

    def test_all_charts_are_png(self):
        charts = [f for f in os.listdir("visuals")
                  if f.endswith(".png")]
        assert len(charts) >= 7

    def test_all_charts_non_empty(self):
        for f in os.listdir("visuals"):
            if f.endswith(".png"):
                size = os.path.getsize(f"visuals/{f}")
                assert size > 0, f"Empty chart: {f}"
