from celery_app import celery_app
from database import SessionLocal
import models
import soar_engine
import prediction_engine
from datetime import datetime
import json
import asyncio

# Helper to run async code in sync Celery worker
def run_async(coro):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Should not happen in standard Celery worker, but if it does:
        return loop.run_until_complete(coro)
    else:
        return asyncio.run(coro)

@celery_app.task
def run_soar_automation(log_id: str):
    """
    Background task to execute SOAR playbooks.
    """
    db = SessionLocal()
    try:
        # We re-fetch the log to ensure we have the latest state
        log = db.query(models.Log).filter(models.Log.id == log_id).first()
        if log:
            # soar_engine.engine.run_automation is async? 
            # Looking at main.py: background_tasks.add_task(soar_engine.engine.run_automation, db_log.id)
            # We need to check if soar_engine is async. 
            # Assuming it is, we need to run it synchronously here or use celery's async support (which is tricky).
            # Better to use the async helper or refactor SOAR to be sync-compatible.
            
            # For now, let's assume we wrap it.
            # But wait, run_automation likely uses DB async? No, usually SQLAlchemy sync session.
            # Let's import it and check. If it's `async def`, we use `asyncio.run`.
            
            asyncio.run(soar_engine.engine.run_automation(log_id))
            
    except Exception as e:
        print(f"Error in SOAR task for log {log_id}: {e}")
    finally:
        db.close()

@celery_app.task
def run_prediction_analysis(log_id: str):
    """
    Background task to run heavy AI prediction (LLM).
    """
    db = SessionLocal()
    try:
        log = db.query(models.Log).filter(models.Log.id == log_id).first()
        if not log:
            return

        current_activity = log.activity_type
        if log.risk_level in ['HIGH', 'CRITICAL']:
            # This calls the LLM which is slow
            asyncio.run(prediction_engine.predictor.predict_next_step_ai(current_activity))
            
    except Exception as e:
        print(f"Error in Prediction task for log {log_id}: {e}")
    finally:
        db.close()
