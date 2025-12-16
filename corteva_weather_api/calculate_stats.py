"""
Statistics Calculation Script

Problem 3: Data Analysis
- Calculates yearly statistics for each weather station:
  * Average maximum temperature (in degrees Celsius)
  * Average minimum temperature (in degrees Celsius)
  * Total accumulated precipitation (in centimeters)
- Ignores missing data (-9999 values, stored as NULL)
- Stores results in WeatherStatistics table
"""

import logging
from datetime import datetime
from sqlalchemy import func, extract

from models import db, WeatherRecord, WeatherStatistics
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def calculate_weather_statistics() -> dict:
    """
    Calculate yearly statistics for all weather stations.
    
    For each station and year, calculates:
    - Average max temperature (converted from tenths of °C to °C)
    - Average min temperature (converted from tenths of °C to °C)
    - Total precipitation (converted from tenths of mm to cm)
    
    Returns:
        Dictionary with calculation statistics
    """
    start_time = datetime.now()
    logger.info(f"Starting statistics calculation at {start_time}")
    
    # Get distinct station/year combinations
    station_years = db.session.query(
        WeatherRecord.station_id,
        extract('year', WeatherRecord.date).label('year')
    ).distinct().order_by(
        WeatherRecord.station_id,
        'year'
    ).all()
    
    total_combinations = len(station_years)
    logger.info(f"Found {total_combinations} station/year combinations to process")
    
    stats_created = 0
    stats_updated = 0
    
    for idx, (station_id, year) in enumerate(station_years, 1):
        year = int(year)
        
        # Calculate average max temperature (excluding NULL values)
        # Convert from tenths of degree Celsius to degrees Celsius
        avg_max_result = db.session.query(
            func.avg(WeatherRecord.max_temp)
        ).filter(
            WeatherRecord.station_id == station_id,
            extract('year', WeatherRecord.date) == year,
            WeatherRecord.max_temp.isnot(None)
        ).scalar()
        
        # Convert from tenths of degree to degrees
        avg_max_temp = avg_max_result / 10.0 if avg_max_result is not None else None
        
        # Calculate average min temperature
        avg_min_result = db.session.query(
            func.avg(WeatherRecord.min_temp)
        ).filter(
            WeatherRecord.station_id == station_id,
            extract('year', WeatherRecord.date) == year,
            WeatherRecord.min_temp.isnot(None)
        ).scalar()
        
        avg_min_temp = avg_min_result / 10.0 if avg_min_result is not None else None
        
        # Calculate total precipitation
        # Convert from tenths of mm to cm (divide by 100)
        total_precip_result = db.session.query(
            func.sum(WeatherRecord.precipitation)
        ).filter(
            WeatherRecord.station_id == station_id,
            extract('year', WeatherRecord.date) == year,
            WeatherRecord.precipitation.isnot(None)
        ).scalar()
        
        total_precipitation = total_precip_result / 100.0 if total_precip_result is not None else None
        
        # Check if statistics already exist for this station/year
        existing_stats = WeatherStatistics.query.filter_by(
            station_id=station_id,
            year=year
        ).first()
        
        if existing_stats:
            # Update existing record
            existing_stats.avg_max_temp = avg_max_temp
            existing_stats.avg_min_temp = avg_min_temp
            existing_stats.total_precipitation = total_precipitation
            stats_updated += 1
        else:
            # Create new statistics record
            new_stats = WeatherStatistics(
                station_id=station_id,
                year=year,
                avg_max_temp=avg_max_temp,
                avg_min_temp=avg_min_temp,
                total_precipitation=total_precipitation
            )
            db.session.add(new_stats)
            stats_created += 1
        
        # Commit periodically
        if idx % 100 == 0:
            db.session.commit()
            logger.info(f"Processed {idx}/{total_combinations} station/year combinations")
    
    # Final commit
    db.session.commit()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 60)
    logger.info("STATISTICS CALCULATION COMPLETE")
    logger.info(f"Start time: {start_time}")
    logger.info(f"End time: {end_time}")
    logger.info(f"Total duration: {duration:.2f} seconds")
    logger.info(f"Station/year combinations processed: {total_combinations}")
    logger.info(f"Statistics records created: {stats_created}")
    logger.info(f"Statistics records updated: {stats_updated}")
    logger.info("=" * 60)
    
    return {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': duration,
        'combinations_processed': total_combinations,
        'stats_created': stats_created,
        'stats_updated': stats_updated
    }


def main():
    """Main entry point for statistics calculation."""
    # Create Flask app and run calculation within app context
    app = create_app()
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # Check if there's data to process
        record_count = WeatherRecord.query.count()
        if record_count == 0:
            logger.error("No weather records found. Please run ingest.py first.")
            return
        
        logger.info(f"Found {record_count} weather records in database")
        
        # Calculate statistics
        stats = calculate_weather_statistics()
        
        print(f"\nStatistics calculation completed successfully!")
        print(f"Statistics created: {stats['stats_created']}")
        print(f"Statistics updated: {stats['stats_updated']}")


if __name__ == '__main__':
    main()


