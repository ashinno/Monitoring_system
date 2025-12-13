import sys
import os
import uuid
import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import database
from soar_engine import SOAREngine

class TestSOARAutomation(unittest.TestCase):
    def setUp(self):
        # Setup in-memory database
        self.engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        
        # Patch database.SessionLocal to use our test database
        self.patcher = patch('database.SessionLocal', return_value=self.db)
        self.mock_session_local = self.patcher.start()
        
        # Initialize SOAR Engine
        self.soar_engine = SOAREngine()

    def tearDown(self):
        self.patcher.stop()
        self.db.close()

    def test_end_to_end_automation(self):
        print("\n--- Starting End-to-End SOAR Automation Test ---")

        # 1. Create a User
        user_id = str(uuid.uuid4())
        user = models.User(
            id=user_id,
            name="test_victim",
            role="User",
            status="ACTIVE",
            hashed_password="hash"
        )
        self.db.add(user)
        self.db.commit()
        print(f"Created user: {user.name} with status: {user.status}")

        # 2. Create a Playbook
        playbook_id = str(uuid.uuid4())
        playbook = models.Playbook(
            id=playbook_id,
            name="Critical Risk Lockout",
            is_active=True,
            trigger_field="riskLevel",
            trigger_operator="equals",
            trigger_value="CRITICAL",
            action_type="LOCK_USER"
        )
        self.db.add(playbook)
        self.db.commit()
        print(f"Created playbook: {playbook.name} (Trigger: {playbook.trigger_field} == {playbook.trigger_value} -> {playbook.action_type})")

        # 3. Create a Log that triggers the playbook
        log_id = str(uuid.uuid4())
        log = models.Log(
            id=log_id,
            user="test_victim",
            activity_type="Unusual Login",
            risk_level="CRITICAL",
            description="Login from unknown location"
        )
        self.db.add(log)
        self.db.commit()
        print(f"Created log: {log.id} with risk_level: {log.risk_level}")

        # 4. Run Automation
        print("Running SOAR Automation...")
        self.soar_engine.run_automation(log_id)

        # 5. Verify User Status
        updated_user = self.db.query(models.User).filter(models.User.name == "test_victim").first()
        print(f"User status after automation: {updated_user.status}")
        
        self.assertEqual(updated_user.status, "LOCKED", "User should be LOCKED by the playbook")

        # 6. Verify System Log
        soar_log = self.db.query(models.Log).filter(models.Log.user == "SOAR_ENGINE").first()
        self.assertIsNotNone(soar_log, "SOAR Engine should create a log entry")
        print(f"SOAR Log found: {soar_log.description} - {soar_log.details}")
        
        print("--- Test Passed Successfully ---")

if __name__ == '__main__':
    unittest.main()
