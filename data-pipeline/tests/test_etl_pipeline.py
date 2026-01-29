"""
Unit tests for ETL pipeline.
"""
import pytest
import os
import sys
import shutil
from pyspark.sql import SparkSession
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from etl_pipeline import (
    create_spark_session,
    transform_data,
    validate_data_quality,
    DataQualityException
)


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    spark = create_spark_session("TestPipeline")
    yield spark
    spark.stop()


@pytest.fixture
def sample_data(spark):
    """Create sample DataFrames for testing."""
    # Create sample customers
    customers_data = [
        (1, "Alice", "alice@example.com", "2023-01-15"),
        (2, "Bob", "bob@example.com", "2023-02-20"),
        (3, "Charlie", None, "2023-03-10"),
        (4, "Diana", "diana@example.com", "2023-04-05"),
        (5, "Eve", "eve@example.com", "2023-05-12")  # Customer with no transactions
    ]
    customers_df = spark.createDataFrame(
        customers_data,
        ["customer_id", "name", "email", "registration_date"]
    )

    # Create sample products
    products_data = [
        (1, "Laptop", "Electronics", 999.99),
        (2, "Shirt", "Clothing", 29.99),
        (3, "Book", None, 15.99),  # Missing category
        (4, "Phone", "Electronics", 699.99)
    ]
    products_df = spark.createDataFrame(
        products_data,
        ["product_id", "product_name", "category", "price"]
    )

    # Create sample transactions
    current_date = datetime.now()
    past_date = current_date - timedelta(days=30)
    future_date = current_date + timedelta(days=10)

    transactions_data = [
        # Valid transactions
        (1, 1, 1, past_date.strftime("%Y-%m-%d"), 1, 999.99),
        (2, 1, 2, past_date.strftime("%Y-%m-%d"), 2, 59.98),
        (3, 2, 1, past_date.strftime("%Y-%m-%d"), 1, 999.99),
        (4, 2, 3, past_date.strftime("%Y-%m-%d"), 1, 15.99),
        (5, 3, 4, past_date.strftime("%Y-%m-%d"), 1, 699.99),
        (6, 4, 2, past_date.strftime("%Y-%m-%d"), 3, 89.97),
        # Invalid: null customer_id
        (7, None, 1, past_date.strftime("%Y-%m-%d"), 1, 999.99),
        # Invalid: negative amount
        (8, 1, 3, past_date.strftime("%Y-%m-%d"), 1, -15.99),
        # Invalid: future date
        (9, 2, 4, future_date.strftime("%Y-%m-%d"), 1, 699.99)
    ]
    transactions_df = spark.createDataFrame(
        transactions_data,
        ["transaction_id", "customer_id", "product_id", "transaction_date", "quantity", "amount"]
    )

    return customers_df, products_df, transactions_df


def test_transform_data_filters_invalid_records(sample_data):
    """Test that invalid records are filtered out."""
    customers_df, products_df, transactions_df = sample_data

    result = transform_data(customers_df, products_df, transactions_df)

    # Should have all 5 customers (including Eve with 0 transactions)
    assert result.count() == 5

    # Check that customer 1 has correct totals (should exclude negative amount)
    customer_1 = result.filter(result.customer_id == 1).collect()[0]
    assert customer_1.transaction_count == 2  # Two valid transactions
    assert abs(customer_1.total_spend - 1059.97) < 0.01  # 999.99 + 59.98


def test_transform_data_handles_zero_transactions(sample_data):
    """Test that customers with zero transactions are handled correctly."""
    customers_df, products_df, transactions_df = sample_data

    result = transform_data(customers_df, products_df, transactions_df)

    # Customer 5 (Eve) has no transactions
    customer_5 = result.filter(result.customer_id == 5).collect()[0]
    assert customer_5.transaction_count == 0
    assert customer_5.total_spend == 0.0
    assert customer_5.average_order_value == 0.0


