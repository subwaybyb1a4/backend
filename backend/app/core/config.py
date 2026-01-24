from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    ODSAY_API_KEY: str = ""
    OPENAI_API_KEY: str = ""  # For LLM-based explanations
    GEMINI_API_KEY: str = ""  # Alternative LLM option
    
    # LLM Settings
    LLM_PROVIDER: str = "openai"  # Options: "openai", "gemini", "mock"
    LLM_MODEL: str = "gpt-3.5-turbo"  # Default model
    
    # Real-time Transit API (if available)
    REALTIME_TRANSIT_API_KEY: str = ""
    USE_MOCK_REALTIME_DATA: bool = True  # Set to False when real API is available
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "안끼길 API"
    VERSION: str = "1.0.0"
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]
    
    # Route Optimization Settings
    COMFORT_ROUTE_MAX_TIME_DELTA: int = 15  # Max additional minutes for comfort route
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
