"""
Test suite for HR Data Warehouse ETL Integration

Tests validate the data integration functionality including:
- Data extraction from multiple sources
- Data transformation and merging logic
- Data quality validation
- Error handling and logging
"""

import pytest
import pandas as pd
import sqlite3
import os
from data_integration import HRDataIntegration


class TestHRDataIntegration:
    """Test cases for HR data integration pipeline"""

    @pytest.fixture
    def setup_database(self):
        """Setup test database before each test"""
        db_path = 'target_warehouse.db'

        # Initialize database with schema
        if os.path.exists(db_path):
            os.remove(db_path)

        conn = sqlite3.connect(db_path)
        with open('warehouse_schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()

        yield db_path

        # Cleanup
        if os.path.exists('error_log.txt'):
            os.remove('error_log.txt')

    def test_extract_all_sources(self, setup_database):
        """Test that all source files are extracted correctly"""
        pipeline = HRDataIntegration()
        hris_df, payroll_df, perf_df = pipeline.extract()

        # Verify data was extracted
        assert len(hris_df) > 0, "HRIS data should be extracted"
        assert len(payroll_df) > 0, "Payroll data should be extracted"
        assert len(perf_df) > 0, "Performance data should be extracted"

        # Verify expected columns exist
        assert 'employee_id' in hris_df.columns
        assert 'full_name' in hris_df.columns
        assert 'department' in hris_df.columns
        assert 'base_salary' in payroll_df.columns
        assert 'performance_score' in perf_df.columns

    def test_data_merge_logic(self, setup_database):
        """Test that data is merged correctly with left joins"""
        pipeline = HRDataIntegration()
        hris_df, payroll_df, perf_df = pipeline.extract()
        merged_df = pipeline.transform(hris_df, payroll_df, perf_df)

        # Number of records should match HRIS (master source)
        assert len(merged_df) == len(hris_df), "Merged data should preserve all HRIS records"

        # Verify all HRIS columns are present
        assert 'employee_id' in merged_df.columns
        assert 'full_name' in merged_df.columns
        assert 'department' in merged_df.columns

    def test_total_compensation_calculation(self, setup_database):
        """Test that total compensation is calculated correctly"""
        pipeline = HRDataIntegration()
        hris_df, payroll_df, perf_df = pipeline.extract()
        merged_df = pipeline.transform(hris_df, payroll_df, perf_df)

        # Check total_compensation column exists
        assert 'total_compensation' in merged_df.columns

        # Verify calculation for records with both salary and bonus
        for idx, row in merged_df.iterrows():
            if not pd.isna(row['base_salary']) and not pd.isna(row['bonus']):
                expected = row['base_salary'] + row['bonus']
                assert row['total_compensation'] == expected, \
                    f"Total compensation should equal base_salary + bonus"

    def test_bonus_default_value(self, setup_database):
        """Test that missing bonus values default to 0"""
        pipeline = HRDataIntegration()
        hris_df, payroll_df, perf_df = pipeline.extract()
        merged_df = pipeline.transform(hris_df, payroll_df, perf_df)

        # Check that no bonus values are NaN
        assert merged_df['bonus'].isna().sum() == 0, "All bonus values should have defaults"

        # Verify employees without bonus in payroll have 0
        for idx, row in merged_df.iterrows():
            if not pd.isna(row['bonus']):
                assert row['bonus'] >= 0, "Bonus should be 0 or positive"

    def test_data_loaded_to_database(self, setup_database):
        """Test that valid records are loaded to the database"""
        pipeline = HRDataIntegration()
        pipeline.run()

        # Verify records were loaded
        conn = sqlite3.connect('target_warehouse.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employee_analytics")
        count = cursor.fetchone()[0]
        conn.close()

        assert count > 0, "Database should contain loaded records"
        assert count == pipeline.stats['records_loaded']

    def test_required_fields_in_database(self, setup_database):
        """Test that all required fields are present in loaded records"""
        pipeline = HRDataIntegration()
        pipeline.run()

        conn = sqlite3.connect('target_warehouse.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT employee_id, full_name, department, base_salary
            FROM employee_analytics
        """)
        records = cursor.fetchall()
        conn.close()

        # Verify all records have core fields
        for record in records:
            employee_id, full_name, department, base_salary = record
            assert employee_id is not None, "employee_id should not be null"
            assert full_name is not None and full_name != '', "full_name should not be null"
            assert department is not None and department != '', "department should not be null"

    def test_no_duplicate_records(self, setup_database):
        """Test that running the pipeline multiple times doesn't create duplicates"""
        pipeline = HRDataIntegration()
        pipeline.run()

        # Get initial count
        conn = sqlite3.connect('target_warehouse.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employee_analytics")
        initial_count = cursor.fetchone()[0]
        conn.close()

        # Run again
        pipeline2 = HRDataIntegration()
        pipeline2.run()

        # Check count is the same
        conn = sqlite3.connect('target_warehouse.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employee_analytics")
        final_count = cursor.fetchone()[0]
        conn.close()

        assert initial_count == final_count, "Running pipeline twice should not create duplicates"

    def test_error_log_created(self, setup_database):
        """Test that error log file is created"""
        pipeline = HRDataIntegration()
        pipeline.run()

        # Error log should be created even if empty
        assert os.path.exists('error_log.txt'), "Error log file should be created"

    def test_statistics_tracking(self, setup_database):
        """Test that ETL statistics are tracked correctly"""
        pipeline = HRDataIntegration()
        pipeline.run()

        # Verify stats are tracked
        assert pipeline.stats['records_processed'] > 0, "Should track processed records"
        assert pipeline.stats['records_loaded'] >= 0, "Should track loaded records"

    def test_employee_master_data_preserved(self, setup_database):
        """Test that employee master data from HRIS is preserved"""
        pipeline = HRDataIntegration()
        pipeline.run()

        conn = sqlite3.connect('target_warehouse.db')
        df = pd.read_sql_query("SELECT * FROM employee_analytics", conn)
        conn.close()

        # Verify all loaded records have HRIS fields
        assert 'full_name' in df.columns
        assert 'department' in df.columns
        assert 'employment_status' in df.columns

        # Verify no null values in HRIS master fields (for loaded records)
        assert df['full_name'].notna().all()
        assert df['department'].notna().all()
