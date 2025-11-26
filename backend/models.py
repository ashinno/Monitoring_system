from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, Text, Float
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    role = Column(String)
    clearance_level = Column(String)
    status = Column(String)
    permissions = Column(JSON)
    hashed_password = Column(String)
    avatar_seed = Column(String, nullable=True)

class Log(Base):
    __tablename__ = "logs"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, default=lambda: datetime.datetime.now().isoformat())
    user = Column(String, index=True)
    activity_type = Column(String)
    risk_level = Column(String)
    description = Column(String)
    details = Column(Text)
    ip_address = Column(String, nullable=True)
    location = Column(String, nullable=True)

class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)
    trigger_field = Column(String)
    trigger_operator = Column(String)
    trigger_value = Column(String)
    action_type = Column(String)
    action_target = Column(String, nullable=True)

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    block_gambling = Column(Boolean, default=True)
    block_social_media = Column(Boolean, default=False)
    enforce_safe_search = Column(Boolean, default=True)
    screen_time_limit = Column(Boolean, default=True)
    alert_on_keywords = Column(Boolean, default=True)
    capture_screenshots = Column(Boolean, default=False)
    keywords = Column(JSON, default=["password", "confidential", "secret", "key"])

class NetworkTraffic(Base):
    __tablename__ = "network_traffic"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, default=lambda: datetime.datetime.now().isoformat())
    source_ip = Column(String, index=True)
    destination_ip = Column(String, index=True)
    port = Column(Integer)
    protocol = Column(String)
    bytes_transferred = Column(Integer)
    packet_count = Column(Integer)
    latency = Column(Integer, default=0) # milliseconds
    is_anomalous = Column(Boolean, default=False)

class SimulationProfile(Base):
    __tablename__ = "simulation_profiles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    traffic_type = Column(String)
    volume = Column(String)
    pattern = Column(String)
    error_rate = Column(Float)
    packet_size_range = Column(JSON) # Store as list [min, max]
    latency = Column(Integer, default=0)
    attack_type = Column(String, nullable=True)

