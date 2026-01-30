# Studyzee - Study Management & Collaboration Platform

A comprehensive web application for students to manage courses, track assignments, generate study materials, and connect with peers.

## Features

- **Course Management**: Upload course syllabi and automatically extract schedule, instructor info, and assignments
- **Task Tracking**: Create custom tasks and track assignments with due dates
- **AI-Powered Flashcards**: Generate study flashcards from notes using OpenAI
- **Social Network**: Find study partners, send friend requests, and manage connections
- **Study Groups**: Create and join study groups with real-time chat
- **Real-time Chat**: Private messaging and group chat with WebSocket support

## Tech Stack

- **Backend**: Flask, Flask-Login, Flask-Bcrypt, Flask-SocketIO
- **Database**: Supabase (PostgreSQL)
- **AI Integration**: OpenAI API (GPT-4)
- **Frontend**: Jinja2 templates, HTML/CSS/JavaScript
- **Real-time**: WebSockets for live messaging
- **File Storage**: Supabase Storage

## Project Structure

```
studyzee/
├── app.py                 # Application factory
├── config.py             # Configuration management
├── models/               # Data models
│   ├── user.py
│   ├── course.py
│   └── social.py
├── routes/               # API endpoints
│   ├── auth.py          # Authentication
│   ├── courses.py       # Course management
│   ├── tasks.py         # Task management
│   ├── flashcards.py    # Flashcard operations
│   ├── social.py        # Friends and profiles
│   └── chat.py          # Messaging
├── services/             # Business logic
│   ├── pdf_processor.py # PDF parsing
│   ├── ai_assistant.py  # AI operations
│   └── user_service.py  # User operations
├── utils/                # Helper utilities
│   ├── db.py            # Database client wrapper
│   ├── validators.py    # Input validation
│   └── constants.py     # Static data
├── static/               # CSS, JS, images
├── templates/            # HTML templates
└── migrations/           # Database schema
    └── schema.sql
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- pip or conda
- Supabase account (create new project)
- OpenAI API key

### 2. Clone Repository

```bash
git clone <repository-url>
cd studyzee
```

### 3. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OPENAI_API_KEY=sk-...
```

### 6. Set Up Supabase

1. Create a new Supabase project
2. Go to SQL Editor in Supabase dashboard
3. Copy content from `migrations/schema.sql`
4. Execute the SQL to create tables
5. Create storage buckets:
   - `course` (for PDFs)
   - `pictures` (for profile pics)

### 7. Run Application

```bash
python -m flask run
```

Visit `http://localhost:5000` in your browser.

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /signup` - User registration
- `GET /logout` - User logout

### Courses
- `GET /courses` - List user's courses
- `POST /add_course` - Add new course
- `POST /upload_course` - Upload syllabus

### Tasks
- `GET /tasks` - Get pending tasks
- `POST /tasks` - Create task
- `GET /complete_task/<id>` - Mark complete

### Flashcards
- `POST /upload-notes` - Generate flashcards
- `GET /flashcard_sets` - List sets

### Social
- `GET /suggested_friends` - Get suggestions
- `POST /send_friend_request` - Send request
- `GET /friends` - List friends

## Code Quality Standards

### Required
- ✅ Docstrings (Google style)
- ✅ Type hints
- ✅ Proper error handling
- ✅ Logging

### Forbidden
- ❌ `print()` statements
- ❌ Bare `except:` clauses
- ❌ Global mutable state
- ❌ Hardcoded secrets

## Database Schema

Key tables:
- `users` - User accounts
- `courses` - Course catalog
- `tasks` - Custom tasks
- `assigned_work` - Course assignments
- `friends` - Relationships
- `chat_messages` - Messages

See `migrations/schema.sql` for complete schema.

## Git Workflow

Small, atomic commits with descriptive messages:

```bash
git commit -m "add feature: description"
```

## Deployment

```bash
FLASK_ENV=production gunicorn -w 4 app:app
```

## Support

Open an issue on GitHub for problems.
