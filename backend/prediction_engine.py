from collections import defaultdict, Counter
from sqlalchemy.orm import Session
import models
from typing import List, Dict, Any
import os
import httpx
import asyncio
import json
import time

# LLM Model Configuration with Quantization Support
# Thesis Claim: 4-bit quantized models for balance of latency/accuracy
LLM_MODEL_CONFIGS = {
    "qwen3:8b": {
        "display_name": "Qwen 3 8B (Full)",
        "quantization": None,
        "bits": 64,
        "description": "Full precision Qwen 3 8B model"
    },
    "qwen3:8b-q4_K_M": {
        "display_name": "Qwen 3 8B (4-bit)",
        "quantization": "q4_K_M",
        "bits": 4,
        "description": "4-bit quantized for reduced latency"
    },
    "qwen3:8b-q5_K_M": {
        "display_name": "Qwen 3 8B (5-bit)",
        "quantization": "q5_K_M",
        "bits": 5,
        "description": "5-bit quantized for better accuracy"
    },
    "qwen3:4b": {
        "display_name": "Qwen 3 4B",
        "quantization": None,
        "bits": 32,
        "description": "Smaller 4B model for faster inference"
    },
    "qwen3:4b-q4_K_M": {
        "display_name": "Qwen 3 4B (4-bit)",
        "quantization": "q4_K_M",
        "bits": 4,
        "description": "4-bit quantized smaller model"
    },
    "mistral:7b": {
        "display_name": "Mistral 7B",
        "quantization": None,
        "bits": 32,
        "description": "Mistral 7B baseline"
    },
    "mistral:7b-q4_0": {
        "display_name": "Mistral 7B (4-bit)",
        "quantization": "q4_0",
        "bits": 4,
        "description": "4-bit quantized Mistral"
    }
}

def get_llm_config(model_name: str = None) -> Dict[str, Any]:
    """Get LLM configuration by model name."""
    model_name = model_name or os.getenv("OLLAMA_MODEL", "qwen3:8b")
    return LLM_MODEL_CONFIGS.get(model_name, LLM_MODEL_CONFIGS["qwen3:8b"])

def list_available_models() -> List[Dict[str, Any]]:
    """List all available model configurations."""
    return [
        {"id": k, **v}
        for k, v in LLM_MODEL_CONFIGS.items()
    ]

class LLMQuantizationBenchmark:
    """Benchmark different quantization levels for thesis latency evaluation."""

    def __init__(self):
        self.results = []

    async def benchmark_model(self, model_name: str, num_requests: int = 10) -> Dict[str, Any]:
        """Benchmark a specific model's latency."""
        config = get_llm_config(model_name)
        latencies = []

        OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

        test_prompt = "Analyze this security event: User failed login attempt."

        for _ in range(num_requests):
            try:
                start = time.perf_counter()
                async with httpx.AsyncClient(trust_env=False) as client:
                    response = await client.post(
                        OLLAMA_URL,
                        json={
                            "model": model_name,
                            "prompt": test_prompt,
                            "stream": False,
                        },
                        timeout=30.0
                    )
                    latency = (time.perf_counter() - start) * 1000  # ms
                    latencies.append(latency)
            except Exception as e:
                print(f"Error benchmarking {model_name}: {e}")

        if latencies:
            return {
                "model": model_name,
                "config": config,
                "avg_latency_ms": sum(latencies) / len(latencies),
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "successful_requests": len(latencies)
            }
        return None

    async def run_benchmark(self) -> List[Dict[str, Any]]:
        """Run benchmark on all configured models."""
        print("Running LLM Quantization Benchmark...")

        tasks = []
        for model_name in LLM_MODEL_CONFIGS.keys():
            task = self.benchmark_model(model_name)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        self.results = [r for r in results if r is not None]

        return self.results

    def get_recommended_model(self) -> str:
        """Get recommended model based on latency/accuracy tradeoff."""
        if not self.results:
            return "qwen3:8b"

        # Find model with best balance (prefer 4-bit if close)
        for r in sorted(self.results, key=lambda x: x["avg_latency_ms"]):
            if r["avg_latency_ms"] < 2000:  # Under 2 seconds
                return r["model"]

        return "qwen3:8b"

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

    async def predict_next_step_ai(self, current_activity: str) -> List[Dict[str, Any]]:
        """
        Uses Ollama AI to predict the next likely security event/action based on context.
        Enhanced for Thesis with Few-Shot prompting and Persona.
        """
        OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
        
        prompt = f"""
        You are a Predictive Security Engine modeled on the MITRE ATT&CK Framework.
        
        Your Task:
        Analyze the 'Current User Activity' and predict the 3 most likely NEXT steps a malicious insider might take.
        
        Examples:
        - Input: "User ran 'whoami' and 'net user' commands"
          Output: [{{"activity": "Privilege Escalation attempt", "probability": 0.9, "reason": "Reconnaissance commands often precede escalation."}}]
        - Input: "User accessed 'payroll.xls' at 2 AM"
          Output: [{{"activity": "Data Exfiltration", "probability": 0.85, "reason": "Accessing sensitive files off-hours is highly suspicious."}}]
          
        Current User Activity: "{current_activity}"
        
        Return strictly valid JSON format:
        [
            {{"activity": "Name of Predicted Action", "probability": 0.0-1.0, "reason": "Technical justification based on security principles"}}
        ]
        """
        
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                response = await client.post(OLLAMA_URL, json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }, timeout=10.0)
                
                if response.status_code == 200:
                    result = response.json()
                    predictions = json.loads(result['response'])
                    # Normalize keys if needed
                    return predictions
        except Exception as e:
            print(f"AI Prediction Error: {e}")
            return []
        
        return []

    def predict_next_step(self, current_activity: str) -> List[Dict[str, Any]]:
        """
        Predicts the top 3 most likely next actions based on the current activity using Markov Chain.
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
                "probability": prob,
                "reason": "Based on historical frequency"
            })
        
        # Sort by probability desc
        probabilities.sort(key=lambda x: x["probability"], reverse=True)
        
        return probabilities[:3]

# Global instance
predictor = MarkovPredictor()
