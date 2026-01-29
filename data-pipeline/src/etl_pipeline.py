"""
ETL Pipeline for Customer Transaction Data.
Reads from SQLite, transforms data, performs quality checks, and writes to parquet.
"""
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, sum as spark_sum, count, avg, coalesce, lit, substring
from datetime import datetime
import json


class DataQualityException(Exception):
    """Raised when data quality checks fail."""
    pass


def create_spark_session(app_name="CustomerTransactionPipeline"):
    """Initialize and return a SparkSession."""
    import os
    jar_path = os.path.join(os.path.dirname(__file__), "..", "jars", "sqlite-jdbc-3.43.0.0.jar")
    return SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.jars", jar_path) \
        .getOrCreate()


def read_tables(spark: SparkSession, db_path: str) -> tuple:
    """
    Read customers, products, and transactions tables from SQLite.

    Args:
        spark: SparkSession
        db_path: Path to SQLite database

    Returns:
        Tuple of (customers_df, products_df, transactions_df)
    """
    jdbc_url = f"jdbc:sqlite:{db_path}"

    customers_df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "customers") \
        .option("driver", "org.sqlite.JDBC") \
        .load()

    products_df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "products") \
        .option("driver", "org.sqlite.JDBC") \
        .load()

    transactions_df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "transactions") \
        .option("driver", "org.sqlite.JDBC") \
        .load()

    return customers_df, products_df, transactions_df


def transform_data(customers_df: DataFrame, products_df: DataFrame, transactions_df: DataFrame) -> DataFrame:
    """
    Transform customer transaction data with aggregations and filtering.

    This function:
    1. Filters out invalid records (null customer IDs, negative amounts, future dates)
    2. Joins tables to create comprehensive customer purchase summary
    3. Calculates aggregated metrics per customer
    4. Handles edge cases (missing product info, customers with zero transactions)

    Args:
        customers_df: Customer data
        products_df: Product data
        transactions_df: Transaction data

    Returns:
        Transformed DataFrame with customer summaries
    """
    # Get current date as string for comparison
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Step 1: Filter invalid transactions
    # - Remove null customer_ids
    # - Remove negative amounts
    # - Remove future-dated transactions
    valid_transactions = transactions_df.filter(
        col("customer_id").isNotNull() &
        (col("amount") >= 0) &
        (col("transaction_date") <= current_date_str)
    )
    
    # Step 2: Join transactions with products (left join to handle missing product info)
    transactions_with_products = valid_transactions.join(
        products_df,
        valid_transactions.product_id == products_df.product_id,
        "left"
    )
    
    # Step 3: Aggregate metrics per customer
    # Calculate: total_spend, transaction_count, average_order_value
    customer_aggregates = transactions_with_products.groupBy("customer_id").agg(
        spark_sum("amount").alias("total_spend"),
        count("transaction_id").alias("transaction_count"),
        avg("amount").alias("average_order_value")
    )
    
    # Step 4: Join with customers table to get customer details
    # Use left join to include customers with zero transactions
    # Alias DataFrames to avoid column name conflicts
    customers_alias = customers_df.alias("customers")
    aggregates_alias = customer_aggregates.alias("aggregates")
    
    customer_summary = customers_alias.join(
        aggregates_alias,
        col("customers.customer_id") == col("aggregates.customer_id"),
        "left"
    )
    
    # Step 5: Handle customers with zero transactions (fill nulls with 0)
    customer_summary = customer_summary.select(
        col("customers.customer_id").alias("customer_id"),
        col("customers.name").alias("name"),
        col("customers.email").alias("email"),
        col("customers.registration_date").alias("registration_date"),
        coalesce(col("aggregates.total_spend"), lit(0.0)).alias("total_spend"),
        coalesce(col("aggregates.transaction_count"), lit(0)).alias("transaction_count"),
        coalesce(col("aggregates.average_order_value"), lit(0.0)).alias("average_order_value")
    )
    
    # Step 6: Extract registration_year from registration_date for partitioning
    # Parse the date string (format: YYYY-MM-DD) and extract year
    customer_summary = customer_summary.withColumn(
        "registration_year",
        substring(col("registration_date"), 1, 4)
    )
    
    # Step 7: Select final columns in the correct order
    result_df = customer_summary.select(
        "customer_id",
        "name",
        "email",
        "registration_date",
        "total_spend",
        "transaction_count",
        "average_order_value",
        "registration_year"
    )
    
    return result_df


def validate_data_quality(df: DataFrame, original_transactions_df: DataFrame) -> None:
    """
    Perform data quality checks on the transformed data.

    Checks:
    1. No duplicate customer IDs
    2. All monetary values are non-negative
    3. Aggregated totals match pre-aggregation sums

    Args:
        df: Transformed DataFrame
        original_transactions_df: Original transactions before transformation

    Raises:
        DataQualityException: If any quality check fails
    """
    # Check for duplicate customer IDs
    total_rows = df.count()
    distinct_customers = df.select("customer_id").distinct().count()
    if total_rows != distinct_customers:
        raise DataQualityException(f"Duplicate customer IDs found: {total_rows} rows but {distinct_customers} distinct customers")

    # Check for negative monetary values
    negative_spend = df.filter(col("total_spend") < 0).count()
    if negative_spend > 0:
        raise DataQualityException(f"Found {negative_spend} customers with negative total_spend")

    negative_aov = df.filter(col("average_order_value") < 0).count()
    if negative_aov > 0:
        raise DataQualityException(f"Found {negative_aov} customers with negative average_order_value")

    # Check aggregated totals match pre-aggregation sums (within 1% tolerance)
    original_total = original_transactions_df.filter(
        (col("customer_id").isNotNull()) &
        (col("amount") >= 0) &
        (col("transaction_date") <= datetime.now().strftime("%Y-%m-%d"))
    ).agg(spark_sum("amount").alias("original_sum")).collect()[0]["original_sum"] or 0

    aggregated_total = df.agg(spark_sum("total_spend").alias("aggregated_sum")).collect()[0]["aggregated_sum"] or 0

    tolerance = 0.01
    if original_total > 0:
        diff_ratio = abs(aggregated_total - original_total) / original_total
        if diff_ratio > tolerance:
            raise DataQualityException(
                f"Aggregated total mismatch: original={original_total}, aggregated={aggregated_total}, "
                f"diff={diff_ratio*100:.2f}% (tolerance={tolerance*100}%)"
            )

    print("✓ All data quality checks passed")


def write_output(df: DataFrame, output_path: str, partition_by: str = "registration_year") -> None:
    """
    Write DataFrame to parquet format with partitioning.

    Args:
        df: DataFrame to write
        output_path: Output directory path
        partition_by: Column to partition by
    """
    df.write \
        .mode("overwrite") \
        .partitionBy(partition_by) \
        .parquet(output_path)


def run_etl_pipeline(config_path: str = "config/config.json") -> str:
    """
    Main ETL pipeline execution.

    Args:
        config_path: Path to configuration file

    Returns:
        Output path where data was written
    """
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Initialize Spark
    spark = create_spark_session(config["spark"]["app_name"])

    try:
        # Read data
        customers_df, products_df, transactions_df = read_tables(
            spark,
            config["database"]["path"]
        )

        # Transform data
        result_df = transform_data(customers_df, products_df, transactions_df)

        # Validate quality
        validate_data_quality(result_df, transactions_df)

        # Write output
        output_path = config["output"]["path"]
        write_output(result_df, output_path)

        print(f"ETL pipeline completed successfully. Output written to {output_path}")
        return output_path

    finally:
        spark.stop()


if __name__ == "__main__":
    run_etl_pipeline()
