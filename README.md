# Examination Slot Booking and Evaluation System

A Flask web app for booking and evaluating oral/practical exams (Viva, Practical, Project).

- **Admin** – manages courses, examinations, examiners, students and approves new users.
- **Examiner** – creates time slots and evaluates students using rubrics.
- **Student** – browses open examinations, books or cancels slots, and views published results.

## Tech Stack

Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Security, Flask-Login, Flask-WTF, Flask-CORS, python-dotenv, Jinja2, SQLite.

## Project Structure

```
app.py          Flask app, extensions and the "seed" command
core/           config, database, models, seed
apps/           blueprints: auth, admin, examiner, student
templates/      Jinja2 HTML templates
db_directory/   SQLite database files
api.yaml        Endpoint definitions
```

## Setup

1. Create a virtual environment and install the packages:

   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install flask flask-sqlalchemy flask-migrate flask-security-too flask-login flask-wtf flask-cors python-dotenv email-validator argon2-cffi
   ```

2. Create a `.env` file in the project root:

   ```
   SECRET_KEY=change-me
   SECURITY_PASSWORD_SALT=change-me-too
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=admin12345
   FIRST_STUDENT_EMAIL=student@example.com
   FIRST_STUDENT_PASSWORD=student12345
   FIRST_EXAMINER_EMAIL=examiner@example.com
   FIRST_EXAMINER_PASSWORD=examiner12345
   ```

3. Create the database and seed the default roles and users:

   ```bash
   mkdir -p db_directory
   flask --app app db upgrade
   flask --app app seed
   ```

   If there is no `migrations/` folder yet, run `flask --app app db init` and `flask --app app db migrate` first.

4. Start the app:

   ```bash
   python app.py
   ```

   Open http://127.0.0.1:5000/auth/login

## How It Works

1. A user registers and waits for admin approval.
2. The admin approves the user and sets up courses, examinations and timelines.
3. Examiners create slots while slot creation is open.
4. Students book a slot while booking is open.
5. Examiners enter rubric scores and remarks; the admin publishes the results.