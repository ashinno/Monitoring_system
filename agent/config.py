import os

class Config:
    BASE_URL = os.getenv("SERVER_URL", "http://localhost:8000")
    USERNAME = os.getenv("AGENT_USER", "admin")
    PASSWORD = os.getenv("AGENT_PASSWORD", "admin")
    # In a real scenario, the encryption key should be securely provisioned.
    # For this thesis/demo, we can hardcode or use env.
    # 32 bytes for AES-256
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef") 
    
    # Flush interval in seconds
    FLUSH_INTERVAL = 2
    # Batch size for logs
    BATCH_SIZE = 50
