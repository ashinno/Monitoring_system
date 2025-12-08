from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from contextlib import asynccontextmanager
import socketio
import uvicorn
import asyncio
import os
import uuid
import httpx
import json
from datetime import datetime, timedelta

import models, schemas, auth, analysis, database, ml_engine, prediction_engine, system_monitor, reporting, notifications
import agent_manager

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
            settings = db.query(models.Settings).first()
            if settings and settings.capture_screenshots:
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = database.SessionLocal()
    try:
        if not db.query(models.User).first():
            print("Seeding database with default users...")
            # Admin
            admin = models.User(
                id="admin",
                name="Admin User",
                role="Administrator",
                clearance_level="ADMIN",
                status="ACTIVE",
                permissions=["READ_LOGS", "EDIT_SETTINGS", "MANAGE_USERS", "EXPORT_DATA"],
                hashed_password=auth.get_password_hash("admin"),
                avatar_seed="admin"
            )
            # Analyst
            analyst = models.User(
                id="analyst",
                name="Alice Williams",
                role="Security Analyst",
                clearance_level="L2",
                status="ACTIVE",
                permissions=["READ_LOGS", "EXPORT_DATA"],
                hashed_password=auth.get_password_hash("password"),
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
            settings = models.Settings(
                id=1,
                block_gambling=True,
                block_social_media=False,
                enforce_safe_search=True,
                screen_time_limit=True,
                alert_on_keywords=True,
                capture_screenshots=False,
                keywords=["password", "confidential", "secret", "key"]
            )
            db.add(settings)
            db.commit()
            
    finally:
        db.close()
    
    # Start screenshot task
    # Trigger reload
    asyncio.create_task(screenshot_loop())
    asyncio.create_task(metrics_loop())
    
    # Train Prediction Engine
    print("Training Prediction Engine...")
    prediction_engine.predictor.train(db)

    yield

app = FastAPI(title="Sentinel AI Backend", lifespan=lifespan)

# Mount screenshots directory
app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

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

@app.post("/logs", response_model=schemas.Log)
async def create_log(log: schemas.LogCreate, db: Session = Depends(get_db)):
    # Save to DB
    log_data = log.model_dump()
    
    # Check Settings for policy enforcement
    settings = db.query(models.Settings).first()
    if settings:
        desc = log_data.get('description', '').lower()
        details = log_data.get('details', '').lower()
        
        # Keyword Alert
        if settings.alert_on_keywords:
            keywords = [k.lower() for k in (settings.keywords or [])]
            if any(k in desc for k in keywords) or any(k in details for k in keywords):
                 if log_data.get('risk_level') not in ['HIGH', 'CRITICAL']:
                    log_data['risk_level'] = 'HIGH'
                    log_data['description'] = log_data['description'] + " [KEYWORD DETECTED]"

        # Gambling Block
        if settings.block_gambling:
            gambling_terms = ["casino", "bet", "poker", "gambling", "lottery"]
            if any(k in desc for k in gambling_terms) or any(k in details for k in gambling_terms):
                log_data['risk_level'] = 'CRITICAL'
                log_data['description'] = log_data['description'] + " [POLICY VIOLATION: GAMBLING]"

        # Social Media Block
        if settings.block_social_media:
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

    # Notifications
    if settings and (log_data.get('risk_level') in ['HIGH', 'CRITICAL']):
        notifications.send_alert(db_log, settings)
    
    # --- Real-time Heatmap ---
    if log_data.get('activity_type') == 'KEYLOG' and log_data.get('activity_summary'):
        try:
            # Parse the summary JSON (counts)
            import json
            counts = json.loads(log_data['activity_summary'])
            # Emit dedicated event
            await sio.emit('key_heatmap_update', counts)
        except Exception as e:
            print(f"Failed to emit heatmap: {e}")

    # --- Prediction Integration ---
    try:
        current_activity = log_data.get('activity_type')
        if current_activity:
            # Hybrid Prediction: Try AI first, fallback to Markov if slow/fails or for comparison
            # For real-time performance, we might race them or prioritize one.
            # Here we will try AI if risk is HIGH+, otherwise standard Markov.
            
            next_steps = []
            if log_data.get('risk_level') in ['HIGH', 'CRITICAL']:
                 print(f"High Risk Activity detected ({current_activity}). Invoking AI Prediction...")
                 next_steps = await prediction_engine.predictor.predict_next_step_ai(current_activity)
            
            if not next_steps:
                # Fallback or standard
                next_steps = prediction_engine.predictor.predict_next_step(current_activity)
            
            # Check for High Risk Predictions
            for step in next_steps:
                # AI usually returns 'activity', Markov returns 'activity'
                act = step.get('activity', 'Unknown')
                prob = step.get('probability', 0.0)
                
                if prob >= 0.7: # Threshold
                    print(f"PRE-EMPTIVE WARNING: High probability of {act}!")
                    await sio.emit('security_alert', {
                        "type": "PREDICTIVE_THREAT",
                        "message": f"High probability of {act} detected.",
                        "details": f"Following {current_activity}, there is a {prob*100:.1f}% chance of {act}. Reason: {step.get('reason', 'Pattern Analysis')}",
                        "timestamp": datetime.now().isoformat()
                    })

            # Emit prediction update
            await sio.emit('prediction_update', {
                "currentActivity": current_activity,
                "predictions": next_steps
            })
    except Exception as e:
        print(f"Prediction Error: {e}")

    return db_log

@app.post("/ml/train")
def train_anomaly_model(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    logs = db.query(models.Log).all()
    ml_engine.train_model(logs)
    return {"message": "Model training triggered"}

# Playbook Routes
@app.get("/playbooks", response_model=List[schemas.Playbook])
def read_playbooks(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    playbooks = db.query(models.Playbook).all()
    # Map flat DB to nested Schema
    # The Pydantic model expects nested trigger/action.
    # We can do this manually or let Pydantic from_attributes try?
    # We added @property to models.py? No I decided to do it in schema or manual.
    # I didn't add properties to models.py. So I must construct them.
    
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
            }
        })
    return results

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
    
    # Serialize context safely
    try:
        context_str = json.dumps(request.context[:10], default=str)
    except:
        context_str = "[]"
    
    prompt = f"""
    You are Sentinel AI, a cybersecurity expert.
    Context Logs: {context_str}
    User Question: {request.message}
    
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
                 return schemas.ChatResponse(
                    role="ai",
                    text=f"[System] Failed to connect to Ollama (Local AI). Please ensure 'ollama serve' is running and '{MODEL}' model is pulled.",
                    actions=[]
                )

            if response.status_code != 200:
                print(f"Ollama Error: {response.text}")
                return schemas.ChatResponse(
                    role="ai",
                    text=f"Error communicating with AI Engine ({response.status_code}).",
                    actions=[]
                )
                
            result = response.json()
            # Ollama returns 'response' field
            ai_content = json.loads(result['response'])
            
            return schemas.ChatResponse(
                role="ai",
                text=ai_content.get('text', 'No text provided.'),
                actions=ai_content.get('actions', [])
            )
            
    except Exception as e:
        print(f"AI Chat Error: {e}")
        return schemas.ChatResponse(
            role="ai",
            text="[System] Internal Error processing AI request.",
            actions=[]
        )

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
                        
        except Exception as e:
            print(f"AI Enhanced Analysis Failed: {e}")
            # Fallback to heuristic result (already calculated)

    return result

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

# --- Simulation Routes ---
from simulation import simulator

@app.post("/simulation/start", response_model=schemas.SimulationStatus)
def start_simulation(config: schemas.SimulationConfig, _: models.User = Depends(auth.get_current_user)):
    simulator.start(config)
    return simulator.get_status()

@app.post("/simulation/stop", response_model=schemas.SimulationStatus)
def stop_simulation(_: models.User = Depends(auth.get_current_user)):
    simulator.stop()
    return simulator.get_status()

@app.get("/simulation/status", response_model=schemas.SimulationStatus)
def get_simulation_status(_: models.User = Depends(auth.get_current_user)):
    return simulator.get_status()

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
app = socketio.ASGIApp(sio, other_asgi_app=app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
