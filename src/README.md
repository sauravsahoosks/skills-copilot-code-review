# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements
- Manage announcements (add, edit, delete) as a signed-in teacher/admin

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/announcements`                                                  | Get active announcements for public display                         |
| GET    | `/announcements/manage?teacher_username={username}`               | List all announcements for the management dialog (requires sign-in) |
| POST   | `/announcements?teacher_username={username}`                      | Create announcement (requires sign-in)                             |
| PUT    | `/announcements/{announcement_id}?teacher_username={username}`    | Update announcement (requires sign-in)                             |
| DELETE | `/announcements/{announcement_id}?teacher_username={username}`    | Delete announcement (requires sign-in)                             |
| POST   | `/auth/login?username={username}&password={password}`             | Sign in teacher/admin account                                       |
| GET    | `/auth/check-session?username={username}`                         | Validate signed-in account                                          |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Data is stored in MongoDB collections and initialized with example records when the collections are empty.
