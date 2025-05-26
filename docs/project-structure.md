This project follows a modular structure for a FastAPI backend application with Docker, database migrations, and testing support. Below is an overview of the main directories and files:

---

## Root Directory

- **.env**  
  Environment variables for local development and Docker.

- **alembic.ini**  
  Alembic configuration for database migrations.

- **docker-compose.yml**  
  Docker Compose configuration for services (app, db, test).

- **Dockerfile.backend**  
  Dockerfile for building the backend application image.

- **Dockerfile.test**  
  Dockerfile for the test runner service.

- **entrypoint.sh**  
  Entrypoint script for running migrations and starting the FastAPI app.

- **Makefile**  
  Common commands for development and deployment.

- **requirements.txt / requirements-with-versions.txt**  
  Python dependencies.

- **README.md**  
  Main documentation and installation guide.

---

## app/

Main application code.

- **main.py**  
  FastAPI application factory and setup.

- **initializer.py**  
  Database initialization logic.

- **crud.py**  
  CRUD operations for users and groups.

- **models.py**  
  SQLModel ORM models and Pydantic schemas.

- **utils.py**  
  Utility functions (permissions, roles, etc).

- **core/**  
  Core modules:
  - **config.py**: Settings and configuration.
  - **database.py**: Database engine and session management.
  - **security.py**: Password hashing, JWT, OTP.
  - **email.py**: Email sending utilities.
  - **verification.py**: (Commented) Email verification logic.

- **api/**  
  API routers and dependencies:
  - **main.py**: API router aggregator.
  - **routes/**: User and group endpoints.
  - **deps.py**: Dependency injection for DB/session/auth.

- **email-templates/**  
  MJML email templates for transactional emails.

- **tests/**  
  Unit and integration tests:
  - **api/routes/**: API endpoint tests.
  - **crud/**: CRUD logic tests.
  - **utils/**: Test utilities and fixtures.
  - **conftest.py**: Pytest fixtures.

---

## alembic/

Database migration scripts.

- **env.py**  
  Alembic environment setup.

- **versions/**  
  Auto-generated migration scripts.

- **script.py.mako**  
  Alembic migration template.

---

## scripts/

- **test.sh**  
  Bash script to run tests in Docker.

---

## docs/

- **custom-exception-logging.md**  
  Guide for implementing custom exception logging.

---

## Other Files

- **mail.py**  
  Example usage of logging.

- **.gitignore**  
  Files and directories to ignore in git.

---

## Summary

- **app/**: Main backend code (API, models, logic, utilities).
- **alembic/**: Database migrations.
- **tests/**: Automated tests.
- **docker-compose.yml & Dockerfiles**: Containerization.
- **scripts/**: Helper scripts.
- **docs/**: Project documentation.

This structure supports scalable development, testing, and deployment for a modern FastAPI application.