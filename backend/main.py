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
from datetime import datetime

import models, schemas, auth, analysis, database, ml_engine
from database import engine

# Create tables
models.Base.metadata.create_all(bind=engine)

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
                    log = models.Log(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now().isoformat(),
                        user="SYSTEM",
                        activity_type="SCREENSHOT",
                        risk_level="INFO",
                        description="Periodic Screenshot Captured",
                        details=f"/screenshots/{filename}",
                        ip_address="127.0.0.1",
                        location="Local"
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
    asyncio.create_task(screenshot_loop())
    
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

@app.post("/analyze", response_model=schemas.AnalysisResult)
def analyze_security_logs(db: Session = Depends(get_db), _: models.User = Depends(auth.get_current_user)):
    # Fetch all logs for analysis
    # In production, might limit to last 24h or similar
    logs = db.query(models.Log).all()
    
    # Convert to list of dicts for pandas
    # We want camelCase keys to match what analysis.py logic might expect (or update analysis.py)
    # analysis.py handles snake_case now (I updated it).
    logs_data = [l.__dict__ for l in logs] 
    # __dict__ includes sqlalchemy internal state, better to use Pydantic
    logs_data = [schemas.Log.model_validate(l).model_dump() for l in logs]
    
    result = analysis.analyze_logs(logs_data)
    return result

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

# Wrap FastAPI with Socket.IO
app = socketio.ASGIApp(sio, other_asgi_app=app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
