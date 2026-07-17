# Database

LeadForge supports SQLite for local development and PostgreSQL for production-style environments.

- Local default: `sqlite:///./leadforge.db`
- PostgreSQL example: `postgresql+psycopg://leadforge:change-me@localhost:5432/leadforge`

Alembic migration files live in `backend/alembic`.
