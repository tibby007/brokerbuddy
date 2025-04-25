"""
BrokerBuddy Production Configuration

This module configures the BrokerBuddy application for production deployment.
"""

import os
from flask import Flask
import sqlite3
import sys
sys.path.append('/home/ubuntu/brokerbuddy')
from database_schema import BrokerBuddyDB
from matching_engine import MatchingEngine

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'brokerbuddy_production_secret_key')

# Production configuration
app.config.update(
    ENV='production',
    DEBUG=False,
    TESTING=False,
    DATABASE_PATH=os.environ.get('DATABASE_PATH', '/home/ubuntu/brokerbuddy/brokerbuddy.db'),
    SERVER_NAME=os.environ.get('SERVER_NAME', None),
    PREFERRED_URL_SCHEME='https'
)

# Database connection helper
def get_db():
    db_path = app.config['DATABASE_PATH']
    db = BrokerBuddyDB(db_path)
    db.connect()
    return db

# Get matching engine
def get_matching_engine():
    db = get_db()
    return MatchingEngine(db.conn)

# Initialize database if it doesn't exist
def init_db():
    if not os.path.exists(app.config['DATABASE_PATH']):
        db = BrokerBuddyDB(app.config['DATABASE_PATH'])
        db.initialize_database()
        print(f"Database initialized at {app.config['DATABASE_PATH']}")

# Import routes after app is created to avoid circular imports
from app import *

# Initialize the application
if __name__ == '__main__':
    # Initialize database if needed
    init_db()
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
