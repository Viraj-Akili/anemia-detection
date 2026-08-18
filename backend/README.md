# PRAHARI Backend

FastAPI + PostgreSQL backend running in Docker.

## Architecture

```
Docker Compose
├── api  → FastAPI (Python 3.12)
└── db   → PostgreSQL 18
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

That's it. No local Python, PostgreSQL, or pip required.

## Quick Start

```bash
# Start everything
docker compose up --build

# Stop everything
docker compose down

# Stop and remove database data
docker compose down -v
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `http://localhost:8000/health` | Application health check |
| GET | `http://localhost:8000/health/db` | Database connectivity check (SELECT 1) |
| GET | `http://localhost:8000/docs` | Swagger UI (interactive API docs) |

## Configuration

Environment variables are configured in `docker-compose.yml`. For local overrides, create a `backend/.env` file:

```bash
cp .env.example .env
# Edit .env with your values
```

See `.env.example` for available variables.

## Project Structure

```
backend/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── app/
    ├── __init__.py
    ├── main.py          # FastAPI app + health endpoints
    ├── config.py         # Pydantic settings (reads env vars)
    └── database.py       # SQLAlchemy engine, session, Base class
```
