import uuid
from datetime import datetime
from sqlalchemy.orm import Session
import models
import schemas
import database
import notifications
import traceback

class SOAREngine:
    """
    Security Orchestration, Automation, and Response (SOAR) Engine.
    Handles automated responses to security events based on defined Playbooks.
    
    Features:
    - Platform-agnostic execution
    - Robust error handling
    - Graceful degradation
    """

    def __init__(self):
        pass

    def run_automation(self, log_id: str):
        """
        Entry point for background automation.
        Creates a fresh DB session to ensure thread safety and data integrity.
        """
        db = database.SessionLocal()
        try:
            log = db.query(models.Log).filter(models.Log.id == log_id).first()
            if not log:
                print(f"[SOAR] Log {log_id} not found. Skipping.")
                return

            self._evaluate_rules(log, db)
        except Exception as e:
            print(f"[SOAR] Critical Engine Error: {e}")
            traceback.print_exc()
        finally:
            db.close()

    def _evaluate_rules(self, log: models.Log, db: Session):
        """
        Evaluates the log against all active playbooks.
        """
        playbooks = db.query(models.Playbook).filter(models.Playbook.is_active == True).all()
        
        for playbook in playbooks:
            try:
                if self._check_trigger(playbook, log):
                    print(f"[SOAR] Playbook '{playbook.name}' triggered by Log {log.id}")
                    self._execute_action(playbook, log, db)
            except Exception as e:
                print(f"[SOAR] Error processing playbook '{playbook.name}': {e}")
                # Continue to next playbook - Graceful degradation

    def _check_trigger(self, playbook: models.Playbook, log: models.Log) -> bool:
        """
        Checks if the log matches the playbook trigger conditions.
        """
        # Get field value dynamically
        field_name = playbook.trigger_field
        
        # Handle mapped fields or direct attributes
        # e.g. "riskLevel" -> "risk_level"
        if field_name == "riskLevel":
            log_value = log.risk_level
        elif field_name == "activityType":
            log_value = log.activity_type
        elif field_name == "description":
            log_value = log.description
        else:
            # Try direct attribute access
            log_value = getattr(log, field_name, None)

        if log_value is None:
            return False

        # Normalize for comparison
        log_value = str(log_value).upper()
        trigger_value = str(playbook.trigger_value).upper()
        operator = playbook.trigger_operator

        if operator == "equals":
            return log_value == trigger_value
        elif operator == "contains":
            return trigger_value in log_value
        
        return False

    def _execute_action(self, playbook: models.Playbook, log: models.Log, db: Session):
        """
        Executes the defined action.
        """
        action_type = playbook.action_type
        
        try:
            if action_type == "LOCK_USER":
                self._action_lock_user(log.user, playbook, db)
            elif action_type == "QUARANTINE_USER":
                self._action_quarantine_user(log.user, playbook, db)
            elif action_type == "ALERT_ADMIN":
                self._action_alert_admin(log, playbook, db)
            else:
                print(f"[SOAR] Unknown action type: {action_type}")

        except Exception as e:
            print(f"[SOAR] Action execution failed: {e}")
            self._log_system_event(
                db, 
                "SOAR_ERROR", 
                "CRITICAL", 
                f"Failed to execute action '{action_type}' for playbook '{playbook.name}'",
                str(e)
            )

    def _action_lock_user(self, username: str, playbook: models.Playbook, db: Session):
        """
        Locks the user account. Platform-agnostic (DB level).
        """
        user = db.query(models.User).filter(models.User.name == username).first()
        if user:
            if user.status != "LOCKED":
                user.status = "LOCKED"
                db.commit()
                print(f"[SOAR] User {username} LOCKED by playbook.")
                
                self._log_system_event(
                    db,
                    "SOAR_ACTION",
                    "INFO",
                    f"User {username} account LOCKED",
                    f"Triggered by playbook: {playbook.name}"
                )
        else:
            print(f"[SOAR] Target user {username} not found for locking.")

    def _action_quarantine_user(self, username: str, playbook: models.Playbook, db: Session):
        """
        Quarantines the user (Restricted Access).
        """
        user = db.query(models.User).filter(models.User.name == username).first()
        if user:
            if user.status != "QUARANTINED":
                user.status = "QUARANTINED"
                # Remove permissions potentially? For now just status.
                db.commit()
                print(f"[SOAR] User {username} QUARANTINED by playbook.")
                
                self._log_system_event(
                    db,
                    "SOAR_ACTION",
                    "INFO",
                    f"User {username} account QUARANTINED",
                    f"Triggered by playbook: {playbook.name}"
                )
        else:
            print(f"[SOAR] Target user {username} not found for quarantine.")

    def _action_alert_admin(self, log: models.Log, playbook: models.Playbook, db: Session):
        """
        Generates a high priority alert.
        """
        # 1. Create a System Log for the alert
        self._log_system_event(
            db,
            "HIGH_PRIORITY_ALERT",
            "CRITICAL",
            f"Alert: {playbook.name}",
            f"Triggered by activity from {log.user}: {log.description}"
        )
        
        # 2. Try to send external notification (Email/SMS) if configured
        # Using the existing notifications module
        settings = db.query(models.Settings).first()
        if settings:
            try:
                notifications.send_alert(log, settings)
            except Exception as e:
                print(f"[SOAR] Failed to send external notification: {e}")

    def _log_system_event(self, db: Session, activity_type: str, risk: str, desc: str, details: str):
        """
        Helper to create a log entry for SOAR actions.
        """
        try:
            log = models.Log(
                id=str(uuid.uuid4()),
                timestamp=datetime.now().isoformat(),
                user="SOAR_ENGINE",
                activity_type=activity_type,
                risk_level=risk,
                description=desc,
                details=details,
                location="Internal"
            )
            db.add(log)
            db.commit()
            
            # Note: We cannot emit to socket.io easily from a synchronous background thread 
            # without an async loop reference. 
            # In a real production app, we might use a queue or redis for this.
            # For this simplified app, the frontend polls or the 'new_log' event won't be sent immediately 
            # for SOAR actions generated in background tasks unless we hook into the main loop.
            # However, since the user sees the *result* (Locked status), it might be fine.
            # Or we can try to fire-and-forget an async call if we had the loop.
            
        except Exception as e:
            print(f"[SOAR] Failed to log system event: {e}")

# Global Instance
engine = SOAREngine()
