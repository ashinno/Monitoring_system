from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from typing import List
from contextlib import asynccontextmanager
import socketio
import uvicorn
import asyncio
import os
import uuid
import httpx
import json
import joblib
from datetime import datetime, timedelta

import models, schemas, auth, analysis, database, ml_engine, prediction_engine, system_monitor, reporting, notifications, soar_engine
import agent_manager
import tasks # Explicit import for Celery tasks
from config import settings
from security.agent_auth import verify_agent_api_key
from llm.sanitizer import sanitize_context_items, sanitize_text
from llm.cache import LLMResponseCache
from llm.contracts import validate_assessment


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)

# --- DB Setup ---
models.Base.metadata.create_all(bind=database.engine)

import base64

# ...

async def analyze_screenshot_context(filepath: str, db: Session):
    """
    Uses Ollama (qwen3:8b) to analyze the screenshot + recent logs to infer user activity.
    """
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    
    # 1. Encode Image to Base64
    try:
        with open(filepath, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error reading screenshot for analysis: {e}")
        return None, None

    # 2. Get Recent Metadata (Logs)
    # We want logs from the last 5 minutes to give context
    five_mins_ago = datetime.now() - timedelta(minutes=5)
    recent_logs = db.query(models.Log).filter(models.Log.timestamp >= five_mins_ago).order_by(models.Log.timestamp.desc()).limit(10).all()
    
    metadata_context = "\n".join([f"[{l.timestamp}] {l.activity_type}: {l.description}" for l in recent_logs])
    if not metadata_context:
        metadata_context = "No recent logs."

    # 3. Prompt for Ollama
    # Note: Qwen 3 (or Qwen 2.5) supports vision if using the VL variant, but standard text models can't see images.
    # Assuming user has a vision-capable model or we are using the "images" parameter of Ollama API which is standard for multimodal models.
    
    prompt = f"""
    You are an AI Activity Recognition Engine.
    
    Input:
    1. Visual Snapshot of the user's screen (attached).
    2. Recent System Logs (Metadata):
    {metadata_context}
    
    Task:
    Analyze the visual content and the logs to infer exactly what the user is doing.
    
    Output strictly valid JSON:
    {{
        "CurrentActivity": "Short label (e.g. 'Coding in Python', 'Writing Email')",
        "Summary": "A concise 1-sentence description of the observed behavior."
    }}
    """
    
    try:
        async with httpx.AsyncClient() as client:
            # Ollama 'generate' endpoint supports 'images' list (base64)
            response = await client.post(OLLAMA_URL, json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "images": [encoded_string] 
            }, timeout=30.0)
            
            if response.status_code == 200:
                result = response.json()
                ai_data = json.loads(result['response'])
                return ai_data.get("CurrentActivity"), ai_data.get("Summary")
            else:
                print(f"Ollama Analysis Failed: {response.status_code} - {response.text}")
                return None, None

    except Exception as e:
        print(f"Context Analysis Error: {e}")
        return None, None

async def screenshot_loop():
    while True:
        try:
            db = database.SessionLocal()
            db_settings = db.query(models.Settings).first()
            if db_settings and db_settings.capture_screenshots:
                # Ensure directory exists
                os.makedirs("screenshots", exist_ok=True)
                
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = os.path.join("screenshots", filename)
                
                # Run screencapture (macOS specific)
                # -x: silent
                proc = await asyncio.create_subprocess_exec(
                    "screencapture", "-x", filepath,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                
                if proc.returncode == 0:
                    # --- Contextual Analysis ---
                    current_activity, activity_summary = await analyze_screenshot_context(filepath, db)
                    
                    log = models.Log(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now().isoformat(),
                        user="SYSTEM",
                        activity_type="SCREENSHOT",
                        risk_level="INFO",
                        description="Periodic Screenshot Captured",
                        details=f"/screenshots/{filename}",
                        ip_address="127.0.0.1",
                        location="Local",
                        current_activity=current_activity,
                        activity_summary=activity_summary
                    )
                    db.add(log)
                    db.commit()
                    
                    # Emit
                    log_response = schemas.Log.model_validate(log)
                    await sio.emit('new_log', log_response.model_dump(by_alias=True))
            
            db.close()
        except Exception as e:
            print(f"Screenshot error: {e}")
            
        await asyncio.sleep(30) # Check every 30 seconds

async def metrics_loop():
    while True:
        try:
            db = database.SessionLocal()
            system_monitor.save_metric(db)
            db.close()
        except Exception as e:
            print(f"Metrics save error: {e}")
        await asyncio.sleep(60) # Save every minute

def ensure_settings_schema():
    inspector = inspect(database.engine)
    if "settings" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("settings")}
    columns = {
        "monitor_clipboard": "BOOLEAN DEFAULT 0",
        "monitor_usb": "BOOLEAN DEFAULT 0",
        "monitor_camera": "BOOLEAN DEFAULT 0",
    }
    with database.engine.begin() as conn:
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE settings ADD COLUMN {name} {ddl}"))

    playbook_columns = {
        "min_confidence": "FLOAT DEFAULT 0.0",
        "requires_approval": "BOOLEAN DEFAULT 0",
        "rate_limit_count": "INTEGER DEFAULT 5",
        "rate_limit_window_seconds": "INTEGER DEFAULT 300",
        "scope": "TEXT DEFAULT 'global'",
    }
    existing_playbook = {col["name"] for col in inspector.get_columns("playbooks")} if "playbooks" in inspector.get_table_names() else set()
    with database.engine.begin() as conn:
        for name, ddl in playbook_columns.items():
            if name not in existing_playbook:
                conn.execute(text(f"ALTER TABLE playbooks ADD COLUMN {name} {ddl}"))


