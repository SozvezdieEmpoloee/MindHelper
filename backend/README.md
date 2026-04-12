# MindHelper Backend

## Stack

- Django
- Django REST Framework
- PostgreSQL
- Django Admin
- pytest + pytest-django

## Project layout

- `config/` - Django settings and root URLs
- `apps/accounts/` - users, roles, linked channels
- `apps/chat/` - single user chat, messages, crisis events
- `apps/assessments/` - templates, sessions, answers
- `apps/directory/` - specialists, locations, appointments, emergency resources
- `apps/platform_ops/` - model versions, moderation, managed site content
- `tests/` - service and selector tests

## Setup plan

1. Install dependencies from `pyproject.toml`
2. Copy `.env.example` to `.env`
3. Apply database upgrade script if the database already exists:
   `docs/db/sql/03_django_admin_upgrade.sql`
4. Create Django migrations and run:
   `python manage.py makemigrations`
   `python manage.py migrate --fake-initial`
5. Create or update admin user data in `user_account`
6. Start server:
   `python manage.py runserver`

## API direction

- `/api/v1/accounts/`
- `/api/v1/chat/`
- `/api/v1/assessments/`
- `/api/v1/directory/`
- `/api/v1/platform/`
- `/admin/`

## Notes

- The backend is aligned to the current PostgreSQL schema in `docs/db/sql/01_schema.sql`
- The frontend lives in `../frontend`
- The current chat design assumes exactly one chat per user
