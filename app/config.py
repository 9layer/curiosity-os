from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL: str = "auto"

    TELEGRAM_BOT_TOKEN: str
    ALLOWED_TELEGRAM_USER_ID: int

    INBOX_TTL_DAYS: int = 14
    EXPLORE_TIMEBOX_MIN: int = 15
    WEEKLY_REVIEW_CRON: str = "0 18 * * SUN"


settings = Settings()