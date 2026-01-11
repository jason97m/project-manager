# Project Manager - Complete Deployment Guide

## Overview

This guide will walk you through deploying the Project Manager application from your local machine to Heroku using GitHub as your code repository.

---

## Part 1: Local Development Setup

### Step 1: Verify Your Local Environment

Make sure you have installed:
- Python 3.11 or higher
- Git
- A code editor (VS Code, PyCharm, etc.)

### Step 2: Set Up the Project Locally

1. Navigate to where you want to store the project:
```bash
cd ~/projects  # or wherever you prefer
```

2. Copy all the project files to this directory

3. Create a virtual environment:
```bash
python -m venv venv
```

4. Activate the virtual environment:
```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

### Step 3: Test Locally

1. Run the application:
```bash
python app.py
```

2. Open your browser to `http://localhost:5000`

3. Test the following:
   - Register a new account
   - Login
   - Create a program
   - Create a project
   - Add a task
   - Create a contact
   - Assign the contact to a task

4. Stop the server (Ctrl+C)

---

## Part 2: GitHub Setup

### Step 1: Create a GitHub Repository

1. Go to https://github.com
2. Click the "+" icon → "New repository"
3. Name it (e.g., `project-manager`)
4. Make it Public or Private (your choice)
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

### Step 2: Initialize Git and Push to GitHub

1. In your project directory, initialize Git:
```bash
git init
```

2. Add all files:
```bash
git add .
```

3. Make your first commit:
```bash
git commit -m "Initial commit - Project Manager application"
```

4. Add your GitHub repository as remote:
```bash
git remote add origin https://github.com/YOUR_USERNAME/project-manager.git
```
Replace `YOUR_USERNAME` with your actual GitHub username.

5. Push to GitHub:
```bash
git branch -M main
git push -u origin main
```

6. Verify on GitHub that all files are uploaded

---

## Part 3: Heroku Deployment

### Step 1: Install Heroku CLI

1. Download from: https://devcenter.heroku.com/articles/heroku-cli
2. Install following the instructions for your OS
3. Verify installation:
```bash
heroku --version
```

### Step 2: Login to Heroku

```bash
heroku login
```

This will open a browser window for you to login.

### Step 3: Create Heroku Application

1. Create a new Heroku app:
```bash
heroku create your-app-name-here
```

Replace `your-app-name-here` with your desired app name (must be unique across all Heroku). If you don't specify a name, Heroku will generate one for you.

2. Verify the app was created:
```bash
heroku apps
```

### Step 4: Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:essential-0
```

This creates a PostgreSQL database for your app. You can verify with:
```bash
heroku addons
```

### Step 5: Set Environment Variables

Set a secret key for Flask sessions:
```bash
heroku config:set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

Or set it manually:
```bash
heroku config:set SECRET_KEY="your-very-long-random-secret-key-here"
```

Verify:
```bash
heroku config
```

You should see both `DATABASE_URL` (auto-set by Heroku) and `SECRET_KEY`.

### Step 6: Deploy to Heroku

1. Make sure all changes are committed:
```bash
git status
```

2. If there are changes, commit them:
```bash
git add .
git commit -m "Prepare for Heroku deployment"
```

3. Push to Heroku:
```bash
git push heroku main
```

Wait for the deployment to complete. You'll see build logs.

### Step 7: Initialize the Database

Once deployed, the database tables need to be created:

```bash
heroku run python
```

Then in the Python shell:
```python
from app import app, db
with app.app_context():
    db.create_all()
exit()
```

### Step 8: Open Your Application

```bash
heroku open
```

This will open your deployed application in a browser!

---

## Part 4: Ongoing Development Workflow

### Making Changes

1. Edit files locally
2. Test locally:
```bash
python app.py
```

3. Commit changes:
```bash
git add .
git commit -m "Description of changes"
```

4. Push to GitHub:
```bash
git push origin main
```

5. Deploy to Heroku:
```bash
git push heroku main
```

### Viewing Logs

If something goes wrong:
```bash
heroku logs --tail
```

Press Ctrl+C to stop viewing logs.

### Accessing the Database

To access the PostgreSQL database:
```bash
heroku pg:psql
```

Useful commands:
- `\dt` - List all tables
- `SELECT * FROM user;` - View all users
- `\q` - Quit

---

## Part 5: Troubleshooting

### Application Won't Start

1. Check logs:
```bash
heroku logs --tail
```

2. Verify environment variables:
```bash
heroku config
```

3. Verify database is attached:
```bash
heroku addons
```

### Database Errors

1. Recreate database tables:
```bash
heroku run python
```
```python
from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
exit()
```

### Changes Not Showing

1. Make sure you committed:
```bash
git status
```

2. Make sure you pushed to Heroku:
```bash
git push heroku main
```

3. Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)

---

## Part 6: Managing the Application

### Scaling

To scale your app (increase/decrease resources):
```bash
heroku ps:scale web=1  # 1 web dyno (free tier)
```

### Restarting

To restart the application:
```bash
heroku restart
```

### Monitoring

View app info:
```bash
heroku apps:info
```

### Backup Database

```bash
heroku pg:backups:capture
heroku pg:backups:download
```

---

## Part 7: Domain Setup (Optional)

### Using a Custom Domain

1. Add domain to Heroku:
```bash
heroku domains:add www.yourdomain.com
```

2. Heroku will provide DNS target

3. Update your domain's DNS settings with your registrar

---

## Quick Reference Commands

### Local Development
```bash
source venv/bin/activate    # Activate virtual environment
python app.py               # Run locally
```

### Git
```bash
git add .                   # Stage changes
git commit -m "message"     # Commit
git push origin main        # Push to GitHub
```

### Heroku
```bash
heroku logs --tail          # View logs
heroku open                 # Open app in browser
git push heroku main        # Deploy
heroku restart              # Restart app
heroku pg:psql              # Access database
```

---

## Support

If you encounter issues:
1. Check the logs: `heroku logs --tail`
2. Verify configuration: `heroku config`
3. Check database: `heroku pg:info`
4. Review the README.md file
5. Check Heroku documentation: https://devcenter.heroku.com

---

## Next Steps

After deployment, consider:
1. Setting up continuous deployment from GitHub
2. Configuring custom domain
3. Setting up monitoring/alerts
4. Implementing database backups
5. Adding more features!

Good luck with your deployment!
