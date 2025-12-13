import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soar_engine import SOAREngine
import models

class TestSOAREngine(unittest.TestCase):
    def setUp(self):
        self.engine = SOAREngine()
        self.mock_db = MagicMock()

    def test_check_trigger_equals(self):
        # Setup Playbook
        playbook = models.Playbook(
            trigger_field="riskLevel",
            trigger_operator="equals",
            trigger_value="CRITICAL"
        )
        
        # Setup Log
        log_match = models.Log(risk_level="CRITICAL")
        log_no_match = models.Log(risk_level="INFO")
        
        # Test
        self.assertTrue(self.engine._check_trigger(playbook, log_match))
        self.assertFalse(self.engine._check_trigger(playbook, log_no_match))

    def test_check_trigger_contains(self):
        playbook = models.Playbook(
            trigger_field="description",
            trigger_operator="contains",
            trigger_value="failed"
        )
        
        log_match = models.Log(description="Login failed multiple times")
        log_no_match = models.Log(description="Login successful")
        
        self.assertTrue(self.engine._check_trigger(playbook, log_match))
        self.assertFalse(self.engine._check_trigger(playbook, log_no_match))

    @patch('soar_engine.SOAREngine._action_lock_user')
    def test_execute_action_lock_user(self, mock_lock):
        playbook = models.Playbook(
            name="Test Rule",
            action_type="LOCK_USER"
        )
        log = models.Log(user="bad_actor", id="123")
        
        self.engine._execute_action(playbook, log, self.mock_db)
        
        mock_lock.assert_called_once_with("bad_actor", playbook, self.mock_db)

    def test_action_lock_user_implementation(self):
        # Mock DB Query for User
        mock_user = models.User(name="bad_actor", status="ACTIVE")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        playbook = models.Playbook(name="Test Rule")
        
        # Patch _log_system_event to avoid side effects (second commit)
        with patch.object(self.engine, '_log_system_event') as mock_log:
            self.engine._action_lock_user("bad_actor", playbook, self.mock_db)
        
        # Verify Status Changed
        self.assertEqual(mock_user.status, "LOCKED")
        # Verify Commit Called (at least once)
        self.mock_db.commit.assert_called()

    @patch('database.SessionLocal')
    def test_error_handling(self, mock_session_local):
        # Ensure exception doesn't crash the engine
        
        # Mock Session
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock query to raise exception
        mock_db.query.side_effect = Exception("DB Connection Failed")
        
        try:
            self.engine.run_automation("123")
        except Exception:
            self.fail("run_automation raised Exception unexpectedly")
        
        # Verify db was closed
        mock_db.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
