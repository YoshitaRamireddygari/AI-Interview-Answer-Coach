from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings managed via environment variables.
    """
    PROJECT_NAME: str = "AI Interview Answer Coach"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    # CORS Origin configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # SQLite Database connection string
    DATABASE_URL: str = "sqlite:///./interview_coach.db"
    
    # AI API configuration (for Stage 2+)
    GEMINI_API_KEY: str = ""
    AI_PROVIDER: str = "gemini"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
