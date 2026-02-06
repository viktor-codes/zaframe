from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    All variables are loaded from .env file automatically.
    If a variable is not in .env, the default value from Field(default=...) is used.
    """

    # === FastAPI settings ===
    APP_NAME: str = Field(default="ZaFrame API", description="Smart Booking Service API")
    APP_VERSION: str = Field(default="0.1.0", description="Api Version")
    DEBUG: bool = Field(default=False, description="Debugging mode")

    # === Сервер ===
    HOST: str = Field(default="0.0.0.0", description="Host for server startup")
    PORT: int = Field(default=8000, description="Port for server startup")
    
    # === Database (PostgreSQL) ===
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/zaframe",
        description="Connection URL to PostgreSQL through asyncpg"
    )
    
    # === Security (for future JWT authentication) ===
    SECRET_KEY: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        description="Secret key for signing JWT tokens"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Lifetime of access token in minutes"
    )
    
    # === CORS ===
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed origins for CORS (frontend URLs)"
    )
    
    # === Pydantic Settings конфигурация ===
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file
        env_file_encoding="utf-8", # Encoding of .env file
        case_sensitive=True,       # Case sensitivity (APP_NAME != app_name)
        extra="ignore",            # Ignore extra variables in .env
    )


# Create a single instance of settings (singleton pattern).
# Import settings in other modules: from app.core.config import settings
settings = Settings()
