# Sports Schedulers - Data Validators
# Author: Jose Ortiz
# Copyright: 2025

import re
from datetime import datetime

def validate_email(email):
    """Validate email format"""
    if not email:
        return True  # Email is optional
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional
    # Remove all non-digit characters
    digits_only = re.sub(r'[^0-9]', '', phone)
    return len(digits_only) >= 10

def validate_date(date_string):
    """Validate date format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_time(time_string):
    """Validate time format (HH:MM)"""
    try:
        datetime.strptime(time_string, '%H:%M')
        return True
    except ValueError:
        return False

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present and not empty"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == '':
            missing_fields.append(field)
    return missing_fields

def sanitize_string(value):
    """Sanitize string input"""
    if not value:
        return ''
    return str(value).strip()
