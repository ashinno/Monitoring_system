# Threat Model - STRIDE Analysis

## Overview

This document provides the STRIDE threat model for the Sentinel AI Cyber Monitoring System, addressing the security requirements referenced in Thesis Chapter 3.

## System Architecture & Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL ZONE                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │   Endpoints  │    │   Ollama     │    │   External   │             │
│  │   (Agents)   │    │   (LLM)      │    │   Services   │             │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘             │
│         │                   │                   │                      │
│         ▼                   ▼                   ▼                      │
├─────────────────────────────────────────────────────────────────────────┤
│                      DMZ / API GATEWAY                                   │
│         │                   │                   │                      │
│         ▼                   ▼                   ▼                      │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                   BACKEND API (FastAPI)                      │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │       │
│  │  │   ML Engine │  │  SOAR       │  │  Prediction    │    │       │
│  │  │  (Anomaly)  │  │  Engine     │  │  Engine        │    │       │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘    │       │
│  └──────────────────────────┬──────────────────────────────────┘       │
│                             │                                            │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                    DATABASE (SQLite)                          │       │
│  │           [Logs, Users, Playbooks, Audit]                    │       │
│  └─────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     SECURE MONITORING ZONE                              │
│         │                                                              │
│         ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │              REACT FRENDEND (Admin Dashboard)                 │       │
│  │     [Dashboard, Live Monitor, AI Analyst, Settings]         │       │
│  └─────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Trust Boundaries

| Boundary | Components | Trust Level |
|----------|------------|-------------|
| External → DMZ | Agents, Ollama, External APIs | Untrusted |
| DMZ → Backend | FastAPI Routes | Partially Trusted |
| Backend → Database | SQL Queries | Trusted |
| Backend → Frontend | WebSocket, REST | Authenticated |
| Frontend → Admin | Browser Session | Authenticated + RBAC |

---

## STRIDE Analysis

### 1. Spoofing

| Threat | Description | Mitigation |
|--------|-------------|------------|
| T1.1 | Agent spoofing - Malicious actor impersonates endpoint agent | API Key authentication (`X-Agent-Api-Key`) |
| T1.2 | User spoofing - Attacker steals admin credentials | JWT tokens + Role-based access control |
| T1.3 | LLM spoofing - Fake Ollama service returning malicious responses | TLS/SSL verification, local model validation |

**Implementation**: `backend/security/agent_auth.py`, `backend/auth.py`

### 2. Tampering

| Threat | Description | Mitigation |
|--------|-------------|------------|
| T2.1 | Log tampering - Attacker modifies logs before ingestion | Agent-side signing, hash verification |
| T2.2 | Database tampering - Direct DB modification | File permissions, SQLite WAL mode |
| T2.3 | Model tampering - Malicious ML model replacement | Model checksum verification |
| T2.4 | Configuration tampering - Runtime config changes | Immutable config, validation |

**Implementation**: `backend/models.py` (immutable audit records), `backend/config.py`

### 3. Repudiation

| Threat | Description | Mitigation |
|--------|-------------|------------|
| T3.1 | User denies action | Immutable audit trail in `playbook_action_audit` |
| T3.2 | Agent denies sending data | Agent ID + timestamp signing |
| T3.3 | LLM denies response | Request/response logging |

**Implementation**: `backend/models.py` - `PlaybookActionAudit` table

### 4. Information Disclosure

| Threat | Description | Mitigation |
|--------|-------------|------------|
| T4.1 | PII exposure in logs | Field-level redaction (clipboard hashing) |
| T4.2 | Sensitive data in database | Encryption at rest (future), access control |
| T4.3 | LLM prompt injection | Prompt sanitization, input validation |
| T4.4 | ML model inversion | Differential privacy in federated learning |

**Implementation**: `backend/llm/sanitizer.py`, `backend/ml_engine.py` (federated DP)

### 5. Denial of Service

| Threat | Description | Mitigation |
|--------|-------------|------------|
| T5.1 | API DoS - Flood endpoints | Rate limiting (100 req/min default) |
| T5.2 | LLM DoS - Prompt flooding | Timeout (30s), queue limits |
| T5.3 | ML DoS - Feature injection | Input validation, anomaly filtering |
| T5.4 | Database DoS - Query flooding | Connection pooling, query timeouts |

**Implementation**: `backend/soar_engine.py` (rate limiting), `backend/config.py`

### 6. Elevation of Privilege

| Threat | Description | Mitigation |
|--------|-------------|------------|
| T6.1 | Privilege escalation - Regular user becomes admin | RBAC enforcement, permission checks |
| T6.2 | SOAR bypass - Playbook injection | Guardrails: approval, confidence threshold |
| T6.3 | Agent privilege - Compromise admin functions | Agent capability restrictions |

**Implementation**: `backend/auth.py`, `backend/soar_engine.py` (guardrails)

---


## Chapter X STRIDE Summary

The following compact matrix is used in the thesis Chapter X additions for quick traceability.

| Threat Category | Examples | Mitigations |
|----------------|----------|-------------|
| Spoofing | Agent impersonation | API Key authentication |
| Tampering | Log modification | Hash verification |
| Repudiation | Deny actions | Immutable audit trail |
| Information Disclosure | PII exposure | Field-level redaction |
| Denial of Service | API flooding | Rate limiting |
| Elevation of Privilege | RBAC bypass | Permission checks |

---

## Security Controls Matrix

| Control | Component | Implementation |
|---------|-----------|----------------|
| Authentication | All endpoints | JWT Bearer tokens |
| Authorization | API routes | RBAC with permissions |
| Input Validation | All inputs | Pydantic schemas |
| Rate Limiting | API | 100 req/min per user |
| Audit Logging | All actions | `playbook_action_audit` |
| Data Redaction | Agent | Clipboard hashing only |
| Prompt Sanitization | LLM | Control char filtering |
| Differential Privacy | FL | Epsilon-greedy aggregation |

---

## Attack Surface Analysis

| Component | Exposed Interfaces | Risk Level | Notes |
|-----------|-------------------|------------|-------|
| Backend API | REST + WebSocket | HIGH | Primary attack vector |
| Agent | TCP ingestion | MEDIUM | Requires API key |
| Frontend | HTTPS | MEDIUM | Browser-based |
| Database | File system | LOW | Local SQLite |
| Ollama | Local HTTP | MEDIUM | No external access |

---

## Validation Against Thesis Claims

| Thesis Claim | Threat Model Coverage |
|--------------|----------------------|
| Privacy-by-Design | T4.1, T4.2, T4.3, T4.4 |
| On-Premise AI | T1.3, T4.3, T5.2 |
| Automated Response Safety | T6.2, T5.3 |
| Federated Learning | T4.4, T3.2 |

---

## References

- OWASP Top 10 (2021)
- STRIDE Methodology (Microsoft)
- MITRE ATT&CK Framework
- Thesis Chapter 3: Security Architecture
