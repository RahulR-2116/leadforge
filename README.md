# LeadForge

LeadForge is an internal CRM and lead generation platform for a web development business. Phase 1 establishes the production-ready project foundation: a FastAPI backend, React dashboard frontend, database configuration for SQLite and PostgreSQL, local Docker services, linting, formatting, and environment-based configuration.

## Installation

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker Desktop, optional for PostgreSQL

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env
```

### Frontend

```powershell
cd frontend
npm install
```

## Running Locally

Start the backend in development mode:

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend:

```powershell
cd frontend
npm run dev
```

Open the dashboard at [http://localhost:5173](http://localhost:5173). The backend health endpoint is available at [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health).

To run PostgreSQL locally:

```powershell
docker compose up -d postgres
```

Then set `DATABASE_URL=postgresql+psycopg://leadforge:change-me@localhost:5432/leadforge` in `backend/.env`.

## Folder Structure

```text
leadforge/
  backend/        FastAPI API, settings, database access, models, tests
  frontend/       React, TypeScript, Vite, TailwindCSS, shadcn-compatible UI
  scraper/        Future scraping services and utilities
  database/       Database notes, migrations support, and local data docs
  docs/           Product and engineering documentation
  .github/        CI workflows
```

## Tooling

Backend:

```powershell
cd backend
ruff check .
ruff format --check .
pytest
```

Frontend:

```powershell
cd frontend
npm run lint
npm run format:check
npm run build
```

## Future Roadmap

- User authentication and role-based access
- Business lead capture and enrichment
- Message and follow-up workflow management
- Demo tracking
- Lead scraping pipelines with Playwright, Requests, and BeautifulSoup
- Statistics dashboards for lead quality, conversion, and outreach velocity
- Production deployment configuration
