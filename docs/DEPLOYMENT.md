# Deployment guide

1. Create a production `.env` from `.env.example`; set a unique 32+ character JWT secret, MySQL credentials, `FRONTEND_ORIGIN`, SMTP credentials, and optional OpenWeather/OpenAI credentials.
2. Never use the SQLite development default in production. Set `DATABASE_URL=mysql+pymysql://...` to a managed MySQL 8 instance with encrypted backups.
3. Run `docker compose up --build -d`. The API is available on port 8000 and the static frontend on 5173 by default.
4. Put a TLS-terminating reverse proxy in front of the containers. Limit API CORS to the deployed frontend origin.
5. Run `python -m scripts.seed_admin` in the API container once with `ADMIN_EMAIL` and `ADMIN_PASSWORD` supplied as environment variables.
6. Persist and back up the Docker MySQL volume plus the API `uploads/` and `models/` directories. Uploaded images, reports, datasets, and trained model artifacts live in those directories.

Health monitoring can call `GET /health`; the endpoint validates an active database connection.
