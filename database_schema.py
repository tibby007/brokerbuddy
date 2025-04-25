"""
BrokerBuddy Database Schema

This module defines the database schema for the BrokerBuddy application.
It includes models for lenders, their criteria, and the relationships between them.
"""

import sqlite3
import os
import json
from datetime import datetime

class BrokerBuddyDB:
    def __init__(self, db_path='/home/ubuntu/brokerbuddy/brokerbuddy.db'):
        """Initialize the database connection."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        return self.conn
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            
    def create_tables(self):
        """Create all necessary tables for the BrokerBuddy application."""
        self.connect()
        
        # Create Lender table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS lenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            program_type TEXT NOT NULL,  -- 'App Only' or 'Full Financials'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Criteria Categories table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS criteria_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Lender Criteria table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS lender_criteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lender_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            value TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lender_id) REFERENCES lenders (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES criteria_categories (id) ON DELETE CASCADE,
            UNIQUE (lender_id, category_id)
        )
        ''')
        
        # Create Client table for saving client profiles
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Client Criteria table for storing client information
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_criteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES criteria_categories (id) ON DELETE CASCADE,
            UNIQUE (client_id, category_id)
        )
        ''')
        
        # Create Matches table for storing match results
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            lender_id INTEGER NOT NULL,
            match_score REAL NOT NULL,
            match_details TEXT,  -- JSON string with detailed match information
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE,
            FOREIGN KEY (lender_id) REFERENCES lenders (id) ON DELETE CASCADE
        )
        ''')
        
        # Create Settings table for application settings
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create CRM Integration table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS crm_integrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            api_key TEXT,
            api_url TEXT,
            settings TEXT,  -- JSON string with integration settings
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Email Templates table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()
        self.close()
        
    def populate_criteria_categories(self):
        """Populate the criteria categories based on the spreadsheet analysis."""
        self.connect()
        
        # Common criteria categories from both program types
        criteria_categories = [
            ("amount_considered", "Amount range considered by the lender"),
            ("time_in_business", "Minimum time in business required"),
            ("personal_credit", "Personal credit score requirements"),
            ("bank_statements", "Bank statement requirements"),
            ("collateral_age", "Age restrictions for equipment collateral"),
            ("titled_vehicles", "Requirements for titled vehicles"),
            ("restricted_industries", "Industries not accepted by the lender"),
            ("restricted_equipment", "Equipment types not accepted by the lender"),
            ("state_restrictions", "States where the lender does not operate"),
            ("cost_of_funds", "Cost of funds ranges"),
            ("max_commission", "Maximum commission allowed"),
            ("syndicator_notes", "Additional notes from the syndicator"),
            ("disclosure_requirements", "Required disclosures"),
            ("startups", "Requirements for startup businesses"),
            ("special_products", "Special product offerings"),
            ("paynet", "Paynet requirements"),
            ("business_credit", "Business credit requirements"),
            ("special_deals", "Special deal offerings")
        ]
        
        for name, description in criteria_categories:
            self.cursor.execute(
                "INSERT OR IGNORE INTO criteria_categories (name, description) VALUES (?, ?)",
                (name, description)
            )
            
        self.conn.commit()
        self.close()
        
    def initialize_database(self):
        """Initialize the database with tables and basic data."""
        self.create_tables()
        self.populate_criteria_categories()
        
        return {"status": "success", "message": "Database initialized successfully"}
