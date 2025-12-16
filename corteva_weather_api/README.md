# Corteva Weather Data API

A REST API for weather data from Nebraska, Iowa, Illinois, Indiana, and Ohio weather stations (1985-2014).

## Overview

This project provides:
- **Data Models**: SQLAlchemy ORM models for weather records and statistics
- **Data Ingestion**: Script to ingest weather data from raw text files
- **Statistics Calculation**: Script to calculate yearly weather statistics
- **REST API**: Flask-based API with Swagger documentation

## Project Structure

```
corteva_weather_api/
├── app.py                 # Flask application and API endpoints
├── models.py              # SQLAlchemy data models
├── ingest.py              # Data ingestion script
├── calculate_stats.py     # Statistics calculation script
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── tests/                 # Unit tests
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_models.py
│   └── test_ingestion.py
└── weather.db             # SQLite database (created after ingestion)
```

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

1. **Clone/download the project**

2. **Create a virtual environment** (recommended):
   ```bash
   cd corteva_weather_api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Data Ingestion

1. **Ensure you have the weather data** from the Corteva code challenge repository:
   ```bash
   git clone https://github.com/corteva/code-challenge-template ../data_source
   ```

2. **Run the ingestion script**:
   ```bash
   python ingest.py ../data_source/wx_data
   ```
   
   This will:
   - Parse all weather data files
   - Insert records into the SQLite database
   - Skip duplicates if run multiple times
   - Log progress with start/end times and record counts

3. **Calculate yearly statistics**:
   ```bash
   python calculate_stats.py
   ```
   
   This will calculate for each station/year:
   - Average maximum temperature (°C)
   - Average minimum temperature (°C)
   - Total accumulated precipitation (cm)

### Running the API

Start the Flask development server:

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

#### Swagger Documentation

- **URL**: `http://localhost:5000/api/docs`
- Interactive API documentation with Swagger UI

#### Weather Records

- **URL**: `GET /api/weather`
- **Query Parameters**:
  - `date` (optional): Filter by date (YYYY-MM-DD format)
  - `station_id` (optional): Filter by station ID
  - `page` (optional): Page number (default: 1)
  - `per_page` (optional): Items per page (default: 50, max: 100)

**Example Requests**:
```bash
# Get all weather records (paginated)
curl http://localhost:5000/api/weather

# Filter by date
curl "http://localhost:5000/api/weather?date=2000-07-04"

# Filter by station
curl "http://localhost:5000/api/weather?station_id=USC00110072"

# Combined filters with pagination
curl "http://localhost:5000/api/weather?station_id=USC00110072&page=2&per_page=20"
```

**Example Response**:
```json
{
  "data": [
    {
      "id": 1,
      "station_id": "USC00110072",
      "date": "2014-12-31",
      "max_temp": 67,
      "min_temp": -17,
      "precipitation": 0
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 100,
    "total_items": 5000
  }
}
```

#### Weather Statistics

- **URL**: `GET /api/weather/stats`
- **Query Parameters**:
  - `year` (optional): Filter by year
  - `station_id` (optional): Filter by station ID
  - `page` (optional): Page number (default: 1)
  - `per_page` (optional): Items per page (default: 50, max: 100)

**Example Requests**:
```bash
# Get all statistics (paginated)
curl http://localhost:5000/api/weather/stats

# Filter by year
curl "http://localhost:5000/api/weather/stats?year=2000"

# Filter by station
curl "http://localhost:5000/api/weather/stats?station_id=USC00110072"
```

**Example Response**:
```json
{
  "data": [
    {
      "id": 1,
      "station_id": "USC00110072",
      "year": 2014,
      "avg_max_temp": 15.23,
      "avg_min_temp": 4.56,
      "total_precipitation": 85.32
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 10,
    "total_items": 500
  }
}
```

### Running Tests

Run the test suite with pytest:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=term-missing
```

## Data Model

### WeatherRecord

Stores daily weather observations from weather stations.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| station_id | String | Weather station identifier |
| date | Date | Date of observation |
| max_temp | Integer | Max temp in tenths of °C (NULL if missing) |
| min_temp | Integer | Min temp in tenths of °C (NULL if missing) |
| precipitation | Integer | Precipitation in tenths of mm (NULL if missing) |

**Constraints**: Unique on (station_id, date)

### WeatherStatistics

Stores yearly aggregated statistics for each weather station.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| station_id | String | Weather station identifier |
| year | Integer | Year of statistics |
| avg_max_temp | Float | Average max temp in °C |
| avg_min_temp | Float | Average min temp in °C |
| total_precipitation | Float | Total precipitation in cm |

**Constraints**: Unique on (station_id, year)

## AWS Deployment (Extra Credit)

### Recommended Architecture

For deploying this application to AWS, I recommend the following architecture:

#### Components

1. **Amazon RDS (PostgreSQL)**
   - Replace SQLite with PostgreSQL for production
   - Use RDS for managed database with automatic backups
   - Enable Multi-AZ for high availability

2. **AWS Elastic Beanstalk or ECS**
   - Deploy the Flask API using Elastic Beanstalk for simplicity
   - Alternatively, use ECS with Fargate for containerized deployment
   - Auto-scaling based on CPU/memory utilization

3. **Amazon API Gateway** (optional)
   - Add API throttling and rate limiting
   - Enable API keys for access control
   - Caching for improved performance

4. **AWS Lambda + EventBridge**
   - Schedule the data ingestion script to run periodically
   - EventBridge rule triggers Lambda function daily/weekly
   - Lambda reads from S3 and updates RDS

5. **Amazon S3**
   - Store raw weather data files
   - Use for data lake pattern

6. **AWS CloudWatch**
   - Application logging and monitoring
   - Set up alarms for errors and performance

#### Infrastructure as Code

Use **AWS CloudFormation** or **Terraform** to define infrastructure:

```yaml
# Example CloudFormation resources
Resources:
  WeatherDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: db.t3.micro
      Engine: postgres
      # ...

  WeatherAPIEnvironment:
    Type: AWS::ElasticBeanstalk::Environment
    Properties:
      ApplicationName: corteva-weather-api
      SolutionStackName: "64bit Amazon Linux 2 v3.x running Python 3.9"
      # ...

  IngestionLambda:
    Type: AWS::Lambda::Function
    Properties:
      Runtime: python3.9
      Handler: lambda_handler.handler
      # ...

  DailyIngestionRule:
    Type: AWS::Events::Rule
    Properties:
      ScheduleExpression: "rate(1 day)"
      Targets:
        - Arn: !GetAtt IngestionLambda.Arn
          Id: "DailyIngestion"
```

#### Deployment Steps

1. **Containerize the application**:
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
   ```

2. **Push to ECR**:
   ```bash
   aws ecr create-repository --repository-name corteva-weather-api
   docker build -t corteva-weather-api .
   docker push <account>.dkr.ecr.<region>.amazonaws.com/corteva-weather-api
   ```

3. **Deploy with ECS or Elastic Beanstalk**

4. **Set up CI/CD with AWS CodePipeline**:
   - Trigger on GitHub push
   - Build with CodeBuild
   - Deploy to ECS/Elastic Beanstalk

#### Cost Optimization

- Use **RDS Reserved Instances** for database
- Enable **auto-scaling** for compute resources
- Use **S3 Intelligent-Tiering** for data storage
- Consider **Aurora Serverless** for variable workloads

## Author

Created for Corteva Data Engineering coding exercise.

## License

MIT License


