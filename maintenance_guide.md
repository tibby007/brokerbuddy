# BrokerBuddy Maintenance Guide

## Overview

This document provides guidelines for maintaining and updating the BrokerBuddy application over time. As lender guidelines change and new lenders become available, you'll need to update the system to ensure it continues to provide accurate matching results.

## Updating Lender Guidelines

### Using the Admin Interface

1. **Access the Admin Panel**: Navigate to the Admin section from the main navigation menu.
2. **Select a Lender**: Find the lender whose guidelines need updating and click "Edit".
3. **Update Guidelines**: Modify the criteria values as needed.
4. **Save Changes**: Click "Save" to update the database with the new guidelines.

### Directly Updating the Database

For bulk updates or when the admin interface is not accessible:

1. Connect to the SQLite database at `/home/ubuntu/brokerbuddy/brokerbuddy.db`
2. Use SQL commands to update the `lender_criteria` table:

```sql
UPDATE lender_criteria 
SET value = 'new_value', updated_at = CURRENT_TIMESTAMP
WHERE lender_id = (SELECT id FROM lenders WHERE name = 'Lender Name')
AND category_id = (SELECT id FROM criteria_categories WHERE name = 'category_name');
```

## Adding New Lenders

### Using the Admin Interface

1. **Access the Admin Panel**: Navigate to the Admin section.
2. **Add New Lender**: Click "Add New Lender".
3. **Enter Lender Details**: Provide the lender name and program type.
4. **Set Criteria Values**: Enter values for all relevant criteria.
5. **Save New Lender**: Click "Save" to add the lender to the database.

### Directly Adding to the Database

For bulk additions:

1. First, insert the lender into the `lenders` table:

```sql
INSERT INTO lenders (name, program_type) 
VALUES ('New Lender Name', 'App Only');
```

2. Then, add criteria for the new lender:

```sql
INSERT INTO lender_criteria (lender_id, category_id, value)
VALUES 
((SELECT id FROM lenders WHERE name = 'New Lender Name'),
 (SELECT id FROM criteria_categories WHERE name = 'amount_considered'),
 '$10k-$150k');
```

Repeat for each criterion.

## Importing New Lender Data from Spreadsheets

To import new lender data from updated spreadsheets:

1. Place the new spreadsheet in an accessible location.
2. Run the data importer script with the path to the new spreadsheet:

```bash
cd /home/ubuntu/brokerbuddy
python3 data_importer.py /path/to/new/spreadsheet.xlsx
```

The importer will add new lenders and update existing ones based on the spreadsheet content.

## Database Maintenance

### Regular Backups

Create regular backups of the database to prevent data loss:

```bash
cp /home/ubuntu/brokerbuddy/brokerbuddy.db /home/ubuntu/brokerbuddy/backups/brokerbuddy_$(date +%Y%m%d).db
```

Consider setting up a cron job for automated backups.

### Database Optimization

Periodically optimize the database to maintain performance:

```bash
sqlite3 /home/ubuntu/brokerbuddy/brokerbuddy.db 'VACUUM;'
```

## Application Updates

### Updating the Matching Algorithm

If you need to modify how client information is matched with lender criteria:

1. Edit the `/home/ubuntu/brokerbuddy/matching_engine.py` file.
2. Focus on the methods in the `MatchingEngine` class, particularly:
   - `calculate_match_score()`
   - The specific matching methods like `match_amount()`, `match_time_in_business()`, etc.
3. Restart the application after making changes.

### Adding New Criteria Categories

To add new types of criteria for matching:

1. Add the new category to the database:

```sql
INSERT INTO criteria_categories (name, description)
VALUES ('new_category_name', 'Description of the new category');
```

2. Update the `client_form.html` template to include fields for the new category.
3. Modify the matching engine to handle the new category.

## CRM Integration Maintenance

### Updating API Keys

If your CRM system requires API key updates:

1. Navigate to the CRM Settings page.
2. Update the API key and other integration settings.
3. Test the integration to ensure it's working correctly.

### Adding New CRM Integrations

To add support for a new CRM system:

1. Add the new CRM to the `crm_integrations` table.
2. Implement the integration logic in the application code.
3. Update the CRM settings interface to include the new option.

## Troubleshooting Common Issues

### Matching Issues

If the system isn't matching clients with appropriate lenders:

1. Check the client data being submitted.
2. Verify lender criteria in the database.
3. Review the matching algorithm logic for the specific criteria causing problems.
4. Check the logs for any errors during the matching process.

### Database Connection Issues

If the application can't connect to the database:

1. Verify the database file exists at `/home/ubuntu/brokerbuddy/brokerbuddy.db`.
2. Check file permissions.
3. Ensure SQLite is installed and functioning.

### Web Server Issues

If the web interface is unavailable:

1. Check if the Flask server is running.
2. Verify port 5000 is open and accessible.
3. Check for error messages in the application logs.
4. Restart the application if necessary.

## Contact for Support

For additional support or custom modifications to the BrokerBuddy system, please contact the development team at support@brokerbuddy.com.