def ensure_audit_table():
    inspector = inspect(database.engine)
    if "playbook_action_audit" in inspector.get_table_names():
        return

    with database.engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE playbook_action_audit (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    playbook_id TEXT,
                    source_log_id TEXT,
                    action_type TEXT,
                    target TEXT,
                    status TEXT,
                    reason TEXT,
                    risk_level TEXT,
                    confidence FLOAT
                )
                """
            )
        )

@asynccontextmanager
async def lifespan(_: FastAPI):
    db = database.SessionLocal()
    disable_background = os.getenv("SENTINEL_DISABLE_BACKGROUND_TASKS") == "1" or os.getenv("SENTINEL_TESTING") == "1"
    try:
        ensure_settings_schema()
        ensure_audit_table()
        if not db.query(models.User).first():
            print("Seeding database with default users...")
            # Admin
            admin = models.User(
                id=settings.DEFAULT_ADMIN_ID,
                name=settings.DEFAULT_ADMIN_NAME,
                role="Administrator",
                clearance_level="ADMIN",
                status="ACTIVE",
                permissions=["READ_LOGS", "EDIT_SETTINGS", "MANAGE_USERS", "EXPORT_DATA"],
                hashed_password=auth.get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                avatar_seed="admin"
            )
            # Analyst
            analyst = models.User(
                id=settings.DEFAULT_ANALYST_ID,
                name=settings.DEFAULT_ANALYST_NAME,
                role="Security Analyst",
                clearance_level="L2",
                status="ACTIVE",
                permissions=["READ_LOGS", "EXPORT_DATA"],
                hashed_password=auth.get_password_hash(settings.DEFAULT_ANALYST_PASSWORD),
                avatar_seed="alice"
            )
            db.add(admin)
            db.add(analyst)
            db.commit()
            print("Database seeded.")
            
        # Seed Playbooks if empty
        if not db.query(models.Playbook).first():
            print("Seeding default playbooks...")
            rule1 = models.Playbook(
                id="rule-1",
                name="Critical Threat Lockout",
                is_active=True,
                trigger_field="riskLevel",
                trigger_operator="equals",
                trigger_value="CRITICAL",
                action_type="LOCK_USER"
            )
            db.add(rule1)
            db.commit()
            
        # Seed Settings if empty
        if not db.query(models.Settings).first():
            print("Seeding default settings...")
            default_settings = models.Settings(
                id=1,
                block_gambling=True,
                block_social_media=False,
                enforce_safe_search=True,
                screen_time_limit=True,
                alert_on_keywords=True,
                capture_screenshots=False,
                keywords=["password", "confidential", "secret", "key"]
            )
            db.add(default_settings)
            db.commit()
        if not disable_background:
            asyncio.create_task(screenshot_loop())
            asyncio.create_task(metrics_loop())
            print("Training Prediction Engine...")
            prediction_engine.predictor.train(db)

        yield
    finally:
        db.close()

app = FastAPI(title="Sentinel AI Backend", lifespan=lifespan)
llm_response_cache = LLMResponseCache(
    max_size=settings.LLM_CACHE_MAX_SIZE,
    ttl_seconds=settings.LLM_CACHE_TTL_SECONDS,
)

screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=screenshots_dir), name="screenshots")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS)

# Dependencies
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()



# Auth Routes
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: auth.OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Try to find user by name or id (since frontend sends 'username' field which could be ID or Name)
    # But usually OAuth2 form sends 'username'.
    user = db.query(models.User).filter(
        (models.User.name == form_data.username) | (models.User.id == form_data.username)
    ).first()
    
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.name})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# User Routes
@app.get("/users", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    db_user = db.query(models.User).filter(models.User.name == user.name).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    # Map Pydantic to ORM
    # Note: Pydantic model has camelCase aliases, but python attributes are snake_case.
    # user.dict() uses snake_case keys by default unless by_alias=True.
    # We want snake_case for DB model kwargs.
    user_data = user.model_dump(exclude={"password"})
    user_data["hashed_password"] = hashed_password
    
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: str, user_update: schemas.UserCreate, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = auth.get_password_hash(update_data.pop("password"))
        
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(db_user)
    db.commit()
    return {"ok": True}

# Log Routes
@app.get("/logs", response_model=List[schemas.Log])
def read_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    # Return latest first
    logs = db.query(models.Log).order_by(models.Log.timestamp.desc()).offset(skip).limit(limit).all()
    return logs

@app.get("/logs/stats/keylogs")
def get_keylog_stats(
    start_date: str = None, 
    end_date: str = None, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Log).filter(models.Log.activity_type == "KEYLOG")
    if start_date:
        query = query.filter(models.Log.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Log.timestamp <= end_date)
    
    # We fetch all matching logs to aggregate. 
    # For a production system, this should be done with SQL aggregation or pre-calculated metrics.
    logs = query.all()
    
    total_sessions = len(logs)
    total_duration = 0.0
    app_usage = {}
    total_keystrokes = 0
    
    for log in logs:
        if log.activity_summary:
            try:
                data = json.loads(log.activity_summary)
                # Handle new format
                if isinstance(data, dict) and "key_counts" in data:
                    total_duration += float(data.get("duration_seconds", 0))
                    total_keystrokes += int(data.get("total_keystrokes", 0))
                    app = data.get("active_window", "Unknown")
                    if not app: app = "Unknown"
                    app_usage[app] = app_usage.get(app, 0) + 1 # Count sessions
                # Handle old format (just counts)
                elif isinstance(data, dict):
                    # Estimate keystrokes from sum of counts
                    count_sum = sum(data.values())
                    total_keystrokes += count_sum
                    # No duration or app data in old format, but count as session
                    app = "Unknown"
                    app_usage[app] = app_usage.get(app, 0) + 1
            except:
                pass
                
    # Sort apps by frequency (sessions)
    # Filter out 'Unknown' if there are other apps, or move it to bottom?
    # Better to exclude it from "Top Apps" to focus on identified activity.
    filtered_apps = {k: v for k, v in app_usage.items() if k != "Unknown"}
    
    # If we have nothing but unknown, we might show it, but usually user wants to see real apps.
    if filtered_apps:
        top_apps = sorted(filtered_apps.items(), key=lambda x: x[1], reverse=True)[:5]
    else:
        # Fallback if only unknown exists
        top_apps = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_sessions": total_sessions,
        "total_duration_seconds": total_duration,
        "total_keystrokes": total_keystrokes,
        "top_apps": [{"name": k, "count": v} for k, v in top_apps]
    }

@app.post("/logs", response_model=schemas.Log)
async def create_log(log: schemas.LogCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Save to DB
    log_data = log.model_dump()
    
    # Check Settings for policy enforcement
    settings_obj = db.query(models.Settings).first()
    if settings_obj:
        desc = log_data.get('description', '').lower()
        details = log_data.get('details', '').lower()
        
        # Keyword Alert
        if settings_obj.alert_on_keywords:
            keywords = [k.lower() for k in (settings_obj.keywords or [])]
            if any(k in desc for k in keywords) or any(k in details for k in keywords):
                 if log_data.get('risk_level') not in ['HIGH', 'CRITICAL']:
                    log_data['risk_level'] = 'HIGH'
                    log_data['description'] = log_data['description'] + " [KEYWORD DETECTED]"

        # Gambling Block
        if settings_obj.block_gambling:
            gambling_terms = ["casino", "bet", "poker", "gambling", "lottery"]
            if any(k in desc for k in gambling_terms) or any(k in details for k in gambling_terms):
                log_data['risk_level'] = 'CRITICAL'
                log_data['description'] = log_data['description'] + " [POLICY VIOLATION: GAMBLING]"

        # Social Media Block
        if settings_obj.block_social_media:
            social_terms = ["facebook", "twitter", "instagram", "tiktok", "linkedin"]
            if any(k in desc for k in social_terms) or any(k in details for k in social_terms):
                if log_data.get('risk_level') != 'CRITICAL': # Don't downgrade if already critical (e.g. gambling)
                    log_data['risk_level'] = 'HIGH'
                log_data['description'] = log_data['description'] + " [POLICY VIOLATION: SOCIAL MEDIA]"

    # ML Anomaly Detection
    try:
        prediction = ml_engine.predict_anomaly(log_data)
        if prediction == -1:
            if log_data.get('risk_level') != 'CRITICAL':
                log_data['risk_level'] = 'HIGH'
            log_data['description'] = log_data['description'] + " [ML_DETECTED]"
    except Exception as e:
        print(f"ML Prediction Error: {e}")

    db_log = models.Log(**log_data)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    # Emit to Socket.IO
    # We emit the data as dict, ensuring camelCase for frontend if needed?
    # schemas.Log.model_validate(db_log).model_dump(by_alias=True) will give camelCase
    log_response = schemas.Log.model_validate(db_log)
    await sio.emit('new_log', log_response.model_dump(by_alias=True))

    # --- SOAR Automation (Background Task) ---
    # Using Celery for scalability
    celery_enabled = os.getenv("SENTINEL_DISABLE_CELERY") != "1"
    if celery_enabled:
        try:
            tasks.run_soar_automation.delay(db_log.id)
        except Exception as e:
            print(f"Warning: Async task failed. Scheduling SOAR in-process. Error: {e}")
            asyncio.create_task(asyncio.to_thread(soar_engine.engine.run_automation, db_log.id))
    else:
        asyncio.create_task(asyncio.to_thread(soar_engine.engine.run_automation, db_log.id))

    # Notifications
    if settings_obj and (log_data.get('risk_level') in ['HIGH', 'CRITICAL']):
        notifications.send_alert(db_log, settings_obj)
    
    # --- Real-time Heatmap ---
    if log_data.get('activity_type') == 'KEYLOG' and log_data.get('activity_summary'):
        try:
            # Parse the summary JSON
            import json
            summary = json.loads(log_data['activity_summary'])
            
            # Support both old (dict of counts) and new (dict with key_counts) format
            if isinstance(summary, dict) and "key_counts" in summary:
                 counts = summary["key_counts"]
            else:
                 counts = summary
                 
            # Emit dedicated event
            await sio.emit('key_heatmap_update', counts)
        except Exception as e:
            print(f"Failed to emit heatmap: {e}")

    # --- Prediction Integration (Background Task) ---
    # Offload heavy AI prediction to Celery, with fallback
    if celery_enabled:
        try:
            tasks.run_prediction_analysis.delay(db_log.id)
        except Exception as e:
            print(f"Warning: Async task failed. Scheduling Prediction in-process. Error: {e}")
            if db_log.risk_level in ['HIGH', 'CRITICAL']:
                asyncio.create_task(prediction_engine.predictor.predict_next_step_ai(db_log.activity_type))
    else:
        if db_log.risk_level in ['HIGH', 'CRITICAL']:
            asyncio.create_task(prediction_engine.predictor.predict_next_step_ai(db_log.activity_type))

    # Immediate (Fast) Prediction for UI feedback if needed
    # We can still run the fast Markov prediction here if we want immediate response
    # but for "Systems" thesis, we rely on async events.
    
    return db_log


@app.post("/api/logs", response_model=schemas.Log)
async def create_agent_log(
    log: schemas.LogCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_api_key),
):
    return await create_log(log, background_tasks, db)

@app.post("/ml/train")
def train_anomaly_model(payload: dict = None, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    config = payload or {}
    ml_engine.train_model(db, train_config=config)
    return {"message": "Model training triggered"}

@app.post("/ml/federated-update")
def receive_federated_update(weights: dict, current_user: models.User = Depends(auth.get_current_user)):
    """
    Endpoint to receive federated updates.

    Supports both:
    - Legacy FedAvg payloads
    - Secure Aggregation + Differential Privacy payloads
    """
    agent_id = str(
        weights.get("agent_id")
        or weights.get("agentId")
        or current_user.id
        or current_user.name
    )

    try:
        result = ml_engine.federated_aggregator.collect_update(agent_id, weights)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if result is None:
        result = {"mode": "legacy", "accepted": True, "global_model_updated": False}

    mode = result.get("mode", "legacy")
    accepted = result.get("accepted", True)

    response = {
        "status": "accepted" if accepted else "rejected",
        "mode": mode,
        "global_model_updated": bool(result.get("global_model_updated", False)),
        "details": result,
    }

    if mode == "legacy" and accepted:
        min_clients = max(1, int(weights.get("min_clients") or weights.get("minClients") or 1))
        if len(ml_engine.federated_aggregator.local_updates) >= min_clients:
            aggregate = ml_engine.federated_aggregator.aggregate()
            response["global_model_updated"] = aggregate is not None
            response["aggregate"] = aggregate

    return response


@app.post("/ml/federated/rounds/start")
def start_federated_round(payload: dict, _: models.User = Depends(auth.get_current_user)):
    min_clients = payload.get("min_clients") or payload.get("minClients")
    timeout_seconds = payload.get("timeout_seconds") or payload.get("timeoutSeconds")
    round_id = payload.get("round_id") or payload.get("roundId")

    round_state = ml_engine.federated_aggregator.start_round(
        min_clients=min_clients,
        timeout_seconds=timeout_seconds,
        round_id=round_id,
    )
    return {"status": "started", "round": round_state}


@app.get("/ml/federated/rounds/{round_id}")
def get_federated_round(round_id: str, _: models.User = Depends(auth.get_current_user)):
    round_state = ml_engine.federated_aggregator.get_round_status(round_id)
    if not round_state:
        raise HTTPException(status_code=404, detail="Round not found")
    return {"round": round_state}


@app.post("/ml/federated/reveal-mask")
def reveal_federated_mask(payload: dict, current_user: models.User = Depends(auth.get_current_user)):
    round_id = payload.get("round_id") or payload.get("roundId")
    mask = payload.get("mask")
    agent_id = str(
        payload.get("agent_id")
        or payload.get("agentId")
        or current_user.id
        or current_user.name
    )

    if not round_id:
        raise HTTPException(status_code=400, detail="round_id is required")
    if mask is None:
        raise HTTPException(status_code=400, detail="mask is required")

    try:
        result = ml_engine.federated_aggregator.reveal_mask(round_id, agent_id, mask)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    response = {
        "status": "accepted" if result.get("accepted") else "rejected",
        "global_model_updated": bool(result.get("global_model_updated", False)),
        "round": result.get("round"),
    }
    if result.get("aggregate") is not None:
        response["aggregate"] = result.get("aggregate")
    return response


@app.get("/ml/federated/global-model")
def get_federated_global_model(_: models.User = Depends(auth.get_current_user)):
    latest = ml_engine.federated_aggregator.latest_secure_global
    if not latest and os.path.exists(ml_engine.GLOBAL_MODEL_PATH):
        try:
            latest = joblib.load(ml_engine.GLOBAL_MODEL_PATH)
        except Exception:
            latest = None
    return {"global_model": latest}

# Playbook Routes
@app.get("/playbooks", response_model=List[schemas.Playbook])
def read_playbooks(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    playbooks = db.query(models.Playbook).all()
    results = []
    for p in playbooks:
        results.append({
            "id": p.id,
            "name": p.name,
            "is_active": p.is_active,
            "trigger": {
                "field": p.trigger_field,
                "operator": p.trigger_operator,
                "value": p.trigger_value
            },
            "action": {
                "type": p.action_type,
                "target": p.action_target
            },
            "min_confidence": _safe_float(p.min_confidence, 0.0),
            "requires_approval": bool(p.requires_approval),
            "rate_limit_count": _safe_int(p.rate_limit_count, 5),
            "rate_limit_window_seconds": _safe_int(p.rate_limit_window_seconds, 300),
            "scope": p.scope or "global",
        })
    return results


@app.post("/playbooks", response_model=schemas.Playbook)
def create_playbook(playbook: schemas.PlaybookCreate, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    db_playbook = models.Playbook(
        id=playbook.id,
        name=playbook.name,
        is_active=playbook.is_active,
        trigger_field=playbook.trigger.field,
        trigger_operator=playbook.trigger.operator,
        trigger_value=playbook.trigger.value,
        action_type=playbook.action.type,
        action_target=playbook.action.target,
        min_confidence=playbook.min_confidence,
        requires_approval=playbook.requires_approval,
        rate_limit_count=playbook.rate_limit_count,
        rate_limit_window_seconds=playbook.rate_limit_window_seconds,
        scope=playbook.scope,
    )
    db.add(db_playbook)
    db.commit()
    db.refresh(db_playbook)
    return {
        "id": db_playbook.id,
        "name": db_playbook.name,
        "is_active": db_playbook.is_active,
        "trigger": {
            "field": db_playbook.trigger_field,
            "operator": db_playbook.trigger_operator,
            "value": db_playbook.trigger_value
        },
        "action": {
            "type": db_playbook.action_type,
            "target": db_playbook.action_target
        },
        "min_confidence": _safe_float(db_playbook.min_confidence, 0.0),
        "requires_approval": bool(db_playbook.requires_approval),
        "rate_limit_count": _safe_int(db_playbook.rate_limit_count, 5),
        "rate_limit_window_seconds": _safe_int(db_playbook.rate_limit_window_seconds, 300),
        "scope": db_playbook.scope or "global",
    }


@app.put("/playbooks/{playbook_id}/toggle", response_model=schemas.Playbook)
def toggle_playbook(playbook_id: str, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    db_playbook = db.query(models.Playbook).filter(models.Playbook.id == playbook_id).first()
    if not db_playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    db_playbook.is_active = not db_playbook.is_active
    db.commit()
    db.refresh(db_playbook)
    return {
        "id": db_playbook.id,
        "name": db_playbook.name,
        "is_active": db_playbook.is_active,
        "trigger": {
            "field": db_playbook.trigger_field,
            "operator": db_playbook.trigger_operator,
            "value": db_playbook.trigger_value
        },
        "action": {
            "type": db_playbook.action_type,
            "target": db_playbook.action_target
        },
        "min_confidence": _safe_float(db_playbook.min_confidence, 0.0),
        "requires_approval": bool(db_playbook.requires_approval),
        "rate_limit_count": _safe_int(db_playbook.rate_limit_count, 5),
        "rate_limit_window_seconds": _safe_int(db_playbook.rate_limit_window_seconds, 300),
        "scope": db_playbook.scope or "global",
    }


@app.delete("/playbooks/{playbook_id}")
def delete_playbook(playbook_id: str, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    db_playbook = db.query(models.Playbook).filter(models.Playbook.id == playbook_id).first()
    if not db_playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    db.delete(db_playbook)
    db.commit()
    return {"ok": True}

# Settings Routes
@app.get("/settings", response_model=schemas.Settings)
def read_settings(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    settings = db.query(models.Settings).first()
    if not settings:
        # Should be seeded, but just in case
        settings = models.Settings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@app.put("/settings", response_model=schemas.Settings)
def update_settings(settings: schemas.SettingsCreate, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    db_settings = db.query(models.Settings).first()
    if not db_settings:
        db_settings = models.Settings(id=1)
        db.add(db_settings)
    
    update_data = settings.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_settings, key, value)
        
    db.commit()
    db.refresh(db_settings)
    return db_settings

@app.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_ollama(request: schemas.ChatRequest, _: models.User = Depends(auth.get_current_user)):
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    # Updated default model to qwen3:8b as requested
    MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    
    safe_message = sanitize_text(request.message, max_length=1200)
    safe_context_items = sanitize_context_items(request.context, max_items=10)
    context_str = json.dumps(safe_context_items, default=str)

    cache_key = f"chat::{safe_message}::{context_str}"
    cached = llm_response_cache.get(cache_key)
    if cached:
        return schemas.ChatResponse.model_validate(cached)
    
    prompt = f"""
    You are Sentinel AI, a cybersecurity expert.
    Context Logs: {context_str}
    User Question: {safe_message}
    
    Analyze the question and logs. Provide a helpful response and suggest actions if needed.
    
    Available Actions (type):
    - BLOCK_IP (target: IP)
    - ISOLATE_HOST (target: Hostname/ID)
    - RESET_PASSWORD (target: Username)
    
    You MUST respond with a valid JSON object using this schema:
    {{
        "text": "Your textual answer here",
        "actions": [
            {{
                "type": "BLOCK_IP",
                "label": "Block IP 1.2.3.4",
                "target": "1.2.3.4",
                "reason": "Suspicious activity"
            }}
        ]
    }}
    If no actions are needed, set "actions" to [].

    Also include this optional object when applicable:
    "llm_assessment": {{
      "risk_level": "BENIGN|SUSPICIOUS|MALICIOUS",
      "threat_type": "string",
      "confidence": 0.0,
      "reasoning": "short justification",
      "recommended_actions": ["block_ip", "isolate_host", "reset_password"]
    }}
    
    IMPORTANT: If your text response recommends taking a specific action (like blocking an IP or resetting a password), YOU MUST include that action in the 'actions' array so the user can click it.
    """
    
    try:
        async with httpx.AsyncClient() as client:
            # Check if Ollama is up
            try:
                response = await client.post(OLLAMA_URL, json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }, timeout=60.0) # Longer timeout for local inference
            except httpx.ConnectError:
                response_obj = schemas.ChatResponse(
                    role="ai",
                    text=f"[System] Failed to connect to Ollama (Local AI). Please ensure 'ollama serve' is running and '{MODEL}' model is pulled.",
                    actions=[]
                )
                llm_response_cache.set(cache_key, response_obj.model_dump())
                return response_obj

            if response.status_code != 200:
                print(f"Ollama Error: {response.text}")
                response_obj = schemas.ChatResponse(
                    role="ai",
                    text=f"Error communicating with AI Engine ({response.status_code}).",
                    actions=[]
                )
                llm_response_cache.set(cache_key, response_obj.model_dump())
                return response_obj
                
            result = response.json()
            # Ollama returns 'response' field
            ai_content = json.loads(result['response'])
            
            llm_assessment = ai_content.get("llm_assessment")
            if isinstance(llm_assessment, dict):
                parsed, _err = validate_assessment(llm_assessment)
                llm_assessment = parsed.model_dump() if parsed else None

            response_obj = schemas.ChatResponse(
                role="ai",
                text=ai_content.get('text', 'No text provided.'),
                actions=ai_content.get('actions', []),
                llm_assessment=llm_assessment,
            )
            llm_response_cache.set(cache_key, response_obj.model_dump())
            return response_obj
            
    except Exception as e:
        print(f"AI Chat Error: {e}")
        response_obj = schemas.ChatResponse(
            role="ai",
            text="[System] Internal Error processing AI request.",
            actions=[]
        )
        llm_response_cache.set(cache_key, response_obj.model_dump())
        return response_obj

@app.post("/analyze", response_model=schemas.AnalysisResult)
async def analyze_security_logs(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    # Fetch all logs for analysis
    # Limit to last 100 for performance in demo but "real" data
    logs = db.query(models.Log).order_by(models.Log.timestamp.desc()).limit(100).all()
    
    # Convert to list of dicts for pandas
    logs_data = [schemas.Log.model_validate(l).model_dump() for l in logs]
    
    # Perform heuristic analysis first (pandas)
    result = analysis.analyze_logs(logs_data)
    
    # --- Enhanced AI Analysis (Ollama) ---
    # If threat score is elevated, get a "second opinion" from AI
    if result['threat_score'] > 30:
        try:
            OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
            MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
            
            # Summarize logs for AI context
            summary_context = json.dumps(logs_data[:15], default=str) # Top 15 most recent logs
            
            prompt = f"""
            You are a senior security analyst.
            Review the following recent system logs and the preliminary heuristic analysis.
            
            Heuristic Summary: {result['summary']}
            Heuristic Threat Score: {result['threat_score']}
            
            Recent Logs:
            {summary_context}
            
            Task:
            1. Provide a more detailed executive summary based on the specific logs.
            2. Suggest 3 concrete, technical recommendations.
            
            Return strictly valid JSON:
            {{
                "ai_summary": "Detailed summary...",
                "ai_recommendations": ["Rec 1", "Rec 2", "Rec 3"]
            }}
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(OLLAMA_URL, json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }, timeout=20.0)
                
                if response.status_code == 200:
                    ai_data = json.loads(response.json()['response'])
                    
                    # Merge AI insights
                    if ai_data.get('ai_summary'):
                        result['summary'] = f"[AI ENHANCED] {ai_data['ai_summary']}"
                    
                    if ai_data.get('ai_recommendations'):
                        # Prepend AI recommendations
                        result['recommendations'] = ai_data['ai_recommendations'] + result['recommendations']

                    candidate_assessment = {
                        "risk_level": "MALICIOUS" if result.get("threat_score", 0) >= 70 else (
                            "SUSPICIOUS" if result.get("threat_score", 0) >= 30 else "BENIGN"
                        ),
                        "threat_type": "multi_event_anomaly",
                        "confidence": min(1.0, max(0.0, float(result.get("threat_score", 0)) / 100.0)),
                        "reasoning": sanitize_text(ai_data.get("ai_summary") or result.get("summary") or ""),
                        "recommended_actions": [
                            "investigate_process_tree",
                            "collect_forensics",
                        ],
                    }
                    parsed_assessment, _err = validate_assessment(candidate_assessment)
                    if parsed_assessment:
                        result["llm_assessment"] = parsed_assessment.model_dump()
                        
        except Exception as e:
            print(f"AI Enhanced Analysis Failed: {e}")
            # Fallback to heuristic result (already calculated)

    return result


