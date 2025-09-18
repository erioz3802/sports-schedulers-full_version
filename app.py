"""Sports Schedulers - Web Application
Author: Jose Ortiz
Date: September 12, 2025
Copyright (c) 2025 Jose Ortiz. All rights reserved.

Professional sports scheduling management system."""

import re
from flask import Flask, make_response, render_template, render_template_string, request, jsonify, redirect, session, Response, g
import sqlite3
import hashlib
import logging
from datetime import datetime
from functools import wraps
import csv
import io
from werkzeug.utils import secure_filename
import tempfile
import json
import os
from decimal import Decimal, InvalidOperation

# Enhanced Access Control Decorators
def require_role(allowed_roles):
    """Enhanced decorator to require specific user roles with league boundary checks"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_league_access(user_id, league_id, required_roles=['admin', 'assigner']):
    """Check if user has access to specific league"""
    if session.get('role') == 'superadmin':
        return True
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    result = cursor.execute("""
        SELECT COUNT(*) as count FROM league_assignments 
        WHERE user_id = ? AND league_id = ? AND role IN ({}) AND is_active = 1
    """.format(','.join(['?' for _ in required_roles])), 
    [user_id, league_id] + required_roles).fetchone()
    
    conn.close()
    return result['count'] > 0

def enforce_user_boundaries(f):
    """Decorator to enforce user access boundaries based on role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = session.get('role')
        user_id = session.get('user_id')
        
        # Superadmin has access to everything
        if user_role == 'superadmin':
            return f(*args, **kwargs)
        
        # Add user context to kwargs for filtering
        kwargs['current_user_id'] = user_id
        kwargs['current_user_role'] = user_role
        
        return f(*args, **kwargs)
    return decorated_function

# Import assistant blueprint - handle missing gracefully
try:
    from assistant import assistant_bp
    ASSISTANT_AVAILABLE = True
except ImportError:
    print("Assistant module not found - continuing without assistant features")
    ASSISTANT_AVAILABLE = False

# Flask app initialization
app = Flask(__name__)
app.secret_key = 'sports-schedulers-secret-key-2025-jose-ortiz'

# Database configuration
DATABASE_PATH = 'scheduler.db'

