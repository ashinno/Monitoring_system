# Sentinel AI - Cyber Monitor

Sentinel AI is a cutting-edge cyber monitoring and threat detection system designed to provide real-time situational awareness, AI-powered threat analysis, and automated incident response. It combines a high-performance backend with a modern, responsive frontend to deliver a comprehensive security dashboard.

## 1. Project Overview

### Purpose
The primary objective of Sentinel AI is to empower security analysts with tools to monitor network traffic, detect anomalies, and enforce security policies efficiently. It acts as a central command center for cybersecurity operations.

### Key Features
- **Real-Time Dashboard**: Live visualization of network traffic and security events using Socket.IO.
- **AI Analyst**: Integrated with Google Gemini AI and a local Pandas-based heuristic engine to score threats and generate actionable intelligence reports.
- **Traffic Simulator**: Built-in tool to simulate various network traffic patterns for testing and training.
- **Automated Playbooks**: Rule-based system to automatically respond to threats (e.g., locking users upon detecting critical risks).
- **User Monitoring**: Activity logging, periodic screenshot capture, and content filtering (gambling, social media, safe search).
- **Role-Based Access Control**: Granular permissions for Administrators and Analysts.

### Technologies Used
- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS, Recharts, Lucide React.
- **Backend**: Python 3, FastAPI, SQLAlchemy, SQLite, Socket.IO, Pandas, NumPy.
- **AI Integration**: Google Generative AI (Gemini), Local Heuristics (Pandas).
- **Authentication**: OAuth2 with JWT (JSON Web Tokens).

## 2. Interface Documentation

### Dashboard
The main dashboard provides a high-level view of the current security posture.


### Network Analysis
Detailed view of network logs, allowing analysts to filter and inspect individual traffic packets.


### AI Analyst
An interactive chat interface where analysts can query the system and generate PDF threat reports.


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
  2. **Generative AI**: Google Gemini analyzes text-based logs to provide natural language summaries and strategic recommendations.
- **Output**: Generates detailed text reports and downloadable threat assessments.

### Automated Playbooks
- **Purpose**: To reduce response time for critical incidents.
- **Configuration**: Users define rules (e.g., `IF RiskLevel == CRITICAL THEN LockUser`).
- **Execution**: The system continuously checks new logs against active playbooks and executes defined actions automatically.

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
