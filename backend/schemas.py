from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional, Any, Dict
from datetime import datetime

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        from_attributes=True
    )

# --- User Schemas ---
class UserBase(BaseSchema):
    id: str
    name: str
    role: str
    clearance_level: str
    status: str
    permissions: List[str]
    avatar_seed: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    pass

class UserLogin(BaseSchema):
    username: str
    password: str

# --- Log Schemas ---
class LogBase(BaseSchema):
    id: str
    timestamp: str
    user: str
    activity_type: str
    risk_level: str
    description: str
    details: str
    ip_address: Optional[str] = None
    location: Optional[str] = None

class LogCreate(LogBase):
    pass

class Log(LogBase):
    pass

# --- Playbook Schemas ---
# Helper models for nested structure
class PlaybookTrigger(BaseSchema):
    field: str
    operator: str
    value: str

class PlaybookAction(BaseSchema):
    type: str
    target: Optional[str] = None

class PlaybookBase(BaseSchema):
    id: str
    name: str
    is_active: bool
    trigger: PlaybookTrigger
    action: PlaybookAction

class PlaybookCreate(PlaybookBase):
    pass

class Playbook(PlaybookBase):
    pass

# --- Analysis Schemas ---
class AnalysisResult(BaseSchema):
    summary: str
    threat_score: float
    recommendations: List[str]
    flagged_logs: List[str]
    explanations: Optional[Dict[str, Dict[str, float]]] = None

# --- Token Schema ---
class Token(BaseSchema):
    access_token: str
    token_type: str

class TokenData(BaseSchema):
    username: Optional[str] = None

# --- Settings Schemas ---
class SettingsBase(BaseSchema):
    block_gambling: bool
    block_social_media: bool
    enforce_safe_search: bool
    screen_time_limit: bool
    alert_on_keywords: bool
    capture_screenshots: bool
    keywords: List[str]

# --- Prediction Schemas ---
class PredictionItem(BaseSchema):
    activity: str
    probability: float

class PredictionResult(BaseSchema):
    current_activity: str
    predictions: List[PredictionItem]

class SettingsCreate(SettingsBase):
    pass

class Settings(SettingsBase):
    id: int

# --- Network Traffic Schemas ---
class NetworkTrafficBase(BaseSchema):
    id: str
    timestamp: str
    source_ip: str
    destination_ip: str
    port: int
    protocol: str
    bytes_transferred: int
    packet_count: int
    latency: int = 0
    is_anomalous: bool = False

class NetworkTrafficCreate(NetworkTrafficBase):
    pass

class NetworkTraffic(NetworkTrafficBase):
    pass

class NetworkAnalysisDetail(BaseSchema):
    type: str
    source: str
    destination: str
    value: str
    id: Optional[str] = None

class NetworkAnalysisResult(BaseSchema):
    summary: str
    anomaly_score: float
    anomalies_detected: int
    details: List[NetworkAnalysisDetail]

# --- Simulation Schemas ---
class SimulationConfig(BaseSchema):
    is_running: bool = False
    traffic_type: str = "HTTP" # HTTP, TCP, UDP
    volume: str = "medium" # low, medium, high
    pattern: str = "steady" # steady, bursty, random
    packet_size_range: List[int] = [500, 1500]
    error_rate: float = 0.0 # 0.0 to 1.0
    latency: int = 0 # milliseconds
    attack_type: Optional[str] = None

class SimulationStats(BaseSchema):
    packets_generated: int
    bytes_generated: int
    errors_simulated: int

class SimulationStatus(BaseSchema):
    is_running: bool
    config: SimulationConfig
    stats: SimulationStats

class SimulationProfileBase(BaseSchema):
    name: str
    description: Optional[str] = None
    traffic_type: str
    volume: str
    pattern: str
    packet_size_range: List[int]
    error_rate: float
    latency: int = 0
    attack_type: Optional[str] = None

class SimulationProfileCreate(SimulationProfileBase):
    pass

class SimulationProfile(SimulationProfileBase):
    id: str
