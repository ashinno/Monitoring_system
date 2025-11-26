from collections import defaultdict, Counter
from sqlalchemy.orm import Session
import models
from typing import List, Dict, Any

class MarkovPredictor:
    def __init__(self):
        self.transition_matrix = defaultdict(Counter)
        self.is_trained = False

    def train(self, db: Session):
        """
        Trains the transition matrix based on historical logs in the database.
        """
        print("Training Markov Chain Predictor...")
        logs = db.query(models.Log).order_by(models.Log.user, models.Log.timestamp).all()
        
        if not logs:
            print("No logs found for training.")
            self.is_trained = True
            return

        # Group logs by user to follow their specific sequences
        user_logs = defaultdict(list)
        for log in logs:
            # We assume activity_type is the state
            if log.activity_type:
                user_logs[log.user].append(log.activity_type)
        
        # Reset matrix
        self.transition_matrix = defaultdict(Counter)

        for user, activities in user_logs.items():
            if len(activities) < 2:
                continue
            for i in range(len(activities) - 1):
                current_act = activities[i]
                next_act = activities[i+1]
                self.transition_matrix[current_act][next_act] += 1
        
        self.is_trained = True
        print(f"Markov Chain Predictor trained on {len(logs)} logs.")

    def predict_next_step(self, current_activity: str) -> List[Dict[str, Any]]:
        """
        Predicts the top 3 most likely next actions based on the current activity.
        """
        if not self.is_trained:
            # If not trained, return empty or default? 
            # Ideally should verify if training is needed, but for now assuming it's called after train.
            return []

        if current_activity not in self.transition_matrix:
            return []
        
        next_activities = self.transition_matrix[current_activity]
        total_count = sum(next_activities.values())
        
        probabilities = []
        for activity, count in next_activities.items():
            prob = count / total_count
            probabilities.append({
                "activity": activity,
                "probability": prob
            })
        
        # Sort by probability desc
        probabilities.sort(key=lambda x: x["probability"], reverse=True)
        
        return probabilities[:3]

# Global instance
predictor = MarkovPredictor()
