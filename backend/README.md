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
- `apps/telegram_bot/` - Telegram bot worker, polling loop, and command handlers
- `apps/neural_engine/` - LLM generation, safety routing, ASQ flow, safety audit logs
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
7. If Ollama is running locally and you want chat responses from the model:
   `python manage.py activate_ollama_model`
8. In Django Admin, open `Platform ops -> Neural model versions -> Ollama Control`
   to pull a model from Ollama and activate its DB version without terminal commands.
9. Configure Telegram bot profile and commands:
   `python manage.py configure_telegram_bot`
10. Run Telegram bot with long polling:
   `python manage.py run_telegram_bot`

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
- For local LLM mode, set `LLM_PROVIDER=ollama` and keep Ollama listening on `http://127.0.0.1:11434`
- The admin page provides a single-click path to pull and activate the configured Ollama model.
- Telegram bot uses the same chat pipeline as the website and links users through `channel_account`.
- If your IDE highlights `apps.*` or `config.*` as unresolved, open the project with `.venv` as the interpreter and keep the repository root as the workspace. The root compatibility packages `apps/`, `config/`, and `pyrightconfig.json` are added to help static analysis from the repo root.
