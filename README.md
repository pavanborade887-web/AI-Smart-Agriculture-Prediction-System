# AI Smart Agriculture Prediction System

An AI-powered farm intelligence platform. This initial module delivers secure farmer authentication and the shared application foundation; the crop, soil, weather, disease, yield, market, reports, assistant, and admin modules follow as separate milestones.

## Module 1: project structure and backend setup

- React/Vite responsive sign-in, registration, recovery, and protected dashboard routes.
- FastAPI REST API with OpenAPI docs at `/docs`.
- Argon2 password hashing, signed short-lived access tokens, refresh-token rotation and revocation.
- Farmer/admin roles plus an API dependency for administrator-only routes.
- MySQL 8 schema and Docker Compose setup; SQLite works automatically for isolated local API development.
- Clean backend layers: API routers, core configuration/security/error handling, persistence models, domain services, repositories, ML package, scripts, and tests.
- Database entities for users, sessions, resets, predictions, weather logs, disease detections, reports, notifications, datasets, and model versions.

## Run locally

1. Copy `.env.example` to `.env` and set a unique `JWT_SECRET_KEY`.
2. Start MySQL with `docker compose up mysql -d`, or use the local SQLite default while developing the API.
3. In `backend`, create a virtual environment and install `pip install -r requirements.txt`; run `uvicorn app.main:app --reload`.
4. In `frontend`, copy `.env.example` to `.env`, run `npm install`, then `npm run dev`.

The browser app is available at `http://localhost:5173`; API documentation is at `http://localhost:8000/docs`.

To provision an admin locally, set `ADMIN_EMAIL` and `ADMIN_PASSWORD`, then run `python -m scripts.seed_admin` from `backend`.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Create a farmer account |
| POST | `/api/v1/auth/login` | Issue access and refresh tokens |
| POST | `/api/v1/auth/refresh` | Rotate a refresh token |
| POST | `/api/v1/auth/logout` | Revoke a refresh token |
| GET | `/api/v1/auth/me` | Return the authenticated user |
| POST | `/api/v1/auth/forgot-password` | Request a password reset |
| POST | `/api/v1/auth/reset-password` | Set a password with a reset token |

The reset endpoint returns a token only in development. Configure an SMTP provider before production and connect it to the reset-token delivery event.

## Module 2: authentication

The complete account flow includes registration, sign-in, refresh-token rotation, sign-out, account recovery, and new-password confirmation. Passwords are hashed with Argon2; access tokens are short-lived and refresh sessions are revocable. Every new account is a farmer; administrator privileges are assigned through the admin provisioning script.

For production password recovery, configure all SMTP values in `.env`. Reset messages are delivered in the background and links expire after 30 minutes. In development, the reset API response intentionally exposes the temporary token so the flow can be tested without an email provider.

## Module 3: dashboard

The protected dashboard aggregates each farmer's persisted predictions, weather records, disease detections, and notifications. `GET /api/v1/dashboard/summary` is the single authenticated data source for the dashboard cards, seven-day activity graph, alert feed, and recommendation history. It intentionally shows the actual empty state until later modules create data—rather than inventing farm insights.

## Repository map

- `backend/app`: API, core platform services, persistence models, service/repository and ML extension layers.
- `backend/scripts/seed_admin.py`: idempotent admin-account provisioning.
- `backend/tests/test_health.py`: API/database health check.
- `frontend/src`: TypeScript client, API adapter, auth state, routes, and premium responsive styles.
- `database/schema.sql`: MySQL schema for this milestone.
- `docker-compose.yml`: MySQL and API services for container deployment.

## Modules 4–15

Crop, fertilizer, weather, disease, yield, soil, irrigation, and market tools are available through protected frontend routes and their matching REST endpoints. The inference engines produce explainable outputs and persist them as prediction history; administrators can upload a CSV, validate/deduplicate it, and train a versioned Random Forest model artifact. Disease image analysis validates the uploaded file and uses HSV-area analysis to identify visible stress patterns with conservative treatment guidance.

Reports export persisted prediction history as PDF, XLSX, or CSV. The chat assistant uses OpenAI when `OPENAI_API_KEY` is configured and a domain-specific offline advisor otherwise. The admin route exposes user and platform analytics, plus CSV dataset upload and model training.

See [API documentation](docs/API.md) and the [deployment guide](docs/DEPLOYMENT.md) for endpoint and production configuration details.
