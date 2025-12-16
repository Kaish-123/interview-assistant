"""
Unit Tests for Database Models

Tests for:
- WeatherRecord model
- WeatherStatistics model
- Unique constraints
- Data serialization
"""

import pytest
from datetime import date
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, WeatherRecord, WeatherStatistics
from sqlalchemy.exc import IntegrityError


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
def session(app):
    """Create database session."""
    with app.app_context():
        yield db.session


class TestWeatherRecordModel:
    """Tests for WeatherRecord model."""
    
    def test_create_weather_record(self, app):
        """Test creating a weather record."""
        with app.app_context():
            record = WeatherRecord(
                station_id='USC00110072',
                date=date(2020, 1, 1),
                max_temp=100,
                min_temp=-50,
                precipitation=25
            )
            db.session.add(record)
            db.session.commit()
            
            assert record.id is not None
            assert record.station_id == 'USC00110072'
            assert record.date == date(2020, 1, 1)
            assert record.max_temp == 100
            assert record.min_temp == -50
            assert record.precipitation == 25
    
    def test_create_weather_record_with_null_values(self, app):
        """Test creating a weather record with NULL (missing) values."""
        with app.app_context():
            record = WeatherRecord(
                station_id='USC00110072',
                date=date(2020, 1, 1),
                max_temp=None,  # Missing value
                min_temp=-50,
                precipitation=None  # Missing value
            )
            db.session.add(record)
            db.session.commit()
            
            assert record.max_temp is None
            assert record.precipitation is None
    
    def test_weather_record_unique_constraint(self, app):
        """Test that duplicate station_id/date combinations are rejected."""
        with app.app_context():
            record1 = WeatherRecord(
                station_id='USC00110072',
                date=date(2020, 1, 1),
                max_temp=100,
                min_temp=-50,
                precipitation=25
            )
            db.session.add(record1)
            db.session.commit()
            
            # Try to add duplicate
            record2 = WeatherRecord(
                station_id='USC00110072',
                date=date(2020, 1, 1),
                max_temp=200,
                min_temp=0,
                precipitation=50
            )
            db.session.add(record2)
            
            with pytest.raises(IntegrityError):
                db.session.commit()
    
    def test_weather_record_to_dict(self, app):
        """Test serialization of weather record to dictionary."""
        with app.app_context():
            record = WeatherRecord(
                station_id='USC00110072',
                date=date(2020, 1, 1),
                max_temp=100,
                min_temp=-50,
                precipitation=25
            )
            db.session.add(record)
            db.session.commit()
            
            record_dict = record.to_dict()
            
            assert record_dict['station_id'] == 'USC00110072'
            assert record_dict['date'] == '2020-01-01'
            assert record_dict['max_temp'] == 100
            assert record_dict['min_temp'] == -50
            assert record_dict['precipitation'] == 25
    
    def test_weather_record_repr(self, app):
        """Test string representation of weather record."""
        with app.app_context():
            record = WeatherRecord(
                station_id='USC00110072',
                date=date(2020, 1, 1),
                max_temp=100,
                min_temp=-50,
                precipitation=25
            )
            
            assert 'USC00110072' in repr(record)
            assert '2020-01-01' in repr(record)


class TestWeatherStatisticsModel:
    """Tests for WeatherStatistics model."""
    
    def test_create_weather_statistics(self, app):
        """Test creating weather statistics."""
        with app.app_context():
            stats = WeatherStatistics(
                station_id='USC00110072',
                year=2020,
                avg_max_temp=15.5,
                avg_min_temp=5.2,
                total_precipitation=85.3
            )
            db.session.add(stats)
            db.session.commit()
            
            assert stats.id is not None
            assert stats.station_id == 'USC00110072'
            assert stats.year == 2020
            assert stats.avg_max_temp == 15.5
            assert stats.avg_min_temp == 5.2
            assert stats.total_precipitation == 85.3
    
    def test_create_statistics_with_null_values(self, app):
        """Test creating statistics with NULL values (no valid data)."""
        with app.app_context():
            stats = WeatherStatistics(
                station_id='USC00110072',
                year=2020,
                avg_max_temp=None,
                avg_min_temp=None,
                total_precipitation=None
            )
            db.session.add(stats)
            db.session.commit()
            
            assert stats.avg_max_temp is None
            assert stats.avg_min_temp is None
            assert stats.total_precipitation is None
    
    def test_statistics_unique_constraint(self, app):
        """Test that duplicate station_id/year combinations are rejected."""
        with app.app_context():
            stats1 = WeatherStatistics(
                station_id='USC00110072',
                year=2020,
                avg_max_temp=15.5,
                avg_min_temp=5.2,
                total_precipitation=85.3
            )
            db.session.add(stats1)
            db.session.commit()
            
            # Try to add duplicate
            stats2 = WeatherStatistics(
                station_id='USC00110072',
                year=2020,
                avg_max_temp=20.0,
                avg_min_temp=10.0,
                total_precipitation=100.0
            )
            db.session.add(stats2)
            
            with pytest.raises(IntegrityError):
                db.session.commit()
    
    def test_statistics_to_dict(self, app):
        """Test serialization of statistics to dictionary."""
        with app.app_context():
            stats = WeatherStatistics(
                station_id='USC00110072',
                year=2020,
                avg_max_temp=15.5555,
                avg_min_temp=5.2222,
                total_precipitation=85.3333
            )
            db.session.add(stats)
            db.session.commit()
            
            stats_dict = stats.to_dict()
            
            assert stats_dict['station_id'] == 'USC00110072'
            assert stats_dict['year'] == 2020
            # Values should be rounded to 2 decimal places
            assert stats_dict['avg_max_temp'] == 15.56
            assert stats_dict['avg_min_temp'] == 5.22
            assert stats_dict['total_precipitation'] == 85.33
    
    def test_statistics_to_dict_with_nulls(self, app):
        """Test serialization of statistics with NULL values."""
        with app.app_context():
            stats = WeatherStatistics(
                station_id='USC00110072',
                year=2020,
                avg_max_temp=None,
                avg_min_temp=None,
                total_precipitation=None
            )
            db.session.add(stats)
            db.session.commit()
            
            stats_dict = stats.to_dict()
            
            assert stats_dict['avg_max_temp'] is None
            assert stats_dict['avg_min_temp'] is None
            assert stats_dict['total_precipitation'] is None
    
    def test_statistics_repr(self, app):
        """Test string representation of statistics."""
        with app.app_context():
            stats = WeatherStatistics(
                station_id='USC00110072',
                year=2020,
                avg_max_temp=15.5,
                avg_min_temp=5.2,
                total_precipitation=85.3
            )
            
            assert 'USC00110072' in repr(stats)
            assert '2020' in repr(stats)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


