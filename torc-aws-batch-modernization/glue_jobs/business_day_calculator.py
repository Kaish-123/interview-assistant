"""
Business Day Calculator for T+2 Settlement
"""
import csv
import datetime
from datetime import timedelta


class BusinessDayCalculator:
    def __init__(self, holidays_file=None):
        """Initialize with holiday calendar"""
        self.holidays = set()
        if holidays_file:
            self.load_holidays(holidays_file)

    def load_holidays(self, holidays_file):
        """Load holidays from CSV file"""
        with open(holidays_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.holidays.add(row['holiday_date'])

    def is_business_day(self, date):
        """Check if a date is a business day (not weekend or holiday)"""
        if isinstance(date, str):
            date = datetime.datetime.strptime(date, '%Y-%m-%d')

        # Check if weekend (Saturday = 5, Sunday = 6)
        if date.weekday() >= 5:
            return False

        # Check if holiday
        date_str = date.strftime('%Y-%m-%d')
        if date_str in self.holidays:
            return False

        return True

    def add_business_days(self, start_date, num_days):
        """Add business days to a date, skipping weekends and holidays"""
        if isinstance(start_date, str):
            current_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            current_date = start_date

        days_added = 0
        while days_added < num_days:
            current_date += timedelta(days=1)
            if self.is_business_day(current_date):
                days_added += 1

        return current_date.strftime('%Y-%m-%d')

    def calculate_t_plus_2(self, trade_date):
        """Calculate T+2 settlement date for a trade date"""
        return self.add_business_days(trade_date, 2)


