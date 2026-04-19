"""
Tests for financial crime data generation.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.abspath("."))
from scripts.data_generator import (
    generate_accounts, generate_transactions,
    generate_fraud_network, save_to_sqlite, save_to_csv
)


@pytest.fixture(scope="module")
def accounts():
    return generate_accounts(500)


@pytest.fixture(scope="module")
def transactions(accounts):
    return generate_transactions(accounts, 5000)


@pytest.fixture(scope="module")
def network():
    return generate_fraud_network(50)


class TestAccountGeneration:

    def test_correct_account_count(self, accounts):
        assert len(accounts) == 500

    def test_account_ids_unique(self, accounts):
        assert accounts["account_id"].nunique() == 500

    def test_no_null_values(self, accounts):
        assert accounts.isnull().sum().sum() == 0

    def test_credit_limit_valid(self, accounts):
        valid = {1000, 2500, 5000, 10000, 25000}
        assert set(accounts["credit_limit"].unique()).issubset(valid)

    def test_risk_score_within_range(self, accounts):
        assert accounts["risk_score"].between(0, 1).all()

    def test_country_values_valid(self, accounts):
        from scripts.data_generator import COUNTRIES
        assert set(accounts["country"].unique()).issubset(set(COUNTRIES))


class TestTransactionGeneration:

    def test_correct_transaction_count(self, transactions):
        assert len(transactions) == 5000

    def test_transaction_ids_unique(self, transactions):
        assert transactions["transaction_id"].nunique() == 5000

    def test_fraud_rate_reasonable(self, transactions):
        fraud_rate = transactions["is_fraud"].mean()
        assert 0.04 <= fraud_rate <= 0.15

    def test_amount_is_positive(self, transactions):
        assert (transactions["amount"] > 0).all()

    def test_hour_within_valid_range(self, transactions):
        assert transactions["hour_of_day"].between(0, 23).all()

    def test_fraud_type_consistent(self, transactions):
        fraud = transactions[transactions["is_fraud"] == True]
        assert (fraud["fraud_type"] != "none").all()

    def test_legit_has_no_fraud_type(self, transactions):
        legit = transactions[transactions["is_fraud"] == False]
        assert (legit["fraud_type"] == "none").all()

    def test_device_values_valid(self, transactions):
        valid = {"mobile", "desktop", "tablet"}
        assert set(transactions["device"].unique()).issubset(valid)


class TestFraudNetwork:

    def test_correct_node_count(self, network):
        assert len(network) == 50

    def test_node_ids_unique(self, network):
        assert network["node_id"].nunique() == 50

    def test_cluster_values_valid(self, network):
        assert network["network_cluster"].between(1, 5).all()

    def test_transaction_count_positive(self, network):
        assert (network["transactions_count"] > 0).all()


class TestDataPersistence:

    def test_save_to_csv_creates_files(self, accounts, transactions, network):
        save_to_csv(accounts, transactions, network)
        assert os.path.exists("data/accounts.csv")
        assert os.path.exists("data/transactions.csv")
        assert os.path.exists("data/fraud_network.csv")

    def test_save_to_sqlite_creates_db(self, accounts, transactions, network):
        path = save_to_sqlite(accounts, transactions, network)
        assert os.path.exists(path)
