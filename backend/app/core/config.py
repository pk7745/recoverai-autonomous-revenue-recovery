import os
import re
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "RecoverAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment ('development', 'demo', 'production')
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./recoverai.db")
    
    # JWT Secret Key (Defaults to secure fallback in dev; must be set in production)
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        os.getenv("RAZORPAY_KEY_SECRET", "sec_recoverai_test_secret_key_2026")
    )
    
    # Frontend URL & CORS Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ORIGINS: Optional[str] = os.getenv("CORS_ORIGINS", None)
    
    # Razorpay Test Mode Credentials
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_recoverai2026")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "sec_recoverai_test_secret_key_2026")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "whsec_recoverai_super_secret_webhook_2026")
    
    # AI Engine Provider (gemini, openai, or local heuristic expert agent)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "hybrid_expert")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)

    # Merchant Default Safety Guardrails
    DEFAULT_AUTONOMOUS_LIMIT: float = 5000.0  # Max transaction amount (INR) for automated action
    DEFAULT_MAX_RETRIES: int = 2
    DEFAULT_MIN_RETRY_INTERVAL_MINS: int = 30
    DEFAULT_RISK_THRESHOLD: float = 0.70  # Risk score >= 0.70 automatically escalates

    def get_async_database_url(self) -> str:
        """
        Parses and formats DATABASE_URL for async SQLAlchemy engines.
        Converts Render / Heroku postgres:// or postgresql:// to postgresql+asyncpg://
        and converts sqlite:// to sqlite+aiosqlite://
        """
        url = self.DATABASE_URL.strip()
        
        # PostgreSQL URL format detection
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # SQLite URL format detection
        elif url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            
        # Clean query parameters for asyncpg compatibility
        if "postgresql+asyncpg://" in url and "sslmode=" in url:
            # asyncpg accepts ssl=require instead of sslmode=require
            url = re.sub(r'sslmode=[^&]+', 'ssl=require', url)
            
        return url

    def get_cors_origins(self) -> List[str]:
        """
        Returns allowed CORS origins based on environment.
        In production: restricts strictly to FRONTEND_URL and explicit CORS_ORIGINS.
        In development/demo: includes localhost ports.
        """
        origins: List[str] = []
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL.rstrip("/"))
            
        if self.CORS_ORIGINS:
            for item in self.CORS_ORIGINS.split(","):
                clean = item.strip().rstrip("/")
                if clean and clean not in origins:
                    origins.append(clean)
                    
        if self.ENVIRONMENT != "production":
            defaults = [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
                "http://127.0.0.1:8000"
            ]
            for d in defaults:
                if d not in origins:
                    origins.append(d)
                    
        return origins

    model_config = {"case_sensitive": True, "env_file": ".env", "extra": "ignore"}

settings = Settings()
