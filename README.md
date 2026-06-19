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
