# Installation guide

## Prerequisites

- Python 3.12
- Node.js 22 with npm
- MySQL 8 (or Docker Desktop)

## Local development

1. Copy `.env.example` to `.env` and set `DATABASE_URL` plus a strong `JWT_SECRET_KEY`.
2. Create the database using `database/schema.sql`, or start it with `docker compose up mysql -d`.
3. In `backend`, create a virtual environment, activate it, then run `pip install -r requirements.txt` and `uvicorn app.main:app --reload`.
4. In `frontend`, copy `.env.example` to `.env`, run `npm install`, then `npm run dev`.
5. Open `http://localhost:5173`; API docs are available at `http://localhost:8000/docs`.

Use `pytest` from `backend` for the supplied service and health tests after the Python environment is installed.
