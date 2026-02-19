# Sentinel Monitoring System - Onboarding Guide

This guide is for developers and analysts who need to run, validate, and debug the project quickly.

## 1. What This Project Is

Sentinel is a cyber monitoring platform with:

- FastAPI backend (`backend/`) for auth, logs, SOAR automation, traffic analysis, and system telemetry
- React + Vite frontend (`/`) for dashboarding and control
- Python endpoint agent (`agent/`) for host monitoring and encrypted log ingestion
- Socket.IO for live updates (`new_log`, `new_traffic`, `prediction_update`, `key_heatmap_update`)

## 2. Architecture at a Glance

- Frontend (default: `http://localhost:3000`) calls backend REST APIs at `http://localhost:8000`
- Frontend and backend both connect to Socket.IO on backend (`/socket.io`)
- Backend stores data in SQLite by default (`sentinel.db`) unless `DATABASE_URL` is set
- Celery + Redis are optional for async jobs; backend gracefully falls back to in-process execution if Redis is down
- Ollama is optional but needed for LLM-powered `/chat` and AI-enhanced analysis

## 3. Prerequisites

- Node.js 18+
- Python 3.9+ recommended
- `npm` and `pip`
- Docker + Docker Compose (for Redis/Postgres/worker stack)
- Ollama (`qwen3:8b` model by default)

## 4. Quick Start (Local, Recommended)

Run from repo root: `Monitoring_system`.

### 4.1 Backend (secure dev launcher)

```bash
backend/run_secure_dev.sh
```

What this script does:

- Uses `./.venv/bin/python` if available
- Enforces stricter security defaults
- Starts Uvicorn with reload on `0.0.0.0:8000`

Secure launcher default credentials:

- Admin: `admin` / `AdminPass_123!`
- Analyst: `analyst` / `AnalystPass_123!`

### 4.2 Backend (manual alternative)

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 main.py
```

Manual mode default seeded credentials (if env vars are not set):

- Admin: `admin` / `admin`
- Analyst: `analyst` / `password`

### 4.3 Frontend

From repo root:

```bash
npm install
npm run dev
```

Expected URL: `http://localhost:3000` (Vite config default).

### 4.4 First Login

Use `admin` (ID) or `Admin User` (name) as username, plus matching password.

`/token` accepts both user ID and user name.

If login fails after switching startup modes, you may be using an old seeded DB. Seed users are only created when the DB is empty.

Reset local SQLite DB if needed:

```bash
rm -f backend/sentinel.db sentinel.db
```

## 5. Optional Services

### 5.1 Redis for Celery

If Redis is down, backend will still work, but async jobs run in-process.

Start only Redis quickly:

```bash
docker compose up -d redis
```

Disable Celery entirely in local dev:

```bash
export SENTINEL_DISABLE_CELERY=1
```

### 5.2 Ollama for LLM Features

Default backend LLM target:

- URL: `http://localhost:11434/api/generate`
- Model: `qwen3:8b`

Set if needed:

```bash
export OLLAMA_URL=http://localhost:11434/api/generate
export OLLAMA_MODEL=qwen3:8b
```

### 5.3 Agent

From repo root:

```bash
python3 -m pip install -r agent/requirements.txt
python3 agent/client.py
```

Useful agent env vars:

- `SERVER_URL` (default `http://localhost:8000`)
- `AGENT_INGEST_PATH` (default `/api/logs`)
- `AGENT_USER` / `AGENT_PASSWORD`
- `AGENT_API_KEY` (optional, must match backend if enabled)

## 6. Full Stack via Docker Compose

This brings up:

- Postgres (`db`)
- Redis (`redis`)
- FastAPI backend (`backend`)
- Celery worker (`worker`)

```bash
docker compose up --build
```

Notes:

- Frontend is not in compose; run it locally via `npm run dev`
- Backend in compose uses Postgres and Redis service DNS names

## 7. Core Functionalities and Expected Results

### 7.1 Auth + RBAC

Expected:

- `POST /token` returns access token
- `GET /users/me` returns authenticated user
- Sidebar menus vary by permissions (`READ_LOGS`, `EDIT_SETTINGS`, `MANAGE_USERS`)

### 7.2 Live Monitoring

Views:

- Dashboard (`Overview`)
- Live Monitor
- Keylogger

Expected:

- New logs appear in near real time via `new_log`
- `Recent Critical Events` table updates
- Key heatmap updates when KEYLOG logs include `activity_summary`

### 7.3 System Metrics

Expected:

- Live mode fetches `/api/system-metrics` every second
- History mode reads `/api/system-metrics/history`
- CPU/memory charts update continuously

### 7.4 Network Traffic + Analysis

Expected:

- `/traffic` logs populate graphs
- `/traffic/analyze` returns anomaly score/details
- Interception panel can list interfaces, start/stop capture, and show packet/byte/error stats

### 7.5 AI Analyst

Expected:

- `Run Deep Scan Analysis` calls `/analyze`
- Chat sends `/chat` messages and gets AI responses
- Action cards can trigger SOAR endpoints (`block-ip`, `isolate-host`, `reset-password`)

### 7.6 Playbooks (SOAR)

Expected:

- Create/toggle/delete playbooks in UI
- New logs trigger rule evaluation
- SOAR actions create additional logs (`SOAR_ACTION`)

### 7.7 Agent Lifecycle

From Settings page:

- `POST /agent/start` starts `agent/client.py` subprocess
- `GET /agent/status` reports running PID
- `POST /agent/stop` terminates process group

