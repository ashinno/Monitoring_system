# Sentinel Monitoring System - Beginner Onboarding Guide

This guide is written for someone new to this project and new to running full-stack apps.

If you follow this file top to bottom, you will:

- run the backend
- run the frontend
- log in successfully
- understand every screen/functionality in the app
- know what to do when something breaks

---

## 1) What You Are Running

Sentinel has 3 parts:

1. Backend API (`backend/`): FastAPI + Socket.IO + database + automation logic
2. Frontend UI (repo root): React dashboard
3. Agent (`agent/`): optional endpoint collector that sends activity logs to backend

Think of it this way:

- Frontend = what you see
- Backend = brain and data storage
- Agent = optional data producer

---

## 2) Prerequisites

You need these installed:

- Node.js 18+
- Python 3.9+
- npm
- pip

Optional but useful:

- Docker Desktop (for Redis/Postgres stack)
- Ollama (for local LLM features like AI chat)

---

## 3) Folder and Terminal Basics

Open terminal in project root:

`/Users/ashinno/Project/Monitoring/Monitoring_system`

Check where you are:

```bash
pwd
```

You should see the path above.

---

## 4) Fastest First Run (Recommended)

## Step 1: Start backend

From project root:

```bash
backend/run_secure_dev.sh
```

Expected result:

- backend starts on `http://0.0.0.0:8000`
- you see Uvicorn startup logs
- no crash

Important:

- keep this terminal running

## Step 2: Start frontend

Open a second terminal in project root:

```bash
npm install
npm run dev
```

Expected result:

- Vite dev server starts
- frontend available at `http://localhost:3000`

## Step 3: Open app and login

Go to:

`http://localhost:3000`

Use secure launcher default credentials:

- Admin username: `admin`
- Admin password: `AdminPass_123!`

Alternative username that also works: `Admin User` (because backend accepts ID or name)

Expected result:

- you enter dashboard
- sidebar shows main modules

---

## 5) If Login Fails

Most common reason: old DB seeded with different passwords.

Reset local SQLite DB and retry:

```bash
rm -f backend/sentinel.db sentinel.db
```

Then restart backend and try login again.

---

## 6) Manual Backend Start (Alternative)