def test_transform_data_calculates_aggregates_correctly(sample_data):
    """Test that aggregated metrics are calculated correctly."""
    customers_df, products_df, transactions_df = sample_data

    result = transform_data(customers_df, products_df, transactions_df)

    # Customer 2 has 2 valid transactions (excluding future-dated one)
    customer_2 = result.filter(result.customer_id == 2).collect()[0]
    assert customer_2.transaction_count == 2
    expected_total = 999.99 + 15.99
    assert abs(customer_2.total_spend - expected_total) < 0.01
    expected_avg = expected_total / 2
    assert abs(customer_2.average_order_value - expected_avg) < 0.01


def test_transform_data_handles_missing_product_info(sample_data):
    """Test that transactions with missing product info are included."""
    customers_df, products_df, transactions_df = sample_data

    result = transform_data(customers_df, products_df, transactions_df)

    # Customer 3 bought a product with missing category - should still work
    customer_3 = result.filter(result.customer_id == 3).collect()[0]
    assert customer_3.transaction_count == 1
    assert abs(customer_3.total_spend - 699.99) < 0.01


def test_transform_data_adds_partition_column(sample_data):
    """Test that partition column is added."""
    customers_df, products_df, transactions_df = sample_data

    result = transform_data(customers_df, products_df, transactions_df)

    # Check that registration_year column exists
    assert "registration_year" in result.columns

    # Check that it's extracted correctly
    customer_1 = result.filter(result.customer_id == 1).collect()[0]
    assert customer_1.registration_year == "2023"


def test_validate_data_quality_passes_for_valid_data(sample_data):
    """Test that quality validation passes for valid data."""
    customers_df, products_df, transactions_df = sample_data

    result = transform_data(customers_df, products_df, transactions_df)

    # Should not raise exception
    validate_data_quality(result, transactions_df)


def test_validate_data_quality_detects_duplicates(spark):
    """Test that duplicate customer IDs are detected."""
    # Create data with duplicates
    data = [
        (1, "Alice", "alice@example.com", "2023-01-15", 100.0, 2, 50.0, "2023"),
        (1, "Alice", "alice@example.com", "2023-01-15", 200.0, 3, 66.67, "2023")  # Duplicate
    ]
    df = spark.createDataFrame(
        data,
        ["customer_id", "name", "email", "registration_date", "total_spend", "transaction_count", "average_order_value", "registration_year"]
    )

    transactions_df = spark.createDataFrame(
        [(1, 1, 1, "2023-01-15", 1, 100.0)],
        ["transaction_id", "customer_id", "product_id", "transaction_date", "quantity", "amount"]
    )

    with pytest.raises(DataQualityException, match="Duplicate customer IDs"):
        validate_data_quality(df, transactions_df)


def test_validate_data_quality_detects_negative_values(spark):
    """Test that negative monetary values are detected."""
    data = [
        (1, "Alice", "alice@example.com", "2023-01-15", -100.0, 2, 50.0, "2023")  # Negative total_spend
    ]
    df = spark.createDataFrame(
        data,
        ["customer_id", "name", "email", "registration_date", "total_spend", "transaction_count", "average_order_value", "registration_year"]
    )

    transactions_df = spark.createDataFrame(
        [(1, 1, 1, "2023-01-15", 1, 100.0)],
        ["transaction_id", "customer_id", "product_id", "transaction_date", "quantity", "amount"]
    )

    with pytest.raises(DataQualityException, match="negative"):
        validate_data_quality(df, transactions_df)


def test_transform_is_idempotent(sample_data):
    """Test that running transform twice produces the same result."""
    customers_df, products_df, transactions_df = sample_data

    result1 = transform_data(customers_df, products_df, transactions_df)
    result2 = transform_data(customers_df, products_df, transactions_df)

    # Both results should have the same count and data
    assert result1.count() == result2.count()

    # Compare a few key metrics
    for customer_id in [1, 2, 3, 4, 5]:
        r1 = result1.filter(result1.customer_id == customer_id).collect()[0]
        r2 = result2.filter(result2.customer_id == customer_id).collect()[0]
        assert r1.total_spend == r2.total_spend
        assert r1.transaction_count == r2.transaction_count
