"""
Database Models for Weather Data API

Problem 1: Data Modeling
- WeatherRecord: Stores raw weather data from weather stations
- WeatherStatistics: Stores calculated yearly statistics per station (Problem 3)

Using SQLAlchemy ORM with SQLite database.
"""

from datetime import date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class WeatherRecord(db.Model):
    """
    Weather Record Model
    
    Stores daily weather observations from weather stations.
    
    Attributes:
        id: Primary key
        station_id: Weather station identifier (from filename, e.g., USC00110072)
        date: Date of the weather observation
        max_temp: Maximum temperature in tenths of a degree Celsius (-9999 = missing)
        min_temp: Minimum temperature in tenths of a degree Celsius (-9999 = missing)
        precipitation: Precipitation in tenths of a millimeter (-9999 = missing)
    
    Constraints:
        - Unique constraint on (station_id, date) to prevent duplicate records
    """
    __tablename__ = 'weather_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_id = db.Column(db.String(20), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    max_temp = db.Column(db.Integer, nullable=True)  # tenths of degree Celsius, NULL if missing
    min_temp = db.Column(db.Integer, nullable=True)  # tenths of degree Celsius, NULL if missing
    precipitation = db.Column(db.Integer, nullable=True)  # tenths of mm, NULL if missing
    
    __table_args__ = (
        db.UniqueConstraint('station_id', 'date', name='unique_station_date'),
    )
    
    def __repr__(self):
        return f"<WeatherRecord {self.station_id} {self.date}>"
    
    def to_dict(self):
        """Convert record to dictionary for API response."""
        return {
            'id': self.id,
            'station_id': self.station_id,
            'date': self.date.isoformat() if self.date else None,
            'max_temp': self.max_temp,
            'min_temp': self.min_temp,
            'precipitation': self.precipitation
        }


class WeatherStatistics(db.Model):
    """
    Weather Statistics Model (Problem 3)
    
    Stores yearly aggregated statistics for each weather station.
    
    Attributes:
        id: Primary key
        station_id: Weather station identifier
        year: Year of the statistics
        avg_max_temp: Average maximum temperature in degrees Celsius (NULL if no valid data)
        avg_min_temp: Average minimum temperature in degrees Celsius (NULL if no valid data)
        total_precipitation: Total accumulated precipitation in centimeters (NULL if no valid data)
    
    Constraints:
        - Unique constraint on (station_id, year) to prevent duplicate statistics
    """
    __tablename__ = 'weather_statistics'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_id = db.Column(db.String(20), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    avg_max_temp = db.Column(db.Float, nullable=True)  # degrees Celsius
    avg_min_temp = db.Column(db.Float, nullable=True)  # degrees Celsius
    total_precipitation = db.Column(db.Float, nullable=True)  # centimeters
    
    __table_args__ = (
        db.UniqueConstraint('station_id', 'year', name='unique_station_year'),
    )
    
    def __repr__(self):
        return f"<WeatherStatistics {self.station_id} {self.year}>"
    
    def to_dict(self):
        """Convert statistics to dictionary for API response."""
        return {
            'id': self.id,
            'station_id': self.station_id,
            'year': self.year,
            'avg_max_temp': round(self.avg_max_temp, 2) if self.avg_max_temp is not None else None,
            'avg_min_temp': round(self.avg_min_temp, 2) if self.avg_min_temp is not None else None,
            'total_precipitation': round(self.total_precipitation, 2) if self.total_precipitation is not None else None
        }


