"""
Unit Tests for Weather API

Tests for:
- Weather records endpoint (/api/weather)
- Weather statistics endpoint (/api/weather/stats)
- Filtering and pagination functionality
"""

import pytest
from datetime import date
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, WeatherRecord, WeatherStatistics


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    with app.app_context():
        db.create_all()
        
        # Add test weather records
        test_records = [
            WeatherRecord(
                station_id='TEST001',
                date=date(2020, 1, 1),
                max_temp=100,  # 10.0°C
                min_temp=-50,  # -5.0°C
                precipitation=25  # 2.5mm
            ),
            WeatherRecord(
                station_id='TEST001',
                date=date(2020, 1, 2),
                max_temp=150,
                min_temp=0,
                precipitation=0
            ),
            WeatherRecord(
                station_id='TEST002',
                date=date(2020, 1, 1),
                max_temp=200,
                min_temp=100,
                precipitation=50
            ),
            WeatherRecord(
                station_id='TEST001',
                date=date(2021, 1, 1),
                max_temp=120,
                min_temp=-30,
                precipitation=10
            ),
        ]
        
        for record in test_records:
            db.session.add(record)
        
        # Add test statistics
        test_stats = [
            WeatherStatistics(
                station_id='TEST001',
                year=2020,
                avg_max_temp=12.5,
                avg_min_temp=-2.5,
                total_precipitation=2.5
            ),
            WeatherStatistics(
                station_id='TEST002',
                year=2020,
                avg_max_temp=20.0,
                avg_min_temp=10.0,
                total_precipitation=5.0
            ),
            WeatherStatistics(
                station_id='TEST001',
                year=2021,
                avg_max_temp=12.0,
                avg_min_temp=-3.0,
                total_precipitation=1.0
            ),
        ]
        
        for stat in test_stats:
            db.session.add(stat)
        
        db.session.commit()
        
        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestWeatherEndpoint:
    """Tests for /api/weather endpoint."""
    
    def test_get_weather_records(self, client):
        """Test retrieving weather records."""
        response = client.get('/api/weather')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'data' in data
        assert 'pagination' in data
        assert len(data['data']) == 4
    
    def test_get_weather_with_date_filter(self, client):
        """Test filtering weather records by date."""
        response = client.get('/api/weather?date=2020-01-01')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 2
        for record in data['data']:
            assert record['date'] == '2020-01-01'
    
    def test_get_weather_with_station_filter(self, client):
        """Test filtering weather records by station ID."""
        response = client.get('/api/weather?station_id=TEST001')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 3
        for record in data['data']:
            assert record['station_id'] == 'TEST001'
    
    def test_get_weather_with_both_filters(self, client):
        """Test filtering by both date and station ID."""
        response = client.get('/api/weather?date=2020-01-01&station_id=TEST001')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 1
        assert data['data'][0]['station_id'] == 'TEST001'
        assert data['data'][0]['date'] == '2020-01-01'
    
    def test_get_weather_invalid_date_format(self, client):
        """Test error handling for invalid date format."""
        response = client.get('/api/weather?date=invalid-date')
        assert response.status_code == 400
    
    def test_get_weather_pagination(self, client):
        """Test pagination of weather records."""
        response = client.get('/api/weather?page=1&per_page=2')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 2
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 2
        assert data['pagination']['total_items'] == 4
        assert data['pagination']['total_pages'] == 2
    
    def test_get_weather_pagination_page_2(self, client):
        """Test getting second page of results."""
        response = client.get('/api/weather?page=2&per_page=2')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 2
        assert data['pagination']['page'] == 2
    
    def test_get_weather_per_page_limit(self, client):
        """Test that per_page is capped at 100."""
        response = client.get('/api/weather?per_page=200')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['pagination']['per_page'] == 100


class TestWeatherStatsEndpoint:
    """Tests for /api/weather/stats endpoint."""
    
    def test_get_weather_stats(self, client):
        """Test retrieving weather statistics."""
        response = client.get('/api/weather/stats')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'data' in data
        assert 'pagination' in data
        assert len(data['data']) == 3
    
    def test_get_stats_with_year_filter(self, client):
        """Test filtering statistics by year."""
        response = client.get('/api/weather/stats?year=2020')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 2
        for stat in data['data']:
            assert stat['year'] == 2020
    
    def test_get_stats_with_station_filter(self, client):
        """Test filtering statistics by station ID."""
        response = client.get('/api/weather/stats?station_id=TEST001')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 2
        for stat in data['data']:
            assert stat['station_id'] == 'TEST001'
    
    def test_get_stats_with_both_filters(self, client):
        """Test filtering by both year and station ID."""
        response = client.get('/api/weather/stats?year=2020&station_id=TEST001')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 1
        assert data['data'][0]['station_id'] == 'TEST001'
        assert data['data'][0]['year'] == 2020
    
    def test_get_stats_pagination(self, client):
        """Test pagination of statistics."""
        response = client.get('/api/weather/stats?page=1&per_page=2')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 2
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 2
        assert data['pagination']['total_items'] == 3
        assert data['pagination']['total_pages'] == 2
    
    def test_stats_response_fields(self, client):
        """Test that statistics response contains expected fields."""
        response = client.get('/api/weather/stats?station_id=TEST001&year=2020')
        assert response.status_code == 200
        
        data = response.get_json()
        stat = data['data'][0]
        
        assert 'id' in stat
        assert 'station_id' in stat
        assert 'year' in stat
        assert 'avg_max_temp' in stat
        assert 'avg_min_temp' in stat
        assert 'total_precipitation' in stat
        
        assert stat['avg_max_temp'] == 12.5
        assert stat['avg_min_temp'] == -2.5
        assert stat['total_precipitation'] == 2.5


class TestSwaggerDocumentation:
    """Tests for Swagger/OpenAPI documentation."""
    
    def test_swagger_ui_available(self, client):
        """Test that Swagger UI is available."""
        response = client.get('/api/docs')
        assert response.status_code == 200
    
    def test_swagger_json_available(self, client):
        """Test that Swagger JSON spec is available."""
        response = client.get('/swagger.json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'swagger' in data or 'openapi' in data
        assert 'paths' in data
        assert '/api/weather' in data['paths']
        assert '/api/weather/stats' in data['paths']


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_result_set(self, client):
        """Test handling of empty result sets."""
        response = client.get('/api/weather?station_id=NONEXISTENT')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) == 0
        assert data['pagination']['total_items'] == 0
    
    def test_negative_page_number(self, client):
        """Test that negative page numbers default to 1."""
        response = client.get('/api/weather?page=-1')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['pagination']['page'] == 1
    
    def test_zero_per_page(self, client):
        """Test that zero per_page defaults to 1."""
        response = client.get('/api/weather?per_page=0')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['pagination']['per_page'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


