from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables."""

    APP_NAME: str = "AI Email Intelligence Assistant"
    DEBUG: bool = True

    FRONTEND_URL: str = "http://localhost:5173"

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    DATABASE_URL: str = "sqlite:///./email_assistant.db"

    GEMINI_API_KEY: str    # NEW
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_MIN_INTERVAL_SECONDS: float = 13.0

    SYNC_MAX_EMAILS: int = 25

    SECRET_KEY: str
    SESSION_DAYS: int = 7
    COOKIE_SECURE: bool = False  # set to True once the site uses https
    COOKIE_SAMESITE: str = "lax"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )



settings = Settings()