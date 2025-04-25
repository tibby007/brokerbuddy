"""
BrokerBuddy Deployment Script

This script prepares and packages the BrokerBuddy application for deployment.
"""

import os
import shutil
import sys
import subprocess

# Define paths
PROJECT_DIR = '/home/ubuntu/brokerbuddy'
DEPLOY_DIR = '/home/ubuntu/brokerbuddy_deploy'

# Create deployment directory
if os.path.exists(DEPLOY_DIR):
    shutil.rmtree(DEPLOY_DIR)
os.makedirs(DEPLOY_DIR)

# Copy all necessary files
files_to_copy = [
    'app.py',
    'wsgi.py',
    'database_schema.py',
    'data_importer.py',
    'matching_engine.py',
    'requirements.txt',
    'user_guide.md',
    'maintenance_guide.md'
]

for file in files_to_copy:
    src = os.path.join(PROJECT_DIR, file)
    dst = os.path.join(DEPLOY_DIR, file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Copied {file}")
    else:
        print(f"Warning: {file} not found")

# Copy directories
dirs_to_copy = [
    'templates',
    'static'
]

for dir_name in dirs_to_copy:
    src_dir = os.path.join(PROJECT_DIR, dir_name)
    dst_dir = os.path.join(DEPLOY_DIR, dir_name)
    if os.path.exists(src_dir):
        shutil.copytree(src_dir, dst_dir)
        print(f"Copied directory {dir_name}")
    else:
        print(f"Warning: Directory {dir_name} not found")

# Copy database if it exists
db_path = os.path.join(PROJECT_DIR, 'brokerbuddy.db')
if os.path.exists(db_path):
    shutil.copy2(db_path, os.path.join(DEPLOY_DIR, 'brokerbuddy.db'))
    print("Copied database")
else:
    print("Warning: Database file not found")

# Create .env file for environment variables
env_content = """
# BrokerBuddy Environment Variables
SECRET_KEY=brokerbuddy_production_secret_key
DATABASE_PATH=/home/ubuntu/brokerbuddy/brokerbuddy.db
PORT=5000
"""

with open(os.path.join(DEPLOY_DIR, '.env'), 'w') as f:
    f.write(env_content)
print("Created .env file")

# Create a simple README
readme_content = """
# BrokerBuddy

A web application for commercial finance brokers to match clients with equipment finance lenders.

## Deployment

1. Install requirements:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   gunicorn --bind 0.0.0.0:5000 wsgi:app
   ```

## Documentation

- See user_guide.md for usage instructions
- See maintenance_guide.md for maintenance information
"""

with open(os.path.join(DEPLOY_DIR, 'README.md'), 'w') as f:
    f.write(readme_content)
print("Created README.md")

print("\nDeployment package created successfully at", DEPLOY_DIR)
print("The application is ready for production deployment.")
