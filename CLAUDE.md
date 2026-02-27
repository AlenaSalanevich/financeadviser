# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Package manager**: Poetry (use `poetry run <cmd>` or activate the venv at `.venv/`)

```bash
# Run development server (hot reload on :8000)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests with coverage
poetry run pytest

# Run a single test file
poetry run pytest tests/test_api/test_health.py -v

# Format code
poetry run black app/ tests/
poetry run isort app/ tests/

# Lint / type check
poetry run flake8 app/
poetry run mypy app/
poetry run pylint app/
poetry run bandit -r app/

# Build PDF vectorstore (run from project root, processes data/*.pdf)
poetry run python data/loader.py

# Database migrations
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "description"
```

## Architecture

**FastAPI + LangChain financial advising app.** Python 3.12, async throughout.

### App layout (`app/`)

```
app/
├── main.py          # FastAPI app, CORS, lifespan events — only implemented file so far
├── config.py        # Settings via pydantic-settings (stub)
├── dependencies.py  # FastAPI dependency injection (stub)
├── api/v1/
│   ├── router.py    # Aggregates all endpoint routers (stub)
│   └── endpoints/   # auth, users, agents, health (stubs)
├── core/            # exceptions, logging, security helpers (stubs)
├── db/              # SQLAlchemy base, async session, models (stubs)
├── schemas/         # Pydantic request/response models (stubs)
├── services/        # Business logic layer (stubs)
├── agents/          # LangChain/LangGraph agent definitions (stubs)
└── tools/           # LangChain tool wrappers (stubs)
```

Most modules are scaffolded but empty — `app/main.py` is the only file with real implementation.

### Data / vector layer (`data/`)

`data/loader.py` is a standalone script (not imported by the app yet) that:
1. Scans `data/` for all `*.pdf` files and loads them page-by-page via `PyPDFLoader`
2. Creates HuggingFace embeddings (`sentence-transformers` default model)
3. Builds a FAISS vectorstore and persists it to `data/movements/`

The saved vectorstore in `data/movements/` is the intended source for the RAG pipeline that agents will use.

### Intended infrastructure

- **PostgreSQL** — primary DB (SQLAlchemy async via `asyncpg`; Alembic migrations)
- **Redis** — caching and pub/sub
- **Celery** — background task queue (workers not yet implemented)
- **Prometheus + Sentry** — observability (dependencies installed, not wired up)

### Auth design

JWT-based (`python-jose`), password hashing with `passlib[bcrypt]`. Stubs live in `app/core/security.py` and `app/api/v1/endpoints/auth.py`.

## Environment

Copy `env.example` to `.env`. Required variables:

```
OPEN_API_KEY=      # OpenAI API key
HF_TOKEN=          # HuggingFace token (for sentence-transformers)
```

Pytest sets its own env automatically (see `[tool.pytest.ini_options].env` in `pyproject.toml`), including a SQLite test DB — no real Postgres needed for tests.

## Code style

- Line length: 88 (Black)
- MyPy strict mode — all new code needs type annotations
- isort profile: `black`
- Pylint suppresses: `missing-docstring`, `invalid-name`, `too-few-public-methods`