If you do not want `run_secure_dev.sh`, use:

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 main.py
```

Manual defaults (if env vars are not set):

- Admin: `admin` / `admin`
- Analyst: `analyst` / `password`

## 6.1) Optional Docker Stack (Backend Services)

If you prefer containers for backend services:

```bash
docker compose up --build
```

This starts:

- Postgres (`db`)
- Redis (`redis`)
- backend API (`backend`)
- Celery worker (`worker`)

Note:

- frontend is still run locally with `npm run dev`

---

## 7) Every Functionality Available (Full Tour)

This section explains all major user-facing functionalities.

## 7.1 Overview (Dashboard)

Purpose:

- live executive view of system state

What you get:

- threat/user/anomaly summary cards
- threat breakdown bar/stack visuals
- AI prediction card (`prediction_update` stream)
- live system metrics panel
- network traffic charts
- recent critical events table
- embedded network graph
- embedded traffic interceptor panel
- embedded network analysis panel
- embedded keymap heatmap

Expected behavior:

- values change as logs/traffic arrive
- socket events update UI in real time

## 7.2 Live Monitor

Purpose:

- inspect raw activity logs in real time

What you can do:

- search logs
- filter by risk level
- export logs
- watch AI Overwatch summary line

Expected behavior:

- new logs stream into table
- filter/search updates results immediately

## 7.3 Keylogger Management

Purpose:

- visualize keyboard-derived stats from KEYLOG events

What you can do:

- view total keystrokes/sessions/duration
- see top applications chart
- inspect key heatmap intensity
- export keylog data (CSV/JSON)

Expected behavior:

- if keylog data exists, charts and counts populate
- heatmap updates with `key_heatmap_update`

## 7.4 AI Analyst

Purpose:

- run deeper analysis and chat with local AI

What you can do:

- click "Run Deep Scan Analysis" (`POST /analyze`)
- see threat score + recommendations
- export text report
- use chat assistant (`POST /chat`)
- execute suggested action: block IP
- execute suggested action: isolate host
- execute suggested action: reset password

Expected behavior:

- analysis panel fills with summary/recommendations
- chat returns AI answers (if LLM reachable)

## 7.5 Auto-Response (Playbook Automation / SOAR)

Purpose:

- auto-react to suspicious events

What you can do:

- create playbook rules (`if trigger then action`)
- toggle playbooks on/off
- delete playbooks

Trigger examples:

- riskLevel equals CRITICAL
- activityType contains NETWORK

Action examples:

- LOCK_USER
- QUARANTINE_USER
- ALERT_ADMIN

Expected behavior:

- when incoming log matches active rule, backend executes corresponding action path
- action results appear as new logs

## 7.6 User Access Management

Purpose:

- control identities, roles, status, permissions

What you can do:

- create user with role and clearance
- set explicit permissions (`READ_LOGS`, `EDIT_SETTINGS`, `MANAGE_USERS`, `EXPORT_DATA`)
- change status (`ACTIVE`, `INACTIVE`, `LOCKED`, `SUSPENDED`, `QUARANTINED`)
- delete users

Expected behavior:

- table/cards reflect changes immediately after API refresh

## 7.7 Policy Control (Settings)

Purpose:

- central controls for monitoring and policies

What you can configure:

- content controls: block gambling/adult, block social media, safe search enforcement
- monitoring controls: screen time limits, screenshot capture, clipboard monitoring, USB monitoring, camera monitoring
- keyword alerts: manage sensitive keyword list
- notifications: email/webhook/SMTP/Twilio fields and test notification endpoint
- agent controls: start, stop, and status/PID monitoring

Expected behavior:

- settings save via backend
- agent state updates every few seconds

## 7.8 Traffic Interception

Purpose:

- collect host network flow info and push to `/traffic`

What you can do:

- list interfaces
- start/stop interception
- choose protocol scope and loopback behavior
- watch packet/byte/error counters

Expected behavior:

- status endpoint updates
- traffic records appear in charts and analysis modules

## 7.9 Backend API Functionalities (Advanced)

Beyond the UI, backend also supports:

- health/readiness: `/health`, `/ready`
- ML training: `/ml/train`
- federated endpoint: `/ml/federated-update`
- federated endpoint: `/ml/federated/rounds/start`
- federated endpoint: `/ml/federated/rounds/{round_id}`
- federated endpoint: `/ml/federated/reveal-mask`
- federated endpoint: `/ml/federated/global-model`
- ingestion endpoint: `/logs` (general)
- ingestion endpoint: `/api/logs` (agent-specific, optional API-key guard)

---

## 8) What "Healthy" Looks Like

Backend healthy:

- starts without crashing
- `/health` returns JSON
- frontend requests return 200
- socket endpoint returns 200 and websocket upgrade accepted

Frontend healthy:

- login screen loads
- login succeeds
- sidebar navigation works
- dashboard data refreshes over time

Quick checks:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/ready
curl -i 'http://127.0.0.1:8000/socket.io/?EIO=4&transport=polling'
```

---

## 9) Optional Components You Might Need

## 9.1 Redis (for Celery worker-backed async)

Start Redis quickly:

```bash
docker compose up -d redis
```

If you do not want Celery in local dev:

```bash
export SENTINEL_DISABLE_CELERY=1
```

## 9.2 Ollama (for AI chat/analysis enhancements)

Default backend settings:

- `OLLAMA_URL=http://localhost:11434/api/generate`
- `OLLAMA_MODEL=qwen3:8b`

Set manually if needed:

```bash
export OLLAMA_URL=http://localhost:11434/api/generate
export OLLAMA_MODEL=qwen3:8b
```

## 9.3 Agent

Run agent manually:

```bash
python3 -m pip install -r agent/requirements.txt
python3 agent/client.py
```

Useful env vars:

- `SERVER_URL` (default `http://localhost:8000`)
- `AGENT_INGEST_PATH` (default `/api/logs`)
- `AGENT_USER`, `AGENT_PASSWORD`
- `AGENT_API_KEY`

