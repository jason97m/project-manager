# Project Manager

A comprehensive web-based project and program management system built with Flask and PostgreSQL.

## Features

- **User Authentication**: Secure registration and login system
- **Programs**: Group multiple projects under programs
- **Projects**: Create standalone or program-linked projects
- **Tasks**: Break down projects into manageable subtasks with priority and progress tracking
- **Milestones**: Track important dates and achievements
- **Contacts**: Manage team members and stakeholders
- **Materials**: Track materials and costs for programs, projects, and tasks
- **Assignments**: Assign contacts to programs, projects, and tasks
- **Date Tracking**: Set start and end dates at all levels

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL (production), SQLite (development)
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Deployment**: Heroku

## Local Development Setup

### Prerequisites

- Python 3.11+
- pip
- Git

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd project_manager
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables (optional for development):
```bash
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="sqlite:///project_manager.db"
```

5. Run the application:
```bash
python app.py
```

6. Open your browser to `http://localhost:5000`

## Heroku Deployment

### Prerequisites

- Heroku CLI installed
- Heroku account
- Git repository

### Deployment Steps

1. Login to Heroku:
```bash
heroku login
```

2. Create a new Heroku app:
```bash
heroku create your-app-name
```

3. Add PostgreSQL addon:
```bash
heroku addons:create heroku-postgresql:essential-0
```

4. Set environment variables:
```bash
heroku config:set SECRET_KEY="your-production-secret-key-here"
```

5. Deploy to Heroku:
```bash
git add .
git commit -m "Initial commit"
git push heroku main
```

6. Initialize the database:
```bash
heroku run python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

7. Open your app:
```bash
heroku open
```

## GitHub Setup

1. Create a new repository on GitHub

2. Initialize Git (if not already done):
```bash
git init
git add .
git commit -m "Initial commit"
```

3. Add remote and push:
```bash
git remote add origin https://github.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

## Usage

1. **Register**: Create a new account
2. **Login**: Access your dashboard
3. **Create a Program**: Group related projects
4. **Create Projects**: Either standalone or under a program
5. **Add Tasks**: Break down projects into tasks
6. **Manage Contacts**: Add team members
7. **Assign People**: Assign contacts to work items
8. **Track Materials**: Add and track materials and costs
9. **Set Milestones**: Track important dates

## Database Schema

- **User**: Authentication and user management
- **Program**: Top-level container for projects
- **Project**: Can be standalone or part of a program
- **Task**: Subtasks within projects
- **Contact**: People/team members
- **Material**: Materials needed (linked to programs/projects/tasks)
- **Milestone**: Important dates (linked to programs/projects)

## Environment Variables

- `SECRET_KEY`: Flask secret key for sessions (required)
- `DATABASE_URL`: Database connection string (auto-set by Heroku)

## Future Enhancements

- File attachments for tasks and projects
- Gantt chart visualization
- Email notifications
- Commenting system
- Time tracking
- Reporting and analytics
- Export to PDF/Excel
- Mobile app

## License

MIT License

## Author

Your Name
