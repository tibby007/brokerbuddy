# BrokerBuddy Render Deployment Instructions

This guide will walk you through deploying the BrokerBuddy application on Render.com.

## Prerequisites

- A Render.com account (sign up at https://render.com if you don't have one)
- The BrokerBuddy application files (provided in the zip file)

## Deployment Steps

### 1. Prepare Your Repository

First, you'll need to upload the BrokerBuddy files to a Git repository:

1. Create a new repository on GitHub, GitLab, or Bitbucket
2. Extract the provided zip file to your local machine
3. Initialize a Git repository in the extracted folder:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```
4. Add your remote repository and push:
   ```
   git remote add origin YOUR_REPOSITORY_URL
   git push -u origin main
   ```

### 2. Create a New Web Service on Render

1. Log in to your Render dashboard
2. Click the "New +" button and select "Web Service"
3. Connect your Git repository where you uploaded the BrokerBuddy files
4. Configure your web service:
   - **Name**: BrokerBuddy (or your preferred name)
   - **Environment**: Python
   - **Region**: Choose the region closest to your users
   - **Branch**: main (or your default branch)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`

### 3. Configure Environment Variables

Add the following environment variables in the Render dashboard:
- **SECRET_KEY**: A secure random string for Flask sessions
- **DATABASE_PATH**: `/var/data/brokerbuddy.db` (Render persistent storage path)
- **PORT**: `10000` (or let Render assign automatically)

### 4. Set Up Persistent Storage (Optional)

If you want to persist the database between deployments:

1. In your Render dashboard, go to your BrokerBuddy web service
2. Click on "Disks" in the left sidebar
3. Click "Create Disk"
4. Configure the disk:
   - **Name**: brokerbuddy-data
   - **Mount Path**: `/var/data`
   - **Size**: 1 GB (or as needed)

### 5. Deploy Your Application

1. Click "Create Web Service" to start the deployment
2. Render will automatically build and deploy your application
3. Once deployment is complete, you can access your application at the provided URL

## Troubleshooting

If you encounter issues during deployment:

1. Check the Render logs for error messages
2. Verify that all required files are present in your repository
3. Ensure your requirements.txt file includes all necessary dependencies
4. Check that your database path matches the configured persistent storage

## Updating Your Application

To update your application after making changes:

1. Make your changes locally
2. Commit and push to your Git repository
3. Render will automatically detect changes and redeploy

## Additional Resources

- Render Python documentation: https://render.com/docs/deploy-python
- Flask on Render guide: https://render.com/docs/deploy-flask
- Render persistent disk documentation: https://render.com/docs/disks
