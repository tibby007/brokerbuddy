"""
BrokerBuddy Data Importer

This module handles importing lender data from the Excel spreadsheet into the database.
"""

import pandas as pd
import sqlite3
import os
import json
from datetime import datetime
import sys
sys.path.append('/home/ubuntu/brokerbuddy')
from database_schema import BrokerBuddyDB

class LenderDataImporter:
    def __init__(self, excel_file, db_path='/home/ubuntu/brokerbuddy/brokerbuddy.db'):
        """Initialize the data importer with the Excel file path."""
        self.excel_file = excel_file
        self.db = BrokerBuddyDB(db_path)
        
    def import_data(self):
        """Import all lender data from the Excel file into the database."""
        # Initialize the database
        self.db.initialize_database()
        
        # Import data from both sheets
        self.import_app_only_data()
        self.import_full_financials_data()
        
        return {"status": "success", "message": "Lender data imported successfully"}
    
    def import_app_only_data(self):
        """Import data from the 'App Only' sheet."""
        try:
            # Read the App Only sheet
            app_only_df = pd.read_excel(self.excel_file, sheet_name='App Only')
            
            # Connect to the database
            self.db.connect()
            
            # Get criteria categories from database
            self.db.cursor.execute("SELECT id, name FROM criteria_categories")
            categories = {row['name']: row['id'] for row in self.db.cursor.fetchall()}
            
            # Map spreadsheet rows to criteria categories
            criteria_mapping = self._get_app_only_criteria_mapping(app_only_df)
            
            # Get lender columns (skip the first column which contains criteria names)
            lender_columns = [col for col in app_only_df.columns if col != 'APP-ONLY Programs' and pd.notna(col)]
            
            # Process each lender
            for lender_name in lender_columns:
                # Insert lender
                self.db.cursor.execute(
                    "INSERT OR IGNORE INTO lenders (name, program_type) VALUES (?, ?)",
                    (lender_name, 'App Only')
                )
                self.db.conn.commit()
                
                # Get lender ID
                self.db.cursor.execute("SELECT id FROM lenders WHERE name = ?", (lender_name,))
                lender_id = self.db.cursor.fetchone()['id']
                
                # Process each criterion for this lender
                for criterion_name, row_index in criteria_mapping.items():
                    if criterion_name in categories:
                        category_id = categories[criterion_name]
                        
                        # Get the value for this lender and criterion
                        value = app_only_df.iloc[row_index, app_only_df.columns.get_loc(lender_name)]
                        
                        # Skip if value is NaN
                        if pd.isna(value):
                            continue
                            
                        # Convert value to string
                        value_str = str(value)
                        
                        # Insert or update lender criterion
                        self.db.cursor.execute("""
                            INSERT OR REPLACE INTO lender_criteria 
                            (lender_id, category_id, value, updated_at) 
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """, (lender_id, category_id, value_str))
            
            self.db.conn.commit()
            
        except Exception as e:
            print(f"Error importing App Only data: {e}")
            if self.db.conn:
                self.db.conn.rollback()
        finally:
            self.db.close()
    
    def import_full_financials_data(self):
        """Import data from the 'Full Financials' sheet."""
        try:
            # Read the Full Financials sheet
            full_financials_df = pd.read_excel(self.excel_file, sheet_name='Full Financials')
            
            # Connect to the database
            self.db.connect()
            
            # Get criteria categories from database
            self.db.cursor.execute("SELECT id, name FROM criteria_categories")
            categories = {row['name']: row['id'] for row in self.db.cursor.fetchall()}
            
            # Map spreadsheet rows to criteria categories
            criteria_mapping = self._get_full_financials_criteria_mapping(full_financials_df)
            
            # Get lender columns (skip the first two columns)
            lender_columns = [col for col in full_financials_df.columns 
                             if col != 'APP-ONLY Programs' and col != 'Unnamed: 1' and pd.notna(col)]
            
            # Process each lender
            for lender_name in lender_columns:
                # Insert lender
                self.db.cursor.execute(
                    "INSERT OR IGNORE INTO lenders (name, program_type) VALUES (?, ?)",
                    (lender_name, 'Full Financials')
                )
                self.db.conn.commit()
                
                # Get lender ID
                self.db.cursor.execute("SELECT id FROM lenders WHERE name = ?", (lender_name,))
                lender_id = self.db.cursor.fetchone()['id']
                
                # Process each criterion for this lender
                for criterion_name, row_index in criteria_mapping.items():
                    if criterion_name in categories:
                        category_id = categories[criterion_name]
                        
                        # Get the value for this lender and criterion
                        value = full_financials_df.iloc[row_index, full_financials_df.columns.get_loc(lender_name)]
                        
                        # Skip if value is NaN
                        if pd.isna(value):
                            continue
                            
                        # Convert value to string
                        value_str = str(value)
                        
                        # Insert or update lender criterion
                        self.db.cursor.execute("""
                            INSERT OR REPLACE INTO lender_criteria 
                            (lender_id, category_id, value, updated_at) 
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """, (lender_id, category_id, value_str))
            
            self.db.conn.commit()
            
        except Exception as e:
            print(f"Error importing Full Financials data: {e}")
            if self.db.conn:
                self.db.conn.rollback()
        finally:
            self.db.close()
    
    def _get_app_only_criteria_mapping(self, df):
        """Map criteria names from App Only sheet to database categories."""
        # Get the first column which contains criteria names
        criteria_column = df.iloc[:, 0]
        
        # Create mapping from spreadsheet criteria to database categories
        mapping = {}
        
        # Find all non-NaN values in the first column
        for i, value in enumerate(criteria_column):
            if pd.notna(value) and value != '':
                # Map spreadsheet criteria names to database category names
                if value == 'Amount considered':
                    mapping['amount_considered'] = i
                elif value == 'Time in Business':
                    mapping['time_in_business'] = i
                elif value == 'Start-ups ':
                    mapping['startups'] = i
                elif value == 'Personal Credit':
                    mapping['personal_credit'] = i
                elif value == 'Paynet':
                    mapping['paynet'] = i
                elif value == 'Bank Statements':
                    mapping['bank_statements'] = i
                elif value == 'Collateral Age':
                    mapping['collateral_age'] = i
                elif value == 'Specialialty Products':
                    mapping['special_products'] = i
                elif value == 'Titled Vehicles':
                    mapping['titled_vehicles'] = i
                elif value == 'Restricted Industries':
                    mapping['restricted_industries'] = i
                elif value == 'Restricted Equipment':
                    mapping['restricted_equipment'] = i
                elif value == 'State Restrictions':
                    mapping['state_restrictions'] = i
                elif value == 'Cost of Funds Ranges':
                    mapping['cost_of_funds'] = i
                elif value == 'Max Commision':
                    mapping['max_commission'] = i
                elif value == 'Syndicator\'s Notes':
                    mapping['syndicator_notes'] = i
                elif value == 'Disclosure Requirements':
                    mapping['disclosure_requirements'] = i
        
        return mapping
    
    def _get_full_financials_criteria_mapping(self, df):
        """Map criteria names from Full Financials sheet to database categories."""
        # Get the first column which contains criteria names
        criteria_column = df.iloc[:, 0]
        
        # Create mapping from spreadsheet criteria to database categories
        mapping = {}
        
        # Find all non-NaN values in the first column
        for i, value in enumerate(criteria_column):
            if pd.notna(value) and value != '':
                # Map spreadsheet criteria names to database category names
                if value == 'Amount considered':
                    mapping['amount_considered'] = i
                elif value == 'Personal Credit':
                    mapping['personal_credit'] = i
                elif value == 'Business Credit':
                    mapping['business_credit'] = i
                elif value == 'Bank Statements':
                    mapping['bank_statements'] = i
                elif value == 'Collateral Age':
                    mapping['collateral_age'] = i
                elif value == 'Special deals':
                    mapping['special_deals'] = i
                elif value == 'Titled Vehicles':
                    mapping['titled_vehicles'] = i
                elif value == 'Time in Business':
                    mapping['time_in_business'] = i
                elif value == 'Start-ups ':
                    mapping['startups'] = i
                elif value == 'Special Industries':
                    mapping['special_products'] = i
                elif value == 'Restricted Industries':
                    mapping['restricted_industries'] = i
                elif value == 'Restricted Equipment':
                    mapping['restricted_equipment'] = i
                elif value == 'State Restrictions':
                    mapping['state_restrictions'] = i
                elif value == 'Cost of Fund':
                    mapping['cost_of_funds'] = i
                elif value == 'Max Commision':
                    mapping['max_commission'] = i
                elif value == 'Syndicator\'s Notes':
                    mapping['syndicator_notes'] = i
                elif value == 'Disclosure Requirements':
                    mapping['disclosure_requirements'] = i
        
        return mapping

# If run directly, import data from the specified Excel file
if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        excel_file = '/home/ubuntu/upload/Syndication Spreadsheet 6.17.xlsx'
    
    importer = LenderDataImporter(excel_file)
    result = importer.import_data()
    print(result)
