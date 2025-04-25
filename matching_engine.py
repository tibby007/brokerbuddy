"""
BrokerBuddy Matching Algorithm

This module implements the matching algorithm for the BrokerBuddy application.
It includes functions to match client information with lender criteria.
"""

import re
import json
import sqlite3
from datetime import datetime

class MatchingEngine:
    def __init__(self, db_connection):
        """Initialize the matching engine with a database connection."""
        self.conn = db_connection
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
    def find_matching_lenders(self, client_data):
        """
        Find lenders that match the client criteria.
        
        Args:
            client_data (dict): Dictionary containing client information
            
        Returns:
            list: List of dictionaries with matching lenders and scores
        """
        # Get all lenders
        self.cursor.execute("""
            SELECT id, name, program_type
            FROM lenders
            ORDER BY name
        """)
        lenders = self.cursor.fetchall()
        
        matches = []
        
        for lender in lenders:
            # Calculate match score for this lender
            match_score, match_details = self.calculate_match_score(lender['id'], client_data)
            
            # Only include lenders with a positive match score
            if match_score > 0:
                matches.append({
                    'lender_id': lender['id'],
                    'lender_name': lender['name'],
                    'program_type': lender['program_type'],
                    'match_score': match_score,
                    'match_details': match_details
                })
        
        # Sort matches by score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches
    
    def calculate_match_score(self, lender_id, client_data):
        """
        Calculate a match score between a lender and client data.
        
        Args:
            lender_id (int): ID of the lender
            client_data (dict): Dictionary containing client information
            
        Returns:
            tuple: (match_score, match_details)
        """
        # Get lender criteria
        self.cursor.execute("""
            SELECT c.name, c.description, lc.value
            FROM lender_criteria lc
            JOIN criteria_categories c ON lc.category_id = c.id
            WHERE lc.lender_id = ?
        """, (lender_id,))
        lender_criteria = self.cursor.fetchall()
        
        # Initialize score and details
        score = 0
        max_possible_score = 0
        details = []
        
        # Define criteria weights (some criteria are more important than others)
        criteria_weights = {
            'amount_considered': 2.0,
            'time_in_business': 1.5,
            'personal_credit': 1.5,
            'business_credit': 1.0,
            'bank_statements': 1.0,
            'collateral_age': 1.0,
            'titled_vehicles': 0.8,
            'restricted_industries': 1.2,
            'restricted_equipment': 1.2,
            'state_restrictions': 1.5,
            'startups': 0.8,
            'special_products': 0.5,
            'paynet': 0.8,
            'special_deals': 0.5
        }
        
        # Default weight for criteria not in the weights dictionary
        default_weight = 1.0
        
        # Check each criterion
        for criterion in lender_criteria:
            criterion_name = criterion['name']
            criterion_value = criterion['value']
            client_value = client_data.get(criterion_name, '')
            
            # Skip if no client value or lender value
            if not client_value or not criterion_value:
                continue
            
            # Get weight for this criterion
            weight = criteria_weights.get(criterion_name, default_weight)
            
            # Different matching logic based on criterion type
            match_result = False
            reason = ''
            
            if criterion_name == 'amount_considered':
                # Check if client amount is within lender's range
                match_result, reason = self.match_amount(client_value, criterion_value)
            elif criterion_name == 'time_in_business':
                # Check if client's time in business meets lender's requirement
                match_result, reason = self.match_time_in_business(client_value, criterion_value)
            elif criterion_name == 'personal_credit' or criterion_name == 'business_credit':
                # Check if client's credit score meets lender's requirement
                match_result, reason = self.match_credit_score(client_value, criterion_value)
            elif criterion_name == 'collateral_age':
                # Check if equipment age meets lender's requirement
                match_result, reason = self.match_collateral_age(client_value, criterion_value)
            elif criterion_name == 'restricted_industries':
                # Check if client's industry is restricted
                match_result, reason = self.match_not_restricted(client_value, criterion_value)
                # Invert result since we want to match when NOT restricted
                match_result = not match_result
            elif criterion_name == 'restricted_equipment':
                # Check if client's equipment type is restricted
                match_result, reason = self.match_not_restricted(client_value, criterion_value)
                # Invert result since we want to match when NOT restricted
                match_result = not match_result
            elif criterion_name == 'state_restrictions':
                # Check if client's state is restricted
                match_result, reason = self.match_not_restricted(client_value, criterion_value)
                # Invert result since we want to match when NOT restricted
                match_result = not match_result
            else:
                # Generic string matching for other criteria
                match_result = self.generic_match(client_value, criterion_value)
                reason = f"Client: {client_value}, Lender: {criterion_value}"
            
            # Update score and details
            max_possible_score += weight
            if match_result:
                score += weight
                details.append({
                    'criterion': criterion_name,
                    'result': 'Match',
                    'reason': reason,
                    'weight': weight
                })
            else:
                details.append({
                    'criterion': criterion_name,
                    'result': 'No Match',
                    'reason': reason,
                    'weight': weight
                })
        
        # Calculate percentage score if there were any criteria to match
        percentage_score = (score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        return percentage_score, details
    
    def match_amount(self, client_amount, lender_range):
        """
        Check if client amount is within lender's range.
        
        Args:
            client_amount (str): Client's requested amount
            lender_range (str): Lender's acceptable amount range
            
        Returns:
            tuple: (match_result, reason)
        """
        try:
            # Remove non-numeric characters and convert to float
            client_amount = float(re.sub(r'[^\d.]', '', client_amount))
            
            # Extract min and max from lender range (e.g., "$10k-$150k")
            lender_range = lender_range.replace('$', '').replace(',', '')
            parts = lender_range.split('-')
            
            min_amount = self.parse_amount(parts[0])
            max_amount = self.parse_amount(parts[1]) if len(parts) > 1 else float('inf')
            
            match_result = min_amount <= client_amount <= max_amount
            reason = f"Client: ${client_amount:,.2f}, Lender: {lender_range}"
            
            return match_result, reason
        except Exception as e:
            return False, f"Could not parse amount: Client: {client_amount}, Lender: {lender_range}. Error: {str(e)}"
    
    def parse_amount(self, amount_str):
        """
        Parse amount string with k/m suffixes.
        
        Args:
            amount_str (str): Amount string with possible k/m suffix
            
        Returns:
            float: Parsed amount in dollars
        """
        amount_str = amount_str.strip().lower()
        
        if 'k' in amount_str:
            return float(amount_str.replace('k', '')) * 1000
        elif 'm' in amount_str:
            return float(amount_str.replace('m', '')) * 1000000
        else:
            return float(amount_str)
    
    def match_time_in_business(self, client_time, lender_requirement):
        """
        Check if client's time in business meets lender's requirement.
        
        Args:
            client_time (str): Client's time in business
            lender_requirement (str): Lender's time in business requirement
            
        Returns:
            tuple: (match_result, reason)
        """
        try:
            # Convert to months for comparison
            client_months = self.parse_time_in_business(client_time)
            
            # Handle special cases in lender requirements
            if "Full Years" in lender_requirement:
                # Extract the number before "Full Years"
                years = float(re.search(r'(\d+)\+?\s+Full Years', lender_requirement).group(1))
                lender_months = years * 12
            else:
                lender_months = self.parse_time_in_business(lender_requirement)
            
            match_result = client_months >= lender_months
            reason = f"Client: {client_time} ({client_months} months), Lender requires: {lender_requirement} ({lender_months} months)"
            
            return match_result, reason
        except Exception as e:
            return False, f"Could not parse time: Client: {client_time}, Lender: {lender_requirement}. Error: {str(e)}"
    
    def parse_time_in_business(self, time_str):
        """
        Parse time in business string to months.
        
        Args:
            time_str (str): Time string with possible year/month indicators
            
        Returns:
            float: Time in months
        """
        time_str = time_str.lower()
        
        if 'year' in time_str or 'yr' in time_str:
            # Extract number of years
            years = float(re.search(r'(\d+\.?\d*)', time_str).group(1))
            return years * 12
        elif 'month' in time_str or 'mo' in time_str:
            # Extract number of months
            return float(re.search(r'(\d+\.?\d*)', time_str).group(1))
        else:
            # Assume it's just a number representing years
            return float(re.search(r'(\d+\.?\d*)', time_str).group(1)) * 12
    
    def match_credit_score(self, client_score, lender_requirement):
        """
        Check if client's credit score meets lender's requirement.
        
        Args:
            client_score (str): Client's credit score
            lender_requirement (str): Lender's credit score requirement
            
        Returns:
            tuple: (match_result, reason)
        """
        try:
            # Extract client score
            client_score = int(re.search(r'(\d+)', client_score).group(1))
            
            # Handle different formats of lender requirements
            if '+' in lender_requirement:
                # Format like "650+"
                min_score = int(re.search(r'(\d+)\+', lender_requirement).group(1))
                match_result = client_score >= min_score
                reason = f"Client: {client_score}, Lender requires: {min_score}+"
            elif '-' in lender_requirement and not lender_requirement.startswith('No'):
                # Format like "650-700"
                match = re.search(r'(\d+)\s*-\s*(\d+)', lender_requirement)
                if match:
                    min_score = int(match.group(1))
                    max_score = int(match.group(2))
                    match_result = min_score <= client_score <= max_score
                    reason = f"Client: {client_score}, Lender requires: {min_score}-{max_score}"
                else:
                    # If we can't parse the range, just extract the first number
                    min_score = int(re.search(r'(\d+)', lender_requirement).group(1))
                    match_result = client_score >= min_score
                    reason = f"Client: {client_score}, Lender requires: {min_score}+"
            else:
                # Just a number or other format
                min_score = int(re.search(r'(\d+)', lender_requirement).group(1))
                match_result = client_score >= min_score
                reason = f"Client: {client_score}, Lender requires: {min_score}"
            
            return match_result, reason
        except Exception as e:
            return False, f"Could not parse credit score: Client: {client_score}, Lender: {lender_requirement}. Error: {str(e)}"
    
    def match_collateral_age(self, client_age, lender_requirement):
        """
        Check if equipment age meets lender's requirement.
        
        Args:
            client_age (str): Client's equipment age
            lender_requirement (str): Lender's equipment age requirement
            
        Returns:
            tuple: (match_result, reason)
        """
        try:
            # Extract client equipment age in years
            client_years = float(re.search(r'(\d+\.?\d*)', client_age).group(1))
            
            # Extract maximum age from lender requirement
            if 'year' in lender_requirement.lower():
                max_years = float(re.search(r'(\d+)', lender_requirement).group(1))
            else:
                max_years = float(re.search(r'(\d+)', lender_requirement).group(1))
            
            match_result = client_years <= max_years
            reason = f"Client: {client_age}, Lender requires: {lender_requirement}"
            
            return match_result, reason
        except Exception as e:
            return False, f"Could not parse collateral age: Client: {client_age}, Lender: {lender_requirement}. Error: {str(e)}"
    
    def match_not_restricted(self, client_value, restricted_list):
        """
        Check if client's value is in the restricted list.
        
        Args:
            client_value (str): Client's value (industry, equipment type, state)
            restricted_list (str): Comma-separated list of restricted values
            
        Returns:
            tuple: (is_restricted, reason)
        """
        try:
            # If restricted_list is "None" or similar, nothing is restricted
            if restricted_list.lower() in ['none', 'no', 'n/a', '']:
                return False, f"No restrictions"
            
            # Split restricted list by commas and clean up
            restricted_items = [item.strip().lower() for item in restricted_list.split(',')]
            
            # Check if client value is in restricted list
            client_value_lower = client_value.lower()
            is_restricted = any(item in client_value_lower or client_value_lower in item for item in restricted_items)
            
            reason = f"Client: {client_value}, Restricted: {restricted_list}"
            
            return is_restricted, reason
        except Exception as e:
            return False, f"Could not check restrictions: Client: {client_value}, Restricted: {restricted_list}. Error: {str(e)}"
    
    def generic_match(self, client_value, lender_value):
        """
        Generic string matching for criteria without specific matching logic.
        
        Args:
            client_value (str): Client's value
            lender_value (str): Lender's value
            
        Returns:
            bool: True if match, False otherwise
        """
        # Convert both to lowercase for case-insensitive comparison
        client_value_lower = client_value.lower()
        lender_value_lower = lender_value.lower()
        
        # Check if client value is in lender value or vice versa
        return client_value_lower in lender_value_lower or lender_value_lower in client_value_lower
    
    def save_match_results(self, client_id, matches):
        """
        Save match results to the database.
        
        Args:
            client_id (int): ID of the client
            matches (list): List of match dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete any existing matches for this client
            self.cursor.execute("DELETE FROM matches WHERE client_id = ?", (client_id,))
            
            # Insert new matches
            for match in matches:
                self.cursor.execute("""
                    INSERT INTO matches 
                    (client_id, lender_id, match_score, match_details) 
                    VALUES (?, ?, ?, ?)
                """, (
                    client_id, 
                    match['lender_id'], 
                    match['match_score'], 
                    json.dumps(match['match_details'])
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error saving match results: {e}")
            return False
