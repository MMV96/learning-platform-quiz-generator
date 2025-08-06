import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service Configuration
    service_name: str = "quiz-generator"
    service_port: int = 8002
    environment: str = "development"
    
    # Database
    mongodb_url: str = "mongodb://admin:password123@localhost:27017/learning_platform?authSource=admin"
    
    # AI API Keys
    anthropic_api_key: str = ""
    
    # AI Configuration
    default_ai_model: str = "claude-3-5-haiku-20241022"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

settings = Settings()