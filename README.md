# Sentinel AI - Cyber Monitor

Sentinel AI is a cutting-edge cyber monitoring and threat detection system designed to provide real-time situational awareness, AI-powered threat analysis, and automated incident response. It combines a high-performance backend with a modern, responsive frontend to deliver a comprehensive security dashboard.

## 1. Project Overview

### Purpose
The primary objective of Sentinel AI is to empower security analysts with tools to monitor network traffic, detect anomalies, and enforce security policies efficiently. It acts as a central command center for cybersecurity operations.

### Key Features
- **Real-Time Dashboard**: Live visualization of network traffic and security events using Socket.IO.
- **AI Analyst**: Local LLM (Ollama/Qwen) plus a local heuristic/ML engine for privacy-preserving threat analysis and reports.
- **Real Traffic Interception**: Built-in host-level interceptor captures live TCP/UDP flows and streams them into the analytics pipeline.
- **Automated Playbooks**: Rule-based system to automatically respond to threats (e.g., locking users upon detecting critical risks).
- **User Monitoring**: Activity logging, periodic screenshot capture, and content filtering (gambling, social media, safe search).
- **Role-Based Access Control**: Granular permissions for Administrators and Analysts.

### Technologies Used
- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS, Recharts, Lucide React.
- **Backend**: Python 3, FastAPI, SQLAlchemy, SQLite, Socket.IO, Pandas, NumPy.
- **AI Integration**: Local Ollama/Qwen runtime, local heuristics/ML pipeline.
- **Authentication**: OAuth2 with JWT (JSON Web Tokens).

## 2. Interface Documentation

### Dashboard
The main dashboard provides a high-level view of the current security posture.


### Network Analysis
Detailed view of network logs, allowing analysts to filter and inspect individual traffic packets.


### AI Analyst
An interactive chat interface where analysts can query the system and generate exportable threat reports.


### Settings & Policy
Configuration panel for managing monitoring rules, content filters, and screenshot intervals.

## 3. Functionality Explanation

### Real-Time Monitoring
- **Purpose**: To provide immediate visibility into network activity.
- **Mechanism**: The backend streams traffic data via WebSocket (Socket.IO) to the frontend.
- **Visualization**: Area charts for bandwidth usage and bar charts for protocol distribution.

### AI Threat Analysis
- **Dual-Engine Approach**:
  1. **Local Heuristics**: Pandas algorithms analyze log severity distributions to calculate a "Threat Score" (0-100).
  2. **Generative AI**: Local Ollama/Qwen analyzes logs to provide natural-language summaries and strategic recommendations.
- **Output**: Generates detailed text reports and downloadable threat assessments.

### Automated Playbooks (SOAR)
- **Purpose**: To reduce response time for critical incidents through Security Orchestration, Automation, and Response.
- **Configuration**: Users define rules (e.g., `IF RiskLevel == CRITICAL THEN LockUser`).
- **Execution**: The robust Python-based backend engine continuously evaluates new logs against active playbooks in the background.
- **Features**:
    - **Platform Agnostic**: Actions like "Lock User" are implemented at the application database level, ensuring compatibility across Windows, macOS, and Linux.
    - **Adaptive Resource Management**: Uses asynchronous background tasks to ensure log ingestion remains high-performance even under heavy automation load.
    - **Graceful Degradation**: Individual playbook failures are logged but do not crash the monitoring pipeline.

### SOAR System Requirements & Limitations
- **Requirements**: Python 3.8+ for backend execution.
- **Limitations**:
    - "Lock User" and "Quarantine" actions currently affect application access only (Database status), not OS-level user accounts.
    - External notifications (Email/SMS) require valid SMTP/Twilio configuration in Settings.
    - Automated actions are processed asynchronously; there may be a slight delay (milliseconds to seconds) between detection and action depending on system load.

### User & Content Monitoring
- **Activity Logging**: Tracks user actions with risk levels (INFO, WARNING, CRITICAL).
- **Screenshot Capture**: Optional background service that captures desktop screenshots for audit trails.
- **Content Filtering**: Configurable blocking of gambling sites, social media, and enforcement of Safe Search.

## 4. Installation & Usage

### Prerequisites
- **Node.js** (v18 or higher)
- **Python** (v3.8 or higher)

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   python main.py
   ```
   The backend API will run on `http://localhost:8000`.

#### Secure one-command backend startup (recommended)
Use the built-in launcher script to start with safer defaults and your project virtualenv automatically:

```bash
cd /Users/ashinno/Project/Monitoring/Monitoring_system
backend/run_secure_dev.sh
```

Optional overrides:

```bash
HOST=127.0.0.1 PORT=8001 RELOAD=0 backend/run_secure_dev.sh
```

By default, this script sets `ENFORCE_STRICT_SECURITY=1` and secure seed passwords unless you override them via environment variables.

### ML Retraining (Improved)
You can trigger stronger retraining with configurable parameters:

```bash
curl -X POST http://localhost:8000/ml/train \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "data_limit": 50000,
    "validation_split": 0.2,
    "autoencoder_epochs": 80,
    "autoencoder_batch_size": 64
  }'
```

Optional environment variables for model tuning:
- `ML_IFOREST_ESTIMATORS` (default: `300`)
- `ML_IFOREST_CONTAMINATION` (default: `0.05`)
- `ML_AE_LR` (default: `0.001`)
- `ML_TRAIN_LIMIT` (default: `50000`)

### Agent Setup
1. Navigate to the agent directory:
   ```bash
   cd agent
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the agent (requires admin privileges for some features):
   ```bash
   sudo python client.py
   ```

### Frontend Setup
1. Navigate to the project root (if not already there):
   ```bash
   cd ..
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   The application will be accessible at `http://localhost:5173`.

### Default Credentials
The system comes pre-seeded with the following accounts:
- **Admin**: `admin` / `admin`
- **Analyst**: `analyst` / `password`

## 5. Additional Information

### License
This project is proprietary software. All rights reserved.
