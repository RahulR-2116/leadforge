# Scraper

Lead collection engines now live inside the backend application package at `backend/app/scraper` so they can share settings, logging, job state, and database imports with FastAPI.

Current engines:

- Google Maps: Playwright-based background scraping with direct CRM import.
- Justdial: package scaffolded for a future implementation.

Every scrape writes a log file under `backend/logs/scrapes`.
