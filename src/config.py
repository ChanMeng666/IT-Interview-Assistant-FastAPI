from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "True").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./interview_assistant.db")
    
    class Config:
        env_file = ".env"

settings = Settings()