@app.get("/health", response_model=schemas.HealthStatus)
def health_status(db: Session = Depends(get_db)):
    components = {
        "api": {"status": "ok", "detail": "running"},
        "database": {"status": "ok", "detail": "connected"},
        "redis": {"status": "unknown", "detail": "not checked"},
        "llm": {"status": "unknown", "detail": "not checked"},
    }

    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        components["database"] = {"status": "degraded", "detail": str(exc)}

    llm_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    if llm_url:
        components["llm"]["detail"] = llm_url

    status_value = "ok"
    if any(c["status"] == "degraded" for c in components.values()):
        status_value = "degraded"

    return {"status": status_value, "components": components}


@app.get("/ready", response_model=schemas.HealthStatus)
def readiness_status(db: Session = Depends(get_db)):
    response = health_status(db)
    status_value = response.get("status") if isinstance(response, dict) else getattr(response, "status", "degraded")
    if status_value != "ok":
        detail = response if isinstance(response, dict) else response.model_dump()
        raise HTTPException(status_code=503, detail=detail)
    return response

@app.get("/predict", response_model=schemas.PredictionResult)
def predict_next_action(current_activity: str, _: models.User = Depends(auth.get_current_user)):
    predictions = prediction_engine.predictor.predict_next_step(current_activity)
    return {
        "current_activity": current_activity,
        "predictions": predictions
    }