# Register assistant blueprint if available
if ASSISTANT_AVAILABLE:
    app.register_blueprint(assistant_bp)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function_admin(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Login required'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function_admin

def admin_required(f):
    @wraps(f)
    def decorated_function_2(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Login required'}), 401
        if session.get('role') not in ['admin', 'superadmin']:
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function_2

# Billing System Functions and Validation
def validate_fee_amount(amount):
    """Validate fee amount with comprehensive checks"""
    try:
        if not amount and amount != 0:
            raise ValueError("Fee amount is required")
        
        # Convert to Decimal for precise handling
        fee_decimal = Decimal(str(amount).strip())
        
        if fee_decimal < 0:
            raise ValueError("Fee amount must be non-negative")
        
        if fee_decimal > Decimal('999999.99'):
            raise ValueError("Fee amount exceeds maximum allowed value")
        
        # Check decimal places
        if fee_decimal.as_tuple().exponent < -2:
            raise ValueError("Fee amount can have maximum 2 decimal places")
        
        return fee_decimal
        
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Invalid fee amount: {str(e)}")

def require_billing_admin(f):
    """Decorator to require admin privileges for billing operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({"error": "Authentication required"}), 401
            return redirect('/login')
        
        user_role = session.get('role', '').lower()
        if user_role not in ['admin', 'superadmin']:
            if request.is_json:
                return jsonify({"error": "Admin privileges required for billing operations"}), 403
            return redirect('/')
        
        # Set g.user for billing system compatibility
        g.user = {
            'id': session.get('user_id'),
            'role': user_role,
            'username': session.get('username'),
            'full_name': session.get('full_name')
        }
        
        return f(*args, **kwargs)
    return decorated_function

def validate_billing_entity_data(data):
    """Validate bill-to entity data with comprehensive checks"""
    errors = []
    
    # Required field validation
    if not data.get('name', '').strip():
        errors.append("Entity name is required")
    elif len(data['name'].strip()) > 200:
        errors.append("Entity name must be 200 characters or less")
    
    # Optional field validation with length limits
    optional_fields = {
        'contact_person': 100,
        'email': 100,
        'phone': 20,
        'address': 200,
        'city': 50,
        'state': 20,
        'zip_code': 10,
        'tax_id': 50
    }
    
    for field, max_length in optional_fields.items():
        if data.get(field) and len(str(data[field]).strip()) > max_length:
            errors.append(f"{field.replace('_', ' ').title()} must be {max_length} characters or less")
    
    # Email format validation (basic)
    if data.get('email') and '@' not in data.get('email', ''):
        errors.append("Invalid email format")
    
    return errors

def validate_billing_structure_data(data):
    """Validate billing structure data with comprehensive checks"""
    errors = []
    
    # Required field validation
    if not data.get('level_name', '').strip():
        errors.append("Level name is required")
    elif len(data['level_name'].strip()) > 100:
        errors.append("Level name must be 100 characters or less")
    
    # Bill amount validation
    if 'bill_amount' not in data:
        errors.append("Bill amount is required")
    else:
        try:
            amount = Decimal(str(data['bill_amount']))
            if amount < Decimal('0.01'):
                errors.append("Bill amount must be at least $0.01")
            elif amount > Decimal('999999.99'):
                errors.append("Bill amount cannot exceed $999,999.99")
            elif amount.as_tuple().exponent < -2:
                errors.append("Bill amount can have at most 2 decimal places")
        except (InvalidOperation, ValueError):
            errors.append("Invalid bill amount format")
    
    # Bill-to entity validation
    if not data.get('bill_to_id'):
        errors.append("Bill-to entity is required")
    elif not isinstance(data['bill_to_id'], int) or data['bill_to_id'] <= 0:
        errors.append("Invalid bill-to entity ID")
    
    # Notes validation (optional)
    if data.get('notes') and len(str(data['notes']).strip()) > 500:
        errors.append("Notes must be 500 characters or less")
    
    return errors

# Enhanced user context for billing system
@app.before_request
def load_user_context():
    """Load user context for billing system compatibility"""
    if 'user_id' in session:
        g.user = {
            'id': session.get('user_id'),
            'role': session.get('role', '').lower(),
            'username': session.get('username'),
            'full_name': session.get('full_name')
        }
    else:
        g.user = None

# Add missing database table initialization
def init_missing_tables():
    """Initialize any missing database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Locations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            contact_person TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            capacity INTEGER,
            notes TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_by INTEGER,
            created_date TEXT,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    """)
    
    # Check if we need to add missing columns to existing tables
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns to users table if they don't exist
        missing_user_columns = {
            'first_name': 'TEXT',
            'last_name': 'TEXT', 
            'address': 'TEXT',
            'city': 'TEXT',
            'state': 'TEXT',
            'zip_code': 'TEXT',
            'certifications': 'TEXT',
            'sports': 'TEXT',
            'experience_years': 'INTEGER DEFAULT 0',
            'availability_notes': 'TEXT'
        }
        
        for column, datatype in missing_user_columns.items():
            if column not in columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {datatype}")
                
    except Exception as e:
        print(f"Column addition warning: {e}")
    
    # Check and add missing columns to games table
    try:
        cursor.execute("PRAGMA table_info(games)")
        columns = [column[1] for column in cursor.fetchall()]
        
        missing_game_columns = {
            'status': 'TEXT DEFAULT "scheduled"',
            'link_group': 'TEXT',
            'assigned_fee': 'DECIMAL(8,2)',
            'fee_override': 'BOOLEAN DEFAULT 0'
        }
        
        for column, datatype in missing_game_columns.items():
            if column not in columns:
                cursor.execute(f"ALTER TABLE games ADD COLUMN {column} {datatype}")
                
    except Exception as e:
        print(f"Games table column addition warning: {e}")
    
    # Official availability table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS official_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            official_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            availability_type TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            reason TEXT,
            created_date TEXT NOT NULL,
            FOREIGN KEY (official_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(official_id, date, start_time, end_time)
        )
    """)
    
    # Game assignment status tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignment_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            official_id INTEGER NOT NULL,
            response TEXT NOT NULL,
            response_date TEXT,
            notes TEXT,
            FOREIGN KEY (assignment_id) REFERENCES assignments (id) ON DELETE CASCADE,
            FOREIGN KEY (official_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(assignment_id, official_id)
        )
    """)
    
    # Billing system tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bill_to_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            tax_id TEXT,
            created_date TEXT NOT NULL,
            created_by INTEGER,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS league_billing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER NOT NULL,
            level_name TEXT NOT NULL,
            bill_amount DECIMAL(10,2) NOT NULL,
            bill_to_id INTEGER NOT NULL,
            created_date TEXT NOT NULL,
            updated_date TEXT,
            created_by INTEGER,
            is_active BOOLEAN DEFAULT 1,
            notes TEXT,
            FOREIGN KEY (league_id) REFERENCES leagues (id) ON DELETE CASCADE,
            FOREIGN KEY (bill_to_id) REFERENCES bill_to_entities (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            UNIQUE(league_id, level_name)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS league_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER NOT NULL,
            level_name TEXT NOT NULL,
            official_fee DECIMAL(8,2) NOT NULL,
            notes TEXT,
            created_date TEXT NOT NULL,
            updated_date TEXT,
            created_by INTEGER,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (league_id) REFERENCES leagues (id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users (id),
            UNIQUE(league_id, level_name)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predetermined_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sport TEXT NOT NULL,
            category TEXT NOT NULL,
            level_name TEXT NOT NULL,
            display_order INTEGER DEFAULT 0,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            UNIQUE(sport, category, level_name)
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database tables verified/updated")

def init_database():
    """Initialize database with all required tables"""
    init_missing_tables()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            role TEXT DEFAULT 'official',
            is_active BOOLEAN DEFAULT 1,
            created_date TEXT,
            last_login TEXT
        )
    """)
    
    # Games table  
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            location TEXT,
            sport TEXT NOT NULL,
            league TEXT,
            level TEXT,
            officials_needed INTEGER DEFAULT 1,
            notes TEXT,
            created_date TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    """)

    # Leagues table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leagues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sport TEXT NOT NULL,
            season TEXT NOT NULL,
            levels TEXT,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    """)

    # League levels table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS league_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER NOT NULL,
            level_name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_date TEXT,
            notes TEXT,
            FOREIGN KEY (league_id) REFERENCES leagues (id) ON DELETE CASCADE
        )
    """)
    
    # Assignments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            official_id INTEGER NOT NULL,
            position TEXT DEFAULT 'Official',
            status TEXT DEFAULT 'pending',
            fee DECIMAL(8,2) DEFAULT 0.00,
            assigned_date TEXT,
            assigned_by INTEGER,
            FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE,
            FOREIGN KEY (official_id) REFERENCES users (id),
            FOREIGN KEY (assigned_by) REFERENCES users (id)
        )
    """)
    
    # Check if test user exists
    test_user = cursor.execute("SELECT id FROM users WHERE username = 'jose_1'").fetchone()
    if not test_user:
        cursor.execute("""
            INSERT INTO users (username, password, full_name, email, role, is_active, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'jose_1', 
            hash_password('Josu2398-1'),
            'Jose Ortiz',
            'jose@sportsschedulers.com', 
            'superadmin',
            1,
            datetime.now().isoformat()
        ))
        print("Created test user: jose_1 / Josu2398-1")
    
    # Insert sample data if tables are empty
    games_count = cursor.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    if games_count == 0:
        print("Adding sample data...")
        sample_games = [
            ('2025-09-05', '19:00', 'Lakers', 'Warriors', 'Staples Center', 'Basketball', 'NBA', 'Professional', 3),
            ('2025-09-06', '20:30', 'Cowboys', 'Giants', 'AT&T Stadium', 'Football', 'NFL', 'Professional', 7),
            ('2025-09-07', '18:00', 'Red Sox', 'Yankees', 'Fenway Park', 'Baseball', 'MLB', 'Professional', 4),
        ]
        
        for game in sample_games:
            cursor.execute("""
                INSERT INTO games (date, time, home_team, away_team, location, sport, league, level, officials_needed, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, game + (datetime.now().isoformat(),))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

# Database migration tables for role-based access control
def create_migration_tables():
    """Create tables for role-based league access control if they don't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # League assignments table for user-league relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS league_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                league_id INTEGER NOT NULL,
                assigned_by INTEGER NOT NULL,
                assigned_date TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (league_id) REFERENCES leagues (id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by) REFERENCES users (id),
                UNIQUE(user_id, league_id)
            )
        """)
        
        # Add created_by to leagues if it doesn't exist
        cursor.execute("PRAGMA table_info(leagues)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'created_by' not in columns:
            cursor.execute("ALTER TABLE leagues ADD COLUMN created_by INTEGER REFERENCES users(id)")
        
        # Add created_by to games if it doesn't exist  
        cursor.execute("PRAGMA table_info(games)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'created_by' not in columns:
            cursor.execute("ALTER TABLE games ADD COLUMN created_by INTEGER REFERENCES users(id)")
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_league_assignments_user ON league_assignments(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_league_assignments_league ON league_assignments(league_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leagues_created_by ON leagues(created_by)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_created_by ON games(created_by)")
        
        conn.commit()
        conn.close()
        print("Migration tables created/verified successfully")
        
    except Exception as e:
        print(f"Error creating migration tables: {e}")

def add_ranking_system():
    """Add ranking system columns to support admin-assigned rankings"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create official_rankings table for league-specific rankings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS official_rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                official_id INTEGER NOT NULL,
                league_id INTEGER NOT NULL,
                ranking INTEGER CHECK(ranking >= 1 AND ranking <= 5),
                assigned_by INTEGER NOT NULL,
                assigned_date TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (official_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (league_id) REFERENCES leagues (id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by) REFERENCES users (id),
                UNIQUE(official_id, league_id)
            )
        """)
        
        # Get current users table structure
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add basic columns if they don't exist
        basic_columns = {
            'phone': 'TEXT',
            'availability': 'TEXT',
            'last_login': 'TEXT'
        }
        
        for column_name, column_type in basic_columns.items():
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                print(f"Added column {column_name} to users table")
        
        conn.commit()
        conn.close()
        print("Ranking system tables created successfully")
        
    except Exception as e:
        print(f"Error creating ranking system: {e}")

# Login template
LOGIN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sports Schedulers - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, rgb(102,126,234) 0%, rgb(118,75,162) 100%); 
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .login-container { 
            background: white; 
            padding: 40px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
            width: 400px; 
            max-width: 90%; 
        }
        .login-header { text-align: center; margin-bottom: 30px; }
        .login-header h1 { color: rgb(51,51,51); margin-bottom: 10px; font-size: 2rem; }
        .login-header p { color: rgb(102,102,102); }
        .form-group { margin-bottom: 20px; }
        .form-group label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600; 
            color: rgb(51,51,51); 
        }
        .form-group input { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid rgb(225,229,233); 
            border-radius: 8px; 
            font-size: 16px; 
            transition: all 0.3s; 
        }
        .form-group input:focus { 
            outline: none; 
            border-color: rgb(102,126,234); 
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); 
        }
        .login-btn { 
            width: 100%; 
            padding: 15px; 
            background: linear-gradient(135deg, rgb(102,126,234) 0%, rgb(118,75,162) 100%); 
            color: white; 
            border: none; 
            border-radius: 8px; 
            font-size: 16px; 
            font-weight: 600; 
            cursor: pointer; 
            transition: all 0.3s; 
        }
        .login-btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3); 
        }
        .alert { 
            padding: 15px; 
            margin-bottom: 20px; 
            border-radius: 8px; 
            background: rgb(248,215,218); 
            color: rgb(114,28,36); 
            border: 1px solid rgb(245,198,203); 
        }
        .footer { 
            text-align: center; 
            margin-top: 20px; 
            color: rgb(102,102,102); 
            font-size: 12px; 
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>Sports Schedulers</h1>
            <p>Professional Sports Management System</p>
        </div>
        {% if error %}
            <div class="alert">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autocomplete="username">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required autocomplete="current-password">
            </div>
            <button type="submit" class="login-btn">Login to System</button>
        </form>
        <div class="footer">
            <p>&copy; 2025 Jose Ortiz. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""

# Helper functions for league access
def get_user_league_ids(user_id):
    """Get league IDs that a user has access to"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user role
        user = cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            conn.close()
            return []
        
        # Superadmin sees all leagues
        if user['role'] == 'superadmin':
            cursor.execute("SELECT id FROM leagues")
            league_ids = [row['id'] for row in cursor.fetchall()]
        else:
            # Admin/Assigner only sees assigned leagues
            cursor.execute("""
                SELECT league_id FROM league_assignments 
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            league_ids = [row['league_id'] for row in cursor.fetchall()]
        
        conn.close()
        return league_ids
    except Exception as e:
        print(f"Error getting user league IDs: {e}")
        return []

def filter_by_user_leagues(query, table_alias="", league_column="league_id"):
    """Add league filtering to a query based on current user"""
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    if user_role == 'superadmin':
        return query, []  # No filtering for superadmin
    
    league_ids = get_user_league_ids(user_id)
    if not league_ids:
        # User has no league access, return impossible condition
        return query + f" AND 1=0", []
    
    # Add league filtering
    table_prefix = f"{table_alias}." if table_alias else ""
    placeholders = ",".join(["?"] * len(league_ids))
    query += f" AND {table_prefix}{league_column} IN ({placeholders})"
    
    return query, league_ids

def check_league_access_simple(league_id):
    """Check if current user has access to a specific league"""
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    if user_role == 'superadmin':
        return True
    
    user_league_ids = get_user_league_ids(user_id)
    return league_id in user_league_ids

# Automatic fee assignment logic
def assign_fee_to_game(league_name, level_name, user_id):
    """Automatically assign fee to game based on league and level"""
    try:
        if not league_name or not level_name:
            return None, False  # No fee, no override
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Look up fee structure
        cursor.execute("""
            SELECT lf.official_fee 
            FROM league_fees lf
            JOIN leagues l ON l.id = lf.league_id
            WHERE l.name = ? AND LOWER(lf.level_name) = LOWER(?) AND lf.is_active = 1
        """, (league_name, level_name))
        
        fee_result = cursor.fetchone()
        conn.close()
        
        if fee_result:
            return float(fee_result[0]), False  # Found fee, not an override
        
        return None, False  # No fee structure found
        
    except Exception as e:
        logger.error(f"Error assigning fee to game: {e}")
        return None, False

# Initialize billing system
def initialize_billing_system():
    """Initialize the billing system components"""
    try:
        print("Billing system initialization complete")
        return True
    except Exception as e:
        print(f"Failed to initialize billing system: {e}")
        print("Application will continue without billing features")
        return False

# Routes

@app.route('/official')
@login_required
def official_dashboard():
    """Official-only dashboard"""
    if session.get('role') != 'official':
        return redirect('/')
    return render_template('official_dashboard.html')

@app.route('/api/officials/my-games', methods=['GET'])
@login_required
def get_my_games():
    """Get games assigned to the current official"""
    if session.get('role') != 'official':
        return jsonify({'success': False, 'message': 'Officials only'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT g.id, g.date, g.time, g.home_team, g.away_team, 
                   g.location, g.sport, g.league, g.level, g.notes,
                   a.position, a.status
            FROM games g
            INNER JOIN assignments a ON g.id = a.game_id
            WHERE a.official_id = ?
            ORDER BY g.date DESC, g.time DESC
        """, (user_id,))
        
        games = []
        for row in cursor.fetchall():
            games.append({
                'id': row['id'],
                'date': row['date'],
                'time': row['time'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'location': row['location'],
                'sport': row['sport'],
                'league': row['league'],
                'level': row['level'],
                'notes': row['notes'],
                'position': row['position'],
                'status': row['status'],
                'response': 'pending',
                'assigned_officials': [],
                'empty_slots': 1,
                'officials_needed': 2
            })
        
        conn.close()
        return jsonify({'success': True, 'games': games})
        
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/officials/my-stats', methods=['GET'])
@login_required
def get_my_stats():
    """Get statistics for the current official"""
    if session.get('role') != 'official':
        return jsonify({'success': False, 'message': 'Officials only'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total games
        total = cursor.execute("""
            SELECT COUNT(*) as count FROM assignments 
            WHERE official_id = ?
        """, (user_id,)).fetchone()
        stats['total'] = total['count'] if total else 0
        
        # Upcoming games
        upcoming = cursor.execute("""
            SELECT COUNT(*) as count FROM assignments a
            INNER JOIN games g ON a.game_id = g.id
            WHERE a.official_id = ? AND g.date >= date('now')
        """, (user_id,)).fetchone()
        stats['upcoming'] = upcoming['count'] if upcoming else 0
        
        # Completed games
        completed = cursor.execute("""
            SELECT COUNT(*) as count FROM assignments a
            INNER JOIN games g ON a.game_id = g.id
            WHERE a.official_id = ? AND g.date < date('now')
        """, (user_id,)).fetchone()
        stats['completed'] = completed['count'] if completed else 0
        
        # This month games
        this_month = cursor.execute("""
            SELECT COUNT(*) as count FROM assignments a
            INNER JOIN games g ON a.game_id = g.id
            WHERE a.official_id = ? 
            AND strftime('%Y-%m', g.date) = strftime('%Y-%m', 'now')
        """, (user_id,)).fetchone()
        stats['this_month'] = this_month['count'] if this_month else 0
        
        conn.close()
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/officials/profile', methods=['GET'])
@login_required
def get_official_profile():
    """Get current official's profile"""
    if session.get('role') != 'official':
        return jsonify({'success': False, 'message': 'Officials only'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, full_name, email, phone, address, 
                   created_date, last_login, is_active
            FROM users WHERE id = ?
        """, (user_id,))
        
        user_data = cursor.fetchone()
        if not user_data:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user = {
            'id': user_data['id'],
            'username': user_data['username'],
            'full_name': user_data['full_name'],
            'email': user_data['email'],
            'phone': user_data['phone'],
            'address': user_data['address'],
            'created_date': user_data['created_date'],
            'last_login': user_data['last_login'],
            'is_active': user_data['is_active']
        }
        
        conn.close()
        return jsonify({'success': True, 'user': user})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/officials/profile', methods=['PUT'])
@login_required
def update_official_profile():
    """Update current official's profile"""
    if session.get('role') != 'official':
        return jsonify({'success': False, 'message': 'Officials only'}), 403
    
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET full_name = ?, email = ?, phone = ?, address = ?
            WHERE id = ?
        """, (
            data.get('full_name'),
            data.get('email'), 
            data.get('phone'),
            data.get('address'),
            user_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def home():
    """Main route with role-based redirection"""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_role = session.get('role')
    
    # Redirect officials to their dedicated interface
    if user_role == 'official':
        return redirect('/official')
    
    # Admin and superadmin users go to regular dashboard
    try:
        return render_template('dashboard.html', session=session)
    except FileNotFoundError:
        return "dashboard.html not found. Please ensure the file exists.", 500

@app.route('/status')
def status():
    """Show application status page"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html', session=session)

@app.route('/login', methods=['GET', 'POST'])  
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template_string(LOGIN_TEMPLATE, error='Please enter username and password')
        
        try:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? AND is_active = 1', 
                (username,)
            ).fetchone()
            
            if user and user['password'] == hash_password(password):
                session['user_id'] = user['id']
                session['username'] = user['username'] 
                session['role'] = user['role']
                session['full_name'] = user['full_name']
                
                # Update last login
                conn.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                           (datetime.now().isoformat(), user['id']))
                conn.commit()
                conn.close()
                
                # Role-based redirect
                if user['role'] == 'official':
                    return redirect('/official')
                else:
                    return redirect('/')
            else:
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error='Invalid username or password')
                
        except Exception as e:
            print(f"Login error: {e}")
            return render_template_string(LOGIN_TEMPLATE, error='Database error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# API Routes
@app.route('/api/session')
@login_required
def get_session():
    """Get current session information"""
    try:
        return jsonify({
            'success': True,
            'session': {
                'user_id': session.get('user_id'),
                'username': session.get('username'),
                'full_name': session.get('full_name'),
                'role': session.get('role')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_auth_me():
    """Get current authenticated user information (for compatibility)"""
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, full_name, email, phone, address, 
                   role, created_date, last_login, is_active
            FROM users WHERE id = ?
        """, (user_id,))
        
        user_data = cursor.fetchone()
        if not user_data:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user = {
            'id': user_data['id'],
            'username': user_data['username'],
            'full_name': user_data['full_name'],
            'email': user_data['email'],
            'phone': user_data['phone'],
            'address': user_data['address'],
            'role': user_data['role'],
            'created_date': user_data['created_date'],
            'last_login': user_data['last_login'],
            'is_active': user_data['is_active']
        }
        
        conn.close()
        return jsonify({'success': True, 'user': user})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard')
@login_required
def api_dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current user info for role-based filtering
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        stats = {}
        
        # Role-based game counting
        if user_role == 'superadmin':
            # Super admins see ALL games
            try:
                stats['upcoming_games'] = conn.execute(
                    'SELECT COUNT(*) as count FROM games WHERE date >= date("now")'
                ).fetchone()['count']
            except Exception as e:
                print(f"Error getting upcoming games: {e}")
                stats['upcoming_games'] = 0
        elif user_role == 'admin':
            # Admins see only games from leagues they're assigned to
            try:
                stats['upcoming_games'] = conn.execute("""
                    SELECT COUNT(*) as count FROM games g
                    WHERE g.date >= date("now")
                    AND (g.league IN (
                        SELECT l.name FROM leagues l
                        JOIN league_assignments la ON l.id = la.league_id
                        WHERE la.user_id = ? AND la.is_active = 1
                    ) OR g.league IS NULL OR g.league = '')
                """, (user_id,)).fetchone()['count']
            except Exception as e:
                print(f"Error getting upcoming games: {e}")
                stats['upcoming_games'] = 0
        elif user_role == 'official':
            # Officials see only games they're assigned to
            try:
                stats['upcoming_games'] = conn.execute("""
                    SELECT COUNT(*) as count FROM games g
                    WHERE g.date >= date("now")
                    AND g.id IN (
                        SELECT a.game_id FROM assignments a
                        WHERE a.official_id = ?
                    )
                """, (user_id,)).fetchone()['count']
            except Exception as e:
                print(f"Error getting upcoming games: {e}")
                stats['upcoming_games'] = 0
        else:
            stats['upcoming_games'] = 0
        
        # Role-based assignment counting
        if user_role == 'superadmin':
            try:
                stats['total_assignments'] = conn.execute(
                    'SELECT COUNT(*) as count FROM assignments'
                ).fetchone()['count']
            except Exception as e:
                print(f"Error getting total assignments: {e}")
                stats['total_assignments'] = 0
        elif user_role == 'admin':
            try:
                stats['total_assignments'] = conn.execute("""
                    SELECT COUNT(*) as count FROM assignments a
                    JOIN games g ON a.game_id = g.id
                    WHERE (g.league IN (
                        SELECT l.name FROM leagues l
                        JOIN league_assignments la ON l.id = la.league_id
                        WHERE la.user_id = ? AND la.is_active = 1
                    ) OR g.league IS NULL OR g.league = '')
                """, (user_id,)).fetchone()['count']
            except Exception as e:
                print(f"Error getting total assignments: {e}")
                stats['total_assignments'] = 0
        elif user_role == 'official':
            try:
                stats['total_assignments'] = conn.execute("""
                    SELECT COUNT(*) as count FROM assignments a
                    WHERE a.official_id = ?
                """, (user_id,)).fetchone()['count']
            except Exception as e:
                print(f"Error getting total assignments: {e}")
                stats['total_assignments'] = 0
        else:
            stats['total_assignments'] = 0
        
        # Active officials - this can remain global for all roles
        try:
            stats['active_officials'] = conn.execute(
                'SELECT COUNT(*) as count FROM users WHERE is_active = 1'
            ).fetchone()['count']
        except Exception as e:
            print(f"Error getting active officials: {e}")
            stats['active_officials'] = 0
        
        # Role-based recent games
        recent_games = []
        if user_role == 'superadmin':
            try:
                games_result = conn.execute("""
                    SELECT id, date, time, home_team, away_team, location, sport 
                    FROM games 
                    WHERE date >= date('now') 
                    ORDER BY date ASC, time ASC 
                    LIMIT 5
                """).fetchall()
            except Exception as e:
                print(f"Error getting recent games: {e}")
                games_result = []
        elif user_role == 'admin':
            try:
                games_result = conn.execute("""
                    SELECT g.id, g.date, g.time, g.home_team, g.away_team, g.location, g.sport 
                    FROM games g
                    WHERE g.date >= date("now")
                    AND (g.league IN (
                        SELECT l.name FROM leagues l
                        JOIN league_assignments la ON l.id = la.league_id
                        WHERE la.user_id = ? AND la.is_active = 1
                    ) OR g.league IS NULL OR g.league = '')
                    ORDER BY g.date ASC, g.time ASC 
                    LIMIT 5
                """, (user_id,)).fetchall()
            except Exception as e:
                print(f"Error getting recent games: {e}")
                games_result = []
        elif user_role == 'official':
            try:
                games_result = conn.execute("""
                    SELECT g.id, g.date, g.time, g.home_team, g.away_team, g.location, g.sport 
                    FROM games g
                    WHERE g.date >= date("now")
                    AND g.id IN (
                        SELECT a.game_id FROM assignments a
                        WHERE a.official_id = ?
                    )
                    ORDER BY g.date ASC, g.time ASC 
                    LIMIT 5
                """, (user_id,)).fetchall()
            except Exception as e:
                print(f"Error getting recent games: {e}")
                games_result = []
        else:
            games_result = []
        
        for game in games_result:
            recent_games.append({
                'id': game['id'],
                'date': game['date'],
                'time': game['time'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'location': game['location'],
                'sport': game['sport']
            })
        
        conn.close()
        
        return jsonify({
            'success': True, 
            'stats': stats,
            'recent_games': recent_games
        })
        
    except Exception as e:
        print(f"Dashboard API error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Dashboard temporarily unavailable',
            'stats': {
                'upcoming_games': 0,
                'active_officials': 0,
                'total_assignments': 0
            },
            'recent_games': []
        }), 500

# Enhanced Games API with all functionalities merged
@app.route('/api/games', methods=['GET'])
@login_required
def get_games():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current user info for role-based filtering
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        # Handle filtering
        search = request.args.get('search', '')
        sport = request.args.get('sport', '')
        date_filter = request.args.get('date', '')
        status_filter = request.args.get('status', '')
        
        # Base query with enhanced fields including link_group and status
        query = """
            SELECT g.*, 
                   COUNT(a.id) as assigned_officials,
                   COALESCE(g.status, 'scheduled') as status,
                   g.link_group
            FROM games g
            LEFT JOIN assignments a ON g.id = a.game_id
            WHERE 1=1
        """
        params = []
        
        # Role-based filtering
        if user_role == 'superadmin':
            # Super admins see ALL games
            pass
        elif user_role == 'admin':
            # Admins see only games from leagues they're assigned to
            query += """
                AND (g.league IN (
                    SELECT l.name FROM leagues l
                    JOIN league_assignments la ON l.id = la.league_id
                    WHERE la.user_id = ? AND la.is_active = 1
                ) OR g.league IS NULL OR g.league = '')
            """
            params.append(user_id)
        elif user_role == 'official':
            # Officials see only games they're assigned to
            query += """
                AND g.id IN (
                    SELECT a.game_id FROM assignments a
                    WHERE a.official_id = ?
                )
            """
            params.append(user_id)
        else:
            # Default: no games visible
            query += " AND 1=0"
        
        # Add search filters
        if search:
            query += " AND (g.home_team LIKE ? OR g.away_team LIKE ? OR g.location LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if sport:
            query += " AND g.sport = ?"
            params.append(sport)
            
        if date_filter:
            query += " AND g.date = ?"
            params.append(date_filter)
            
        if status_filter:
            query += " AND COALESCE(g.status, 'scheduled') = ?"
            params.append(status_filter)
        
        query += " GROUP BY g.id ORDER BY g.date DESC, g.time DESC"
        
        games = cursor.execute(query, params).fetchall()
        conn.close()
        
        # Convert to list of dictionaries with enhanced fields
        games_list = []
        for game in games:
            game_dict = dict(game)
            # Ensure status has a default value
            if not game_dict.get('status'):
                game_dict['status'] = 'scheduled'
            games_list.append(game_dict)
        
        return jsonify({
            'success': True,
            'games': games_list
        })
        
    except Exception as e:
        print(f"Get games error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games', methods=['POST'])
@login_required
@admin_required
def create_game_enhanced():
    """Enhanced game creation with automatic fee assignment"""
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['date', 'time', 'home_team', 'away_team', 'sport']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Sanitize inputs
        game_data = {
            'date': str(data['date']).strip(),
            'time': str(data['time']).strip(),
            'home_team': str(data['home_team']).strip()[:100],
            'away_team': str(data['away_team']).strip()[:100],
            'location': str(data.get('location', '')).strip()[:100],
            'sport': str(data['sport']).strip()[:50],
            'league': str(data.get('league', '')).strip()[:100],
            'level': str(data.get('level', '')).strip()[:100],
            'officials_needed': int(data.get('officials_needed', 1)),
            'notes': str(data.get('notes', '')).strip()[:500]
        }
        
        # Validate officials_needed
        if game_data['officials_needed'] < 1 or game_data['officials_needed'] > 10:
            return jsonify({'success': False, 'error': 'Officials needed must be between 1 and 10'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Automatic fee assignment
        assigned_fee = None
        fee_override = False
        
        # Check if manual fee override provided
        if 'assigned_fee' in data:
            try:
                assigned_fee = validate_fee_amount(data['assigned_fee'])
                fee_override = True
                logger.info(f"Manual fee override: ${assigned_fee}")
            except ValueError as e:
                return jsonify({'success': False, 'error': f'Invalid fee amount: {str(e)}'}), 400
        else:
            # Try automatic fee assignment
            if game_data['league'] and game_data['level']:
                auto_fee, _ = assign_fee_to_game(game_data['league'], game_data['level'], session.get('user_id'))
                if auto_fee is not None:
                    assigned_fee = auto_fee
                    fee_override = False
                    logger.info(f"Automatic fee assigned: ${assigned_fee}")
        
        # Create game with fee information
        cursor.execute("""
            INSERT INTO games 
            (date, time, home_team, away_team, location, sport, league, level, 
             officials_needed, notes, assigned_fee, fee_override, created_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """, (
            game_data['date'], game_data['time'], game_data['home_team'], game_data['away_team'],
            game_data['location'], game_data['sport'], game_data['league'], game_data['level'],
            game_data['officials_needed'], game_data['notes'], 
            float(assigned_fee) if assigned_fee else None, fee_override, session.get('user_id')
        ))
        
        game_id = cursor.lastrowid
        conn.commit()
        
        # Prepare response
        game_response = {
            'id': game_id,
            'assigned_fee': float(assigned_fee) if assigned_fee else None,
            'fee_override': fee_override,
            'fee_source': 'override' if fee_override else 'automatic' if assigned_fee else 'none'
        }
        game_response.update(game_data)
        
        logger.info(f"Created game {game_id} with fee ${assigned_fee or 0} (override: {fee_override}) by user {session.get('user_id')}")
        
        return jsonify({
            'success': True,
            'message': 'Game created successfully',
            'game': game_response
        })
        
    except Exception as e:
        logger.error(f"Error creating game: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/games/<int:game_id>', methods=['GET'])
@login_required  
def get_game(game_id):
    try:
        conn = get_db_connection()
        game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
        conn.close()
        
        if not game:
            return jsonify({'success': False, 'error': 'Game not found'}), 404
            
        return jsonify({'success': True, 'game': dict(game)})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games/<int:game_id>', methods=['PUT'])
@login_required
def update_game(game_id):
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE games 
            SET date=?, time=?, home_team=?, away_team=?, location=?, sport=?, league=?, level=?, officials_needed=?, notes=?, status=?, link_group=?
            WHERE id = ?
        """, (
            data['date'], data['time'], data['home_team'], data['away_team'],
            data.get('location', ''), data['sport'], data.get('league', ''),
            data.get('level', ''), data.get('officials_needed', 1),
            data.get('notes', ''), data.get('status', 'scheduled'),
            data.get('link_group', ''), game_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Game updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games/<int:game_id>', methods=['DELETE'])
@login_required
def delete_game(game_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete related assignments first
        cursor.execute("DELETE FROM assignments WHERE game_id = ?", (game_id,))
        cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Game deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Enhanced bulk operations for games
@app.route('/api/games/bulk-link', methods=['POST'])
@login_required
def bulk_link_games():
    """Link multiple games together with auto-generated link group"""
    try:
        data = request.get_json()
        game_ids = data.get('game_ids', [])
        link_group = data.get('link_group')
        
        if len(game_ids) < 2:
            return jsonify({'success': False, 'error': 'At least 2 games required for linking'}), 400
        
        if not link_group:
            return jsonify({'success': False, 'error': 'Link group name required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update games with link group
        placeholders = ','.join(['?'] * len(game_ids))
        cursor.execute(f"""
            UPDATE games 
            SET link_group = ? 
            WHERE id IN ({placeholders})
        """, [link_group] + game_ids)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'{len(game_ids)} games linked as {link_group}',
            'linked_count': len(game_ids)
        })
        
    except Exception as e:
        logger.error(f"Error linking games: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games/bulk-unlink', methods=['POST'])
@login_required
def bulk_unlink_games():
    """Unlink multiple games by removing their link group"""
    try:
        data = request.get_json()
        game_ids = data.get('game_ids', [])
        
        if not game_ids:
            return jsonify({'success': False, 'error': 'No games specified for unlinking'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Remove link group from games
        placeholders = ','.join(['?'] * len(game_ids))
        cursor.execute(f"""
            UPDATE games 
            SET link_group = NULL 
            WHERE id IN ({placeholders})
        """, game_ids)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'{len(game_ids)} games unlinked successfully',
            'unlinked_count': len(game_ids)
        })
        
    except Exception as e:
        logger.error(f"Error unlinking games: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_games():
    """Delete multiple games"""
    try:
        data = request.get_json()
        game_ids = data.get('game_ids', [])
        
        if not game_ids:
            return jsonify({'success': False, 'error': 'No games specified for deletion'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete related assignments first
        placeholders = ','.join(['?'] * len(game_ids))
        cursor.execute(f"""
            DELETE FROM assignments WHERE game_id IN ({placeholders})
        """, game_ids)
        
        # Delete games
        cursor.execute(f"""
            DELETE FROM games WHERE id IN ({placeholders})
        """, game_ids)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{len(game_ids)} games deleted successfully',
            'deleted_count': len(game_ids)
        })
        
    except Exception as e:
        logger.error(f"Error deleting games: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games/next-link-group', methods=['GET'])
@login_required
def get_next_link_group():
    """Get next available link group name"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find highest existing link group number
        cursor.execute("""
            SELECT link_group FROM games 
            WHERE link_group LIKE 'LINK-%' 
            ORDER BY link_group DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result['link_group']:
            # Extract number from LINK-XXX format
            try:
                current_num = int(result['link_group'].split('-')[1])
                next_num = current_num + 1
            except (IndexError, ValueError):
                next_num = 1
        else:
            next_num = 1
        
        link_group_name = f"LINK-{next_num:03d}"
        
        return jsonify({
            'success': True,
            'link_group_name': link_group_name
        })
        
    except Exception as e:
        logger.error(f"Error getting next link group: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Games import/export functionality
@app.route('/api/games/template.csv', methods=['GET'])
@login_required
def download_games_csv_template():
    """Download CSV template for game imports"""
    try:
        # Create CSV template with headers and example data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'date', 'time', 'home_team', 'away_team', 'sport', 'league', 
            'location', 'level', 'officials_needed', 'notes'
        ])
        
        # Example data
        writer.writerow([
            '2025-09-15', '19:00', 'Lakers', 'Warriors', 'Basketball', 'NBA',
            'Staples Center', 'Professional', '3', 'Championship game'
        ])
        writer.writerow([
            '2025-09-16', '20:30', 'Cowboys', 'Giants', 'Football', 'NFL',
            'AT&T Stadium', 'Professional', '7', 'Division game'
        ])
        
        csv_content = output.getvalue()
        output.close()
        
        # Create response
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=games_import_template.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating CSV template: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games/import', methods=['POST'])
@login_required
def import_games_csv():
    """Import games from CSV file with validation"""
    try:
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be a CSV'}), 400
        
        # Read and parse CSV
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        imported_count = 0
        total_rows = 0
        errors = []
        warnings = []
        
        # Predefined sports list for validation
        VALID_SPORTS = [
            "Basketball", "Football", "Soccer", "Baseball", "Volleyball", 
            "Tennis", "Swimming", "Track", "Wrestling", "Hockey",
            "Lacrosse", "Golf", "Cross Country", "Softball", "Badminton",
            "Table Tennis", "Water Polo"
        ]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for row_num, row in enumerate(csv_reader, start=1):
            total_rows += 1
            row_errors = []
            
            # Validate required fields
            required_fields = ['date', 'time', 'home_team', 'away_team', 'sport']
            for field in required_fields:
                if not row.get(field, '').strip():
                    row_errors.append(f"Missing required field: {field}")
            
            # Validate date format
            try:
                datetime.strptime(row.get('date', ''), '%Y-%m-%d')
            except ValueError:
                row_errors.append("Invalid date format (use YYYY-MM-DD)")
            
            # Validate time format
            try:
                datetime.strptime(row.get('time', ''), '%H:%M')
            except ValueError:
                row_errors.append("Invalid time format (use HH:MM)")
            
            # Validate sport
            sport = row.get('sport', '').strip()
            if sport and sport not in VALID_SPORTS:
                warnings.append(f"Row {row_num}: Unknown sport '{sport}' (will be imported but consider using: {', '.join(VALID_SPORTS[:5])}...)")
            
            # Validate officials needed
            officials_needed = row.get('officials_needed', '1')
            try:
                officials_count = int(officials_needed) if officials_needed else 1
                if officials_count < 1 or officials_count > 10:
                    row_errors.append("Officials needed must be between 1 and 10")
            except ValueError:
                row_errors.append("Officials needed must be a number")
                officials_count = 1
            
            if row_errors:
                errors.extend([f"Row {row_num}: {error}" for error in row_errors])
                continue
            
            # Import the row
            try:
                cursor.execute("""
                    INSERT INTO games (date, time, home_team, away_team, sport, league, location, level, officials_needed, notes, created_date, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('date', '').strip(),
                    row.get('time', '').strip(),
                    row.get('home_team', '').strip(),
                    row.get('away_team', '').strip(),
                    row.get('sport', '').strip(),
                    row.get('league', '').strip(),
                    row.get('location', '').strip(),
                    row.get('level', '').strip(),
                    officials_count,
                    row.get('notes', '').strip(),
                    datetime.now().isoformat(),
                    session.get('user_id')
                ))
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: Database error - {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'imported_count': imported_count,
            'total_rows': total_rows,
            'errors': errors,
            'warnings': warnings,
            'message': f'Successfully imported {imported_count} of {total_rows} games'
        })
        
    except Exception as e:
        logger.error(f"Error importing games CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games/export-selected', methods=['POST'])
@login_required
def export_selected_games():
    """Export selected games to CSV"""
    try:
        data = request.get_json()
        game_ids = data.get('game_ids', [])
        
        if not game_ids:
            return jsonify({'success': False, 'error': 'No games selected for export'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get selected games
        placeholders = ','.join(['?'] * len(game_ids))
        cursor.execute(f"""
            SELECT date, time, home_team, away_team, sport, league, location, level, 
                   officials_needed, notes, status, link_group, created_date
            FROM games 
            WHERE id IN ({placeholders})
            ORDER BY date, time
        """, game_ids)
        
        games = cursor.fetchall()
        conn.close()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'Date', 'Time', 'Home Team', 'Away Team', 'Sport', 'League',
            'Location', 'Level', 'Officials Needed', 'Notes', 'Status', 'Link Group', 'Created Date'
        ])
        
        # Data rows
        for game in games:
            writer.writerow([
                game['date'] or '',
                game['time'] or '',
                game['home_team'] or '',
                game['away_team'] or '',
                game['sport'] or '',
                game['league'] or '',
                game['location'] or '',
                game['level'] or '',
                game['officials_needed'] or 1,
                game['notes'] or '',
                game['status'] or 'scheduled',
                game['link_group'] or '',
                game['created_date'] or ''
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return jsonify({
            'success': True,
            'csv_content': csv_content,
            'filename': f'selected_games_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        logger.error(f"Error exporting selected games: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Users API - Enhanced version only
@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user - Enhanced version with comprehensive validation"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if session.get('role') not in ['superadmin', 'admin']:
        return jsonify({'error': 'Insufficient privileges'}), 403
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'full_name', 'email', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for duplicate username
        cursor.execute("SELECT id FROM users WHERE username = ?", (data['username'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Username already exists'}), 400
        
        # Check for duplicate email
        cursor.execute("SELECT id FROM users WHERE email = ?", (data['email'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Email already exists'}), 400
        
        # Hash default password
        default_password = data.get('password', 'password')
        password_hash = hash_password(default_password)
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users 
            (username, password, role, full_name, email, phone, address, 
             is_active, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['username'], password_hash, data['role'], data['full_name'],
            data['email'], data.get('phone', ''), data.get('address', ''),
            data.get('is_active', True), datetime.now().isoformat()
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'user_id': user_id})
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/api/users', methods=['GET'])
@require_role(['admin', 'superadmin'])
def get_users():
    """Get users with role-based access control"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        user_role = session.get('role')
        user_id = session.get('user_id')
        
        if user_role == 'superadmin':
            # Superadmin sees all users
            users = cursor.execute("""
                SELECT id, username, full_name, email, role, is_active, created_date
                FROM users 
                ORDER BY created_date DESC
            """).fetchall()
        else:
            # Admin sees only users in their leagues
            users = cursor.execute("""
                SELECT DISTINCT u.id, u.username, u.full_name, u.email, u.role, u.is_active, u.created_date
                FROM users u
                INNER JOIN league_assignments la ON u.id = la.user_id
                INNER JOIN league_assignments admin_la ON la.league_id = admin_la.league_id
                WHERE admin_la.user_id = ? AND admin_la.is_active = 1 AND la.is_active = 1
                ORDER BY u.created_date DESC
            """, (user_id,)).fetchall()
        
        users_list = [dict(user) for user in users]
        conn.close()
        
        return jsonify({
            'success': True, 
            'users': users_list,
            'show_all': user_role == 'superadmin'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    try:
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, username, full_name, email, phone, role, is_active FROM users WHERE id = ?', 
            (user_id,)
        ).fetchone()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
        return jsonify({'success': True, 'user': dict(user)})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user with relationship checking - Enhanced version"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if session.get('role') not in ['superadmin', 'admin']:
        return jsonify({'error': 'Insufficient privileges'}), 403
    
    # Prevent self-deletion
    if session['user_id'] == user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        username = user[0]
        
        # Check for dependencies
        dependencies = []
        
        # Check assignments
        cursor.execute("SELECT COUNT(*) FROM assignments WHERE official_id = ?", (user_id,))
        if cursor.fetchone()[0] > 0:
            dependencies.append("Game assignments")
        
        if dependencies:
            conn.close()
            return jsonify({
                'error': 'User has dependencies',
                'dependencies': dependencies,
                'requires_cascade': True
            }), 400
        
        # Safe to delete
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500

@app.route('/api/users/search', methods=['POST'])
@require_role(['admin', 'superadmin'])
def search_users():
    """Search for users by email - for admins to add users to their league"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search for user by email
        user = cursor.execute("""
            SELECT id, username, full_name, email, role, is_active, created_date
            FROM users 
            WHERE email = ? AND is_active = 1
        """, (email,)).fetchone()
        
        if user:
            user_dict = dict(user)
            
            # Check if user is already in admin's league
            if session.get('role') == 'admin':
                admin_leagues = cursor.execute("""
                    SELECT league_id FROM league_assignments 
                    WHERE user_id = ? AND is_active = 1
                """, (session.get('user_id'),)).fetchall()
                
                league_ids = [row['league_id'] for row in admin_leagues]
                
                if league_ids:
                    existing = cursor.execute("""
                        SELECT COUNT(*) as count FROM league_assignments 
                        WHERE user_id = ? AND league_id IN ({})
                    """.format(','.join(['?' for _ in league_ids])), 
                    [user['id']] + league_ids).fetchone()
                    
                    user_dict['already_in_league'] = existing['count'] > 0
                else:
                    user_dict['already_in_league'] = False
            
            conn.close()
            return jsonify({'success': True, 'user': user_dict})
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/add-to-league', methods=['POST'])
@require_role(['admin', 'superadmin'])
def add_user_to_league():
    """Add existing user to admin's league"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID is required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get admin's leagues
        admin_id = session.get('user_id')
        admin_leagues = cursor.execute("""
            SELECT league_id FROM league_assignments 
            WHERE user_id = ? AND is_active = 1
        """, (admin_id,)).fetchall()
        
        if not admin_leagues:
            conn.close()
            return jsonify({'success': False, 'error': 'Admin has no assigned leagues'}), 400
        
        # Add user to all admin's leagues
        for league_row in admin_leagues:
            league_id = league_row['league_id']
            
            # Check if assignment already exists
            existing = cursor.execute("""
                SELECT id FROM league_assignments 
                WHERE user_id = ? AND league_id = ?
            """, (user_id, league_id)).fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO league_assignments (user_id, league_id, assigned_by, assigned_date)
                    VALUES (?, ?, ?, ?)
                """, (user_id, league_id, admin_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User added to league successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Enhanced Officials API
@app.route('/api/officials', methods=['GET'])
@login_required
def get_officials():
    """Get officials with league-based filtering for admins"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        user_role = session.get('role')
        user_id = session.get('user_id')
        
        if user_role == 'superadmin':
            # Superadmin sees all officials
            officials = cursor.execute("""
                SELECT id, username, full_name, email, phone, 
                       availability, is_active, created_date
                FROM users 
                WHERE 1=1 
                ORDER BY full_name
            """).fetchall()
        elif user_role in ['admin', 'assigner']:
            # Admin/Assigner sees only officials in their leagues
            officials = cursor.execute("""
                SELECT DISTINCT u.id, u.username, u.full_name, u.email, u.phone, 
                       u.availability, u.is_active, u.created_date
                FROM users u
                INNER JOIN league_assignments la ON u.id = la.user_id
                INNER JOIN league_assignments admin_la ON la.league_id = admin_la.league_id
                WHERE 1=1 
                AND admin_la.user_id = ? AND admin_la.is_active = 1 AND la.is_active = 1
                ORDER BY u.full_name
            """, (user_id,)).fetchall()
        else:
            # Officials see only themselves
            officials = cursor.execute("""
                SELECT id, username, full_name, email, phone, 
                       availability, is_active, created_date
                FROM users 
                WHERE id = ? AND role = 'official'
            """, (user_id,)).fetchall()
        
        officials_list = [dict(official) for official in officials]
        conn.close()
        
        return jsonify({'success': True, 'officials': officials_list})
        
    except Exception as e:
        print(f"ERROR in get_officials: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/officials', methods=['POST'])
@admin_required
def create_official_enhanced():
    """Create a new official with sport-specific information"""
    try:
        data = request.get_json()
        
        required_fields = ['username', 'password', 'full_name', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username exists
        existing = cursor.execute("SELECT id FROM users WHERE username = ?", (data['username'],)).fetchone()
        if existing:
            conn.close()
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        # Handle sports as comma-separated string
        sports = data.get('sports', '')
        if isinstance(sports, list):
            sports = ', '.join(sports)
        
        cursor.execute("""
            INSERT INTO users (
                username, password, full_name, email, phone, role, is_active, created_date,
                certifications, sports, experience_years, availability_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['username'],
            hash_password(data['password']),
            data['full_name'],
            data['email'],
            data.get('phone', ''),
            'official',
            1,
            datetime.now().isoformat(),
            data.get('certifications', ''),
            sports,
            data.get('experience_years', 0),
            data.get('availability_notes', '')
        ))
        
        official_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': official_id, 'message': 'Official created successfully'})
        
    except Exception as e:
        logger.error(f"Error creating official: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/officials/<int:official_id>', methods=['PUT'])
@admin_required
def update_official_enhanced(official_id):
    """Update official with sport-specific information"""
    try:
        data = request.get_json()
        
        # Handle sports as comma-separated string
        sports = data.get('sports', '')
        if isinstance(sports, list):
            sports = ', '.join(sports)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE id = ? AND is_active = 1", (official_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Official not found'}), 404
        
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND id != ? AND is_active = 1",
            (data['username'], official_id)
        )
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        cursor.execute("""
            UPDATE users SET
                full_name = ?, email = ?, phone = ?,
                certifications = ?, sports = ?, experience_years = ?,
                availability_notes = ?
            WHERE id = ?
        """, (
            data['full_name'],
            data['email'],
            data.get('phone', ''),
            data.get('certifications', ''),
            sports,
            data.get('experience_years', 0),
            data.get('availability_notes', ''),
            official_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Official updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating official: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/officials/<int:official_id>', methods=['GET'])
@login_required
def get_official_details_enhanced(official_id):
    """Get detailed information for a specific official"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id,
                   u.username,
                   u.full_name,
                   u.email,
                   u.phone,
                   u.role,
                   u.created_date,
                   u.last_login,
                   u.is_active,
                   COALESCE(u.certifications, '') as certifications,
                   COALESCE(u.sports, '') as sports,
                   COALESCE(u.experience_years, 0) as experience_years,
                   COALESCE(u.availability_notes, '') as availability_notes,
                   COUNT(a.id) as total_assignments,
                   MAX(g.date) as last_assignment_date
            FROM users u
            LEFT JOIN assignments a ON u.id = a.official_id
            LEFT JOIN games g ON a.game_id = g.id
            WHERE u.id = ?
            GROUP BY u.id
        """, (official_id,))
        
        official = cursor.fetchone()
        
        if not official:
            conn.close()
            return jsonify({'success': False, 'error': 'Official not found'}), 404
        
        cursor.execute("""
            SELECT g.date, g.time, g.home_team, g.away_team, g.sport, a.position, a.status
            FROM assignments a
            JOIN games g ON a.game_id = g.id
            WHERE a.official_id = ?
            ORDER BY g.date DESC
            LIMIT 10
        """, (official_id,))
        
        recent_assignments = cursor.fetchall()
        conn.close()
        
        official_data = {
            'id': official['id'],
            'username': official['username'],
            'full_name': official['full_name'],
            'email': official['email'],
            'phone': official['phone'],
            'role': official['role'],
            'created_date': official['created_date'],
            'last_login': official['last_login'],
            'is_active': official['is_active'],
            'certifications': official['certifications'],
            'sports': official['sports'],
            'experience_years': official['experience_years'],
            'availability_notes': official['availability_notes'],
            'total_assignments': official['total_assignments'],
            'last_assignment_date': official['last_assignment_date'],
            'recent_assignments': [dict(row) for row in recent_assignments]
        }
        
        return jsonify({'success': True, 'official': official_data})
        
    except Exception as e:
        logger.error(f"Error getting official details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Assignments API
@app.route('/api/assignments', methods=['GET'])
@login_required
def get_assignments():
    try:
        conn = get_db_connection()
        
        assignments = conn.execute("""
            SELECT a.id, a.game_id, a.official_id, a.position, a.status, a.assigned_date,
                   g.date, g.time, g.home_team, g.away_team, g.sport, g.location,
                   u.full_name, u.username as name
            FROM assignments a
            JOIN games g ON a.game_id = g.id  
            LEFT JOIN users u ON a.official_id = u.id
            ORDER BY g.date DESC, g.time DESC
        """).fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'assignments': [dict(row) for row in assignments]
        })
        
    except Exception as e:
        print(f"Get assignments error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/assignments', methods=['POST'])
@admin_required
def create_assignment():
    try:
        data = request.get_json()
        
        if not data.get('game_id') or not data.get('official_id'):
            return jsonify({'success': False, 'error': 'Game and official are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if assignment already exists
        existing = cursor.execute(
            "SELECT id FROM assignments WHERE game_id = ? AND official_id = ?",
            (data['game_id'], data['official_id'])
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'error': 'Assignment already exists'}), 400
        
        cursor.execute("""
            INSERT INTO assignments (game_id, official_id, position, status, assigned_date, assigned_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data['game_id'], data['official_id'], data.get('position', 'Official'),
            data.get('status', 'pending'),
            datetime.now().isoformat(), session.get('user_id')
        ))
        
        assignment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': assignment_id, 'message': 'Assignment created successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
@admin_required
def delete_assignment(assignment_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Assignment deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# League Management Routes
@app.route('/api/leagues', methods=['GET'])
@login_required
def get_leagues():
    """Get leagues with access control based on user assignments"""
    try:
        search = request.args.get('search', '')
        sport = request.args.get('sport', '')
        season = request.args.get('season', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check user role for access control
        user_role = session.get('role')
        user_id = session.get('user_id')
        
        if user_role == 'superadmin':
            # Superadmins see all leagues
            query = """
                SELECT id, name, sport, season, levels, description
                FROM leagues l 
                WHERE 1=1
            """
            params = []
        else:
            # Admin/assigner users only see assigned leagues
            query = """
                SELECT DISTINCT l.id, l.name, l.sport, l.season, l.levels, l.description
                FROM leagues l
                INNER JOIN league_assignments la ON l.id = la.league_id
                WHERE la.user_id = ? AND la.is_active = 1
            """
            params = [user_id]
        
        # Add search filters
        if search:
            query += " AND (l.name LIKE ? OR l.sport LIKE ? OR l.season LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
            
        if sport:
            query += " AND l.sport = ?"
            params.append(sport)
            
        if season:
            query += " AND l.season = ?"
            params.append(season)
        
        query += " ORDER BY l.name ASC"
        
        cursor.execute(query, params)
        leagues = []
        
        for row in cursor.fetchall():
            leagues.append({
                'id': row[0],
                'name': row[1],
                'sport': row[2],
                'season': row[3],
                'levels': row[4],
                'description': row[5]               
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'leagues': leagues,
            'user_role': user_role,
            'filtered': user_role != 'superadmin'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leagues', methods=['POST'])
@login_required
def create_league():
    """Create a new league"""
    try:
        data = request.get_json()
        required_fields = ['name', 'sport', 'season']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for duplicate name
        cursor.execute("SELECT id FROM leagues WHERE name = ? AND season = ?", (data['name'], data['season']))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'League name already exists for this season'}), 400
        
        insert_sql = '''INSERT INTO leagues (name, sport, season, levels, description, is_active, created_by) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)'''
        cursor.execute(insert_sql, (
            data['name'],
            data['sport'],
            data['season'],
            data.get('levels', ''),
            data.get('description', ''),
            data.get('is_active', True),
            session.get('user_id', 1)
        ))
        
        league_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'league_id': league_id, 'message': 'League created successfully'})
        
    except Exception as e:
        logger.error(f"Error creating league: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leagues/<int:league_id>', methods=['GET'])
@login_required
def get_league(league_id):
    """Get a specific league"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leagues WHERE id = ? AND is_active = 1", (league_id,))
        league = cursor.fetchone()
        conn.close()
        
        if league:
            return jsonify({'success': True, 'league': dict(league)})
        else:
            return jsonify({'success': False, 'error': 'League not found'}), 404
            
    except Exception as e:
        logger.error(f"Error fetching league {league_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leagues/<int:league_id>', methods=['PUT'])
@login_required
def update_league(league_id):
    """Update a league"""
    try:
        data = request.get_json()
        required_fields = ['name', 'sport', 'season']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM leagues WHERE id = ? AND is_active = 1", (league_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'League not found'}), 404
        
        cursor.execute(
            "SELECT id FROM leagues WHERE name = ? AND season = ? AND id != ? AND is_active = 1",
            (data['name'], data['season'], league_id)
        )
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'A league with this name already exists for this season'}), 409
        
        cursor.execute("""
            UPDATE leagues SET
                name = ?, sport = ?, season = ?, levels = ?, description = ? 
            WHERE id = ?
        """, (
            data['name'],
            data['sport'],
            data['season'],
            data.get('levels', ''),
            data.get('description', ''),
            league_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'League updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating league {league_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leagues/<int:league_id>', methods=['DELETE'])
@login_required
def delete_league(league_id):
    """Delete a league"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM leagues WHERE id = ? AND is_active = 1", (league_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'League not found'}), 404
        
        # Soft delete the league
        cursor.execute('''
            UPDATE leagues 
            SET is_active = 0, updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), league_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'League deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting league {league_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/locations', methods=['GET'])
@login_required
def get_locations():
    """Get all locations"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        locations = cursor.execute("""
            SELECT id, name, address, city, state, zip_code, capacity, 
                   contact_person, contact_phone, notes, is_active, created_date
            FROM locations 
            ORDER BY name
        """).fetchall()
        
        locations_list = [dict(location) for location in locations]
        conn.close()
        
        return jsonify({'success': True, 'locations': locations_list})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sports', methods=['GET'])
@login_required
def get_sports():
    """Get list of sports for league creation"""
    sports = [
        "Soccer", "Basketball", "Football", "Baseball", "Softball",
        "Volleyball", "Tennis", "Track", "Wrestling", "Swimming",
        "Hockey", "Lacrosse", "Golf", "Cross Country", "Other"
    ]
    return jsonify({'success': True, 'sports': sports})

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total counts
        total_users = cursor.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
        total_officials = cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'official'").fetchone()['count']
        total_games = cursor.execute("SELECT COUNT(*) as count FROM games").fetchone()['count']
        total_assignments = cursor.execute("SELECT COUNT(*) as count FROM assignments").fetchone()['count']
        total_leagues = cursor.execute("SELECT COUNT(*) as count FROM leagues").fetchone()['count']
        total_locations = cursor.execute("SELECT COUNT(*) as count FROM locations").fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_officials': total_officials,
                'total_games': total_games,
                'total_assignments': total_assignments,
                'total_leagues': total_leagues,
                'total_locations': total_locations
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    """Get current user profile information"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'No active session'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query only the columns that exist
        user = cursor.execute("""
            SELECT id, username, full_name, email, role, is_active, created_date
            FROM users 
            WHERE id = ?
        """, (user_id,)).fetchone()
        
        conn.close()
        
        if user:
            user_dict = dict(user)
            return jsonify({'success': True, 'user': user_dict})
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
    except Exception as e:
        print(f"ERROR in get_user_profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leagues/<int:league_id>/levels', methods=['GET'])
@login_required
def get_league_levels(league_id):
    """Get all levels for a specific league"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ll.*, l.name as league_name 
            FROM league_levels ll
            JOIN leagues l ON ll.league_id = l.id
            WHERE ll.league_id = ?
            ORDER BY ll.level_name
        """, (league_id,))
        
        levels = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        levels_list = []
        for level in levels:
            levels_list.append({
                'id': level['id'],
                'league_id': level['league_id'],
                'level_name': level['level_name'],
                'is_active': level['is_active'],
                'created_date': level['created_date'],
                'notes': level['notes'],
                'league_name': level['league_name']
            })
        
        return jsonify({'success': True, 'levels': levels_list})
        
    except Exception as e:
        logger.error(f"Error getting league levels: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/leagues/<int:league_id>/assign', methods=['POST'])
@login_required
def assign_league_to_user(league_id):
    """Assign a league to a user"""
    try:
        if session.get('role') != 'superadmin':
            return jsonify({'success': False, 'error': 'Super admin access required'}), 403
            
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert league assignment
        cursor.execute("""
            INSERT OR REPLACE INTO league_assignments 
            (user_id, league_id, assigned_by, assigned_date, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (user_id, league_id, session.get('user_id'), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'League assigned successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Predetermined Levels API
@app.route('/api/predetermined-levels', methods=['GET'])
@login_required
def api_get_predetermined_levels():
    """Get all available predetermined levels"""
    try:
        sport = request.args.get('sport')
        category = request.args.get('category')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, sport, category, level_name, display_order, description
            FROM predetermined_levels 
            WHERE is_active = 1
        """
        params = []
        
        if sport:
            query += " AND sport = ?"
            params.append(sport)
        
        if category:
            query += " AND category = ?"
            params.append(category)
            
        query += " ORDER BY sport, category, display_order"
        
        cursor.execute(query, params)
        levels = cursor.fetchall()
        conn.close()
        
        levels_list = []
        for level in levels:
            levels_list.append({
                'id': level[0],
                'sport': level[1], 
                'category': level[2],
                'level_name': level[3],
                'display_order': level[4],
                'description': level[5]
            })
        
        return jsonify({'success': True, 'levels': levels_list})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predetermined-levels/sport/<sport>', methods=['GET'])
@login_required
def api_get_levels_by_sport(sport):
    """Get predetermined levels for a specific sport"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, category, level_name, display_order, description
            FROM predetermined_levels 
            WHERE sport = ? AND is_active = 1
            ORDER BY category, display_order
        """, (sport,))
        
        levels = cursor.fetchall()
        conn.close()
        
        # Group by category
        grouped_levels = {}
        for level in levels:
            category = level[1]
            if category not in grouped_levels:
                grouped_levels[category] = []
            
            grouped_levels[category].append({
                'id': level[0],
                'level_name': level[2],
                'display_order': level[3],
                'description': level[4]
            })
        
        return jsonify({'success': True, 'sport': sport, 'levels': grouped_levels})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sports-list', methods=['GET'])
@login_required
def api_get_available_sports():
    """Get list of available sports from predetermined levels"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT sport 
            FROM predetermined_levels 
            WHERE is_active = 1
            ORDER BY sport
        """)
        
        sports = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'sports': sports})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/categories-list', methods=['GET'])
@login_required
def api_get_available_categories():
    """Get list of available categories from predetermined levels"""
    try:
        sport = request.args.get('sport')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if sport:
            cursor.execute("""
                SELECT DISTINCT category 
                FROM predetermined_levels 
                WHERE sport = ? AND is_active = 1
                ORDER BY category
            """, (sport,))
        else:
            cursor.execute("""
                SELECT DISTINCT category 
                FROM predetermined_levels 
                WHERE is_active = 1
                ORDER BY category
            """)
        
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'categories': categories})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Fee Management API Endpoints
@app.route('/api/leagues/<int:league_id>/fees', methods=['GET'])
@login_required
def get_league_fees(league_id):
    """Get all fee structures for a league"""
    conn = None
    try:
        if league_id <= 0:
            return jsonify({'success': False, 'error': 'Invalid league ID'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify league exists and get name
        league_result = cursor.execute("SELECT name FROM leagues WHERE id = ?", (league_id,))
        league = league_result.fetchone()
        if not league:
            return jsonify({'success': False, 'error': 'League not found'}), 404
        
        # Get fee structures
        cursor.execute("""
            SELECT lf.id, lf.level_name, lf.official_fee, lf.notes, 
                   lf.created_date, lf.updated_date, lf.is_active,
                   u.full_name as created_by_name
            FROM league_fees lf
            LEFT JOIN users u ON lf.created_by = u.id
            WHERE lf.league_id = ? AND lf.is_active = 1
            ORDER BY lf.level_name
        """, (league_id,))
        
        fees = []
        for row in cursor.fetchall():
            fees.append({
                'id': row[0],
                'level_name': row[1],
                'official_fee': float(row[2]) if row[2] else 0.0,
                'notes': row[3],
                'created_date': row[4],
                'updated_date': row[5],
                'is_active': bool(row[6]),
                'created_by_name': row[7] or 'Unknown'
            })
        
        return jsonify({
            'success': True,
            'league_name': league[0],
            'fees': fees
        })
        
    except Exception as e:
        logger.error(f"Error getting league fees: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/leagues/<int:league_id>/fees', methods=['POST'])
@login_required
@admin_required
def create_league_fee(league_id):
    """Create new fee structure for league + level combination"""
    conn = None
    try:
        if league_id <= 0:
            return jsonify({'success': False, 'error': 'Invalid league ID'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['level_name', 'official_fee']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate and sanitize inputs
        level_name = str(data['level_name']).strip()
        if not level_name or len(level_name) > 100:
            return jsonify({'success': False, 'error': 'Invalid level name'}), 400
        
        # Validate fee amount
        try:
            official_fee = validate_fee_amount(data['official_fee'])
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        
        notes = str(data.get('notes', '')).strip()[:500]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify league exists
        cursor.execute("SELECT name FROM leagues WHERE id = ?", (league_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'League not found'}), 404
        
        # Check if fee structure already exists for this level
        cursor.execute("""
            SELECT id FROM league_fees 
            WHERE league_id = ? AND LOWER(level_name) = LOWER(?) AND is_active = 1
        """, (league_id, level_name))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Fee structure already exists for this level'}), 400
        
        # Create fee structure
        cursor.execute("""
            INSERT INTO league_fees 
            (league_id, level_name, official_fee, notes, created_by, created_date, updated_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (league_id, level_name, float(official_fee), notes, session.get('user_id'), 
              datetime.now().isoformat(), datetime.now().isoformat()))
        
        fee_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Created fee structure: League {league_id}, Level '{level_name}', Fee ${official_fee} by user {session.get('user_id')}")
        
        return jsonify({
            'success': True,
            'message': 'Fee structure created successfully',
            'fee_id': fee_id,
            'fee': {
                'id': fee_id,
                'level_name': level_name,
                'official_fee': float(official_fee),
                'notes': notes
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating league fee: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/leagues/<int:league_id>/fees/<int:fee_id>', methods=['PUT'])
@login_required
@admin_required
def update_league_fee(league_id, fee_id):
    """Update an existing fee structure"""
    conn = None
    try:
        if league_id <= 0 or fee_id <= 0:
            return jsonify({'success': False, 'error': 'Invalid league or fee ID'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate fields
        level_name = str(data.get('level_name', '')).strip()
        official_fee = data.get('official_fee')
        notes = str(data.get('notes', '')).strip() if data.get('notes') else None
        
        if not level_name:
            return jsonify({'success': False, 'error': 'level_name required'}), 400
        if official_fee is not None:
            try:
                official_fee = validate_fee_amount(official_fee)
            except ValueError as e:
                return jsonify({'success': False, 'error': str(e)}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if fee structure exists
        cursor.execute('''
            SELECT id FROM league_fees 
            WHERE id = ? AND league_id = ? AND is_active = 1
        ''', (fee_id, league_id))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Fee structure not found'}), 404
        
        # Update fee structure
        cursor.execute("""
            UPDATE league_fees 
            SET level_name = ?, official_fee = ?, notes = ?, updated_date = ?
            WHERE id = ?
        """, (
            level_name, 
            str(official_fee), 
            notes, 
            datetime.now().isoformat(),
            fee_id
        ))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Fee structure updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating league fee: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/leagues/<int:league_id>/fees/<int:fee_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_league_fee(league_id, fee_id):
    """Delete a fee structure"""
    conn = None
    try:
        if league_id <= 0 or fee_id <= 0:
            return jsonify({'success': False, 'error': 'Invalid league or fee ID'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if fee structure exists
        cursor.execute('''
            SELECT id FROM league_fees 
            WHERE id = ? AND league_id = ? AND is_active = 1
        ''', (fee_id, league_id))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Fee structure not found'}), 404
        
        # Soft delete the fee structure
        cursor.execute('''
            UPDATE league_fees 
            SET is_active = 0, updated_date = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), fee_id))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Fee structure deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting league fee: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/leagues/schema-check', methods=['GET'])
@login_required
def api_leagues_schema_check():
    """Check if leagues table schema is properly set up"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if leagues table exists and has required columns
        cursor.execute("PRAGMA table_info(leagues)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = ['id', 'name', 'sport', 'season', 'description', 'is_active']
        missing_columns = [col for col in required_columns if col not in columns]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'schema_valid': len(missing_columns) == 0,
            'missing_columns': missing_columns,
            'existing_columns': columns
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bill-to-entities', methods=['GET'])
@login_required
@admin_required
def get_bill_to_entities():
    """Get all bill-to entities"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, contact_person, email, phone, address, 
                   city, state, zip_code, tax_id, created_date
            FROM bill_to_entities
            WHERE is_active = 1
            ORDER BY name
        """)
        
        entities = []
        for row in cursor.fetchall():
            entities.append({
                'id': row[0],
                'name': row[1],
                'contact_person': row[2],
                'email': row[3],
                'phone': row[4],
                'address': row[5],
                'city': row[6],
                'state': row[7],
                'zip_code': row[8],
                'tax_id': row[9],
                'created_date': row[10]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'entities': entities
        })
        
    except Exception as e:
        logger.error(f"Error getting bill-to entities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



# League Billing API Endpoints - Phase 4
# Generated by Jose Ortiz - September 12, 2025

@app.route('/api/leagues/<int:league_id>/billing', methods=['GET'])
@admin_required
def api_get_league_billing(league_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM leagues WHERE id = ?", (league_id,))
        league = cursor.fetchone()
        if not league:
            conn.close()
            return jsonify({'success': False, 'error': 'League not found'}), 404
        
        cursor.execute('''
            SELECT 
                lb.id, lb.level_name, lb.bill_amount, lb.bill_to_id,
                bte.name as entity_name, lb.notes, lb.created_date
            FROM league_billing lb
            JOIN bill_to_entities bte ON lb.bill_to_id = bte.id
            WHERE lb.league_id = ? AND lb.is_active = 1
            ORDER BY lb.level_name
        ''', (league_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'level_name': row[1], 
                'bill_amount': float(row[2]) if row[2] else 0.0,
                'bill_to_id': row[3],
                'entity_name': row[4],
                'notes': row[5],
                'created_date': row[6]
            })
        
        conn.close()
        return jsonify({
            'success': True,
            'billing_structures': results,
            'league_name': league[0],
            'league_id': league_id
        })
        
    except Exception as e:
        app.logger.error(f"Error in get_league_billing: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/leagues/<int:league_id>/billing', methods=['POST'])
@admin_required  
def api_create_league_billing(league_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        level_name = str(data.get('level_name', '')).strip()
        bill_to_id = int(data.get('bill_to_id', 0))
        bill_amount = Decimal(str(data.get('bill_amount', 0)))
        notes = str(data.get('notes', '')).strip() if data.get('notes') else None
        
        if not level_name:
            return jsonify({'success': False, 'error': 'level_name required'}), 400
        if bill_to_id <= 0:
            return jsonify({'success': False, 'error': 'Invalid bill_to_id'}), 400
        if bill_amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid bill_amount'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check league exists
            cursor.execute("SELECT id FROM leagues WHERE id = ?", (league_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'League not found'}), 404
            
            # Check entity exists  
            cursor.execute("SELECT id FROM bill_to_entities WHERE id = ? AND is_active = 1", (bill_to_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Bill-to entity not found'}), 400
            
            # Check for duplicate
            cursor.execute('''
                SELECT id FROM league_billing 
                WHERE league_id = ? AND level_name = ? AND is_active = 1
            ''', (league_id, level_name))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Billing structure already exists'}), 400
            
            # Create it
            cursor.execute('''
                INSERT INTO league_billing 
                (league_id, level_name, bill_amount, bill_to_id, notes, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (league_id, level_name, str(bill_amount), bill_to_id, notes, 
                  datetime.now().isoformat(), session['user_id']))
            
            billing_id = cursor.lastrowid
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Billing structure created',
                'billing_id': billing_id
            })
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error in create_league_billing: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/leagues/<int:league_id>/billing/<int:billing_id>', methods=['PUT'])
@admin_required
def api_update_league_billing(league_id, billing_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check exists
            cursor.execute('''
                SELECT id FROM league_billing 
                WHERE id = ? AND league_id = ? AND is_active = 1
            ''', (billing_id, league_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Billing structure not found'}), 404
            
            # Build update
            updates = []
            params = []
            
            if 'bill_amount' in data:
                bill_amount = Decimal(str(data['bill_amount']))
                if bill_amount > 0:
                    updates.append("bill_amount = ?")
                    params.append(str(bill_amount))
            
            if 'bill_to_id' in data:
                bill_to_id = int(data['bill_to_id'])
                if bill_to_id > 0:
                    # Verify entity exists
                    cursor.execute("SELECT id FROM bill_to_entities WHERE id = ? AND is_active = 1", (bill_to_id,))
                    if cursor.fetchone():
                        updates.append("bill_to_id = ?")
                        params.append(bill_to_id)
            
            if 'notes' in data:
                notes = str(data['notes']).strip() if data['notes'] else None
                updates.append("notes = ?")
                params.append(notes)
            
            if not updates:
                return jsonify({'success': False, 'error': 'No valid updates provided'}), 400
            
            # Add timestamp
            updates.append("updated_date = ?")
            params.append(datetime.now().isoformat())
            params.append(billing_id)
            
            cursor.execute(f'''
                UPDATE league_billing 
                SET {', '.join(updates)}
                WHERE id = ? AND is_active = 1
            ''', params)
            
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Billing structure updated'})
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error in update_league_billing: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/leagues/<int:league_id>/billing/<int:billing_id>', methods=['DELETE'])
@admin_required
def api_delete_league_billing(league_id, billing_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check exists
            cursor.execute('''
                SELECT id FROM league_billing 
                WHERE id = ? AND league_id = ? AND is_active = 1
            ''', (billing_id, league_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Billing structure not found'}), 404
            
            # Soft delete
            cursor.execute('''
                UPDATE league_billing 
                SET is_active = 0, updated_date = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), billing_id))
            
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Billing structure deleted'})
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error in delete_league_billing: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500






# ============================================================================
# BILL-TO ENTITY API ENDPOINTS
# Author: Jose Ortiz
# Copyright: 2025
# ============================================================================

@app.route('/api/bill-to-entities', methods=['POST'])
@login_required
def create_bill_to_entity():
    """Create new bill-to entity (admin only)"""
    if session.get('role') not in ['superadmin', 'admin']:
        return jsonify({'error': 'Insufficient privileges'}), 403
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Entity name is required'}), 400
        
        # Input validation and sanitization
        name = data['name'].strip()[:255]
        contact_person = data.get('contact_person', '').strip()[:255] if data.get('contact_person') else None
        email = data.get('email', '').strip()[:255] if data.get('email') else None
        phone = data.get('phone', '').strip()[:20] if data.get('phone') else None
        address = data.get('address', '').strip()[:500] if data.get('address') else None
        city = data.get('city', '').strip()[:100] if data.get('city') else None
        state = data.get('state', '').strip()[:2] if data.get('state') else None
        zip_code = data.get('zip_code', '').strip()[:10] if data.get('zip_code') else None
        tax_id = data.get('tax_id', '').strip()[:50] if data.get('tax_id') else None
        notes = data.get('notes', '').strip()[:500] if data.get('notes') else None
        
        if not name:
            return jsonify({'success': False, 'error': 'Entity name cannot be empty'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for duplicate name
        cursor.execute("SELECT id FROM bill_to_entities WHERE name = ? AND is_active = 1", (name,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Entity with this name already exists'}), 400
        
        # Insert new entity
        cursor.execute("""
            INSERT INTO bill_to_entities 
            (name, contact_person, email, phone, address, city, state, zip_code, tax_id, 
             created_date, created_by, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, 1)
        """, (name, contact_person, email, phone, address, city, state, zip_code, tax_id, 
                session.get('user_id')))
        
        entity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the activity
        logger.info(f"Created bill-to entity: {name} (ID: {entity_id}) by user {session.get('user_id')}")
        
        return jsonify({
            'success': True,
            'message': 'Bill-to entity created successfully',
            'entity_id': entity_id
        })
        
    except Exception as e:
        logger.error(f"Error creating bill-to entity: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/bill-to-entities/<int:entity_id>', methods=['GET'])
@login_required
def get_bill_to_entity(entity_id):
    """Get specific bill-to entity (admin only)"""
    if session.get('role') not in ['superadmin', 'admin']:
        return jsonify({'error': 'Insufficient privileges'}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, contact_person, email, phone, address, 
                   city, state, zip_code, tax_id, created_date, created_by, is_active
            FROM bill_to_entities 
            WHERE id = ?
        """, (entity_id,))
        
        entity = cursor.fetchone()
        conn.close()
        
        if not entity:
            return jsonify({'success': False, 'error': 'Entity not found'}), 404
        
        return jsonify({
            'success': True,
            'entity': {
                'id': entity['id'],
                'name': entity['name'],
                'contact_person': entity['contact_person'],
                'email': entity['email'],
                'phone': entity['phone'],
                'address': entity['address'],
                'city': entity['city'],
                'state': entity['state'],
                'zip_code': entity['zip_code'],
                'tax_id': entity['tax_id'],
                'created_date': entity['created_date'],
                'created_by': entity['created_by'],
                'is_active': entity['is_active']
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching bill-to entity {entity_id}: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/bill-to-entities/<int:entity_id>', methods=['PUT'])
@login_required
def update_bill_to_entity(entity_id):
    """Update bill-to entity (admin only)"""
    if session.get('role') not in ['superadmin', 'admin']:
        return jsonify({'error': 'Insufficient privileges'}), 403
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Entity name is required'}), 400
        
        # Input validation and sanitization
        name = data['name'].strip()[:255]
        contact_person = data.get('contact_person', '').strip()[:255] if data.get('contact_person') else None
        email = data.get('email', '').strip()[:255] if data.get('email') else None
        phone = data.get('phone', '').strip()[:20] if data.get('phone') else None
        address = data.get('address', '').strip()[:500] if data.get('address') else None
        city = data.get('city', '').strip()[:100] if data.get('city') else None
        state = data.get('state', '').strip()[:2] if data.get('state') else None
        zip_code = data.get('zip_code', '').strip()[:10] if data.get('zip_code') else None
        tax_id = data.get('tax_id', '').strip()[:50] if data.get('tax_id') else None
        
        if not name:
            return jsonify({'success': False, 'error': 'Entity name cannot be empty'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if entity exists
        cursor.execute("SELECT id FROM bill_to_entities WHERE id = ?", (entity_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Entity not found'}), 404
        
        # Check for duplicate name (excluding current entity)
        cursor.execute("SELECT id FROM bill_to_entities WHERE name = ? AND id != ? AND is_active = 1", 
                      (name, entity_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Entity with this name already exists'}), 400
        
        # Update entity
        cursor.execute("""
            UPDATE bill_to_entities 
            SET name = ?, contact_person = ?, email = ?, phone = ?, address = ?, 
                city = ?, state = ?, zip_code = ?, tax_id = ?, updated_date = datetime('now')
            WHERE id = ?
        """, (name, contact_person, email, phone, address, city, state, zip_code, tax_id, entity_id))
        
        conn.commit()
        conn.close()
        
        # Log the activity
        logger.info(f"Updated bill-to entity: {name} (ID: {entity_id}) by user {session.get('user_id')}")
        
        return jsonify({
            'success': True,
            'message': 'Bill-to entity updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating bill-to entity {entity_id}: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/bill-to-entities/<int:entity_id>', methods=['DELETE'])
@login_required
def delete_bill_to_entity(entity_id):
    """Delete bill-to entity (soft delete - admin only)"""
    if session.get('role') not in ['superadmin', 'admin']:
        return jsonify({'error': 'Insufficient privileges'}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if entity exists
        cursor.execute("SELECT name FROM bill_to_entities WHERE id = ? AND is_active = 1", (entity_id,))
        entity = cursor.fetchone()
        
        if not entity:
            conn.close()
            return jsonify({'success': False, 'error': 'Entity not found'}), 404
        
        entity_name = entity['name']
        
        # Soft delete (set is_active = 0)
        cursor.execute("""
            UPDATE bill_to_entities 
            SET is_active = 0
            WHERE id = ?
        """, (entity_id,))
        
        conn.commit()
        conn.close()
        
        # Log the activity
        logger.info(f"Deleted bill-to entity: {entity_name} (ID: {entity_id}) by user {session.get('user_id')}")
        
        return jsonify({
            'success': True,
            'message': 'Bill-to entity deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting bill-to entity {entity_id}: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# =============================================================================
# PHASE 5: ADVANCED FILTERING SYSTEM API ENDPOINTS
# Created by: Jose Ortiz - September 14, 2025
# =============================================================================

@app.route('/api/leagues/filter-options', methods=['GET'])
@login_required
def get_league_filter_options():
    """Get available filter options for leagues"""
    try:
        conn = sqlite3.connect('scheduler.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get unique sports
        cursor.execute("SELECT DISTINCT sport FROM leagues WHERE is_active = 1 ORDER BY sport")
        sports = [row[0] for row in cursor.fetchall() if row[0]]
        
        # Get unique seasons
        cursor.execute("SELECT DISTINCT season FROM leagues WHERE is_active = 1 ORDER BY season") 
        seasons = [row[0] for row in cursor.fetchall() if row[0]]
        
        # Get available levels
        cursor.execute("SELECT DISTINCT level_name FROM league_levels ORDER BY level_name")
        levels = [row[0] for row in cursor.fetchall() if row[0]]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'filters': {
                'sports': sports,
                'seasons': seasons, 
                'levels': levels,
                'status_options': ['Active', 'Inactive', 'All']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leagues/advanced-search', methods=['POST'])
@login_required  
def advanced_search_leagues():
    """Advanced search with multiple criteria"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No search criteria provided'}), 400
        
        conn = sqlite3.connect('scheduler.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query based on user role (COPYING EXISTING PATTERN)
        user_role = session.get('role')
        user_id = session.get('user_id')
        
        if user_role == 'superadmin':
            base_query = """
                SELECT DISTINCT l.id, l.name, l.sport, l.season, l.description, l.is_active,
                       l.created_date
                FROM leagues l
                WHERE 1=1
            """
            params = []
        else:
            base_query = """
                SELECT DISTINCT l.id, l.name, l.sport, l.season, l.description, l.is_active,
                       l.created_date
                FROM leagues l
                INNER JOIN league_assignments la ON l.id = la.league_id
                WHERE la.user_id = ? AND la.is_active = 1
            """
            params = [user_id]
        
        # Add filters
        search_text = data.get('search', '').strip()
        if search_text:
            base_query += " AND (l.name LIKE ? OR l.description LIKE ? OR l.sport LIKE ?)"
            search_param = f"%{search_text}%"
            params.extend([search_param, search_param, search_param])
        
        sport = data.get('sport', '').strip()
        if sport and sport != 'All':
            base_query += " AND l.sport = ?"
            params.append(sport)
        
        season = data.get('season', '').strip()
        if season and season != 'All':
            base_query += " AND l.season = ?"
            params.append(season)
        
        status = data.get('status', 'All').strip()
        if status == 'Active':
            base_query += " AND l.is_active = 1"
        elif status == 'Inactive':
            base_query += " AND l.is_active = 0"
        
        date_from = data.get('date_from', '').strip()
        date_to = data.get('date_to', '').strip()
        
        if date_from:
            base_query += " AND DATE(l.created_date) >= DATE(?)"
            params.append(date_from)
        
        if date_to:
            base_query += " AND DATE(l.created_date) <= DATE(?)"
            params.append(date_to)
        
        base_query += " ORDER BY l.name ASC"
        
        cursor.execute(base_query, params)
        leagues = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'leagues': leagues,
            'pagination': {'total_count': len(leagues)},
            'search_criteria': data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/filter-presets', methods=['GET'])
@login_required
def get_user_filter_presets(user_id):
    """Get user's saved filter presets"""
    try:
        # Security check
        current_user_id = session.get('user_id')
        user_role = session.get('role')
        
        if current_user_id != user_id and user_role not in ['admin', 'superadmin']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        conn = sqlite3.connect('scheduler.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, preset_name, filter_criteria, is_default, created_date, updated_date
            FROM filter_presets
            WHERE user_id = ?
            ORDER BY is_default DESC, preset_name ASC
        """, (user_id,))
        
        presets = []
        for row in cursor.fetchall():
            preset = dict(row)
            try:
                preset['filter_criteria'] = json.loads(preset['filter_criteria'])
            except:
                preset['filter_criteria'] = {}
            presets.append(preset)
        
        conn.close()
        
        return jsonify({'success': True, 'presets': presets})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/filter-presets', methods=['POST'])
@login_required
def create_filter_preset(user_id):
    """Save new filter preset"""
    try:
        # Security check
        current_user_id = session.get('user_id')
        user_role = session.get('role')
        
        if current_user_id != user_id and user_role not in ['admin', 'superadmin']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        preset_name = data.get('preset_name', '').strip()
        filter_criteria = data.get('filter_criteria', {})
        is_default = bool(data.get('is_default', False))
        
        if not preset_name:
            return jsonify({'success': False, 'error': 'Preset name is required'}), 400
        
        conn = sqlite3.connect('scheduler.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # If default, unset others
        if is_default:
            cursor.execute("""
                UPDATE filter_presets 
                SET is_default = 0 
                WHERE user_id = ? AND is_default = 1
            """, (user_id,))
        
        # Insert new preset
        cursor.execute("""
            INSERT INTO filter_presets 
            (user_id, preset_name, filter_criteria, is_default, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            preset_name,
            json.dumps(filter_criteria),
            is_default,
            datetime.now().isoformat()
        ))
        
        preset_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'preset_id': preset_id,
            'message': 'Filter preset saved successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/filter-presets/<int:preset_id>', methods=['DELETE'])
@login_required
def delete_filter_preset(user_id, preset_id):
    """Delete filter preset"""
    try:
        # Security check
        current_user_id = session.get('user_id')
        user_role = session.get('role')
        
        if current_user_id != user_id and user_role not in ['admin', 'superadmin']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        conn = sqlite3.connect('scheduler.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if preset exists and belongs to user
        cursor.execute("""
            SELECT id FROM filter_presets 
            WHERE id = ? AND user_id = ?
        """, (preset_id, user_id))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Filter preset not found'}), 404
        
        # Delete preset
        cursor.execute("DELETE FROM filter_presets WHERE id = ? AND user_id = ?", (preset_id, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Filter preset deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



if __name__ == '__main__':
    # Initialize database and create tables
    init_database()
    create_migration_tables()
    add_ranking_system()
    initialize_billing_system()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
