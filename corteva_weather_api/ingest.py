"""
Data Ingestion Script

Problem 2: Ingestion
- Reads weather data from raw text files
- Inserts records into SQLite database
- Handles duplicates (skips if record already exists)
- Produces log output with start/end times and record counts
"""

import os
import logging
from datetime import datetime
from pathlib import Path

from models import db, WeatherRecord
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Missing value indicator in the data files
MISSING_VALUE = -9999


def parse_weather_file(filepath: Path) -> list[dict]:
    """
    Parse a weather data file.
    
    Args:
        filepath: Path to the weather data file
        
    Returns:
        List of dictionaries containing parsed weather records
    """
    records = []
    station_id = filepath.stem  # Extract station ID from filename (e.g., USC00110072)
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) != 4:
                logger.warning(f"Skipping malformed line {line_num} in {filepath}: {line}")
                continue
            
            try:
                date_str, max_temp, min_temp, precipitation = parts
                
                # Parse date from YYYYMMDD format
                record_date = datetime.strptime(date_str.strip(), '%Y%m%d').date()
                
                # Parse temperature and precipitation values
                max_temp_val = int(max_temp.strip())
                min_temp_val = int(min_temp.strip())
                precip_val = int(precipitation.strip())
                
                records.append({
                    'station_id': station_id,
                    'date': record_date,
                    'max_temp': max_temp_val if max_temp_val != MISSING_VALUE else None,
                    'min_temp': min_temp_val if min_temp_val != MISSING_VALUE else None,
                    'precipitation': precip_val if precip_val != MISSING_VALUE else None
                })
                
            except ValueError as e:
                logger.warning(f"Error parsing line {line_num} in {filepath}: {e}")
                continue
    
    return records


def ingest_weather_data(data_dir: str, batch_size: int = 1000) -> dict:
    """
    Ingest weather data from all files in the specified directory.
    
    Args:
        data_dir: Path to directory containing weather data files
        batch_size: Number of records to insert per batch
        
    Returns:
        Dictionary with ingestion statistics
    """
    start_time = datetime.now()
    logger.info(f"Starting weather data ingestion at {start_time}")
    logger.info(f"Data directory: {data_dir}")
    
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Get all .txt files in the directory
    weather_files = sorted(data_path.glob('*.txt'))
    total_files = len(weather_files)
    logger.info(f"Found {total_files} weather data files")
    
    total_records_parsed = 0
    total_records_inserted = 0
    total_duplicates_skipped = 0
    
    for file_idx, filepath in enumerate(weather_files, 1):
        file_start = datetime.now()
        logger.info(f"Processing file {file_idx}/{total_files}: {filepath.name}")
        
        records = parse_weather_file(filepath)
        file_records_parsed = len(records)
        file_records_inserted = 0
        file_duplicates = 0
        
        # Insert records in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            for record_data in batch:
                # Check for existing record (duplicate prevention)
                existing = WeatherRecord.query.filter_by(
                    station_id=record_data['station_id'],
                    date=record_data['date']
                ).first()
                
                if existing:
                    file_duplicates += 1
                    continue
                
                # Create new record
                record = WeatherRecord(**record_data)
                db.session.add(record)
                file_records_inserted += 1
            
            # Commit batch
            db.session.commit()
        
        file_duration = (datetime.now() - file_start).total_seconds()
        logger.info(
            f"  Completed {filepath.name}: "
            f"{file_records_parsed} parsed, "
            f"{file_records_inserted} inserted, "
            f"{file_duplicates} duplicates skipped "
            f"({file_duration:.2f}s)"
        )
        
        total_records_parsed += file_records_parsed
        total_records_inserted += file_records_inserted
        total_duplicates_skipped += file_duplicates
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info(f"Start time: {start_time}")
    logger.info(f"End time: {end_time}")
    logger.info(f"Total duration: {duration:.2f} seconds")
    logger.info(f"Files processed: {total_files}")
    logger.info(f"Total records parsed: {total_records_parsed}")
    logger.info(f"Total records inserted: {total_records_inserted}")
    logger.info(f"Total duplicates skipped: {total_duplicates_skipped}")
    logger.info("=" * 60)
    
    return {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': duration,
        'files_processed': total_files,
        'records_parsed': total_records_parsed,
        'records_inserted': total_records_inserted,
        'duplicates_skipped': total_duplicates_skipped
    }


def main():
    """Main entry point for data ingestion."""
    import sys
    
    # Default data directory (relative to project root)
    default_data_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data_source', 'wx_data'
    )
    
    # Allow override via command line argument
    data_dir = sys.argv[1] if len(sys.argv) > 1 else default_data_dir
    
    # Create Flask app and run ingestion within app context
    app = create_app()
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Run ingestion
        stats = ingest_weather_data(data_dir)
        
        print(f"\nIngestion completed successfully!")
        print(f"Records inserted: {stats['records_inserted']}")


if __name__ == '__main__':
    main()


