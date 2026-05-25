from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Ilm AI API"
    app_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    is_test_mode: bool = True

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_storage_bucket: str = "materials"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ilm_ai"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    cohere_api_key: str = ""

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""

    payme_id: str = ""
    payme_key: str = ""
    click_service_id: str = ""
    click_merchant_id: str = ""
    click_merchant_user_id: str = ""
    click_secret_key: str = ""
    paytech_license_api_key: str = ""

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    sentry_dsn: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = Field(default="https://cloud.langfuse.com")


settings = Settings()