# Network Traffic Routes
@app.post("/traffic", response_model=schemas.NetworkTraffic)
async def create_traffic_log(traffic: schemas.NetworkTrafficCreate, db: Session = Depends(get_db)):
    traffic_data = traffic.model_dump()
    db_traffic = models.NetworkTraffic(**traffic_data)
    db.add(db_traffic)
    db.commit()
    db.refresh(db_traffic)

    # Emit to Socket.IO
    traffic_response = schemas.NetworkTraffic.model_validate(db_traffic)
    print(f"Emitting new_traffic event to {traffic_response.id}")
    await sio.emit('new_traffic', traffic_response.model_dump(by_alias=True))

    return db_traffic

@app.get("/traffic", response_model=List[schemas.NetworkTraffic])
def read_traffic(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    return db.query(models.NetworkTraffic).order_by(models.NetworkTraffic.timestamp.desc()).offset(skip).limit(limit).all()

@app.get("/traffic/analyze", response_model=schemas.NetworkAnalysisResult)
def analyze_network_traffic_endpoint(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    # Fetch recent traffic
    traffic = db.query(models.NetworkTraffic).limit(1000).all() # Limit for demo
    
    traffic_data = [schemas.NetworkTraffic.model_validate(t).model_dump() for t in traffic]
    
    result = analysis.analyze_network_traffic(traffic_data)
    return result

# --- Traffic Interception Routes ---
from interception import interceptor


@app.post("/interception/start", response_model=schemas.InterceptionStatus)
def start_interception(config: schemas.InterceptionConfig, _: models.User = Depends(auth.get_current_user)):
    try:
        interceptor.start(config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return interceptor.get_status()


@app.post("/interception/stop", response_model=schemas.InterceptionStatus)
def stop_interception(_: models.User = Depends(auth.get_current_user)):
    interceptor.stop()
    return interceptor.get_status()


@app.get("/interception/status", response_model=schemas.InterceptionStatus)
def get_interception_status(_: models.User = Depends(auth.get_current_user)):
    return interceptor.get_status()


@app.get("/interception/interfaces", response_model=List[str])
def list_interception_interfaces(_: models.User = Depends(auth.get_current_user)):
    return interceptor.get_available_interfaces()

# --- Simulation Profile Routes ---
@app.post("/simulation/profiles", response_model=schemas.SimulationProfile)
def create_simulation_profile(profile: schemas.SimulationProfileCreate, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    # Check if name exists
    if db.query(models.SimulationProfile).filter(models.SimulationProfile.name == profile.name).first():
        raise HTTPException(status_code=400, detail="Profile with this name already exists")
    
    db_profile = models.SimulationProfile(
        id=str(uuid.uuid4()),
        **profile.model_dump()
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@app.get("/simulation/profiles", response_model=List[schemas.SimulationProfile])
def read_simulation_profiles(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    return db.query(models.SimulationProfile).all()

@app.delete("/simulation/profiles/{profile_id}")
def delete_simulation_profile(profile_id: str, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    db_profile = db.query(models.SimulationProfile).filter(models.SimulationProfile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    db.delete(db_profile)
    db.commit()
    return {"ok": True}

# --- System Monitor Routes ---
@app.get("/api/system-metrics", response_model=schemas.SystemMetrics)
def get_system_metrics(_: models.User = Depends(auth.get_current_user)):
    return system_monitor.get_system_metrics()

@app.get("/api/system-metrics/history", response_model=List[schemas.SystemMetrics])
def get_system_metrics_history(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    return system_monitor.get_history(db)

# --- Reporting Routes ---
@app.get("/api/reports/export")
def export_data(format: str = "csv", compress: bool = False, start_date: str = None, end_date: str = None, db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    query = db.query(models.Log)
    
    if start_date:
        query = query.filter(models.Log.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Log.timestamp <= end_date)
        
    logs = query.all()
    return reporting.export_logs(logs, format, compress)

@app.post("/api/notifications/test")
def test_notification(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    settings = db.query(models.Settings).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return notifications.test_notification(settings)

# --- Agent Management Routes ---
@app.get("/agent/status")
def get_agent_status(_: models.User = Depends(auth.get_current_user)):
    return agent_manager.agent_manager.get_status()

@app.post("/agent/start")
def start_agent(_: models.User = Depends(auth.get_current_user)):
    return agent_manager.agent_manager.start_agent()

@app.post("/agent/stop")
def stop_agent(_: models.User = Depends(auth.get_current_user)):
    return agent_manager.agent_manager.stop_agent()

# --- SOAR Actions ---
@app.post("/actions/block-ip", response_model=schemas.ActionResponse)
async def block_ip(action: schemas.ActionRequest, db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    # Simulate IP Blocking
    print(f"ACTION: Blocking IP {action.target} by {user.name}")
    
    # Log the action
    log = models.Log(
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        user=user.name,
        activity_type="SOAR_ACTION",
        risk_level="INFO",
        description=f"Blocked IP Address: {action.target}",
        details=f"Reason: {action.reason or 'Manual Action'}",
        ip_address=action.target,
        location="Internal"
    )
    db.add(log)
    db.commit()
    
    await sio.emit('new_log', schemas.Log.model_validate(log).model_dump(by_alias=True))
    
    return {
        "success": True,
        "message": f"IP {action.target} has been successfully blocked.",
        "action_id": log.id
    }

@app.post("/actions/isolate-host", response_model=schemas.ActionResponse)
async def isolate_host(action: schemas.ActionRequest, db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    # Simulate Host Isolation
    print(f"ACTION: Isolating Host {action.target} by {user.name}")
    
    log = models.Log(
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        user=user.name,
        activity_type="SOAR_ACTION",
        risk_level="HIGH",
        description=f"Isolated Host: {action.target}",
        details=f"Reason: {action.reason or 'Manual Action'}",
        location="Internal"
    )
    db.add(log)
    db.commit()
    
    await sio.emit('new_log', schemas.Log.model_validate(log).model_dump(by_alias=True))
    
    return {
        "success": True,
        "message": f"Host {action.target} has been isolated from the network.",
        "action_id": log.id
    }

@app.post("/actions/reset-password", response_model=schemas.ActionResponse)
async def reset_password(action: schemas.ActionRequest, db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    # In a real app, this would reset the user's password.
    # For now, we simulate the action.
    target_user = db.query(models.User).filter(models.User.name == action.target).first()
    if not target_user:
         # Try by ID
         target_user = db.query(models.User).filter(models.User.id == action.target).first()
    
    if target_user:
        # Reset to default 'password123' or generate random
        new_pass = "TemporaryPass123!"
        target_user.hashed_password = auth.get_password_hash(new_pass)
        db.commit()
        msg = f"Password for {target_user.name} reset to {new_pass}"
    else:
        msg = f"User {action.target} not found, but action logged."

    print(f"ACTION: Reset Password for {action.target} by {user.name}")
    
    log = models.Log(
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        user=user.name,
        activity_type="SOAR_ACTION",
        risk_level="MEDIUM",
        description=f"Reset Password for User: {action.target}",
        details=f"Reason: {action.reason or 'Manual Action'}",
        location="Internal"
    )
    db.add(log)
    db.commit()
    
    await sio.emit('new_log', schemas.Log.model_validate(log).model_dump(by_alias=True))
    
    return {
        "success": True,
        "message": msg,
        "action_id": log.id
    }

# Wrap FastAPI with Socket.IO
fastapi_app = app
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
