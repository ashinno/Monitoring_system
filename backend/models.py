from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, Text
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
