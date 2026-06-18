# FinTrack

FinTrack is a full-stack banking operations demo built with Django REST Framework, PostgreSQL, and React. It models role-based banking workflows for admins, bank employees, and members.

## Highlights

- JWT authentication with 30-day demo sessions
- Role-based dashboards for admin, employee, and member users
- Deposits, withdrawals, transfers, beneficiaries, loans, and notifications
- Admin approval flow for high-value transactions, employee deposits, loans, and registrations
- PostgreSQL as the default stable database
- Seed command for predictable demo credentials
- Backend tests for the main financial workflows

## Tech Stack

- Backend: Django 4.2, Django REST Framework
- Database: PostgreSQL, optional SQLite fallback for quick local testing
- Frontend: React 18, Vite, Ant Design
- Auth: Custom JWT bearer tokens

## Demo Accounts

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin123` |
| Employee | `employee` | `employee123` |
| Member | `member` | `member123` |

The login page also shows these demo accounts for client review.

## Project Structure

```text
FinTrack/
  e_fintrack_backend/    Django REST API
  e_fintrack_frontend/   React client
```

## Backend Setup

Create a PostgreSQL database named `fintrack`, then configure the backend environment:

```powershell
cd e_fintrack_backend
copy .env.example .env
```

Update `.env` with your real database password and Django secret. For local development, this project currently uses:

```text
POSTGRES_DB=fintrack
POSTGRES_USER=postgres
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Install dependencies, migrate, and seed demo data:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py seed_demo
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Run backend checks:

```powershell
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test banking
```

## Frontend Setup

```powershell
cd e_fintrack_frontend
npm install
npm run dev -- --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

If your backend runs somewhere else, create `e_fintrack_frontend/.env`:

```text
VITE_API_URL=http://127.0.0.1:8000/api
```

## Main API Routes

- `POST /api/auth/login/`
- `POST /api/auth/register/`
- `GET /api/me/`
- `GET /api/accounts/`
- `GET /api/transactions/`
- `POST /api/transactions/deposit/`
- `POST /api/transactions/withdraw/`
- `POST /api/transactions/transfer/`
- `GET /api/loans/`
- `POST /api/loans/issue/`
- `GET /api/admin/transactions/pending/`
- `POST /api/admin/transactions/<id>/approve/`
- `POST /api/admin/accounts/<id>/freeze/`

## Configuration Notes

- Backend settings load `e_fintrack_backend/.env` automatically.
- Use `.env.example` as the template for new machines or deployments.
- Keep `.env` private; it is intentionally ignored by git.
- Set `DJANGO_DEBUG=False` and a strong `DJANGO_SECRET_KEY` before deployment.
- Keep PostgreSQL running before starting the backend.

## Optional SQLite Fallback

For quick experiments only:

```text
FINTRACK_DB_ENGINE=sqlite
FINTRACK_SQLITE_PATH=fintrack.sqlite3
```

PostgreSQL is recommended for normal development and client review.
