# Thesis Requirements Traceability (Implementation)

This file maps core thesis FR/NFR claims to code artifacts in this repository.

## FR1.x Agent & Ingestion

- FR1.2 local redaction/hashing: `agent/monitor.py` (clipboard hash only).
- FR1.3 secure ingestion endpoint: `backend/main.py` (`POST /api/logs`) with optional `X-Agent-Api-Key` guard via `backend/security/agent_auth.py`.
- Resilience buffering: `agent/offline_queue.py` and flush workflow in `agent/client.py`.

## FR2.x Hybrid Threat Analysis

- Fast-path ingestion + local anomaly screen: `backend/main.py` + `backend/ml_engine.py`.
- Structured LLM contract validation: `backend/llm/contracts.py`.
- Prompt sanitization + bounded context: `backend/llm/sanitizer.py`.
- LLM duplicate caching: `backend/llm/cache.py`.

## FR3.x Automated Response (SOAR)

- Playbooks + async execution: `backend/main.py`, `backend/tasks.py`, `backend/soar_engine.py`.
- Guardrails (confidence, approval, rate limit, scope): `backend/soar_engine.py`, playbook fields in `backend/models.py` and `backend/schemas.py`.
- Immutable action audit records: `playbook_action_audit` model in `backend/models.py`.

## FR4.x Visualization

- Real-time streaming: Socket.IO events in `backend/main.py`, consumers in `App.tsx` and dashboard components.
- AI Analyst panel with structured assessment rendering: `components/AIAnalyst.tsx` and `types.ts`.

## NFR Highlights

- On-prem AI boundary: local Ollama calls in `backend/main.py` and `backend/prediction_engine.py`.
- Health checks: `GET /health` and `GET /ready` in `backend/main.py`.
- Security posture controls: `backend/config.py` strict mode and seeded credential checks.

