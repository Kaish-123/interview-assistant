"""
Database initialization script.
Creates SQLite database with sample customer transaction data.
"""
import sqlite3
import random
from datetime import datetime, timedelta
import os

def init_database(db_path="data/transactions.db"):
    """Initialize the SQLite database with sample data."""

    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create customers table
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            registration_date TEXT
        )
    """)

    # Create products table
    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT,
            price REAL
        )
    """)

    # Create transactions table
    cursor.execute("""
        CREATE TABLE transactions (
            transaction_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            transaction_date TEXT,
            quantity INTEGER,
            amount REAL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # Insert sample customers
    customers = []
    for i in range(1, 1001):
        reg_date = datetime.now() - timedelta(days=random.randint(1, 730))
        customers.append((
            i,
            f"Customer_{i}",
            f"customer{i}@example.com",
            reg_date.strftime("%Y-%m-%d")
        ))

    # Add some customers with missing emails (edge case)
    for i in range(1001, 1051):
        reg_date = datetime.now() - timedelta(days=random.randint(1, 730))
        customers.append((
            i,
            f"Customer_{i}",
            None,
            reg_date.strftime("%Y-%m-%d")
        ))

    cursor.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?)",
        customers
    )

    # Insert sample products
    categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
    products = []
    for i in range(1, 201):
        products.append((
            i,
            f"Product_{i}",
            random.choice(categories),
            round(random.uniform(10.0, 500.0), 2)
        ))

    # Add some products with missing category (edge case)
    for i in range(201, 211):
        products.append((
            i,
            f"Product_{i}",
            None,
            round(random.uniform(10.0, 500.0), 2)
        ))

    cursor.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?)",
        products
    )

    # Insert sample transactions
    transactions = []
    transaction_id = 1
    base_date = datetime.now() - timedelta(days=90)

    # Regular transactions
    for _ in range(9000):
        customer_id = random.randint(1, 1050)
        product_id = random.randint(1, 210)
        days_offset = random.randint(0, 90)
        trans_date = base_date + timedelta(days=days_offset)
        quantity = random.randint(1, 5)
        amount = round(random.uniform(20.0, 1000.0), 2)

        transactions.append((
            transaction_id,
            customer_id,
            product_id,
            trans_date.strftime("%Y-%m-%d"),
            quantity,
            amount
        ))
        transaction_id += 1

    # Add edge cases
    # Invalid: NULL customer_id
    transactions.append((
        transaction_id,
        None,
        random.randint(1, 210),
        (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
        1,
        100.0
    ))
    transaction_id += 1

    # Invalid: Negative amount
    transactions.append((
        transaction_id,
        random.randint(1, 1050),
        random.randint(1, 210),
        (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
        1,
        -50.0
    ))
    transaction_id += 1

    # Invalid: Future-dated transaction
    transactions.append((
        transaction_id,
        random.randint(1, 1050),
        random.randint(1, 210),
        (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        1,
        200.0
    ))
    transaction_id += 1

    # Add customers with zero transactions (some customer IDs won't be in transactions)
    # This is already handled by having 1050 customers but only ~9000 transactions

    cursor.executemany(
        "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
        transactions
    )

    conn.commit()
    conn.close()

    print(f"Database initialized successfully at {db_path}")
    print(f"Created {len(customers)} customers, {len(products)} products, {len(transactions)} transactions")

if __name__ == "__main__":
    init_database()
