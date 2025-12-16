"""
Unit Tests for Data Ingestion

Tests for:
- File parsing
- Duplicate handling
- Missing value handling
"""

import pytest
from datetime import date
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, WeatherRecord
from ingest import parse_weather_file, ingest_weather_data
from pathlib import Path


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def temp_data_dir():
    """Create temporary directory with test data files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = os.path.join(tmpdir, 'TEST001.txt')
        with open(test_file, 'w') as f:
            f.write("19850101\t100\t-50\t25\n")
            f.write("19850102\t150\t0\t0\n")
            f.write("19850103\t-9999\t-100\t-9999\n")  # Missing values
        
        yield tmpdir


class TestParseWeatherFile:
    """Tests for parse_weather_file function."""
    
    def test_parse_valid_file(self, temp_data_dir):
        """Test parsing a valid weather data file."""
        filepath = Path(temp_data_dir) / 'TEST001.txt'
        records = parse_weather_file(filepath)
        
        assert len(records) == 3
        
        # Check first record
        assert records[0]['station_id'] == 'TEST001'
        assert records[0]['date'] == date(1985, 1, 1)
        assert records[0]['max_temp'] == 100
        assert records[0]['min_temp'] == -50
        assert records[0]['precipitation'] == 25
    
    def test_parse_missing_values(self, temp_data_dir):
        """Test that missing values (-9999) are converted to None."""
        filepath = Path(temp_data_dir) / 'TEST001.txt'
        records = parse_weather_file(filepath)
        
        # Third record has missing max_temp and precipitation
        assert records[2]['max_temp'] is None
        assert records[2]['precipitation'] is None
        assert records[2]['min_temp'] == -100  # Not missing
    
    def test_parse_extracts_station_id_from_filename(self, temp_data_dir):
        """Test that station ID is extracted from filename."""
        filepath = Path(temp_data_dir) / 'TEST001.txt'
        records = parse_weather_file(filepath)
        
        for record in records:
            assert record['station_id'] == 'TEST001'


class TestIngestWeatherData:
    """Tests for ingest_weather_data function."""
    
    def test_ingest_creates_records(self, app, temp_data_dir):
        """Test that ingestion creates database records."""
        with app.app_context():
            stats = ingest_weather_data(temp_data_dir)
            
            assert stats['records_inserted'] == 3
            assert stats['duplicates_skipped'] == 0
            
            # Verify records in database
            records = WeatherRecord.query.all()
            assert len(records) == 3
    
    def test_ingest_handles_duplicates(self, app, temp_data_dir):
        """Test that running ingestion twice doesn't create duplicates."""
        with app.app_context():
            # First run
            stats1 = ingest_weather_data(temp_data_dir)
            assert stats1['records_inserted'] == 3
            
            # Second run
            stats2 = ingest_weather_data(temp_data_dir)
            assert stats2['records_inserted'] == 0
            assert stats2['duplicates_skipped'] == 3
            
            # Verify only 3 records in database
            records = WeatherRecord.query.all()
            assert len(records) == 3
    
    def test_ingest_nonexistent_directory(self, app):
        """Test that ingestion raises error for non-existent directory."""
        with app.app_context():
            with pytest.raises(FileNotFoundError):
                ingest_weather_data('/nonexistent/path')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