Expected:

- `agent_runtime.log` receives runtime output
- Agent-sent logs appear via `/api/logs`

## 8. Typical Healthy Startup Signals

Backend healthy indicators:

- Uvicorn starts on `http://0.0.0.0:8000`
- App startup completes
- `/health` returns status `ok` or `degraded` with component details

Frontend healthy indicators:

- Login page renders
- Successful login redirects to dashboard
- Socket.IO polling and/or websocket upgrade returns HTTP 200

## 9. Debugging Playbook

### 9.1 `http://localhost:3001 is not an accepted origin` or Socket.IO 400

Cause:

- Origin not in backend CORS/Socket.IO allowlist.

Fix:

- Use frontend port `3000` by default, or set `CORS_ALLOWED_ORIGINS` to include your exact origin.
- Current defaults already include:
- `localhost/127.0.0.1` on ports `5173`, `3000`, `3001`.

Quick check:

```bash
curl -i -X OPTIONS http://127.0.0.1:8000/users/me \
  -H 'Origin: http://localhost:3001' \
  -H 'Access-Control-Request-Method: GET'
```

### 9.2 `celery.backends.redis: Connection to Redis lost`

Cause:

- Redis backend unavailable at configured URL.

Fix options:

1. Start Redis (`docker compose up -d redis`)
2. Disable Celery (`export SENTINEL_DISABLE_CELERY=1`)
3. Keep running; backend now falls back to in-process task execution when Redis is unreachable

### 9.3 Many `OPTIONS` and frequent `GET /api/system-metrics` requests

Cause:

- Frontend polling is aggressive by design in dev:
- System metrics every 1s
- Interception status every ~2s
- Other periodic refreshes in multiple panels
- React StrictMode can double-invoke effects during development

Action:

- This is normal in development unless volume is causing local performance issues.

### 9.4 `SECRET_KEY not provided` and weak default credential warnings

Cause:

- Running without hardened env vars.

Fix:

- Use `backend/run_secure_dev.sh`, or set:
- `SECRET_KEY`
- `DEFAULT_ADMIN_PASSWORD`
- `DEFAULT_ANALYST_PASSWORD`
- Optionally `ENFORCE_STRICT_SECURITY=1`

### 9.5 Agent logs not arriving

Checks:

1. Agent can authenticate (`/token`)
2. Agent posts to `SERVER_URL + AGENT_INGEST_PATH` (default `/api/logs`)
3. If backend enforces `AGENT_API_KEY`, agent sends matching `X-Agent-Api-Key`
4. Inspect `agent_runtime.log` and `agent_buffer.db` (offline queue)

### 9.6 Keylogger/screenshot features not working

macOS notes:

- Keylogger (`pynput`) requires Accessibility/Input Monitoring permissions
- Screenshot capture uses `screencapture`; backend background tasks must be enabled
- Screenshot logs depend on `captureScreenshots=true` in settings

### 9.7 Matplotlib cache warnings

Symptom:

- `Matplotlib is building the font cache` or unwritable cache dir warnings.

Fix:

```bash
export MPLCONFIGDIR=/tmp/sentinel_mplconfig
mkdir -p "$MPLCONFIGDIR"
```

## 10. Useful Smoke Checks

#### 10.1 API health

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/ready
```

#### 10.2 Login/token

```bash
# Replace password with your current seeded value (e.g. AdminPass_123! in secure launcher mode)
curl -sS -X POST http://127.0.0.1:8000/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=AdminPass_123%21'
```

#### 10.3 Socket.IO handshake

```bash
curl -i 'http://127.0.0.1:8000/socket.io/?EIO=4&transport=polling'
```

#### 10.4 Create a test log

```bash
curl -sS -X POST http://127.0.0.1:8000/logs \
  -H 'Content-Type: application/json' \
  -d '{
    "id":"onboarding-log-1",
    "timestamp":"2026-02-19T00:00:00",
    "user":"admin",
    "activityType":"SYSTEM",
    "riskLevel":"INFO",
    "description":"Onboarding smoke log",
    "details":"manual test",
    "ipAddress":"127.0.0.1",
    "location":"local"
  }'
```

## 11. Test Commands

### 11.1 Backend + Agent Python tests

```bash
python3 -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
python3 -m pip install -r agent/requirements.txt -r agent/requirements-dev.txt
python3 -m pytest
```

Performance tests:

```bash
SENTINEL_P95_MS=500 python3 -m pytest -m performance
```

### 11.2 Frontend tests

```bash
npm ci
npm run test:unit
```

### 11.3 E2E tests

```bash
npx playwright install
npm run test:e2e
```

Artifacts are generated under `reports/`.

## 12. Key Files to Know

- `backend/main.py` - main API, sockets, auth, ingestion, SOAR wiring
- `backend/config.py` - env settings, security posture checks, CORS origins
- `backend/interception.py` - live traffic interception engine
- `backend/simulation.py` - synthetic traffic generation
- `backend/soar_engine.py` - rule evaluation + action execution
- `agent/client.py` - endpoint agent runtime + secure log sending
- `services/api.ts` - frontend API client and auth interceptor
- `components/` - UI modules by feature

---

If you are onboarding a teammate, the fastest path is:

1. Start backend with `backend/run_secure_dev.sh`
2. Start frontend with `npm run dev`
3. Login as `admin`
4. Open Dashboard, AI Analyst, Automation, Settings
5. Run smoke checks in section 10 if anything looks off
