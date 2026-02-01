# IRIS Digital Invoicing Backend

Backend API for submitting invoices to FBR/IRIS 2.0 Digital Invoicing platform.

## Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.12
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Migrations**: Alembic

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL (or Docker)

### Setup

1. Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Unix
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Edit `.env` with your settings (especially `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`)

5. Run the development server:
```bash
uvicorn app.main:app --reload
```

6. Open http://localhost:8000/docs for API documentation

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app entry point
│   ├── config.py        # Settings management
│   ├── database.py      # SQLAlchemy configuration
│   ├── models/          # ORM models
│   ├── schemas/         # Pydantic schemas
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   └── utils/           # Shared utilities
├── tests/               # Test suite
├── alembic/             # Database migrations
└── pyproject.toml       # Project configuration
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Linting & Formatting

```bash
# Lint
ruff check .

# Format
black .
```
