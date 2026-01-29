"""
HR Data Warehouse ETL Integration Pipeline

This script consolidates employee data from multiple source systems:
- HRIS (Human Resources Information System) - master source
- Payroll System
- Performance Management System

The pipeline performs Extract, Transform, and Load (ETL) operations
to create a unified analytics data warehouse.
"""

import pandas as pd
import sqlite3
import logging
from datetime import datetime
from typing import Tuple, Optional
import os


class HRDataIntegration:
    """ETL pipeline for HR data integration"""

    def __init__(self, db_path: str = 'target_warehouse.db'):
        """
        Initialize the HR Data Integration pipeline

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.stats = {
            'records_processed': 0,
            'records_loaded': 0,
            'errors': 0
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('error_log.txt'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def extract(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Extract data from all three source CSV files

        Returns:
            Tuple of (hris_df, payroll_df, perf_df) DataFrames
        """
        try:
            # Extract HRIS data (master source)
            hris_path = 'source_systems/hris_extract.csv'
            self.logger.info(f"Extracting HRIS data from {hris_path}")
            hris_df = pd.read_csv(hris_path)
            self.logger.info(f"Extracted {len(hris_df)} records from HRIS")

            # Extract Payroll data
            payroll_path = 'source_systems/payroll_extract.csv'
            self.logger.info(f"Extracting Payroll data from {payroll_path}")
            payroll_df = pd.read_csv(payroll_path)
            self.logger.info(f"Extracted {len(payroll_df)} records from Payroll")

            # Extract Performance Management data
            perf_path = 'source_systems/perf_mgmt_extract.csv'
            self.logger.info(f"Extracting Performance Management data from {perf_path}")
            perf_df = pd.read_csv(perf_path)
            self.logger.info(f"Extracted {len(perf_df)} records from Performance Management")

            return hris_df, payroll_df, perf_df

        except FileNotFoundError as e:
            self.logger.error(f"Source file not found: {e}")
            self.stats['errors'] += 1
            raise
        except Exception as e:
            self.logger.error(f"Error during extraction: {e}")
            self.stats['errors'] += 1
            raise

    def transform(self, hris_df: pd.DataFrame, payroll_df: pd.DataFrame, 
                  perf_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform and merge data from all sources

        Args:
            hris_df: HRIS master data
            payroll_df: Payroll data
            perf_df: Performance management data

        Returns:
            Merged DataFrame with all employee data
        """
        try:
            self.logger.info("Starting data transformation...")

            # Step 1: Merge HRIS with Payroll (left join - preserve all HRIS records)
            self.logger.info("Merging HRIS with Payroll data...")
            merged_df = pd.merge(
                hris_df,
                payroll_df,
                on='employee_id',
                how='left'
            )
            self.logger.info(f"After payroll merge: {len(merged_df)} records")

            # Step 2: Merge with Performance data (left join - preserve all HRIS records)
            self.logger.info("Merging with Performance Management data...")
            merged_df = pd.merge(
                merged_df,
                perf_df,
                on='employee_id',
                how='left'
            )
            self.logger.info(f"After performance merge: {len(merged_df)} records")

            # Step 3: Set default values for missing optional fields
            # Set bonus=0 if null
            merged_df['bonus'] = merged_df['bonus'].fillna(0)
            self.logger.info("Set default bonus=0 for missing values")
            
            # Set base_salary=0 if null (required field, but handle missing payroll records)
            merged_df['base_salary'] = merged_df['base_salary'].fillna(0)
            self.logger.info("Set default base_salary=0 for missing values")

            # Step 4: Calculate total_compensation = base_salary + bonus
            # Both base_salary and bonus should have defaults now, so simple addition
            merged_df['total_compensation'] = merged_df['base_salary'] + merged_df['bonus']
            self.logger.info("Calculated total_compensation for all records")

            # Step 5: Derive performance_category from performance_score
            def categorize_performance(score):
                """Categorize performance based on score"""
                if pd.isna(score):
                    return None
                elif score >= 4.5:
                    return 'Excellent'
                elif score >= 4.0:
                    return 'Very Good'
                elif score >= 3.5:
                    return 'Good'
                elif score >= 3.0:
                    return 'Satisfactory'
                else:
                    return 'Needs Improvement'

            merged_df['performance_category'] = merged_df['performance_score'].apply(
                categorize_performance
            )
            self.logger.info("Derived performance_category from performance_score")

            # Update statistics
            self.stats['records_processed'] = len(merged_df)

            self.logger.info("Data transformation completed successfully")
            return merged_df

        except Exception as e:
            self.logger.error(f"Error during transformation: {e}")
            self.stats['errors'] += 1
            raise

    def load(self, df: pd.DataFrame) -> None:
        """
        Load transformed data into the target warehouse database

        Args:
            df: Transformed DataFrame to load
        """
        try:
            self.logger.info("Starting data load...")

            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Prevent duplicate loads by clearing existing data
            self.logger.info("Clearing existing data from employee_analytics table...")
            cursor.execute("DELETE FROM employee_analytics")
            conn.commit()
            self.logger.info("Existing data cleared")

            # Prepare data for insertion
            # Map DataFrame columns to database columns
            records_loaded = 0
            for _, row in df.iterrows():
                try:
                    # Insert record into database
                    cursor.execute("""
                        INSERT INTO employee_analytics (
                            employee_id, full_name, department, hire_date, employment_status,
                            base_salary, bonus, total_compensation,
                            performance_score, performance_category, review_date, load_timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        int(row['employee_id']),
                        str(row['full_name']),
                        str(row['department']),
                        str(row['hire_date']) if pd.notna(row['hire_date']) else None,
                        str(row['employment_status']) if pd.notna(row['employment_status']) else None,
                        float(row['base_salary']) if pd.notna(row['base_salary']) else None,
                        float(row['bonus']) if pd.notna(row['bonus']) else None,
                        float(row['total_compensation']) if pd.notna(row['total_compensation']) else None,
                        float(row['performance_score']) if pd.notna(row['performance_score']) else None,
                        str(row['performance_category']) if pd.notna(row['performance_category']) else None,
                        str(row['review_date']) if pd.notna(row['review_date']) else None,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    records_loaded += 1

                except Exception as e:
                    self.logger.warning(f"Error loading record for employee_id {row.get('employee_id', 'unknown')}: {e}")
                    self.stats['errors'] += 1
                    continue

            # Commit all changes
            conn.commit()
            conn.close()

            self.stats['records_loaded'] = records_loaded
            self.logger.info(f"Successfully loaded {records_loaded} records into database")

        except Exception as e:
            self.logger.error(f"Error during load: {e}")
            self.stats['errors'] += 1
            raise

    def run(self) -> None:
        """
        Execute the complete ETL pipeline
        """
        try:
            self.logger.info("=" * 50)
            self.logger.info("Starting HR Data Integration ETL Pipeline")
            self.logger.info("=" * 50)

            # Extract
            hris_df, payroll_df, perf_df = self.extract()

            # Transform
            merged_df = self.transform(hris_df, payroll_df, perf_df)

            # Load
            self.load(merged_df)

            # Summary
            self.logger.info("=" * 50)
            self.logger.info("ETL Pipeline Completed Successfully")
            self.logger.info(f"Records Processed: {self.stats['records_processed']}")
            self.logger.info(f"Records Loaded: {self.stats['records_loaded']}")
            self.logger.info(f"Errors: {self.stats['errors']}")
            self.logger.info("=" * 50)

        except Exception as e:
            self.logger.error(f"ETL Pipeline failed: {e}")
            raise


if __name__ == '__main__':
    pipeline = HRDataIntegration()
    pipeline.run()
