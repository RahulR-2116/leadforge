# LeadForge

LeadForge is an internal CRM and lead generation platform for a web development business. The app now includes a production-oriented FastAPI backend, React dashboard frontend, database configuration for SQLite and PostgreSQL, local Docker services, linting, formatting, environment-based configuration, and a Lead Management CRM for business prospects.

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
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend:

```powershell
cd frontend
npm run dev
```

Open the dashboard at [http://localhost:5173](http://localhost:5173). The backend health endpoint is available at [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health).

The Lead Management page is available from the in-app Leads navigation. It supports lead creation, search, pagination, filtering by category/city/state/website/status, status badges, bulk delete, bulk status changes, notes, demo history, message history, follow-ups, and CSV/Excel export.

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
alembic upgrade head
ruff check .
ruff format --check .
pytest
```

Useful CRM API endpoints:

```text
GET    /api/v1/businesses
POST   /api/v1/businesses
GET    /api/v1/businesses/{business_id}
PATCH  /api/v1/businesses/{business_id}
DELETE /api/v1/businesses/{business_id}
PATCH  /api/v1/businesses/{business_id}/status
POST   /api/v1/businesses/{business_id}/follow-ups
POST   /api/v1/businesses/{business_id}/demos
POST   /api/v1/businesses/{business_id}/messages
GET    /api/v1/businesses/export?format=csv
GET    /api/v1/businesses/export?format=xlsx
GET    /api/v1/businesses/stats
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
- Lead import and scraper integration
- Message template generation
- Follow-up automation
- Lead scraping pipelines with Playwright, Requests, and BeautifulSoup
- Statistics dashboards for lead quality, conversion, and outreach velocity
- Production deployment configuration
