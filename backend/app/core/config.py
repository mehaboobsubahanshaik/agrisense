from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- app ---
    APP_NAME: str = "AgriSense AI"
    API_V1: str = "/api/v1"
    ENV: str = "development"
    DEV_MODE: bool = True          # returns OTP in the API response, no SMS credits needed
    LOG_LEVEL: str = "INFO"

    # --- security ---
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 30
    CORS_ORIGINS: str = "*"

    # --- otp policy (matches the spec exactly) ---
    OTP_LENGTH: int = 6
    OTP_TTL_SECONDS: int = 300     # 5 minutes
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_SECONDS: int = 30
    OTP_DAILY_LIMIT: int = 15

    # --- rate limiting ---
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW: int = 60

    # --- infrastructure ---
    DATABASE_URL: str = "postgresql+asyncpg://agri:agri@postgres:5432/agrisense"
    REDIS_URL: str = "redis://redis:6379/0"
    CHROMA_URL: str = "http://chromadb:8000"
    CHROMA_ENABLED: bool = True
    AI_SERVICE_URL: str = "http://ai-service:9000"
    UPLOAD_DIR: str = "/app/uploads"

    # --- external providers (all optional: every one has an offline fallback) ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    # data.gov.in Open Government Data platform. The default is the sample key
    # the portal itself publishes: rate limited, fine for a demo. Register a free
    # key at data.gov.in for real use.
    DATA_GOV_API_KEY: str = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
    SCHEME_REFRESH_ENABLED: bool = True

    WEATHER_PROVIDER: str = "open-meteo"   # open-meteo | weatherapi | openweather
    WEATHERAPI_KEY: str = ""
    OPENWEATHER_KEY: str = ""
    SMS_PROVIDER: str = "console"          # console | msg91 | twilio
    MSG91_AUTH_KEY: str = ""
    MSG91_TEMPLATE_ID: str = ""
    MSG91_SENDER: str = "AGRISN"
    TWILIO_SID: str = ""
    TWILIO_TOKEN: str = ""
    TWILIO_FROM: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
