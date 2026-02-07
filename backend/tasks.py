from celery_app import celery_app
from database import SessionLocal
import models
import soar_engine
import prediction_engine
import asyncio

@celery_app.task
def run_soar_automation(log_id: str):
    """
    Background task to execute SOAR playbooks.
    """
    try:
        soar_engine.engine.run_automation(log_id)
    except Exception as e:
        print(f"Error in SOAR task for log {log_id}: {e}")

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
