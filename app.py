"""
BrokerBuddy Web Interface Design

This module defines the Flask web application for the BrokerBuddy tool.
It includes routes for the main pages, client input form, and lender matching.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import sqlite3
import json
import os
import sys
sys.path.append('/home/ubuntu/brokerbuddy')
from database_schema import BrokerBuddyDB

# Create Flask application
app = Flask(__name__)
app.secret_key = 'brokerbuddy_secret_key'  # For session and flash messages

# Database connection helper
def get_db():
    db = BrokerBuddyDB()
    db.connect()
    return db

# Routes
@app.route('/')
def index():
    """Home page with introduction and navigation."""
    return render_template('index.html')

@app.route('/client-form')
def client_form():
    """Client information input form."""
    # Get criteria categories for the form
    db = get_db()
    db.cursor.execute("""
        SELECT id, name, description 
        FROM criteria_categories 
        ORDER BY name
    """)
    categories = db.cursor.fetchall()
    db.close()
    
    return render_template('client_form.html', categories=categories)

@app.route('/submit-client', methods=['POST'])
def submit_client():
    """Process client form submission and find matching lenders."""
    if request.method == 'POST':
        # Get form data
        client_data = {}
        for field in request.form:
            client_data[field] = request.form[field]
        
        # Store in session for results page
        session['client_data'] = client_data
        
        # Redirect to results page
        return redirect(url_for('results'))
    
    # If not POST, redirect to form
    return redirect(url_for('client_form'))

@app.route('/results')
def results():
    """Display matching lenders based on client information."""
    # Get client data from session
    client_data = session.get('client_data', {})
    if not client_data:
        flash('No client data found. Please fill out the form first.')
        return redirect(url_for('client_form'))
    
    # Find matching lenders
    matches = find_matching_lenders(client_data)
    
    return render_template('results.html', 
                          client_data=client_data, 
                          matches=matches)

@app.route('/lender/<int:lender_id>')
def lender_details(lender_id):
    """Display detailed information about a specific lender."""
    db = get_db()
    
    # Get lender information
    db.cursor.execute("""
        SELECT id, name, program_type
        FROM lenders
        WHERE id = ?
    """, (lender_id,))
    lender = db.cursor.fetchone()
    
    if not lender:
        db.close()
        flash('Lender not found.')
        return redirect(url_for('index'))
    
    # Get lender criteria
    db.cursor.execute("""
        SELECT c.name, c.description, lc.value
        FROM lender_criteria lc
        JOIN criteria_categories c ON lc.category_id = c.id
        WHERE lc.lender_id = ?
        ORDER BY c.name
    """, (lender_id,))
    criteria = db.cursor.fetchall()
    
    db.close()
    
    return render_template('lender_details.html', 
                          lender=lender, 
                          criteria=criteria)

@app.route('/admin')
def admin():
    """Admin page for managing lenders and criteria."""
    db = get_db()
    
    # Get all lenders
    db.cursor.execute("""
        SELECT id, name, program_type
        FROM lenders
        ORDER BY name
    """)
    lenders = db.cursor.fetchall()
    
    # Get all criteria categories
    db.cursor.execute("""
        SELECT id, name, description
        FROM criteria_categories
        ORDER BY name
    """)
    categories = db.cursor.fetchall()
    
    db.close()
    
    return render_template('admin.html', 
                          lenders=lenders, 
                          categories=categories)

@app.route('/update-lender/<int:lender_id>', methods=['GET', 'POST'])
def update_lender(lender_id):
    """Update lender information and criteria."""
    db = get_db()
    
    if request.method == 'POST':
        # Update lender information
        name = request.form.get('name')
        program_type = request.form.get('program_type')
        
        db.cursor.execute("""
            UPDATE lenders
            SET name = ?, program_type = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, program_type, lender_id))
        
        # Update criteria values
        for field in request.form:
            if field.startswith('criterion_'):
                category_id = int(field.split('_')[1])
                value = request.form[field]
                
                db.cursor.execute("""
                    INSERT OR REPLACE INTO lender_criteria
                    (lender_id, category_id, value, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (lender_id, category_id, value))
        
        db.conn.commit()
        flash('Lender updated successfully.')
        return redirect(url_for('admin'))
    
    # GET request - show form with current values
    db.cursor.execute("""
        SELECT id, name, program_type
        FROM lenders
        WHERE id = ?
    """, (lender_id,))
    lender = db.cursor.fetchone()
    
    if not lender:
        db.close()
        flash('Lender not found.')
        return redirect(url_for('admin'))
    
    # Get all criteria categories
    db.cursor.execute("""
        SELECT id, name, description
        FROM criteria_categories
        ORDER BY name
    """)
    categories = db.cursor.fetchall()
    
    # Get current criteria values for this lender
    db.cursor.execute("""
        SELECT category_id, value
        FROM lender_criteria
        WHERE lender_id = ?
    """, (lender_id,))
    criteria_values = {row['category_id']: row['value'] for row in db.cursor.fetchall()}
    
    db.close()
    
    return render_template('update_lender.html', 
                          lender=lender, 
                          categories=categories, 
                          criteria_values=criteria_values)

@app.route('/email-lender/<int:lender_id>', methods=['GET', 'POST'])
def email_lender(lender_id):
    """Email a lender about a client or deal."""
    db = get_db()
    
    # Get lender information
    db.cursor.execute("""
        SELECT id, name, program_type
        FROM lenders
        WHERE id = ?
    """, (lender_id,))
    lender = db.cursor.fetchone()
    
    if not lender:
        db.close()
        flash('Lender not found.')
        return redirect(url_for('results'))
    
    # Get email templates
    db.cursor.execute("""
        SELECT id, name, subject
        FROM email_templates
        ORDER BY name
    """)
    templates = db.cursor.fetchall()
    
    db.close()
    
    if request.method == 'POST':
        # In a real application, this would send an email
        # For now, just show a success message
        flash(f'Email sent to {lender["name"]}!')
        return redirect(url_for('results'))
    
    return render_template('email_lender.html', 
                          lender=lender, 
                          templates=templates,
                          client_data=session.get('client_data', {}))

@app.route('/crm-settings')
def crm_settings():
    """CRM integration settings."""
    db = get_db()
    
    # Get CRM integrations
    db.cursor.execute("""
        SELECT id, name, api_url
        FROM crm_integrations
        ORDER BY name
    """)
    integrations = db.cursor.fetchall()
    
    db.close()
    
    return render_template('crm_settings.html', integrations=integrations)

# Helper functions
def find_matching_lenders(client_data):
    """Find lenders that match the client criteria."""
    db = get_db()
    
    # Get all lenders
    db.cursor.execute("""
        SELECT id, name, program_type
        FROM lenders
        ORDER BY name
    """)
    lenders = db.cursor.fetchall()
    
    matches = []
    
    for lender in lenders:
        # Calculate match score for this lender
        match_score, match_details = calculate_match_score(db, lender['id'], client_data)
        
        if match_score > 0:
            matches.append({
                'lender_id': lender['id'],
                'lender_name': lender['name'],
                'program_type': lender['program_type'],
                'match_score': match_score,
                'match_details': match_details
            })
    
    db.close()
    
    # Sort matches by score (highest first)
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return matches

def calculate_match_score(db, lender_id, client_data):
    """Calculate a match score between a lender and client data."""
    # Get lender criteria
    db.cursor.execute("""
        SELECT c.name, c.description, lc.value
        FROM lender_criteria lc
        JOIN criteria_categories c ON lc.category_id = c.id
        WHERE lc.lender_id = ?
    """, (lender_id,))
    lender_criteria = db.cursor.fetchall()
    
    # Initialize score and details
    score = 0
    max_possible_score = 0
    details = []
    
    # Check each criterion
    for criterion in lender_criteria:
        criterion_name = criterion['name']
        criterion_value = criterion['value']
        client_value = client_data.get(criterion_name, '')
        
        # Skip if no client value or lender value
        if not client_value or not criterion_value:
            continue
        
        # Different matching logic based on criterion type
        match_result = False
        reason = ''
        
        if criterion_name == 'amount_considered':
            # Check if client amount is within lender's range
            match_result, reason = match_amount(client_value, criterion_value)
        elif criterion_name == 'time_in_business':
            # Check if client's time in business meets lender's requirement
            match_result, reason = match_time_in_business(client_value, criterion_value)
        elif criterion_name == 'personal_credit':
            # Check if client's credit score meets lender's requirement
            match_result, reason = match_credit_score(client_value, criterion_value)
        else:
            # Generic string matching for other criteria
            match_result = client_value.lower() in criterion_value.lower()
            reason = f"Client: {client_value}, Lender: {criterion_value}"
        
        # Update score and details
        max_possible_score += 1
        if match_result:
            score += 1
            details.append({
                'criterion': criterion_name,
                'result': 'Match',
                'reason': reason
            })
        else:
            details.append({
                'criterion': criterion_name,
                'result': 'No Match',
                'reason': reason
            })
    
    # Calculate percentage score if there were any criteria to match
    percentage_score = (score / max_possible_score * 100) if max_possible_score > 0 else 0
    
    return percentage_score, details

def match_amount(client_amount, lender_range):
    """Check if client amount is within lender's range."""
    try:
        # Remove non-numeric characters and convert to float
        client_amount = float(client_amount.replace('$', '').replace(',', ''))
        
        # Extract min and max from lender range (e.g., "$10k-$150k")
        lender_range = lender_range.replace('$', '').replace(',', '')
        parts = lender_range.split('-')
        
        min_amount = parse_amount(parts[0])
        max_amount = parse_amount(parts[1]) if len(parts) > 1 else float('inf')
        
        match_result = min_amount <= client_amount <= max_amount
        reason = f"Client: ${client_amount:,.2f}, Lender: {lender_range}"
        
        return match_result, reason
    except:
        return False, f"Could not parse amount: Client: {client_amount}, Lender: {lender_range}"

def parse_amount(amount_str):
    """Parse amount string with k/m suffixes."""
    amount_str = amount_str.strip().lower()
    
    if 'k' in amount_str:
        return float(amount_str.replace('k', '')) * 1000
    elif 'm' in amount_str:
        return float(amount_str.replace('m', '')) * 1000000
    else:
        return float(amount_str)

def match_time_in_business(client_time, lender_requirement):
    """Check if client's time in business meets lender's requirement."""
    try:
        # Convert to months for comparison
        client_months = parse_time_in_business(client_time)
        lender_months = parse_time_in_business(lender_requirement)
        
        match_result = client_months >= lender_months
        reason = f"Client: {client_time}, Lender requires: {lender_requirement}"
        
        return match_result, reason
    except:
        return False, f"Could not parse time: Client: {client_time}, Lender: {lender_requirement}"

def parse_time_in_business(time_str):
    """Parse time in business string to months."""
    time_str = time_str.lower()
    
    if 'year' in time_str or 'yr' in time_str:
        # Extract number of years
        years = float(''.join(c for c in time_str if c.isdigit() or c == '.'))
        return years * 12
    elif 'month' in time_str or 'mo' in time_str:
        # Extract number of months
        return float(''.join(c for c in time_str if c.isdigit() or c == '.'))
    else:
        # Assume it's just a number representing years
        return float(''.join(c for c in time_str if c.isdigit() or c == '.')) * 12

def match_credit_score(client_score, lender_requirement):
    """Check if client's credit score meets lender's requirement."""
    try:
        client_score = int(''.join(c for c in client_score if c.isdigit()))
        
        # Extract minimum score from lender requirement
        if '+' in lender_requirement:
            # Format like "650+"
            min_score = int(''.join(c for c in lender_requirement if c.isdigit()))
            match_result = client_score >= min_score
        elif '-' in lender_requirement:
            # Format like "650-700"
            parts = lender_requirement.split('-')
            min_score = int(''.join(c for c in parts[0] if c.isdigit()))
            max_score = int(''.join(c for c in parts[1] if c.isdigit()))
            match_result = min_score <= client_score <= max_score
        else:
            # Just a number
            min_score = int(''.join(c for c in lender_requirement if c.isdigit()))
            match_result = client_score >= min_score
        
        reason = f"Client: {client_score}, Lender requires: {lender_requirement}"
        
        return match_result, reason
    except:
        return False, f"Could not parse credit score: Client: {client_score}, Lender: {lender_requirement}"

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
