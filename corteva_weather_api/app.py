"""
Flask Application Factory

Creates and configures the Flask application with:
- SQLite database
- Flask-RESTX for REST API with Swagger documentation
- Weather and Statistics API endpoints
"""

import os
from flask import Flask
from flask_restx import Api, Resource, Namespace, fields, reqparse
from models import db, WeatherRecord, WeatherStatistics


def create_app(config=None):
    """
    Application factory for creating Flask app.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Default configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///weather.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['RESTX_MASK_SWAGGER'] = False
    
    # Override with custom config if provided
    if config:
        app.config.update(config)
    
    # Initialize database
    db.init_app(app)
    
    # Create tables within app context
    with app.app_context():
        db.create_all()
    
    # Initialize API with Swagger documentation
    api = Api(
        app,
        version='1.0',
        title='Corteva Weather API',
        description='REST API for weather data and statistics from Nebraska, Iowa, Illinois, Indiana, and Ohio weather stations (1985-2014)',
        doc='/api/docs'  # Swagger UI endpoint
    )
    
    # Create namespaces
    weather_ns = Namespace('weather', description='Weather data operations', path='/api')
    
    # Define API models for Swagger documentation
    weather_model = weather_ns.model('WeatherRecord', {
        'id': fields.Integer(description='Unique identifier'),
        'station_id': fields.String(description='Weather station ID'),
        'date': fields.String(description='Date of observation (YYYY-MM-DD)'),
        'max_temp': fields.Integer(description='Maximum temperature in tenths of degree Celsius (null if missing)'),
        'min_temp': fields.Integer(description='Minimum temperature in tenths of degree Celsius (null if missing)'),
        'precipitation': fields.Integer(description='Precipitation in tenths of millimeter (null if missing)')
    })
    
    weather_stats_model = weather_ns.model('WeatherStatistics', {
        'id': fields.Integer(description='Unique identifier'),
        'station_id': fields.String(description='Weather station ID'),
        'year': fields.Integer(description='Year of statistics'),
        'avg_max_temp': fields.Float(description='Average maximum temperature in degrees Celsius'),
        'avg_min_temp': fields.Float(description='Average minimum temperature in degrees Celsius'),
        'total_precipitation': fields.Float(description='Total accumulated precipitation in centimeters')
    })
    
    pagination_model = weather_ns.model('Pagination', {
        'page': fields.Integer(description='Current page number'),
        'per_page': fields.Integer(description='Items per page'),
        'total_pages': fields.Integer(description='Total number of pages'),
        'total_items': fields.Integer(description='Total number of items')
    })
    
    weather_response_model = weather_ns.model('WeatherResponse', {
        'data': fields.List(fields.Nested(weather_model)),
        'pagination': fields.Nested(pagination_model)
    })
    
    stats_response_model = weather_ns.model('StatsResponse', {
        'data': fields.List(fields.Nested(weather_stats_model)),
        'pagination': fields.Nested(pagination_model)
    })
    
    # Request parsers for query parameters
    weather_parser = reqparse.RequestParser()
    weather_parser.add_argument('date', type=str, help='Filter by date (YYYY-MM-DD)', location='args')
    weather_parser.add_argument('station_id', type=str, help='Filter by station ID', location='args')
    weather_parser.add_argument('page', type=int, default=1, help='Page number', location='args')
    weather_parser.add_argument('per_page', type=int, default=50, help='Items per page (max 100)', location='args')
    
    stats_parser = reqparse.RequestParser()
    stats_parser.add_argument('year', type=int, help='Filter by year', location='args')
    stats_parser.add_argument('station_id', type=str, help='Filter by station ID', location='args')
    stats_parser.add_argument('page', type=int, default=1, help='Page number', location='args')
    stats_parser.add_argument('per_page', type=int, default=50, help='Items per page (max 100)', location='args')
    
    @weather_ns.route('/weather')
    class WeatherList(Resource):
        """Weather data endpoint."""
        
        @weather_ns.doc('get_weather')
        @weather_ns.expect(weather_parser)
        @weather_ns.marshal_with(weather_response_model)
        def get(self):
            """
            Get weather records with optional filtering and pagination.
            
            Filter by date and/or station_id using query parameters.
            Results are paginated (default 50 per page, max 100).
            """
            args = weather_parser.parse_args()
            
            # Build query
            query = WeatherRecord.query
            
            # Apply filters
            if args['date']:
                try:
                    from datetime import datetime
                    filter_date = datetime.strptime(args['date'], '%Y-%m-%d').date()
                    query = query.filter(WeatherRecord.date == filter_date)
                except ValueError:
                    weather_ns.abort(400, 'Invalid date format. Use YYYY-MM-DD')
            
            if args['station_id']:
                query = query.filter(WeatherRecord.station_id == args['station_id'])
            
            # Order by date and station
            query = query.order_by(WeatherRecord.date.desc(), WeatherRecord.station_id)
            
            # Pagination
            page = max(1, args['page'])
            per_page = min(100, max(1, args['per_page']))
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'data': [record.to_dict() for record in pagination.items],
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total_pages': pagination.pages,
                    'total_items': pagination.total
                }
            }
    
    @weather_ns.route('/weather/stats')
    class WeatherStatsList(Resource):
        """Weather statistics endpoint."""
        
        @weather_ns.doc('get_weather_stats')
        @weather_ns.expect(stats_parser)
        @weather_ns.marshal_with(stats_response_model)
        def get(self):
            """
            Get weather statistics with optional filtering and pagination.
            
            Filter by year and/or station_id using query parameters.
            Statistics include:
            - Average max temperature (°C)
            - Average min temperature (°C)
            - Total precipitation (cm)
            
            Results are paginated (default 50 per page, max 100).
            """
            args = stats_parser.parse_args()
            
            # Build query
            query = WeatherStatistics.query
            
            # Apply filters
            if args['year']:
                query = query.filter(WeatherStatistics.year == args['year'])
            
            if args['station_id']:
                query = query.filter(WeatherStatistics.station_id == args['station_id'])
            
            # Order by year and station
            query = query.order_by(WeatherStatistics.year.desc(), WeatherStatistics.station_id)
            
            # Pagination
            page = max(1, args['page'])
            per_page = min(100, max(1, args['per_page']))
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'data': [stat.to_dict() for stat in pagination.items],
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total_pages': pagination.pages,
                    'total_items': pagination.total
                }
            }
    
    # Register namespace
    api.add_namespace(weather_ns)
    
    return app


# Create app instance for running directly
app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

