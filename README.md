# Recipe Manager API

A production-grade REST API for managing personal recipe collections — CRUD operations, rich filtering (vegetarian, servings, ingredient include/exclude, instruction text search), and JWT-based per-user ownership.

Full architecture rationale and trade-off discussion: [`docs/architecture.md`](docs/architecture.md).
Decision records for key choices: [`docs/adr/`](docs/adr/).

## Tech stack

- **FastAPI** + **Uvicorn** — async REST framework
- **SQLAlchemy 2.0 (async)** + **asyncpg** + **Alembic** — ORM, driver, migrations
- **PostgreSQL 16** — primary datastore (GIN/tsvector full-text search on instructions)
- **Redis** — refresh-token blacklist (logout/revocation)
- **Pydantic v2** — request/response validation
- **structlog** — structured JSON logging, request-correlated, with Prometheus-compatible metrics exposed at `/health/metrics`
- **slowapi** — rate limiting on auth endpoints
- **pytest** + **pytest-asyncio** + **httpx** — unit + integration tests

## Architecture summary

Layered design: `API Router → Service → Repository → Database`, with one `AsyncSession` per request (unit-of-work pattern — commits in the dependency layer, never inside services). See [`docs/architecture.md`](docs/architecture.md) for the full container/sequence diagrams and trade-off tables.

## Running locally (no Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

cp .env.example .env   # edit JWT_SECRET_KEY for anything beyond local testing

# Start Postgres + Redis only
docker compose up -d db redis

alembic upgrade head
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs` (Swagger) and `/redoc`.

## Running with Docker (full stack)

```bash
cp .env.example .env
docker compose up --build
```

This brings up `db`, `redis`, a one-shot `migrate` service (`alembic upgrade head`), and the `api` service. The API is reachable at `http://localhost:8000`.

> **Current scope note**: this compose file runs a **single** API instance. The architecture plan describes a multi-replica topology behind `nginx` (see §13–14 of `docs/architecture.md`). Prometheus/Grafana dashboards are a planned future enhancement — the app already exposes raw metrics at `/health/metrics`, ready to be scraped once that stack is added.

## Example walkthrough

```bash
# Register
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"chef@example.com","password":"password123"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"chef@example.com","password":"password123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create a recipe
curl -s -X POST http://localhost:8000/api/v1/recipes \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Potato Stew","instructions":"Roast potatoes in the oven","servings":4,"is_vegetarian":true,"ingredients":[{"name":"potatoes"}]}'

# Filter: all vegetarian recipes
curl -s "http://localhost:8000/api/v1/recipes?is_vegetarian=true" -H "Authorization: Bearer $TOKEN"

# Filter: servings=4 AND includes "potatoes"
curl -s "http://localhost:8000/api/v1/recipes?servings=4&include_ingredients=potatoes" -H "Authorization: Bearer $TOKEN"

# Filter: excludes "salmon" AND instructions mention "oven"
curl -s "http://localhost:8000/api/v1/recipes?exclude_ingredients=salmon&instructions_contains=oven" -H "Authorization: Bearer $TOKEN"
```

## Running tests

```bash
pytest --cov=app --cov-report=term-missing
```

Runs both `tests/unit/` (mocked repositories) and `tests/integration/` (real Postgres/Redis) in one pass. Coverage must stay ≥80% (enforced via `pyproject.toml`).

## CI/CD

`.github/workflows/abn-amro-dev-ci.yml` runs on every push/PR: ruff lint + format check, mypy, `pip-audit`, migrations against a live Postgres service container, the full test suite, and a Docker build — see the workflow file for the exact steps.

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `ENVIRONMENT` | `development` | |
| `DEBUG` | `false` | |
| `DATABASE_URL` | — | required, `postgresql+asyncpg://...` |
| `REDIS_URL` | `redis://localhost:6379` | |
| `JWT_SECRET_KEY` | — | required, generate via `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | |
| `CORS_ORIGINS` | `["http://localhost:8080"]` | JSON array string |
| `RATE_LIMIT_PER_MINUTE` | `60` | |
| `LOG_LEVEL` | `INFO` | |

## Project structure

```
app/
├── main.py                  # FastAPI app, middleware, exception handlers
├── core/                    # config, security, logging, middleware, exceptions, rate limiter
├── api/v1/                  # routers (auth, recipes, health) + dependencies
├── models/                  # SQLAlchemy ORM models
├── schemas/                 # Pydantic request/response schemas
├── repositories/            # data access layer
├── services/                # business logic layer
└── db/                      # session/engine, Redis client
alembic/                     # migrations
tests/{unit,integration}/    # pytest suites
docs/{architecture.md,adr/}  # design docs and decision records
```

## Known limitations / not implemented

- **Multi-instance topology** (nginx load balancing across 2 API replicas) was designed in `docs/architecture.md` §13–14 but not built — current Docker setup runs a single `api` instance.
- **Monitoring dashboards** (Prometheus scraping + Grafana) are a planned future enhancement for production deployments — the app already exposes Prometheus-format metrics at `/health/metrics`; only the scraper/dashboard stack itself is not yet wired up.
- **CORS middleware and security-headers middleware** (HSTS, X-Frame-Options, etc.) were planned but not added to `app/main.py` — rate limiting on auth endpoints is in place, but the other two hardening pieces from the security section are outstanding.
- Integration tests run against the same Postgres database as local dev rather than an isolated test database — acceptable for this scope since CI uses fresh ephemeral service containers per run.
