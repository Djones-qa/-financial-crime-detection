"""
Tests for fraud detection algorithms accuracy.
"""
import pytest
import pandas as pd
import sys, os
sys.path.insert(0, os.path.abspath("."))
from scripts.data_generator import (
    generate_accounts, generate_transactions,
    generate_fraud_network, save_to_sqlite
)
from scripts.fraud_detector import (
    calculate_velocity_score, detect_geographic_anomalies,
    detect_amount_anomalies, detect_structuring,
    calculate_risk_score, run_sql_investigations
)


@pytest.fixture(scope="module")
def accounts():
    return generate_accounts(500)


@pytest.fixture(scope="module")
def transactions(accounts):
    return generate_transactions(accounts, 5000)


@pytest.fixture(scope="module")
def db(accounts, transactions):
    network = __import__(
        "scripts.data_generator",
        fromlist=["generate_fraud_network"]
    ).generate_fraud_network(50)
    save_to_sqlite(accounts, transactions, network)
    return "data/financial_crimes.db"


class TestVelocityDetection:

    def test_velocity_returns_dataframe(self, transactions):
        result = calculate_velocity_score(transactions)
        assert isinstance(result, pd.DataFrame)

    def test_velocity_has_required_columns(self, transactions):
        result = calculate_velocity_score(transactions)
        assert "velocity_flag" in result.columns
        assert "max_txn_per_hour" in result.columns

    def test_velocity_flag_is_boolean(self, transactions):
        result = calculate_velocity_score(transactions)
        assert result["velocity_flag"].dtype == bool

    def test_max_txn_per_hour_is_positive(self, transactions):
        result = calculate_velocity_score(transactions)
        assert (result["max_txn_per_hour"] >= 0).all()


class TestGeographicDetection:

    def test_geo_returns_dataframe(self, transactions, accounts):
        result = detect_geographic_anomalies(transactions, accounts)
        assert isinstance(result, pd.DataFrame)

    def test_geo_mismatch_is_boolean(self, transactions, accounts):
        result = detect_geographic_anomalies(transactions, accounts)
        assert result["geo_mismatch"].dtype == bool

    def test_geo_risk_score_within_range(self, transactions, accounts):
        result = detect_geographic_anomalies(transactions, accounts)
        assert result["geo_risk_score"].between(0, 1).all()

    def test_geo_has_transaction_id(self, transactions, accounts):
        result = detect_geographic_anomalies(transactions, accounts)
        assert "transaction_id" in result.columns


class TestAmountAnomalyDetection:

    def test_amount_returns_dataframe(self, transactions):
        result = detect_amount_anomalies(transactions)
        assert isinstance(result, pd.DataFrame)

    def test_z_score_column_exists(self, transactions):
        result = detect_amount_anomalies(transactions)
        assert "z_score" in result.columns

    def test_amount_anomaly_is_boolean(self, transactions):
        result = detect_amount_anomalies(transactions)
        assert result["amount_anomaly"].dtype == bool

    def test_anomalies_detected(self, transactions):
        result = detect_amount_anomalies(transactions)
        assert result["amount_anomaly"].sum() > 0


class TestStructuringDetection:

    def test_structuring_returns_dataframe(self, transactions):
        result = detect_structuring(transactions)
        assert isinstance(result, pd.DataFrame)

    def test_structuring_flag_is_boolean(self, transactions):
        result = detect_structuring(transactions)
        assert result["structuring_flag"].dtype == bool

    def test_structured_count_non_negative(self, transactions):
        result = detect_structuring(transactions)
        assert (result["structured_count"] >= 0).all()


class TestRiskScoring:

    def test_risk_score_returns_dataframe(self, transactions, accounts):
        result = calculate_risk_score(transactions, accounts)
        assert isinstance(result, pd.DataFrame)

    def test_composite_score_within_range(self, transactions, accounts):
        result = calculate_risk_score(transactions, accounts)
        assert result["composite_risk_score"].between(0, 1).all()

    def test_risk_level_values_valid(self, transactions, accounts):
        result = calculate_risk_score(transactions, accounts)
        valid = {"Low", "Medium", "High", "Critical"}
        actual = set(result["risk_level"].dropna().astype(str).unique())
        assert actual.issubset(valid)

    def test_high_risk_accounts_exist(self, transactions, accounts):
        result = calculate_risk_score(transactions, accounts)
        high_risk = result[result["risk_level"].isin(["High", "Critical"])]
        assert len(high_risk) > 0


class TestSQLInvestigations:

    def test_sql_returns_all_queries(self, db):
        results = run_sql_investigations(db)
        expected = ["fraud_by_type", "high_risk_accounts",
                    "fraud_by_country", "fraud_by_hour",
                    "large_transactions", "structuring_suspects"]
        for key in expected:
            assert key in results

    def test_fraud_by_type_not_empty(self, db):
        results = run_sql_investigations(db)
        assert len(results["fraud_by_type"]) > 0

    def test_fraud_by_country_has_all_countries(self, db):
        results = run_sql_investigations(db)
        assert len(results["fraud_by_country"]) >= 5

    def test_fraud_by_hour_has_24_rows(self, db):
        results = run_sql_investigations(db)
        assert len(results["fraud_by_hour"]) == 24
