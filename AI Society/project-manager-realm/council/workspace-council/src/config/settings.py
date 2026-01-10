from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    app_name: str = "Workspace Council"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    # Database Settings
    database_url: str = "postgresql+asyncpg://workspace_council:dev_password@localhost:5432/workspace_council"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # Security
    encryption_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
