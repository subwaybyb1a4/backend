from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum as SQLEnum, JSON, Text
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.db.session import Base


class RouteType(str, enum.Enum):
    """Route type enumeration for database"""
    FASTEST = "fastest"
    LEAST_WALKING = "least_walking"
    COMFORT_OPTIMIZED = "comfort_optimized"


class Route(Base):
    """Route model for storing search results"""
    
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    search_group_id = Column(String, index=True, nullable=True)
    route_type = Column(SQLEnum(RouteType), nullable=False)
    
    start_location = Column(String, nullable=False)
    end_location = Column(String, nullable=False)
    
    # Transit information stored as JSON
    transit_info = Column(JSON, nullable=True)
    
    # Scores and metrics
    comfort_score = Column(Float, nullable=True)  # Deprecated
    crowding_score = Column(Float, nullable=True)
    walking_distance = Column(Float, nullable=True)
    stairs_count = Column(Integer, nullable=True)
    
    # LLM-generated explanation
    explanation = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SavedRoute(Base):
    """Saved route model for favorites"""
    
    __tablename__ = "saved_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=True)
    user_id = Column(String, nullable=True, index=True)
    device_id = Column(String, nullable=True, index=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    saved_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
