# Testing Guide

## Scope

This repository contains three runtime surfaces:

- Backend API (FastAPI + Socket.IO) under `backend/`
- Frontend UI (React + Vite) at the repo root
- Agent (Python) under `agent/`

The automated suite covers:

- Unit tests (pure functions, request/response shaping, UI components)
- Integration tests (API endpoints + DB interactions with an isolated SQLite DB)
- End-to-end tests (browser login workflow against real servers)
- Performance tests (marked, opt-in)
- Negative/edge-case tests (auth failures, duplicates, missing records, 401 handling)

## Reports

All automated runs write artifacts to `reports/`:

- `reports/pytest-junit.xml` (Python JUnit)
- `reports/coverage.xml` (Python coverage Cobertura XML)
- `reports/vitest-junit.xml` (Frontend unit JUnit)
- `reports/vitest-coverage/` (Frontend coverage)
- `reports/playwright-junit.xml` and `reports/playwright-html/` (E2E)

## Quick Start (Local)

### Python (Backend + Agent)

Install dependencies:

```bash
python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
python -m pip install -r agent/requirements.txt -r agent/requirements-dev.txt
```

Run unit + integration tests:

```bash
python -m pytest
```

Run performance tests (opt-in):

```bash
SENTINEL_P95_MS=500 python -m pytest -m performance
```

### Frontend Unit Tests

Install dependencies:

```bash
npm ci
```

Run unit tests (includes coverage + JUnit):

```bash
npm run test:unit
```

### End-to-End (Browser) Tests

Install browsers once:

```bash
npx playwright install
```

Run E2E:

```bash
npm run test:e2e
```

Playwright starts:

- Backend on `http://127.0.0.1:8000` (from `backend/`, with background tasks disabled)
- Frontend dev server on `http://127.0.0.1:3000`

## Data Setup / Teardown

### Backend integration DB

Pytest uses an isolated SQLite database created under a temporary directory. Each test recreates the schema to ensure isolation and repeatability.

### E2E DB

Playwright starts the backend with:

- `DATABASE_URL=sqlite:///./sentinel_e2e.db` (file created inside `backend/`)
- `SENTINEL_DISABLE_BACKGROUND_TASKS=1` to prevent screenshot capture and model training

If you want a clean E2E run, delete `backend/sentinel_e2e.db` before running.

## Manual Test Procedures (When Automation Isn’t Feasible)

### Screenshot capture loop (macOS)

1. Start backend normally (without `SENTINEL_DISABLE_BACKGROUND_TASKS=1`).
2. Enable screenshots in Settings (`captureScreenshots=true`).
3. Confirm a screenshot appears under `backend/screenshots/` and a `SCREENSHOT` log is created.

Pass criteria:

- A screenshot file is created.
- A new log entry is stored and broadcast to the UI (live monitor updates).

### Keylogger agent (OS permission dependent)

1. Run the agent on a workstation with the required permissions granted to the terminal/app.
2. Confirm key events are collected and periodically sent to the backend.

Pass criteria:

- Agent successfully authenticates.
- Backend receives `KEYLOG` events and key heatmap updates are visible in the UI.

## CI/CD

The scripts are designed to run headlessly:

- Python tests: `python -m pytest`
- Frontend unit tests: `npm run test:unit`
- E2E tests: `npm run test:e2e` (Playwright runs headless by default in CI)