---

## 10) Common Problems and Fixes (Beginner Friendly)

## 10.1 Error: `localhost:3001 is not an accepted origin`

Cause:

- frontend origin not accepted by backend CORS/Socket.IO list

Fix:

1. run frontend on `3000` (`npm run dev` default)
2. or include your origin in `CORS_ALLOWED_ORIGINS`

Check:

```bash
curl -i -X OPTIONS http://127.0.0.1:8000/users/me \
  -H 'Origin: http://localhost:3001' \
  -H 'Access-Control-Request-Method: GET'
```

## 10.2 Repeated Redis/Celery retry errors

Cause:

- Redis not running but Celery backend URL points to Redis

Fix options:

1. start Redis
2. disable Celery (`SENTINEL_DISABLE_CELERY=1`)
3. continue running: backend now falls back in-process when Redis unreachable

## 10.3 Too many `OPTIONS` / `GET /api/system-metrics` logs

Cause:

- expected frontend polling (especially in dev + StrictMode)

Action:

- normal behavior unless performance is impacted

## 10.4 Warning: weak/default security values

Cause:

- missing `SECRET_KEY` or weak default passwords

Fix:

- prefer `backend/run_secure_dev.sh`
- or set env vars manually:
- `SECRET_KEY`
- `DEFAULT_ADMIN_PASSWORD`
- `DEFAULT_ANALYST_PASSWORD`
- `ENFORCE_STRICT_SECURITY=1`

## 10.5 Agent not sending logs

Checklist:

1. agent login works against `/token`
2. `SERVER_URL` correct
3. backend reachable from agent host
4. if API key enabled on backend, agent key matches
5. inspect `agent_runtime.log` and `agent_buffer.db`

## 10.6 Keylogger or screenshot data missing (macOS)

Cause:

- OS permissions not granted

Fix:

- grant Input Monitoring / Accessibility permissions
- enable screenshot setting in UI
- ensure backend background tasks are not disabled

## 10.7 Matplotlib cache warnings

Fix:

```bash
export MPLCONFIGDIR=/tmp/sentinel_mplconfig
mkdir -p "$MPLCONFIGDIR"
```

---

## 11) Beginner Smoke Test (Copy/Paste)

Run these after startup.

## 11.1 Get token

```bash
curl -sS -X POST http://127.0.0.1:8000/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=AdminPass_123%21'
```

If using manual backend defaults, change password to `admin`.

## 11.2 Create a test log

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

Expected result:

- API returns saved log JSON
- log appears in UI lists shortly

---

## 12) Testing Commands

## 12.1 Python tests (backend + agent)

```bash
python3 -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
python3 -m pip install -r agent/requirements.txt -r agent/requirements-dev.txt
python3 -m pytest
```

Performance tests:

```bash
SENTINEL_P95_MS=500 python3 -m pytest -m performance
```

## 12.2 Frontend unit tests

```bash
npm ci
npm run test:unit
```

## 12.3 E2E tests

```bash
npx playwright install
npm run test:e2e
```

Reports are written to `reports/`.

---

## 13) File Map (Where to Look in Code)

- `backend/main.py`: API routes, socket events, startup seeding, SOAR dispatch
- `backend/config.py`: environment settings, security posture checks, CORS defaults
- `backend/interception.py`: live traffic interception logic
- `backend/simulation.py`: synthetic traffic generation
- `backend/soar_engine.py`: playbook evaluation and action execution
- `agent/client.py`: agent runtime, auth, log send, offline queue flush
- `services/api.ts`: frontend API baseURL + auth interceptor
- `components/`: each UI module

---

## 14) 10-Minute Guided Demo Path

If you are demoing to someone new, do this sequence:

1. start backend (`backend/run_secure_dev.sh`)
2. start frontend (`npm run dev`)
3. login as admin
4. open Overview and confirm live widgets render
5. open Live Monitor and use search/filter
6. open AI Analyst and run deep scan
7. open Auto-Response and create one playbook
8. open Settings and toggle one policy + save
9. run smoke test log command and watch UI update

You now validated the full main flow.
