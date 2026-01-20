from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, Text, Float, BigInteger
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
    details = Column(String)
    ip_address = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # Contextual Activity Recognition
    current_activity = Column(String, nullable=True)
    activity_summary = Column(String, nullable=True)

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
    screen_time_duration_minutes = Column(Integer, default=120)
    alert_on_keywords = Column(Boolean, default=True)
    capture_screenshots = Column(Boolean, default=False)
    keywords = Column(JSON, default=["password", "confidential", "secret", "key"])
    
    # Notification Settings
    email_notifications = Column(Boolean, default=False)
    notification_email = Column(String, nullable=True)
    webhook_url = Column(String, nullable=True)
    quiet_hours_start = Column(String, nullable=True) # e.g. "22:00"
    quiet_hours_end = Column(String, nullable=True) # e.g. "08:00"
    
    # Advanced Notification Settings
    smtp_server = Column(String, nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_username = Column(String, nullable=True)
    smtp_password = Column(String, nullable=True)
    
    sms_notifications = Column(Boolean, default=False)
    twilio_account_sid = Column(String, nullable=True)
    twilio_auth_token = Column(String, nullable=True)
    twilio_from_number = Column(String, nullable=True)
    twilio_to_number = Column(String, nullable=True)

class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    cpu_usage = Column(Float)
    memory_total = Column(BigInteger) # Changed to BigInteger
    memory_used = Column(BigInteger)  # Changed to BigInteger
    memory_percent = Column(Float)
    disk_total = Column(BigInteger)   # Changed to BigInteger
    disk_used = Column(BigInteger)    # Changed to BigInteger
    disk_percent = Column(Float)


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

